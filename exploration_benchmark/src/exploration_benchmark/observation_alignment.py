"""Align R2 predicted layers with timestamp-canonical actual observations."""

import csv
import json
import math
import statistics
from pathlib import Path

from exploration_benchmark.core import atomic_write_json
from exploration_benchmark.r1_snapshot import load_frozen_map, load_snapshot
from exploration_benchmark.r1_visibility import LegacyVisibilityConfig


LAYERS = ("prm_raw", "prm_shortcut", "bspline", "odom_prefix")


def set_metrics(predicted, actual):
    predicted = set(predicted); actual = set(actual)
    intersection = len(predicted & actual)
    union = len(predicted | actual)
    return {
        "predicted_count": len(predicted),
        "actual_count": len(actual),
        "intersection_count": intersection,
        "precision": intersection/len(predicted) if predicted else None,
        "recall": intersection/len(actual) if actual else None,
        "jaccard": intersection/union if union else 1.0,
        "count_error": len(predicted)-len(actual),
        "absolute_count_error": abs(len(predicted)-len(actual)),
        "relative_count_error": (abs(len(predicted)-len(actual))/len(actual)
                                 if actual else None),
    }


def transition_metrics(source, target):
    source = set(source); target = set(target)
    intersection = len(source & target)
    union = len(source | target)
    return {
        "source_count": len(source),
        "target_count": len(target),
        "intersection_count": intersection,
        "source_retention": intersection/len(source) if source else None,
        "target_novel_fraction": len(target-source)/len(target) if target else None,
        "jaccard": intersection/union if union else 1.0,
    }


def staleness_band(seconds):
    if seconds is None or not math.isfinite(seconds) or seconds < -1e-6:
        return "invalid"
    if seconds <= 2.0:
        return "fresh"
    if seconds <= 10.0:
        return "moderate"
    return "stale"


def comparable_actual_set(addresses, grid, config):
    comparable = set()
    out_of_map = 0
    for address in addresses:
        address = int(address)
        if address < 0 or address >= grid.voxel_count:
            out_of_map += 1
            continue
        position = grid.position(grid.index(address))
        in_region = all(config.planning_min[axis] <= position[axis] <=
                        config.planning_max[axis] for axis in range(3))
        if in_region and grid.is_unknown(address) and not grid.is_inflated(address):
            comparable.add(address)
    return comparable, out_of_map


def _rankdata(values):
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(order):
        end = cursor + 1
        while end < len(order) and values[order[end]] == values[order[cursor]]:
            end += 1
        rank = (cursor + end - 1) / 2.0
        for index in order[cursor:end]:
            ranks[index] = rank
        cursor = end
    return ranks


def _pearson(first, second):
    if len(first) < 2 or len(first) != len(second):
        return None
    first_mean = statistics.mean(first); second_mean = statistics.mean(second)
    numerator = sum((a-first_mean)*(b-second_mean) for a, b in zip(first, second))
    first_norm = math.sqrt(sum((a-first_mean)**2 for a in first))
    second_norm = math.sqrt(sum((b-second_mean)**2 for b in second))
    return numerator/(first_norm*second_norm) if first_norm and second_norm else None


def spearman(first, second):
    return _pearson(_rankdata(first), _rankdata(second))


def _jsonl_index(path):
    rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip()]
    return {int(row["interval_id"]): row for row in rows}


def _mean(values):
    values = [value for value in values if value is not None]
    return statistics.mean(values) if values else None


def _median(values):
    values = [value for value in values if value is not None]
    return statistics.median(values) if values else None


