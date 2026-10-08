#!/usr/bin/env python3
"""Read-only I2-00 diagnosis of I1 planning, execution and sensor logs."""

import argparse
import bisect
import csv
import hashlib
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from exploration_benchmark.core import atomic_write_json


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip()]


def median(values):
    values = [value for value in values if value is not None]
    return statistics.median(values) if values else None


def polyline_length(points):
    return sum(math.dist(first, second) for first, second in zip(points, points[1:]))


def coverage_lookup(rows):
    ordered = sorted((float(row["sim_time"]), float(row["free_coverage"]))
                     for row in rows if row.get("free_coverage"))
    times = [item[0] for item in ordered]
    values = [item[1] for item in ordered]

    def at(timestamp):
        index = bisect.bisect_right(times, timestamp) - 1
        return values[index] if index >= 0 else None

    return at


def coverage_stage(value):
    if value is None:
        return "unknown"
    if value < 0.8:
        return "before_80"
    if value < 0.95:
        return "from_80_to_95"
    return "at_least_95"


def nearest_odom(rows, timestamp):
    return min(rows, key=lambda item: abs(float(item["sim_time"])-timestamp))


def longest_rapid_block(plans, paths, trajectory, coverage_at, log_lines):
    if not plans:
        return None
    blocks = []
    start = 0
    for index in range(len(plans)-1):
        gap = float(plans[index+1]["sim_time"])-float(plans[index]["sim_time"])
        if gap >= 1.0:
            blocks.append((start, index))
            start = index+1
    blocks.append((start, len(plans)-1))
    first, last = max(blocks, key=lambda pair: pair[1]-pair[0])
    selected = plans[first:last+1]
    start_time = float(selected[0]["sim_time"])
    end_time = float(selected[-1]["sim_time"])
    endpoints = []
    for item in selected:
        path = paths.get(("prm", int(item["sequence"])))
        if path and path.get("points"):
            endpoints.append(tuple(round(float(value), 3) for value in path["points"][-1]))
    before = nearest_odom(trajectory, start_time)
    after = nearest_odom(trajectory, end_time)
    xyz = lambda item: [float(item[axis]) for axis in ("x", "y", "z")]
    preceding_unsafe = 0
    matching_log_plans = 0
    for index, line in enumerate(log_lines):
        match = re.search(r",\s*([0-9]+(?:\.[0-9]+)?)\]: \[AutoFlight\] Planning wall time:", line)
        if not match:
            continue
        logged_time = float(match.group(1))
        if start_time <= logged_time <= end_time+0.2:
            matching_log_plans += 1
            if index > 0 and "The current local goal is unsafe" in log_lines[index-1]:
                preceding_unsafe += 1
    return {
        "plan_count": len(selected),
        "sequence_first": int(selected[0]["sequence"]),
        "sequence_last": int(selected[-1]["sequence"]),
        "start_sim": start_time,
        "end_sim": end_time,
        "duration_sim": end_time-start_time,
        "coverage_start": coverage_at(start_time),
        "coverage_end": coverage_at(end_time),
        "distinct_selected_goal_count": len(set(endpoints)),
        "selected_goal_examples": [list(item) for item, _ in Counter(endpoints).most_common(3)],
        "legacy_unique_same_candidate_count": sum(
            item.get("legacy_selected_candidate") == item.get("unique_selected_candidate")
            for item in selected),
        "selected_path_length_median": median([
            float(item["selected_path_length"]) for item in selected
            if item.get("selected_path_length")]),
        "odom_position_start": xyz(before),
        "odom_position_end": xyz(after),
        "odom_net_displacement": math.dist(xyz(before), xyz(after)),
        "odom_cumulative_distance_increment": (float(after["cumulative_distance"])-
                                                float(before["cumulative_distance"])),
        "matching_log_plan_count": matching_log_plans,
        "preceded_by_local_goal_unsafe_count": preceding_unsafe,
    }


