"""Compare local input paths, B-spline samples, and ID-associated odometry."""
import csv
import json
import math
from pathlib import Path

import numpy as np

from exploration_benchmark.core import atomic_write_json, value_summary


FIELDS = [
    "trajectory_id", "global_sequence", "phase", "input_length", "bspline_length",
    "executed_length", "bspline_to_input_length_ratio",
    "executed_to_bspline_length_ratio", "odom_sample_count",
    "execution_duration", "bspline_to_input_mean_distance",
    "bspline_to_input_max_distance", "odom_to_bspline_mean_distance",
    "odom_to_bspline_max_distance",
]

METRIC_FIELDS = (
    "bspline_to_input_length_ratio", "executed_to_bspline_length_ratio",
    "bspline_to_input_mean_distance", "bspline_to_input_max_distance",
    "odom_to_bspline_mean_distance", "odom_to_bspline_max_distance",
)


def polyline_length(points):
    points = np.asarray(points, dtype=float)
    if len(points) < 2:
        return 0.0
    return float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum())


def point_to_polyline_distances(points, polyline):
    points = np.asarray(points, dtype=float)
    polyline = np.asarray(polyline, dtype=float)
    if points.size == 0:
        return np.array([], dtype=float)
    if len(polyline) == 0:
        return np.full(len(points), np.nan)
    if len(polyline) == 1:
        return np.linalg.norm(points-polyline[0], axis=1)
    best = np.full(len(points), np.inf)
    for start, end in zip(polyline, polyline[1:]):
        segment = end-start
        denominator = float(np.dot(segment, segment))
        if denominator == 0:
            distance = np.linalg.norm(points-start, axis=1)
        else:
            fraction = np.clip((points-start).dot(segment)/denominator, 0.0, 1.0)
            projected = start + fraction[:, None]*segment
            distance = np.linalg.norm(points-projected, axis=1)
        best = np.minimum(best, distance)
    return best


def summarize_run(run_dir):
    run_dir = Path(run_dir)
    paths = [json.loads(line) for line in
             (run_dir/"planned_paths.jsonl").read_text(encoding="utf-8").splitlines()
             if line.strip()]
    indexed = {(item["kind"], int(item["id"])): item for item in paths}
    with (run_dir/"trajectory.csv").open(newline="", encoding="utf-8") as stream:
        trajectory = list(csv.DictReader(stream))
    odom_by_id = {}
    for row in trajectory:
        identifier = int(row.get("trajectory_id") or 0)
        if identifier:
            odom_by_id.setdefault(identifier, []).append(row)

    rows = []
    for (kind, identifier), bspline in sorted(indexed.items()):
        if kind != "bspline":
            continue
        input_path = indexed.get(("input", identifier))
        if input_path is None:
            continue
        input_points = np.asarray(input_path["points"], dtype=float)
        bspline_points = np.asarray(bspline["points"], dtype=float)
        odom_rows = odom_by_id.get(identifier, [])
        odom_points = np.asarray([[float(row[axis]) for axis in ("x", "y", "z")]
                                  for row in odom_rows], dtype=float)
        input_length = polyline_length(input_points)
        bspline_length = polyline_length(bspline_points)
        executed_length = polyline_length(odom_points)
        bspline_input_distance = point_to_polyline_distances(bspline_points, input_points)
        odom_bspline_distance = point_to_polyline_distances(odom_points, bspline_points)
        duration = (float(odom_rows[-1]["sim_time"])-float(odom_rows[0]["sim_time"])
                    if len(odom_rows) >= 2 else 0.0)
        rows.append({
            "trajectory_id": identifier,
            "global_sequence": bspline.get("global_sequence"),
            "phase": ("exploration" if int(bspline.get("global_sequence") or 0) > 0
                      else "return"),
            "input_length": input_length,
            "bspline_length": bspline_length,
            "executed_length": executed_length,
            "bspline_to_input_length_ratio": (bspline_length/input_length
                                                if input_length > 0 else None),
            "executed_to_bspline_length_ratio": (executed_length/bspline_length
                                                   if bspline_length > 0 else None),
            "odom_sample_count": len(odom_rows),
            "execution_duration": duration,
            "bspline_to_input_mean_distance": (float(bspline_input_distance.mean())
                                                 if bspline_input_distance.size else None),
            "bspline_to_input_max_distance": (float(bspline_input_distance.max())
                                                if bspline_input_distance.size else None),
            "odom_to_bspline_mean_distance": (float(odom_bspline_distance.mean())
                                                if odom_bspline_distance.size else None),
            "odom_to_bspline_max_distance": (float(odom_bspline_distance.max())
                                               if odom_bspline_distance.size else None),
        })
    return rows


def summarize_rows(rows):
    return {
        "trajectory_count": len(rows),
        "trajectories_with_odom": sum(row["odom_sample_count"] > 0 for row in rows),
        "metrics": {
            field: value_summary([row[field] for row in rows if row[field] is not None])
            for field in METRIC_FIELDS
        },
    }


def write_run_metrics(run_dir):
    run_dir = Path(run_dir)
    rows = summarize_run(run_dir)
    with (run_dir/"trajectory_alignment.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    phases = {phase: summarize_rows([row for row in rows if row["phase"] == phase])
              for phase in ("exploration", "return")}
    summary = {
        "schema_version": 2,
        "status": "VALID" if rows else "NO_ASSOCIATED_TRAJECTORIES",
        "primary_phase": "exploration",
        "trajectory_count": len(rows),
        "trajectories_with_odom": sum(row["odom_sample_count"] > 0 for row in rows),
        "metrics": phases["exploration"]["metrics"],
        "phases": phases,
    }
    atomic_write_json(run_dir/"trajectory_alignment_summary.json", summary)
    return summary
