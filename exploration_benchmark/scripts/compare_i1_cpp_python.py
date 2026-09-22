#!/usr/bin/env python3
"""Require exact C++/Python I1 path-gain agreement on frozen snapshots."""

import argparse
import json
import math
import subprocess
from pathlib import Path

from exploration_benchmark.core import atomic_write_json
from exploration_benchmark.r1_path_gain import evaluate_candidate_path, sample_candidate_path
from exploration_benchmark.r1_snapshot import load_frozen_map, load_snapshot
from exploration_benchmark.r1_visibility import LegacyVisibilityConfig, visible_unknown_voxels


def python_details(grid, candidate, config, spacing):
    evaluated = evaluate_candidate_path(grid, candidate, config, spacing)
    addresses = set()
    for sample in sample_candidate_path(candidate["waypoints"], spacing):
        addresses.update(visible_unknown_voxels(grid, sample.position, sample.yaw, config))
    return evaluated, sorted(addresses)


def compare_snapshot(snapshot_directory, runner, spacing):
    snapshot_directory = Path(snapshot_directory)
    snapshot = load_snapshot(snapshot_directory)
    grid = load_frozen_map(snapshot_directory, snapshot)
    config = LegacyVisibilityConfig.from_planner(snapshot["planner"])
    completed = subprocess.run(
        [str(runner), str(snapshot_directory), str(spacing)],
        check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cpp = json.loads(completed.stdout)
    cpp_candidates = {int(row["candidate_id"]): row for row in cpp["candidates"]}
    errors = []
    rows = []
    for candidate in snapshot["planner"]["candidate_paths"]:
        identifier = int(candidate["id"])
        python_result, python_addresses = python_details(grid, candidate, config, spacing)
        cpp_result = cpp_candidates.get(identifier)
        if cpp_result is None:
            errors.append("candidate %d missing from C++ output" % identifier)
            continue
        exact_fields = {
            "sample_count": python_result["sample_count"],
            "raw_gain": python_result["raw_gain"],
            "unique_gain": python_result["unique_gain"],
            "marginal_gains": python_result["marginal_gains"],
            "unique_addresses": python_addresses,
        }
        mismatches = []
        for field, expected in exact_fields.items():
            if cpp_result.get(field) != expected:
                mismatches.append(field)
        for field in ("duplicate_ratio", "unique_utility"):
            expected = python_result[field]
            actual = cpp_result.get(field)
            if expected is None or actual is None:
                if expected != actual:
                    mismatches.append(field)
            elif not math.isclose(float(expected), float(actual), rel_tol=1e-12, abs_tol=1e-12):
                mismatches.append(field)
        if mismatches:
            errors.append("candidate %d differs: %s" % (identifier, ",".join(mismatches)))
        rows.append({
            "candidate_id": identifier,
            "match": not mismatches,
            "mismatches": mismatches,
            "sample_count": python_result["sample_count"],
            "raw_gain": python_result["raw_gain"],
            "unique_gain": python_result["unique_gain"],
            "unique_address_count": len(python_addresses),
        })
    unexpected = sorted(set(cpp_candidates)-{int(item["id"])
                                              for item in snapshot["planner"]["candidate_paths"]})
    if unexpected:
        errors.append("unexpected C++ candidates: %s" % unexpected)
    return {
        "snapshot": snapshot_directory.name,
        "map_version": grid.version,
        "candidate_count": len(rows),
        "matched_candidate_count": sum(row["match"] for row in rows),
        "status": "MATCH" if not errors else "MISMATCH",
        "errors": errors,
        "candidates": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot_root")
    parser.add_argument("--runner", required=True)
    parser.add_argument("--spacing", type=float, default=0.25)
    parser.add_argument("--snapshot", action="append", dest="snapshots")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.snapshot_root)
    directories = ([root/name for name in args.snapshots] if args.snapshots else
                   sorted(path for path in root.iterdir() if path.is_dir()))
    reports = [compare_snapshot(path, Path(args.runner), args.spacing)
               for path in directories]
    result = {
        "schema": "cerlab-i1-cpp-python-agreement-v1",
        "spacing": args.spacing,
        "snapshot_count": len(reports),
        "candidate_count": sum(item["candidate_count"] for item in reports),
        "matched_candidate_count": sum(item["matched_candidate_count"] for item in reports),
        "status": "MATCH" if all(item["status"] == "MATCH" for item in reports) else "MISMATCH",
        "snapshots": reports,
    }
    atomic_write_json(args.output, result)
    print(json.dumps({key: value for key, value in result.items() if key != "snapshots"},
                     indent=2, sort_keys=True))
    return 0 if result["status"] == "MATCH" else 1


if __name__ == "__main__":
    raise SystemExit(main())
