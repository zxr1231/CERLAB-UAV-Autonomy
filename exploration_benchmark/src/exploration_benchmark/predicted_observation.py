"""Construct R2 predicted observation sets at four path/execution layers."""

import csv
import json
import math
import os
from pathlib import Path

from exploration_benchmark.core import atomic_write_json
from exploration_benchmark.r1_path_gain import sample_candidate_path
from exploration_benchmark.r1_snapshot import load_frozen_map, load_snapshot
from exploration_benchmark.r1_visibility import (LegacyVisibilityConfig,
                                                  visible_set_sha256,
                                                  visible_unknown_voxels)


LAYERS = ("prm_raw", "prm_shortcut", "bspline", "odom_prefix")


def _angle_difference(first, second):
    return abs((first-second+math.pi) % (2*math.pi)-math.pi)


def sample_constant_yaw_polyline(points, yaw, spacing):
    waypoints = [{"position": list(point), "yaw": float(yaw)} for point in points]
    return sample_candidate_path(waypoints, spacing)


def sample_odom_prefix(rows, spacing=0.25, yaw_spacing=0.1):
    if spacing <= 0 or yaw_spacing <= 0:
        raise ValueError("odom sampling thresholds must be positive")
    if not rows:
        return []
    samples = []
    last_position = None
    last_yaw = None
    for row in rows:
        position = tuple(float(row[axis]) for axis in ("x", "y", "z"))
        yaw = float(row["yaw"])
        if (last_position is None or math.dist(position, last_position) >= spacing or
                _angle_difference(yaw, last_yaw) >= yaw_spacing):
            samples.append({"position": position, "yaw": yaw,
                            "sim_time": float(row["sim_time"])})
            last_position, last_yaw = position, yaw
    final = rows[-1]
    final_position = tuple(float(final[axis]) for axis in ("x", "y", "z"))
    final_yaw = float(final["yaw"])
    if (not samples or samples[-1]["position"] != final_position or
            samples[-1]["yaw"] != final_yaw):
        samples.append({"position": final_position, "yaw": final_yaw,
                        "sim_time": float(final["sim_time"])})
    return samples


def visible_union(grid, config, samples, visibility_fn=visible_unknown_voxels):
    union = set()
    for sample in samples:
        position = sample.position if hasattr(sample, "position") else sample["position"]
        yaw = sample.yaw if hasattr(sample, "yaw") else sample["yaw"]
        union.update(visibility_fn(grid, position, yaw, config))
    return union


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _load_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip()]


