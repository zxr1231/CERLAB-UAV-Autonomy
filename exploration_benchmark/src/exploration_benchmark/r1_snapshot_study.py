"""Batch and aggregate R1 path-gain diagnostics without selecting outcomes."""

import csv
import json
import math
import os
import statistics
import tempfile
from pathlib import Path

from exploration_benchmark.r1_path_gain import diagnose_snapshot_paths


STAGES = ("early", "middle", "late")


def discover_snapshots(root):
    root = Path(root)
    return sorted((path for path in root.iterdir()
                   if path.is_dir() and (path / "manifest.json").is_file()),
                  key=lambda path: path.name)


def select_decorrelated_snapshots(paths, min_position_delta=1.0,
                                  min_map_version_delta=500000,
                                  keep_final=True):
    """Select by state change only; gain and ranking values are never inspected."""
    if min_position_delta < 0 or min_map_version_delta < 0:
        raise ValueError("decorrelation thresholds must be nonnegative")
    paths = list(paths)
    selected = []
    last_position = None
    last_version = None
    for path in paths:
        planner = json.loads((path / "planner.json").read_text(encoding="utf-8"))
        position = tuple(float(value) for value in planner["vehicle"]["position"])
        version = int(planner["map_version"])
        distance = (math.dist(position, last_position)
                    if last_position is not None else math.inf)
        version_delta = version - last_version if last_version is not None else math.inf
        if distance >= min_position_delta or version_delta >= min_map_version_delta:
            selected.append(path)
            last_position = position
            last_version = version
    if keep_final and paths and (not selected or selected[-1] != paths[-1]):
        selected.append(paths[-1])
    return selected


def _mean(values):
    return statistics.mean(values) if values else None


def _median(values):
    return statistics.median(values) if values else None


def _rank_spearman(first, second):
    if len(first) != len(second) or set(first) != set(second):
        return None
    count = len(first)
    if count < 2:
        return 1.0 if count == 1 else None
    positions = {value: index for index, value in enumerate(second)}
    squared = sum((index - positions[value]) ** 2 for index, value in enumerate(first))
    return 1.0 - 6.0 * squared / (count * (count * count - 1))


def summarize_report(report):
    candidates = report["candidates"]
    if not candidates:
        raise ValueError("path diagnostic contains no candidates")
    by_id = {candidate["candidate_id"]: candidate for candidate in candidates}
    raw_rank = report["rankings"]["raw_utility"]
    unique_rank = report["rankings"]["unique_utility"]
    legacy_rank = report["rankings"]["legacy_score"]
    if not raw_rank or not unique_rank or not legacy_rank:
        raise ValueError("path diagnostic lacks a complete utility ranking")

    duplicate_ratios = [candidate["duplicate_ratio"] for candidate in candidates]
    marginal_values = [value for candidate in candidates
                       for value in candidate["marginal_gains"]]
    selected = by_id.get(report["selected_candidate"])
    best_unique_id = unique_rank[0]
    best_unique = by_id[best_unique_id]["unique_utility"]
    runner_unique = (by_id[unique_rank[1]]["unique_utility"]
                     if len(unique_rank) > 1 else None)
    margin = best_unique - runner_unique if runner_unique is not None else None
    selected_unique = selected["unique_utility"] if selected else None
    regret = best_unique - selected_unique if selected_unique is not None else None
    relative_regret = regret / best_unique if regret is not None and best_unique > 0 else None
    raw_best_id = raw_rank[0]
    raw_choice_unique = by_id[raw_best_id]["unique_utility"]
    raw_choice_regret = best_unique - raw_choice_unique
    raw_choice_relative_regret = (raw_choice_regret / best_unique
                                  if best_unique > 0 else None)
    zero_marginals = sum(value == 0 for value in marginal_values)

    return {
        "planning_sequence": report["planning_sequence"],
        "map_version": report["map_version"],
        "selected_candidate": report["selected_candidate"],
        "raw_best_candidate": raw_best_id,
        "unique_best_candidate": best_unique_id,
        "candidate_count": len(candidates),
        "sample_count": sum(candidate["sample_count"] for candidate in candidates),
        "duplicate_ratio_mean": _mean(duplicate_ratios),
        "duplicate_ratio_median": _median(duplicate_ratios),
        "duplicate_ratio_min": min(duplicate_ratios),
        "duplicate_ratio_max": max(duplicate_ratios),
        "selected_duplicate_ratio": selected["duplicate_ratio"] if selected else None,
        "marginal_mean": _mean(marginal_values),
        "marginal_median": _median(marginal_values),
        "zero_marginal_fraction": zero_marginals / len(marginal_values) if marginal_values else None,
        "legacy_unique_top1_changed": legacy_rank[0] != unique_rank[0],
        "raw_unique_top1_changed": raw_rank[0] != unique_rank[0],
        "legacy_unique_order_changed": legacy_rank != unique_rank,
        "raw_unique_order_changed": raw_rank != unique_rank,
        "raw_unique_rank_spearman": _rank_spearman(raw_rank, unique_rank),
        "unique_top_margin": margin,
        "unique_top_relative_margin": margin / best_unique if margin is not None and best_unique > 0 else None,
        "selected_unique_regret": regret,
        "selected_unique_relative_regret": relative_regret,
        "raw_choice_unique_regret": raw_choice_regret,
        "raw_choice_unique_relative_regret": raw_choice_relative_regret,
        "diagnostic_wall_seconds": report["total_wall_seconds"],
    }


