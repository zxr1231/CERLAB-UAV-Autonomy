#!/usr/bin/env python3
"""Audit first-valid I1 attempts and summarize paired Legacy/Unique runs."""

import argparse
import csv
import json
import statistics
from pathlib import Path

from exploration_benchmark.aggregate import (first_state_time, load_jsonl,
                                             summarize_run)
from exploration_benchmark.core import atomic_write_json


METRICS = (
    "t80_seconds", "t90_seconds", "t95_seconds", "exploration_duration_sim",
    "exploration_distance_m", "final_mission_distance_m", "free_coverage",
    "surface_coverage", "global_planning_mean_ms", "global_planning_p95_ms",
    "exploration_cpu_mean", "exploration_rss_mean_mib", "mean_rtf",
    "actual_accessible_voxels_per_meter", "actual_accessible_voxels_per_second",
    "low_new_interval_fraction",
)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def first_valid_attempt(task):
    """Use runner artifacts, since a matrix wrapper may die after its child succeeds."""
    for attempt in sorted(task["attempts"], key=lambda item: item["attempt"]):
        location = attempt.get("result_dir")
        if not location:
            continue
        directory = Path(location)
        try:
            run = read_json(directory / "run.json")
            runner = read_json(directory / "runner_result.json")
            summary = read_json(directory / "summary.json")
            resource = read_json(directory / "resource_summary.json")
            trajectory = read_json(directory / "trajectory_alignment_summary.json")
        except (OSError, ValueError):
            continue
        if (run.get("status") == "VERIFIED" and run.get("outcome") == "HOME_REACHED"
                and runner.get("outcome") == "HOME_REACHED"
                and (summary.get("coverage") or {}).get("valid")
                and summary.get("collision", {}).get("status") == "VALID"
                and resource.get("status") == "VALID"
                and trajectory.get("status") == "VALID"):
            return attempt, directory, run, summary
    return None


def latest_coverage(rows, timestamp):
    selected = [row for row in rows if row.get("sim_time") and
                float(row["sim_time"]) <= timestamp]
    return selected[-1] if selected else None


def actual_observation_metrics(directory, run, row):
    actual = read_json(directory / "actual_observation_summary.json")
    if actual.get("status") != "VALID" or actual.get("artificial_clear_included"):
        raise ValueError("actual observation provenance failed: %s" % directory)
    coverage = read_csv(directory / "coverage.csv")
    values = [int(item["accessible_observed"]) for item in coverage]
    if values != sorted(values):
        raise ValueError("nonmonotonic sensor Coverage: %s" % directory)
    events = load_jsonl(directory / "events.jsonl")
    completion = first_state_time(events, {"RETURNING_HOME", "RETURN_BLOCKED"})
    start = float(run["planning_start_sim"])
    if completion is None or completion <= start:
        raise ValueError("missing exploration completion time: %s" % directory)
    initial = latest_coverage(coverage, start)
    final = latest_coverage(coverage, completion)
    if initial is None or final is None:
        raise ValueError("missing sensor Coverage boundary: %s" % directory)
    new_voxels = int(final["accessible_observed"]) - int(initial["accessible_observed"])
    if new_voxels < 0:
        raise ValueError("negative actual observation delta: %s" % directory)
    intervals = read_csv(directory / "actual_observation_intervals.csv")
    eligible = [item for item in intervals
                if item["valid"] == "True" and int(item["global_sequence"]) > 0
                and float(item["executed_distance"]) >= 0.5
                and float(item["start_sim"]) >= start - 1e-6
                and float(item["end_sim"]) <= completion + 1e-6]
    # Exploratory diagnostic: <0.1 m^3 of first observations per flown metre.
    low = [item for item in eligible
           if float(item["actual_new_voxels_per_meter"]) < 100.0]
    rates = [float(item["actual_new_voxels_per_meter"]) for item in eligible]
    distance = row["exploration_distance_m"]
    duration = row["exploration_duration_sim"]
    if not distance or not duration:
        raise ValueError("missing exploration distance/time: %s" % directory)
    return {
        "actual_accessible_new_voxels": new_voxels,
        "actual_accessible_voxels_per_meter": new_voxels / distance,
        "actual_accessible_voxels_per_second": new_voxels / duration,
        "low_new_interval_threshold_voxels_per_meter": 100.0,
        "eligible_moving_interval_count": len(eligible),
        "low_new_interval_count": len(low),
        "low_new_interval_fraction": len(low) / len(eligible) if eligible else None,
        "moving_interval_voxels_per_meter_median": statistics.median(rates) if rates else None,
        "observation_boundary_start_sim": start,
        "observation_boundary_completion_sim": completion,
    }


