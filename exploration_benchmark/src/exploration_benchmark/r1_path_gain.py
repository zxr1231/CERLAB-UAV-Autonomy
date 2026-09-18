"""Offline raw/unique/marginal path-gain diagnostics for Phase R1."""

import math
import time
from dataclasses import dataclass

from exploration_benchmark.r1_snapshot import load_frozen_map, load_snapshot
from exploration_benchmark.r1_visibility import (LegacyVisibilityConfig,
                                                  visible_set_sha256,
                                                  visible_unknown_voxels)


@dataclass(frozen=True)
class PathSample:
    index: int
    position: tuple
    yaw: float
    segment: int
    distance_along_path: float


def _distance(first, second):
    return math.sqrt(sum((second[i] - first[i]) ** 2 for i in range(3)))


def sample_candidate_path(waypoints, spacing):
    """Sample a polyline without duplicating shared segment endpoints."""
    if not math.isfinite(spacing) or spacing <= 0:
        raise ValueError("sample spacing must be finite and positive")
    if not waypoints:
        return []
    normalized = []
    for waypoint in waypoints:
        position = tuple(float(value) for value in waypoint["position"])
        yaw = float(waypoint["yaw"])
        if len(position) != 3 or not all(math.isfinite(value) for value in position):
            raise ValueError("waypoint position must contain three finite values")
        if not math.isfinite(yaw):
            raise ValueError("waypoint yaw must be finite")
        normalized.append((position, yaw))

    samples = []
    cumulative = 0.0
    for segment in range(len(normalized) - 1):
        start, yaw = normalized[segment]
        end, _ = normalized[segment + 1]
        length = _distance(start, end)
        if length <= 1e-12:
            if not samples:
                samples.append(PathSample(0, start, yaw, segment, cumulative))
            continue
        direction = tuple((end[axis] - start[axis]) / length for axis in range(3))
        offset = 0.0
        while offset < length - 1e-12:
            position = tuple(start[axis] + offset * direction[axis] for axis in range(3))
            samples.append(PathSample(len(samples), position, yaw, segment,
                                      cumulative + offset))
            offset += spacing
        cumulative += length

    terminal_position, terminal_yaw = normalized[-1]
    if not samples or (_distance(samples[-1].position, terminal_position) > 1e-12 or
                       abs(samples[-1].yaw - terminal_yaw) > 1e-12):
        samples.append(PathSample(len(samples), terminal_position, terminal_yaw,
                                  max(0, len(normalized) - 2), cumulative))
    return samples


def evaluate_candidate_path(grid, candidate, config, spacing,
                            visibility_fn=visible_unknown_voxels):
    """Evaluate one candidate with an independent path-history set."""
    samples = sample_candidate_path(candidate["waypoints"], spacing)
    history = set()
    raw_gain = 0
    sample_gains = []
    marginal_gains = []
    sample_records = []
    started = time.perf_counter()
    for sample in samples:
        visible = frozenset(visibility_fn(grid, sample.position, sample.yaw, config))
        marginal = visible.difference(history)
        sample_gain = len(visible)
        marginal_gain = len(marginal)
        raw_gain += sample_gain
        sample_gains.append(sample_gain)
        marginal_gains.append(marginal_gain)
        history.update(visible)
        sample_records.append({
            "sample_index": sample.index,
            "segment": sample.segment,
            "distance_along_path": sample.distance_along_path,
            "position": list(sample.position),
            "yaw": sample.yaw,
            "raw_sample_gain": sample_gain,
            "marginal_gain": marginal_gain,
            "visible_set_sha256": visible_set_sha256(visible),
        })
    elapsed = time.perf_counter() - started
    unique_gain = len(history)
    if raw_gain < unique_gain:
        raise AssertionError("raw gain is smaller than unique gain")
    if any(value < 0 for value in marginal_gains):
        raise AssertionError("negative marginal gain")
    if sum(marginal_gains) != unique_gain:
        raise AssertionError("marginal gains do not sum to unique gain")

    duplicate_ratio = 0.0 if raw_gain == 0 else 1.0 - unique_gain / raw_gain
    legacy = candidate.get("legacy_metrics")
    estimated_time = None
    if legacy and legacy.get("valid"):
        estimated_time = float(legacy["estimated_time"])
    raw_utility = raw_gain / estimated_time if estimated_time and estimated_time > 0 else None
    unique_utility = unique_gain / estimated_time if estimated_time and estimated_time > 0 else None
    return {
        "candidate_id": int(candidate["id"]),
        "sample_count": len(samples),
        "sample_spacing": spacing,
        "raw_gain": raw_gain,
        "unique_gain": unique_gain,
        "marginal_gains": marginal_gains,
        "sample_gains": sample_gains,
        "duplicate_count": raw_gain - unique_gain,
        "duplicate_ratio": duplicate_ratio,
        "unique_set_sha256": visible_set_sha256(history),
        "raw_utility": raw_utility,
        "unique_utility": unique_utility,
        "legacy_metrics": legacy,
        "evaluation_wall_seconds": elapsed,
        "samples": sample_records,
    }


