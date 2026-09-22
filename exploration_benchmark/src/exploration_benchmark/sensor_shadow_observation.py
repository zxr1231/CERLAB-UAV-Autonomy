"""Build and compare R2 mapper-matched frozen-map shadow predictions."""

import csv
import json
import os
import statistics
import time
from pathlib import Path

from exploration_benchmark.core import atomic_write_json
from exploration_benchmark.observation_alignment import (comparable_actual_set,
                                                          set_metrics, spearman)
from exploration_benchmark.predicted_observation import sample_odom_prefix
from exploration_benchmark.r1_snapshot import load_frozen_map, load_snapshot
from exploration_benchmark.r1_visibility import LegacyVisibilityConfig, visible_set_sha256
from exploration_benchmark.sensor_shadow import (CameraShadowConfig,
                                                  visible_shadow_union)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _jsonl_index(path):
    return {int(row["interval_id"]): row for row in
            (json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()
             if line.strip())}


def _mean(values):
    values = [value for value in values if value is not None]
    return statistics.mean(values) if values else None


def _median(values):
    values = [value for value in values if value is not None]
    return statistics.median(values) if values else None


def _pearson(first, second):
    if len(first) < 2 or len(first) != len(second):
        return None
    first_mean, second_mean = statistics.mean(first), statistics.mean(second)
    numerator = sum((a-first_mean)*(b-second_mean) for a, b in zip(first, second))
    first_norm = sum((a-first_mean)**2 for a in first) ** 0.5
    second_norm = sum((b-second_mean)**2 for b in second) ** 0.5
    return numerator/(first_norm*second_norm) if first_norm and second_norm else None