def assign_stages(rows):
    ordered = sorted(rows, key=lambda row: row["planning_sequence"])
    count = len(ordered)
    for index, row in enumerate(ordered):
        row["stage"] = STAGES[min(2, index * 3 // count)]
    return ordered


def aggregate_rows(rows):
    def aggregate(group):
        numeric = lambda key: [row[key] for row in group if row.get(key) is not None]
        return {
            "snapshot_count": len(group),
            "candidate_count": sum(row["candidate_count"] for row in group),
            "legacy_unique_top1_change_rate": _mean(numeric("legacy_unique_top1_changed")),
            "raw_unique_top1_change_rate": _mean(numeric("raw_unique_top1_changed")),
            "legacy_unique_order_change_rate": _mean(numeric("legacy_unique_order_changed")),
            "raw_unique_order_change_rate": _mean(numeric("raw_unique_order_changed")),
            "duplicate_ratio_snapshot_mean": _mean(numeric("duplicate_ratio_mean")),
            "selected_duplicate_ratio_mean": _mean(numeric("selected_duplicate_ratio")),
            "raw_unique_rank_spearman_mean": _mean(numeric("raw_unique_rank_spearman")),
            "selected_unique_relative_regret_mean": _mean(numeric("selected_unique_relative_regret")),
            "selected_unique_relative_regret_max": max(numeric("selected_unique_relative_regret"), default=None),
            "raw_choice_unique_relative_regret_mean": _mean(numeric("raw_choice_unique_relative_regret")),
            "raw_choice_unique_relative_regret_max": max(numeric("raw_choice_unique_relative_regret"), default=None),
            "zero_marginal_fraction_mean": _mean(numeric("zero_marginal_fraction")),
            "diagnostic_wall_seconds_sum": sum(numeric("diagnostic_wall_seconds")),
        }

    return {
        "overall": aggregate(rows),
        "by_stage": {stage: aggregate([row for row in rows if row["stage"] == stage])
                     for stage in STAGES},
    }


def _atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent),
                                     prefix=path.name + ".", suffix=".tmp",
                                     delete=False) as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")
        temporary = stream.name
    os.replace(temporary, str(path))


def run_snapshot_study(snapshot_root, output_directory, spacing=0.5, resume=True,
                       min_position_delta=1.0, min_map_version_delta=500000,
                       keep_final=True):
    snapshot_root = Path(snapshot_root)
    output_directory = Path(output_directory)
    report_directory = output_directory / "reports"
    report_directory.mkdir(parents=True, exist_ok=True)
    discovered = discover_snapshots(snapshot_root)
    snapshots = select_decorrelated_snapshots(discovered, min_position_delta,
                                               min_map_version_delta, keep_final)
    rows = []
    failures = []
    for snapshot in snapshots:
        report_path = report_directory / (snapshot.name + ".json")
        try:
            if resume and report_path.is_file():
                report = json.loads(report_path.read_text(encoding="utf-8"))
                if (report.get("source_snapshot") != str(snapshot) or
                        report.get("sampling", {}).get("position_spacing") != spacing):
                    raise ValueError("existing report does not match snapshot/spacing")
            else:
                report = diagnose_snapshot_paths(snapshot, spacing)
                _atomic_json(report_path, report)
            row = summarize_report(report)
            row["snapshot"] = snapshot.name
            rows.append(row)
        except Exception as error:
            failures.append({"snapshot": snapshot.name, "error": str(error)})

    rows = assign_stages(rows) if rows else []
    summary = {
        "schema": "cerlab-r1-snapshot-study-v1",
        "snapshot_root": str(snapshot_root),
        "sample_spacing": spacing,
        "discovered_snapshot_count": len(discovered),
        "selected_snapshot_count": len(snapshots),
        "selection_policy": {
            "type": "state_change_decorrelation",
            "min_position_delta_m": min_position_delta,
            "min_map_version_delta": min_map_version_delta,
            "keep_first": True,
            "keep_final": keep_final,
            "uses_gain_or_ranking": False,
        },
        "stage_policy": "equal-count planning-sequence tertiles",
        "rows": rows,
        "failures": failures,
        "aggregate": aggregate_rows(rows) if rows else None,
    }
    _atomic_json(output_directory / "summary.json", summary)
    if rows:
        fields = list(rows[0].keys())
        with (output_directory / "snapshots.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    return summary