def build_alignment(run_directory, snapshot_root):
    run_directory = Path(run_directory); snapshot_root = Path(snapshot_root)
    actual = _jsonl_index(run_directory / "actual_observation_sets.jsonl")
    predicted = _jsonl_index(run_directory / "predicted_observation_sets.jsonl")
    with (run_directory / "actual_observation_intervals.csv").open(
            newline="", encoding="utf-8") as stream:
        actual_rows = {int(row["interval_id"]): row for row in csv.DictReader(stream)}
    with (run_directory / "planning.csv").open(newline="", encoding="utf-8") as stream:
        planning = list(csv.DictReader(stream))
    global_times = {int(row["sequence"]): float(row["sim_time"]) for row in planning
                    if row["kind"] == "global" and row["sequence"]}
    local_times = {int(row["trajectory_id"]): float(row["trajectory_start_sim"])
                   for row in planning if row["kind"] == "local" and row["trajectory_id"]
                   and row["success"].lower() == "true"}

    errors = []
    all_ids = sorted(set(actual) | set(predicted))
    if set(actual) != set(predicted):
        errors.append("actual and predicted interval IDs differ")
    snapshot_cache = {}
    records = []
    for interval_id in all_ids:
        interval_errors = []
        actual_record = actual.get(interval_id)
        predicted_record = predicted.get(interval_id)
        actual_row = actual_rows.get(interval_id)
        if actual_record is None or predicted_record is None or actual_row is None:
            interval_errors.append("missing actual/predicted/interval record")
            records.append({"interval_id": interval_id, "valid": False,
                            "analysis_eligible": False, "errors": interval_errors})
            errors.extend("interval %d: %s" % (interval_id, item) for item in interval_errors)
            continue
        global_sequence = int(predicted_record["global_sequence"])
        if predicted_record.get("status") != "VALID":
            interval_errors.append("predicted interval is not valid")
        if actual_row["valid"].lower() != "true":
            interval_errors.append("actual interval is not valid")
        snapshot_path = snapshot_root / ("execution_%06d" % interval_id)
        if interval_id not in snapshot_cache:
            if not snapshot_path.is_dir():
                interval_errors.append("missing global snapshot")
            else:
                snapshot = load_snapshot(snapshot_path)
                snapshot_cache[interval_id] = (
                    load_frozen_map(snapshot_path, snapshot),
                    LegacyVisibilityConfig.from_planner(snapshot["planner"]))
        if interval_id not in snapshot_cache:
            records.append({"interval_id": interval_id, "global_sequence": global_sequence,
                            "valid": False, "analysis_eligible": False,
                            "errors": interval_errors})
            errors.extend("interval %d: %s" % (interval_id, item) for item in interval_errors)
            continue
        grid, config = snapshot_cache[interval_id]
        comparable, out_of_map = comparable_actual_set(actual_record["addresses"], grid, config)
        if out_of_map:
            interval_errors.append("actual set contains %d out-of-map addresses" % out_of_map)
        global_time = global_times.get(global_sequence)
        local_time = local_times.get(interval_id)
        plan_to_execution_seconds = (None if global_time is None or local_time is None
                                     else local_time-global_time)
        band = staleness_band(plan_to_execution_seconds)
        if band == "invalid":
            interval_errors.append("invalid or missing plan-to-execution time")
        layer_sets = {layer: set(predicted_record.get("layers", {}).get(layer, {})
                                 .get("addresses", [])) for layer in LAYERS}
        missing_layers = [layer for layer in LAYERS if layer not in predicted_record.get("layers", {})]
        if missing_layers:
            interval_errors.append("missing predicted layers: " + ",".join(missing_layers))
        layer_metrics = {layer: set_metrics(layer_sets[layer], comparable) for layer in LAYERS}
        transitions = {
            "prm_raw_to_shortcut": transition_metrics(layer_sets["prm_raw"],
                                                        layer_sets["prm_shortcut"]),
            "shortcut_to_bspline": transition_metrics(layer_sets["prm_shortcut"],
                                                        layer_sets["bspline"]),
            "bspline_to_odom_prefix": transition_metrics(layer_sets["bspline"],
                                                           layer_sets["odom_prefix"]),
        }
        version_delta = (None if predicted_record.get("local_start_map_version") is None
                         else int(predicted_record["local_start_map_version"])-
                         int(predicted_record["snapshot_map_version"]))
        snapshot_fresh = version_delta is not None and 0 <= version_delta <= 2
        analysis_eligible = (not interval_errors and snapshot_fresh and
                             len(comparable) > 0 and len(layer_sets["odom_prefix"]) > 0 and
                             int(actual_row["odom_count"]) >= 2)
        record = {
            "interval_id": interval_id,
            "global_sequence": global_sequence,
            "plan_to_execution_seconds": plan_to_execution_seconds,
            "plan_to_execution_band": band,
            "execution_snapshot_map_version_delta": version_delta,
            "execution_snapshot_fresh": snapshot_fresh,
            "actual_full_count": len(actual_record["addresses"]),
            "actual_comparable_count": len(comparable),
            "actual_filter_retention": (len(comparable)/len(actual_record["addresses"])
                                        if actual_record["addresses"] else None),
            "boundary_mismatch_count": int(actual_row["logged_association_mismatch_count"]),
            "valid": not interval_errors,
            "analysis_eligible": analysis_eligible,
            "errors": interval_errors,
            "layers": layer_metrics,
            "transitions": transitions,
        }
        records.append(record)
        errors.extend("interval %d: %s" % (interval_id, item) for item in interval_errors)

    eligible = [record for record in records if record.get("analysis_eligible")]
    layer_summary = {}
    for layer in LAYERS:
        metrics = [record["layers"][layer] for record in eligible]
        predicted_counts = [metric["predicted_count"] for metric in metrics]
        actual_counts = [metric["actual_count"] for metric in metrics]
        layer_summary[layer] = {
            "interval_count": len(metrics),
            "precision_mean": _mean([metric["precision"] for metric in metrics]),
            "precision_median": _median([metric["precision"] for metric in metrics]),
            "recall_mean": _mean([metric["recall"] for metric in metrics]),
            "recall_median": _median([metric["recall"] for metric in metrics]),
            "jaccard_mean": _mean([metric["jaccard"] for metric in metrics]),
            "jaccard_median": _median([metric["jaccard"] for metric in metrics]),
            "count_pearson": _pearson(predicted_counts, actual_counts),
            "count_spearman": spearman(predicted_counts, actual_counts),
        }
    transition_summary = {}
    for name in ("prm_raw_to_shortcut", "shortcut_to_bspline",
                 "bspline_to_odom_prefix"):
        metrics = [record["transitions"][name] for record in eligible]
        transition_summary[name] = {
            "interval_count": len(metrics),
            "source_retention_mean": _mean([metric["source_retention"]
                                             for metric in metrics]),
            "source_retention_median": _median([metric["source_retention"]
                                                 for metric in metrics]),
            "target_novel_fraction_mean": _mean([metric["target_novel_fraction"]
                                                  for metric in metrics]),
            "jaccard_mean": _mean([metric["jaccard"] for metric in metrics]),
            "jaccard_median": _median([metric["jaccard"] for metric in metrics]),
        }
    return {
        "schema": "cerlab-r2-observation-alignment-v1",
        "run_directory": str(run_directory),
        "snapshot_root": str(snapshot_root),
        "plan_to_execution_fresh_threshold_seconds": 2.0,
        "plan_to_execution_moderate_threshold_seconds": 10.0,
        "execution_snapshot_max_version_delta": 2,
        "interval_count": len(records),
        "valid_interval_count": sum(record.get("valid", False) for record in records),
        "analysis_eligible_interval_count": len(eligible),
        "plan_to_execution_band_counts": {
            band: sum(record.get("plan_to_execution_band") == band for record in records)
            for band in ("fresh", "moderate", "stale", "invalid")},
        "fresh_execution_snapshot_count": sum(record.get("execution_snapshot_fresh", False)
                                              for record in records),
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
        "eligible_layer_summary": layer_summary,
        "eligible_transition_summary": transition_summary,
        "actual_filter_retention_mean": _mean([
            record.get("actual_filter_retention") for record in eligible]),
        "boundary_mismatch_count": sum(record.get("boundary_mismatch_count", 0)
                                       for record in records),
        "execution_snapshot_map_version_delta_max": max(
            (record.get("execution_snapshot_map_version_delta")
             for record in records
             if record.get("execution_snapshot_map_version_delta") is not None),
            default=None),
        "intervals": records,
    }


def write_alignment(run_directory, snapshot_root, output_directory=None):
    output_directory = Path(output_directory) if output_directory else Path(run_directory)
    result = build_alignment(run_directory, snapshot_root)
    summary = {key: value for key, value in result.items() if key != "intervals"}
    atomic_write_json(output_directory / "observation_alignment_summary.json", summary)
    atomic_write_json(output_directory / "observation_alignment_intervals.json",
                      {"schema": result["schema"], "intervals": result["intervals"]})
    return summary