def _write_jsonl(path, records):
    temporary = Path(str(path)+".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, sort_keys=True)+"\n")
        stream.flush(); os.fsync(stream.fileno())
    os.replace(str(temporary), str(path))


def build_sensor_shadow_observation(run_directory, snapshot_root, mapping_config,
                                    spacing=0.1, yaw_spacing=0.05,
                                    evaluation_pixel_skip=None):
    run_directory = Path(run_directory); snapshot_root = Path(snapshot_root)
    intervals = _read_csv(run_directory/"execution_intervals.csv")
    trajectory = _read_csv(run_directory/"trajectory.csv")
    odom = {}
    for row in trajectory:
        identifier = int(row.get("execution_interval_id") or 0)
        if identifier:
            odom.setdefault(identifier, []).append(row)
    records, errors = [], []
    start = time.monotonic()
    for interval in intervals:
        identifier = int(interval["interval_id"])
        global_sequence = int(interval["global_sequence"])
        if global_sequence <= 0:
            records.append({"interval_id": identifier, "status": "SKIPPED_RETURN",
                            "errors": [], "addresses": []})
            continue
        interval_errors = []
        snapshot_path = snapshot_root/("execution_%06d" % identifier)
        if not snapshot_path.is_dir():
            interval_errors.append("missing execution-start snapshot")
        samples = sample_odom_prefix(odom.get(identifier, []), spacing, yaw_spacing)
        if not samples:
            interval_errors.append("execution interval has no odometry prefix")
        addresses = set(); config = None; grid = None
        interval_start = time.monotonic()
        if not interval_errors:
            snapshot = load_snapshot(snapshot_path)
            grid = load_frozen_map(snapshot_path, snapshot)
            region = snapshot["planner"]["planning_region"]
            config = CameraShadowConfig.from_yaml(
                mapping_config, region["min"], region["max"], evaluation_pixel_skip)
            addresses = visible_shadow_union(grid, samples, config)
        errors.extend("interval %d: %s" % (identifier, item) for item in interval_errors)
        ordered = sorted(addresses)
        records.append({
            "interval_id": identifier,
            "trajectory_id": int(interval["trajectory_id"]),
            "global_sequence": global_sequence,
            "status": "VALID" if not interval_errors else "INVALID",
            "errors": interval_errors,
            "sample_count": len(samples),
            "predicted_unknown_voxels": len(ordered),
            "set_sha256": visible_set_sha256(ordered),
            "wall_seconds": time.monotonic()-interval_start,
            "map_version": None if grid is None else grid.version,
            "model": None if config is None else config.provenance(),
            "addresses": ordered,
        })
    return {
        "schema": "cerlab-r2-sensor-shadow-v1",
        "run_directory": str(run_directory),
        "snapshot_root": str(snapshot_root),
        "mapping_config": str(Path(mapping_config).resolve()),
        "spacing": spacing, "yaw_spacing": yaw_spacing,
        "interval_count": len(records),
        "valid_interval_count": sum(row["status"] == "VALID" for row in records),
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
        "total_wall_seconds": time.monotonic()-start,
        "intervals": records,
    }


def write_sensor_shadow_observation(run_directory, snapshot_root, mapping_config,
                                    output_directory=None, spacing=0.1,
                                    yaw_spacing=0.05, evaluation_pixel_skip=None):
    output = Path(output_directory) if output_directory else Path(run_directory)
    output.mkdir(parents=True, exist_ok=True)
    result = build_sensor_shadow_observation(
        run_directory, snapshot_root, mapping_config, spacing, yaw_spacing,
        evaluation_pixel_skip)
    summary = {key: value for key, value in result.items() if key != "intervals"}
    atomic_write_json(output/"sensor_shadow_summary.json", summary)
    _write_jsonl(output/"sensor_shadow_sets.jsonl", result["intervals"])
    return summary


def _assign_stages(records):
    ordered = sorted(records, key=lambda row: row["interval_id"])
    count = len(ordered)
    for index, row in enumerate(ordered):
        third = min(2, (3*index)//count) if count else 0
        row["stage"] = ("early", "middle", "late")[third]
    return ordered


def _model_summary(records, key):
    metrics = [row[key] for row in records]
    predicted = [metric["predicted_count"] for metric in metrics]
    actual = [metric["actual_count"] for metric in metrics]
    return {
        "interval_count": len(metrics),
        "precision_mean": _mean([item["precision"] for item in metrics]),
        "precision_median": _median([item["precision"] for item in metrics]),
        "recall_mean": _mean([item["recall"] for item in metrics]),
        "recall_median": _median([item["recall"] for item in metrics]),
        "jaccard_mean": _mean([item["jaccard"] for item in metrics]),
        "jaccard_median": _median([item["jaccard"] for item in metrics]),
        "count_pearson": _pearson(predicted, actual),
        "count_spearman": spearman(predicted, actual),
    }


def compare_sensor_shadow(run_directory, snapshot_root):
    run_directory = Path(run_directory); snapshot_root = Path(snapshot_root)
    actual = _jsonl_index(run_directory/"actual_observation_sets.jsonl")
    legacy = _jsonl_index(run_directory/"predicted_observation_sets.jsonl")
    shadow = _jsonl_index(run_directory/"sensor_shadow_sets.jsonl")
    identifier_sets = (set(actual), set(legacy), set(shadow))
    common = sorted(set.intersection(*identifier_sets))
    records, errors = [], []
    if not all(items == identifier_sets[0] for items in identifier_sets[1:]):
        errors.append("actual, legacy and shadow interval IDs differ")
    for identifier in common:
        if legacy[identifier].get("status") != "VALID" or shadow[identifier].get("status") != "VALID":
            continue
        snapshot_path = snapshot_root/("execution_%06d" % identifier)
        snapshot = load_snapshot(snapshot_path)
        grid = load_frozen_map(snapshot_path, snapshot)
        if int(shadow[identifier].get("map_version", -1)) != grid.version:
            errors.append("interval %d shadow map version mismatch" % identifier)
            continue
        legacy_config = LegacyVisibilityConfig.from_planner(snapshot["planner"])
        comparable, out_of_map = comparable_actual_set(
            actual[identifier]["addresses"], grid, legacy_config)
        if out_of_map or not comparable:
            errors.append("interval %d has invalid/empty comparable actual set" % identifier)
            continue
        legacy_addresses = legacy[identifier]["layers"]["odom_prefix"]["addresses"]
        records.append({
            "interval_id": identifier,
            "actual_full_count": len(actual[identifier]["addresses"]),
            "actual_comparable_count": len(comparable),
            "legacy": set_metrics(legacy_addresses, comparable),
            "sensor_shadow": set_metrics(shadow[identifier]["addresses"], comparable),
            "shadow_wall_seconds": shadow[identifier]["wall_seconds"],
        })
    records = _assign_stages(records)
    by_stage = {}
    for stage in ("early", "middle", "late"):
        subset = [row for row in records if row["stage"] == stage]
        by_stage[stage] = {
            "legacy": _model_summary(subset, "legacy"),
            "sensor_shadow": _model_summary(subset, "sensor_shadow"),
        }
    legacy_summary = _model_summary(records, "legacy")
    shadow_summary = _model_summary(records, "sensor_shadow")
    return {
        "schema": "cerlab-r2-shadow-comparison-v1",
        "status": "VALID" if records and not errors else "INVALID",
        "errors": errors,
        "eligible_interval_count": len(records),
        "stage_definition": "equal_count_ordered_execution_intervals",
        "overall": {"legacy": legacy_summary, "sensor_shadow": shadow_summary},
        "delta_shadow_minus_legacy": {
            key: (None if shadow_summary[key] is None or legacy_summary[key] is None
                  else shadow_summary[key]-legacy_summary[key])
            for key in ("precision_mean", "recall_mean", "jaccard_mean",
                        "count_pearson", "count_spearman")
        },
        "by_stage": by_stage,
        "intervals": records,
    }


def write_sensor_shadow_comparison(run_directory, snapshot_root,
                                   output_directory=None):
    output = Path(output_directory) if output_directory else Path(run_directory)
    result = compare_sensor_shadow(run_directory, snapshot_root)
    summary = {key: value for key, value in result.items() if key != "intervals"}
    atomic_write_json(output/"sensor_shadow_comparison_summary.json", summary)
    atomic_write_json(output/"sensor_shadow_comparison_intervals.json",
                      {"schema": result["schema"], "intervals": result["intervals"]})
    return summary