def summarize_run(task, directory):
    planning = read_csv(directory / "planning.csv")
    global_plans = [row for row in planning if row["kind"] == "global"]
    all_intervals = read_csv(directory / "execution_intervals.csv")
    all_actual = read_csv(directory / "actual_observation_intervals.csv")
    if ({row["interval_id"] for row in all_intervals} !=
            {row["interval_id"] for row in all_actual} or
            any(row["valid"] != "True" for row in all_actual)):
        raise ValueError("execution/actual interval integrity failure: %s" % directory)
    intervals = [row for row in all_intervals if int(row["global_sequence"]) > 0]
    actual = {int(row["interval_id"]): row for row in all_actual}
    paths = {(row["kind"], int(row["id"])): row
             for row in read_jsonl(directory / "planned_paths.jsonl")}
    alignment = read_csv(directory / "trajectory_alignment.csv")
    trajectory = read_csv(directory / "trajectory.csv")
    log_lines = (directory / "exploration.log").read_text(
        encoding="utf-8", errors="replace").splitlines()
    coverage_at = coverage_lookup(read_csv(directory / "coverage.csv"))
    sequences = [int(row["sequence"]) for row in global_plans]
    if len(sequences) != len(set(sequences)) or any(
            ("prm", sequence) not in paths or ("prm_raw", sequence) not in paths
            for sequence in sequences):
        raise ValueError("global-plan path integrity failure: %s" % directory)

    intervals_by_global = defaultdict(list)
    for row in intervals:
        intervals_by_global[int(row["global_sequence"])].append(row)
    alignment_by_global = defaultdict(list)
    for row in alignment:
        if row.get("phase") == "exploration" and int(row.get("global_sequence") or 0) > 0:
            alignment_by_global[int(row["global_sequence"])].append(row)

    records = []
    for row in global_plans:
        sequence = int(row["sequence"])
        linked = intervals_by_global.get(sequence, [])
        actual_rows = [actual[int(item["interval_id"])] for item in linked
                       if int(item["interval_id"]) in actual]
        distance = sum(float(item["executed_distance"]) for item in linked)
        actual_new = sum(int(item["actual_new_voxels"]) for item in actual_rows)
        raw = paths.get(("prm_raw", sequence), {}).get("points", [])
        shortcut = paths.get(("prm", sequence), {}).get("points", [])
        raw_length = polyline_length(raw)
        shortcut_length = polyline_length(shortcut)
        aligned = alignment_by_global.get(sequence, [])
        odom_bspline = [float(item["odom_to_bspline_mean_distance"])
                        for item in aligned if item.get("odom_to_bspline_mean_distance")]
        records.append({
            "sequence": sequence,
            "sim_time": float(row["sim_time"]),
            "coverage": coverage_at(float(row["sim_time"])),
            "stage": coverage_stage(coverage_at(float(row["sim_time"]))),
            "success": row["success"] == "True",
            "candidate_count": int(row["candidate_paths"]),
            "changed_top1": row.get("unique_top1_changed") == "True",
            "legacy_selected_candidate": (int(row["legacy_selected_candidate"])
                                          if row.get("legacy_selected_candidate") else None),
            "unique_selected_candidate": (int(row["unique_selected_candidate"])
                                          if row.get("unique_selected_candidate") else None),
            "legacy_best_path_gain": (int(row["best_path_gain"])
                                      if row.get("best_path_gain") else None),
            "selected_unique_gain": (int(row["selected_unique_gain"])
                                     if row.get("selected_unique_gain") else None),
            "selected_duplicate_ratio": (float(row["selected_duplicate_ratio"])
                                         if row.get("selected_duplicate_ratio") else None),
            "raw_prm_length": raw_length,
            "shortcut_prm_length": shortcut_length,
            "shortcut_length_retention": (shortcut_length/raw_length
                                          if raw_length > 0 else None),
            "selected_path_length_logged": (float(row["selected_path_length"])
                                            if row.get("selected_path_length") else None),
            "execution_interval_count": len(linked),
            "executed_interval_with_odom_count": sum(int(item["odom_count"]) >= 2
                                                    for item in linked),
            "executed_distance": distance,
            "actual_first_observed_full_map_voxels": actual_new,
            "actual_full_map_voxels_per_executed_meter": (actual_new/distance
                                                          if distance >= 0.5 else None),
            "bspline_alignment_count": len(aligned),
            "odom_to_bspline_mean_distance_median": median(odom_bspline),
        })
    return {
        "task_id": task["task_id"],
        "result_dir": str(directory),
        "global_plan_count": len(records),
        "successful_global_plan_count": sum(item["success"] for item in records),
        "changed_top1_count": sum(item["changed_top1"] for item in records),
        "changed_top1_by_stage": dict(Counter(item["stage"] for item in records
                                              if item["changed_top1"])),
        "global_plan_by_stage": dict(Counter(item["stage"] for item in records)),
        "changed_with_execution_count": sum(item["changed_top1"] and
                                            item["execution_interval_count"] > 0
                                            for item in records),
        "changed_with_at_least_half_meter_count": sum(
            item["changed_top1"] and item["executed_distance"] >= 0.5
            for item in records),
        "plan_without_execution_count": sum(item["execution_interval_count"] == 0
                                            for item in records),
        "median_changed_full_map_voxels_per_meter": median([
            item["actual_full_map_voxels_per_executed_meter"] for item in records
            if item["changed_top1"]]),
        "median_unchanged_full_map_voxels_per_meter": median([
            item["actual_full_map_voxels_per_executed_meter"] for item in records
            if not item["changed_top1"]]),
        "median_changed_shortcut_length_retention": median([
            item["shortcut_length_retention"] for item in records
            if item["changed_top1"]]),
        "median_unchanged_shortcut_length_retention": median([
            item["shortcut_length_retention"] for item in records
            if not item["changed_top1"]]),
        "median_changed_odom_bspline_distance": median([
            item["odom_to_bspline_mean_distance_median"] for item in records
            if item["changed_top1"]]),
        "median_unchanged_odom_bspline_distance": median([
            item["odom_to_bspline_mean_distance_median"] for item in records
            if not item["changed_top1"]]),
        "log_local_goal_unsafe_count": sum("The current local goal is unsafe" in line
                                           for line in log_lines),
        "rapid_replan_block": longest_rapid_block(global_plans, paths, trajectory,
                                                  coverage_at, log_lines),
        "plans": records,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-state", required=True)
    parser.add_argument("--r2-model-comparison", required=True)
    parser.add_argument("--i1-reference-agreement", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    state = read_json(args.batch_state)
    summaries = []
    for task in state["tasks"]:
        if not task.get("analysis_primary_result_dir"):
            raise ValueError("missing primary result: %s" % task["task_id"])
        summaries.append(summarize_run(task, Path(task["analysis_primary_result_dir"])))
    model = read_json(args.r2_model_comparison)
    reference = read_json(args.i1_reference_agreement)
    if model["status"] != "VALID" or reference["status"] != "MATCH":
        raise ValueError("reference evidence is invalid")
    report = {
        "schema": "cerlab-i2-00-execution-diagnosis-v1",
        "source_corpus": "six I1-06 primary runs, existing R2 model comparison and I1 frozen agreement",
        "batch_state_sha256": hashlib.sha256(Path(args.batch_state).read_bytes()).hexdigest(),
        "r2_model_comparison": {
            "eligible_interval_count": model["eligible_interval_count"],
            "planner_proxy": model["overall"]["legacy"],
            "mapper_shadow": model["overall"]["sensor_shadow"],
        },
        "i1_reference_agreement": {
            "snapshot_count": reference["snapshot_count"],
            "candidate_count": reference["candidate_count"],
            "matched_candidate_count": reference["matched_candidate_count"],
        },
        "i1_candidate_map_snapshots_available": any(
            (Path(task["analysis_primary_result_dir"]) / "snapshots").is_dir()
            for task in state["tasks"]),
        "counterfactual_unselected_actual_observation_available": False,
        "runs": summaries,
    }
    atomic_write_json(args.output, report)
    concise = [{key: item[key] for key in (
        "task_id", "global_plan_count", "changed_top1_count",
        "changed_with_execution_count", "changed_with_at_least_half_meter_count",
        "plan_without_execution_count", "log_local_goal_unsafe_count",
        "rapid_replan_block")} for item in summaries]
    print(json.dumps(concise, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