def _rank(candidates, field):
    usable = [candidate for candidate in candidates if candidate.get(field) is not None]
    return [candidate["candidate_id"] for candidate in
            sorted(usable, key=lambda item: (-item[field], item["candidate_id"]))]


def diagnose_snapshot_paths(directory, spacing=0.5,
                            visibility_fn=visible_unknown_voxels):
    """Evaluate all exported candidates without changing planner state."""
    started = time.perf_counter()
    stage_started = time.perf_counter()
    snapshot = load_snapshot(directory)
    snapshot_load_seconds = time.perf_counter() - stage_started
    planner = snapshot["planner"]
    stage_started = time.perf_counter()
    grid = load_frozen_map(directory, snapshot=snapshot)
    frozen_map_load_seconds = time.perf_counter() - stage_started
    config = LegacyVisibilityConfig.from_planner(planner)
    stage_started = time.perf_counter()
    candidates = [evaluate_candidate_path(grid, candidate, config, spacing, visibility_fn)
                  for candidate in planner["candidate_paths"]]
    candidate_evaluation_seconds = time.perf_counter() - stage_started
    legacy_rank = [candidate["candidate_id"] for candidate in sorted(
        (candidate for candidate in candidates
         if candidate.get("legacy_metrics") and candidate["legacy_metrics"].get("valid")),
        key=lambda item: (-float(item["legacy_metrics"]["score"]), item["candidate_id"]))]
    raw_rank = _rank(candidates, "raw_utility")
    unique_rank = _rank(candidates, "unique_utility")
    total_wall_seconds = time.perf_counter() - started
    return {
        "schema": "cerlab-r1-path-gain-v1",
        "source_snapshot": str(directory),
        "planning_sequence": planner["planning_sequence"],
        "map_version": grid.version,
        "visibility_model": "legacy_proxy_v1",
        "sampling": {
            "position_spacing": spacing,
            "edge_yaw": "exported_outgoing_segment_heading",
            "terminal_yaw": "exported_legacy_best_yaw",
            "rotation_only_samples": False,
        },
        "selected_candidate": planner["selected_candidate"],
        "candidates": candidates,
        "rankings": {
            "legacy_score": legacy_rank,
            "raw_utility": raw_rank,
            "unique_utility": unique_rank,
        },
        "ranking_changes": {
            "legacy_to_unique_top1": bool(legacy_rank and unique_rank and
                                           legacy_rank[0] != unique_rank[0]),
            "raw_to_unique_top1": bool(raw_rank and unique_rank and
                                        raw_rank[0] != unique_rank[0]),
        },
        "invariants": {
            "raw_ge_unique": all(item["raw_gain"] >= item["unique_gain"]
                                 for item in candidates),
            "marginal_nonnegative": all(all(value >= 0 for value in item["marginal_gains"])
                                        for item in candidates),
            "marginal_sum_equals_unique": all(sum(item["marginal_gains"]) == item["unique_gain"]
                                               for item in candidates),
            "candidate_histories_independent": True,
        },
        "timing": {
            "snapshot_validation_load_seconds": snapshot_load_seconds,
            "frozen_map_reload_seconds": frozen_map_load_seconds,
            "candidate_evaluation_seconds": candidate_evaluation_seconds,
            "candidate_inner_seconds_sum": sum(candidate["evaluation_wall_seconds"]
                                               for candidate in candidates),
        },
        "total_wall_seconds": total_wall_seconds,
    }