def build_predicted_observation(run_directory, snapshot_root, spacing=0.25,
                                odom_yaw_spacing=0.1):
    run_directory = Path(run_directory)
    snapshot_root = Path(snapshot_root)
    intervals = _read_csv(run_directory / "execution_intervals.csv")
    planning = _read_csv(run_directory / "planning.csv")
    paths = _load_jsonl(run_directory / "planned_paths.jsonl")
    trajectory = _read_csv(run_directory / "trajectory.csv")
    path_index = {(item["kind"], int(item["id"])): item for item in paths}
    local_plans = {int(row["trajectory_id"]): row for row in planning
                   if row["kind"] == "local" and row["success"].lower() == "true"
                   and row["trajectory_id"]}
    odom_by_interval = {}
    for row in trajectory:
        identifier = int(row.get("execution_interval_id") or 0)
        if identifier:
            odom_by_interval.setdefault(identifier, []).append(row)

    errors = []
    records = []
    snapshot_cache = {}
    global_layer_cache = {}
    for interval in intervals:
        interval_id = int(interval["interval_id"])
        global_sequence = int(interval["global_sequence"])
        if global_sequence <= 0:
            records.append({"interval_id": interval_id, "global_sequence": global_sequence,
                            "status": "SKIPPED_RETURN", "errors": [], "layers": {}})
            continue
        snapshot_path = snapshot_root / ("snapshot_%06d" % global_sequence)
        interval_errors = []
        if not snapshot_path.is_dir():
            interval_errors.append("missing snapshot for global sequence %d" % global_sequence)
            records.append({"interval_id": interval_id, "global_sequence": global_sequence,
                            "status": "INVALID", "errors": interval_errors, "layers": {}})
            errors.extend("interval %d: %s" % (interval_id, item) for item in interval_errors)
            continue
        if global_sequence not in snapshot_cache:
            snapshot = load_snapshot(snapshot_path)
            snapshot_cache[global_sequence] = (
                snapshot, load_frozen_map(snapshot_path, snapshot),
                LegacyVisibilityConfig.from_planner(snapshot["planner"]))
        snapshot, grid, config = snapshot_cache[global_sequence]
        selected_id = int(snapshot["planner"]["selected_candidate"])
        candidates = {int(item["id"]): item for item in snapshot["planner"]["candidate_paths"]}
        candidate = candidates.get(selected_id)
        if candidate is None:
            interval_errors.append("selected candidate absent from snapshot")
            raw_waypoints = shortcut_waypoints = []
        else:
            raw_waypoints = candidate.get("raw_waypoints") or []
            shortcut_waypoints = candidate.get("waypoints") or []
            if not raw_waypoints:
                interval_errors.append("snapshot lacks selected raw PRM waypoints")

        cache_key = global_sequence
        if cache_key not in global_layer_cache and not interval_errors:
            raw_samples = sample_candidate_path(raw_waypoints, spacing)
            shortcut_samples = sample_candidate_path(shortcut_waypoints, spacing)
            global_layer_cache[cache_key] = {
                "prm_raw": (raw_samples, visible_union(grid, config, raw_samples)),
                "prm_shortcut": (shortcut_samples,
                                 visible_union(grid, config, shortcut_samples)),
            }
        local = local_plans.get(interval_id)
        if local is None:
            interval_errors.append("missing successful local planning row")
            start_yaw = 0.0
        else:
            start_yaw = float(local.get("start_yaw") or 0.0)
        bspline_path = path_index.get(("bspline", interval_id))
        if bspline_path is None:
            interval_errors.append("missing B-spline path")
            bspline_samples = []
        else:
            bspline_samples = sample_constant_yaw_polyline(
                bspline_path["points"], start_yaw, spacing)
        odom_samples = sample_odom_prefix(
            odom_by_interval.get(interval_id, []), spacing, odom_yaw_spacing)
        if not odom_samples:
            interval_errors.append("execution interval has no odometry prefix")

        layer_data = {}
        if cache_key in global_layer_cache:
            for name in ("prm_raw", "prm_shortcut"):
                samples, addresses = global_layer_cache[cache_key][name]
                layer_data[name] = {"sample_count": len(samples), "addresses": addresses}
        layer_data["bspline"] = {
            "sample_count": len(bspline_samples),
            "addresses": visible_union(grid, config, bspline_samples),
        }
        layer_data["odom_prefix"] = {
            "sample_count": len(odom_samples),
            "addresses": visible_union(grid, config, odom_samples),
        }
        serialized_layers = {}
        for name, data in layer_data.items():
            addresses = sorted(data["addresses"])
            serialized_layers[name] = {
                "sample_count": data["sample_count"],
                "predicted_unknown_voxels": len(addresses),
                "set_sha256": visible_set_sha256(addresses),
                "addresses": addresses,
            }
        if interval_errors:
            errors.extend("interval %d: %s" % (interval_id, item) for item in interval_errors)
        records.append({
            "interval_id": interval_id,
            "trajectory_id": int(interval["trajectory_id"]),
            "global_sequence": global_sequence,
            "snapshot_map_version": int(snapshot["map"]["version"]),
            "local_start_map_version": (None if local is None or not local.get("map_version")
                                        else int(local["map_version"])),
            "spacing": spacing,
            "odom_yaw_spacing": odom_yaw_spacing,
            "status": "VALID" if not interval_errors else "INVALID",
            "errors": interval_errors,
            "layers": serialized_layers,
        })
    return {
        "schema": "cerlab-r2-predicted-observation-v1",
        "run_directory": str(run_directory),
        "snapshot_root": str(snapshot_root),
        "spacing": spacing,
        "odom_yaw_spacing": odom_yaw_spacing,
        "interval_count": len(records),
        "valid_interval_count": sum(record["status"] == "VALID" for record in records),
        "skipped_return_interval_count": sum(record["status"] == "SKIPPED_RETURN"
                                             for record in records),
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
        "intervals": records,
    }


def write_predicted_observation(run_directory, snapshot_root, output_directory=None,
                                spacing=0.25, odom_yaw_spacing=0.1):
    output_directory = Path(output_directory) if output_directory else Path(run_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    result = build_predicted_observation(run_directory, snapshot_root, spacing,
                                         odom_yaw_spacing)
    summary = {key: value for key, value in result.items() if key != "intervals"}
    summary["layer_interval_counts"] = {
        layer: sum(layer in record.get("layers", {}) for record in result["intervals"])
        for layer in LAYERS
    }
    atomic_write_json(output_directory / "predicted_observation_summary.json", summary)
    path = output_directory / "predicted_observation_sets.jsonl"
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        for record in result["intervals"]:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(str(temporary), str(path))
    return summary