def distribution(values):
    values = [value for value in values if value is not None]
    return {
        "count": len(values),
        "mean": statistics.mean(values) if values else None,
        "median": statistics.median(values) if values else None,
        "sample_std": statistics.stdev(values) if len(values) > 1 else None,
        "positive_count": sum(value > 0 for value in values),
        "negative_count": sum(value < 0 for value in values),
        "zero_count": sum(value == 0 for value in values),
        "values": values,
    }


def build_report(state_path, expected_commit):
    state = read_json(state_path)
    errors = []
    rows = []
    reference_files = None
    reference_submodules = None
    reference_denominator = None
    for task in state["tasks"]:
        chosen = first_valid_attempt(task)
        if chosen is None:
            errors.append("no verified run: %s" % task["task_id"])
            continue
        attempt, directory, run, summary = chosen
        if (task.get("analysis_primary_attempt") is not None and
                task["analysis_primary_attempt"] != attempt["attempt"]):
            errors.append("primary attempt mismatch: %s" % task["task_id"])
        if run.get("main_commit") != expected_commit or run.get("git_status"):
            errors.append("source version/cleanliness mismatch: %s" % task["task_id"])
        if (run.get("environment_seed") != task["environment_seed"] or
                run.get("planner_seed") != task["planner_seed"] or
                run.get("mode") != "full" or run.get("record_rosbag") is not False or
                run.get("completion_gain_threshold") != 500):
            errors.append("seed/protocol mismatch: %s" % task["task_id"])
        denominator = (summary.get("coverage") or {}).get("accessible_denominator")
        if reference_files is None:
            reference_files = run["files"]
            reference_submodules = run["submodules"]
            reference_denominator = denominator
        elif run["files"] != reference_files or run["submodules"] != reference_submodules:
            errors.append("configuration/submodule mismatch: %s" % task["task_id"])
        if denominator != reference_denominator:
            errors.append("Coverage denominator mismatch: %s" % task["task_id"])
        mode = task["path_gain_mode"]
        if run.get("path_gain_mode") != mode:
            errors.append("gain mode mismatch: %s" % task["task_id"])
        metric = summarize_run(directory, task["task_id"], attempt["attempt"])
        if (not metric["coverage_valid"] or metric["collision_episodes"] != 0
                or not metric["return_success"] or metric["trajectory_status"] != "VALID"
                or metric["resource_status"] != "VALID"):
            errors.append("measurement invalid: %s" % task["task_id"])
        metric.update(actual_observation_metrics(directory, run, metric))
        plans = [item for item in read_csv(directory / "planning.csv")
                 if item["kind"] == "global"]
        metric.update({
            "path_gain_mode": mode,
            "primary_attempt": attempt["attempt"],
            "source_commit": run["main_commit"],
            "global_plan_count": len(plans),
            "unique_selection_count": sum(item.get("selection_gain_mode") == "unique"
                                          for item in plans),
            "unique_valid_count": sum(item.get("unique_evaluation_status") == "valid"
                                      for item in plans),
            "unique_top1_change_count": sum(item.get("unique_top1_changed") == "True"
                                            for item in plans),
            "fallback_count": sum(bool(item.get("gain_fallback_reason")) for item in plans),
        })
        rows.append(metric)
    pairs = []
    for seed in sorted({row["environment_seed"] for row in rows}):
        by_mode = {row["path_gain_mode"]: row for row in rows
                   if row["environment_seed"] == seed}
        if set(by_mode) != {"legacy", "unique_online"}:
            errors.append("incomplete pair for seed %s" % seed)
            continue
        legacy, unique = by_mode["legacy"], by_mode["unique_online"]
        pairs.append({"seed": seed, "legacy_result_dir": legacy["result_dir"],
                      "unique_result_dir": unique["result_dir"],
                      "delta_unique_minus_legacy": {
                          key: (unique[key] - legacy[key]
                                if unique.get(key) is not None and legacy.get(key) is not None
                                else None) for key in METRICS}})
    paired = {key: distribution([item["delta_unique_minus_legacy"][key]
                                 for item in pairs]) for key in METRICS}
    return {
        "schema": "cerlab-i1-paired-pilot-v1",
        "status": "VALID" if len(rows) == 6 and len(pairs) == 3 and not errors else "INVALID",
        "errors": errors,
        "source_commit": expected_commit,
        "batch_config_sha256": state["config_sha256"],
        "primary_policy": state.get("analysis_primary_policy"),
        "run_count": len(rows), "pair_count": len(pairs),
        "low_new_interval_rule": "valid exploration interval, >=0.5 m executed, <100 first-observed full-map voxels/m; exploratory threshold",
        "runs": rows, "pairs": pairs, "paired_delta": paired,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-state", required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = build_report(args.batch_state, args.expected_commit)
    atomic_write_json(args.output, report)
    print(json.dumps({"status": report["status"], "run_count": report["run_count"],
                      "pair_count": report["pair_count"], "errors": report["errors"],
                      "paired_delta": report["paired_delta"]}, indent=2, sort_keys=True))
    return 0 if report["status"] == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
