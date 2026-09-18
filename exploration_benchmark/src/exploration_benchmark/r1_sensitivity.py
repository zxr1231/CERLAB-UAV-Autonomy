"""Compare R1 path diagnostics across spatial sampling intervals."""

import json
import math
import statistics
from pathlib import Path


def _mean(values):
    return statistics.mean(values) if values else None


def _rank_spearman(first, second):
    if len(first) != len(second) or set(first) != set(second):
        return None
    count = len(first)
    if count < 2:
        return 1.0 if count == 1 else None
    positions = {value: index for index, value in enumerate(second)}
    squared = sum((index - positions[value]) ** 2 for index, value in enumerate(first))
    return 1.0 - 6.0 * squared / (count * (count * count - 1))


def _load_reports(study_directory):
    study_directory = Path(study_directory)
    summary = json.loads((study_directory / "summary.json").read_text(encoding="utf-8"))
    reports = {}
    for row in summary["rows"]:
        name = row["snapshot"]
        reports[name] = json.loads((study_directory / "reports" / (name + ".json"))
                                   .read_text(encoding="utf-8"))
    return summary, reports


def _candidate_map(report):
    return {candidate["candidate_id"]: candidate for candidate in report["candidates"]}


def _pose_key(sample):
    yaw = (float(sample["yaw"]) + math.pi) % (2 * math.pi) - math.pi
    return tuple(round(float(value), 6) for value in sample["position"]) + (round(yaw, 6),)


def _reuse_profile(reports):
    sample_total = 0
    sample_unique = 0
    edge_total = 0
    edge_unique = 0
    candidate_inner = 0.0
    total_wall = 0.0
    for report in reports.values():
        pose_keys = []
        edge_keys = []
        for candidate in report["candidates"]:
            candidate_inner += candidate["evaluation_wall_seconds"]
            pose_keys.extend(_pose_key(sample) for sample in candidate["samples"])
            waypoints = [tuple(round(float(value), 6) for value in sample["position"])
                         for sample in candidate["samples"]]
            edge_keys.extend(zip(waypoints[:-1], waypoints[1:]))
        sample_total += len(pose_keys)
        sample_unique += len(set(pose_keys))
        edge_total += len(edge_keys)
        edge_unique += len(set(edge_keys))
        total_wall += report["total_wall_seconds"]
    return {
        "sample_occurrences": sample_total,
        "unique_pose_yaw_samples": sample_unique,
        "exact_sample_reuse_fraction": (1.0 - sample_unique / sample_total
                                        if sample_total else 0.0),
        "sampled_directed_edge_occurrences": edge_total,
        "unique_sampled_directed_edges": edge_unique,
        "exact_directed_edge_reuse_fraction": (1.0 - edge_unique / edge_total
                                                if edge_total else 0.0),
        "candidate_inner_seconds_sum": candidate_inner,
        "report_total_wall_seconds_sum": total_wall,
        "candidate_inner_wall_fraction": candidate_inner / total_wall if total_wall else None,
    }


def compare_sampling_studies(studies):
    """Compare ``{spacing: study_directory}`` against the finest spacing."""
    if len(studies) < 2:
        raise ValueError("at least two sampling studies are required")
    loaded = {float(spacing): _load_reports(path) for spacing, path in studies.items()}
    reference_spacing = min(loaded)
    reference_summary, reference_reports = loaded[reference_spacing]
    reference_names = set(reference_reports)
    comparisons = {}
    for spacing in sorted(loaded):
        summary, reports = loaded[spacing]
        if set(reports) != reference_names:
            raise ValueError("sampling studies do not contain the same snapshots")
        relative_errors = []
        top1_matches = []
        full_rank_matches = []
        rank_correlations = []
        sample_count = 0
        for name in sorted(reference_names):
            reference = reference_reports[name]
            current = reports[name]
            reference_candidates = _candidate_map(reference)
            current_candidates = _candidate_map(current)
            if set(reference_candidates) != set(current_candidates):
                raise ValueError("sampling studies do not contain the same candidates")
            for candidate_id, reference_candidate in reference_candidates.items():
                value = current_candidates[candidate_id]["unique_gain"]
                reference_value = reference_candidate["unique_gain"]
                relative_errors.append(abs(value - reference_value) / max(1, reference_value))
                sample_count += current_candidates[candidate_id]["sample_count"]
            reference_rank = reference["rankings"]["unique_utility"]
            current_rank = current["rankings"]["unique_utility"]
            top1_matches.append(reference_rank[0] == current_rank[0])
            full_rank_matches.append(reference_rank == current_rank)
            rank_correlations.append(_rank_spearman(reference_rank, current_rank))
        comparisons[str(spacing)] = {
            "sample_count": sample_count,
            "candidate_count": len(relative_errors),
            "unique_gain_relative_error_mean_vs_finest": _mean(relative_errors),
            "unique_gain_relative_error_median_vs_finest": statistics.median(relative_errors),
            "unique_gain_relative_error_max_vs_finest": max(relative_errors),
            "unique_top1_agreement_vs_finest": _mean(top1_matches),
            "unique_full_rank_agreement_vs_finest": _mean(full_rank_matches),
            "unique_rank_spearman_mean_vs_finest": _mean(rank_correlations),
            "diagnostic_wall_seconds_sum": sum(report["total_wall_seconds"]
                                               for report in reports.values()),
            "process_max_rss_kib": summary.get("process_max_rss_kib"),
        }

    reference_reuse = _reuse_profile(reference_reports)
    half_spacing = sorted(loaded)[1] if len(loaded) > 1 else reference_spacing
    operational_reuse = _reuse_profile(loaded[half_spacing][1])
    edge_reuse = operational_reuse["exact_directed_edge_reuse_fraction"]
    scoring_share = operational_reuse["candidate_inner_wall_fraction"]
    cache_recommendation = (
        "do_not_build_dependency_aware_edge_cache_yet"
        if edge_reuse < 0.20 else "edge_cache_profiling_gate_passed"
    )
    return {
        "schema": "cerlab-r1-sampling-sensitivity-v1",
        "reference_spacing": reference_spacing,
        "snapshot_count": len(reference_names),
        "comparisons": comparisons,
        "finest_spacing_reuse": reference_reuse,
        "operational_spacing": half_spacing,
        "operational_reuse": operational_reuse,
        "cache_gate": {
            "scoring_share_observed": scoring_share,
            "exact_directed_edge_reuse_observed": edge_reuse,
            "minimum_edge_reuse_gate": 0.20,
            "recommendation": cache_recommendation,
            "scope": "offline_python_diagnostic_only_not_online_cpp",
        },
    }
