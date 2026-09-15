"""Aggregate Benchmark v2 runs while preserving failures and censoring."""
import csv
import json
import math
import statistics
from collections import Counter
from pathlib import Path

from exploration_benchmark.core import atomic_write_json, percentile


RUN_FIELDS = [
    "run_id", "task_id", "attempt", "result_dir", "environment_seed",
    "planner_seed", "mode", "status", "outcome", "manifest_readable",
    "git_clean", "algorithm_completed", "return_success", "planning_start_sim",
    "completion_sim", "home_reached_sim", "exploration_duration_sim",
    "return_duration_sim", "exploration_distance_m", "final_mission_distance_m",
    "free_coverage", "surface_coverage", "coverage_valid", "coverage_status",
    "t80_seconds", "t80_censored", "t90_seconds", "t90_censored",
    "t95_seconds", "t95_censored", "collision_status", "collision_episodes",
    "collision_free", "trajectory_status", "resource_status",
    "global_planning_count", "global_planning_mean_ms",
    "global_planning_p95_ms", "exploration_local_planning_count",
    "exploration_local_planning_mean_ms", "exploration_local_planning_p95_ms",
    "executed_to_bspline_length_ratio_mean", "odom_to_bspline_mean_distance_mean",
    "exploration_cpu_mean", "exploration_cpu_p95", "exploration_rss_mean_mib",
    "exploration_rss_peak_mib", "logger_cpu_mean", "logger_rss_mean_mib",
    "simulator_cpu_mean", "simulator_rss_mean_mib", "mean_rtf",
    "mission_sim_duration", "mission_wall_duration",
]


def load_json(path):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream)


def load_jsonl(path):
    if not Path(path).is_file():
        return []
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip()]


def load_csv(path):
    if not Path(path).is_file():
        return []
    with Path(path).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def first_state_time(events, states):
    values = [float(event["sim_time"]) for event in events
              if event.get("event") == "MISSION_STATE" and
              event.get("current") in states and event.get("sim_time") is not None]
    return min(values) if values else None


def latest_at_or_before(rows, sim_time):
    if sim_time is None:
        return None
    eligible = [row for row in rows if row.get("sim_time") and
                float(row["sim_time"]) <= sim_time]
    return eligible[-1] if eligible else None


def optional_float(value):
    return None if value is None or value == "" else float(value)


def distribution_summary(values):
    values = [float(value) for value in values if value is not None and value != ""]
    if not values:
        return {"count": 0, "mean": None, "sample_std": None, "median": None,
                "p25": None, "p75": None, "p95": None, "min": None, "max": None}
    return {
        "count": len(values),
        "mean": statistics.mean(values),
        "sample_std": statistics.stdev(values) if len(values) >= 2 else None,
        "median": statistics.median(values),
        "p25": percentile(values, 25),
        "p75": percentile(values, 75),
        "p95": percentile(values, 95),
        "min": min(values),
        "max": max(values),
    }


def rate_summary(successes, total):
    successes, total = int(successes), int(total)
    if total <= 0:
        return {"successes": successes, "total": total, "rate": None,
                "wilson95_low": None, "wilson95_high": None}
    z = 1.959963984540054
    observed = successes / total
    denominator = 1.0 + z * z / total
    center = (observed + z * z / (2.0 * total)) / denominator
    half = z * math.sqrt(observed * (1.0-observed) / total +
                         z * z / (4.0 * total * total)) / denominator
    return {"successes": successes, "total": total, "rate": observed,
            "wilson95_low": max(0.0, center-half),
            "wilson95_high": min(1.0, center+half)}


def planning_values(rows, kind, exploration_only=False):
    selected = []
    for row in rows:
        if row.get("kind") != kind or not row.get("total_ms"):
            continue
        if exploration_only and int(row.get("global_sequence") or 0) <= 0:
            continue
        selected.append(float(row["total_ms"]))
    return selected


def metric_value(summary, component, metric, statistic):
    return optional_float(summary.get("components", {}).get(component, {})
                          .get(metric, {}).get(statistic))


def summarize_run(run_dir, task_id="", attempt=None, attempt_status=""):
    run_dir = Path(run_dir).resolve()
    try:
        run = load_json(run_dir / "run.json")
        summary = load_json(run_dir / "summary.json")
    except (OSError, ValueError):
        return {field: None for field in RUN_FIELDS} | {
            "run_id": "%s_attempt%02d" % (task_id or "unknown", attempt or 0),
            "task_id": task_id, "attempt": attempt, "result_dir": str(run_dir),
            "status": attempt_status, "outcome": "UNREADABLE_RESULT",
            "manifest_readable": False,
        }
    events = load_jsonl(run_dir / "events.jsonl")
    trajectory = load_csv(run_dir / "trajectory.csv")
    planning = load_csv(run_dir / "planning.csv")
    alignment = (load_json(run_dir / "trajectory_alignment_summary.json")
                 if (run_dir / "trajectory_alignment_summary.json").is_file() else {})
    resources = (load_json(run_dir / "resource_summary.json")
                 if (run_dir / "resource_summary.json").is_file() else {})
    coverage = summary.get("coverage") or {}
    collision = summary.get("collision") or {}
    planning_start = optional_float(run.get("planning_start_sim"))
    completion = first_state_time(events, {"RETURNING_HOME", "RETURN_BLOCKED"})
    home = first_state_time(events, {"HOME_REACHED"})
    at_completion = latest_at_or_before(trajectory, completion)
    global_times = planning_values(planning, "global")
    local_times = planning_values(planning, "local", exploration_only=True)
    primary_alignment = alignment.get("metrics", {})

    def threshold(name):
        value = coverage.get("thresholds", {}).get(name, {})
        return optional_float(value.get("seconds")), bool(value.get("censored", True))

    t80, t80_censored = threshold("T80")
    t90, t90_censored = threshold("T90")
    t95, t95_censored = threshold("T95")
    collision_valid = collision.get("status") == "VALID"
    row = {field: None for field in RUN_FIELDS}
    row.update({
        "run_id": "%s_attempt%02d" % (task_id or run_dir.name, attempt or 1),
        "task_id": task_id,
        "attempt": attempt or 1,
        "result_dir": str(run_dir),
        "environment_seed": run.get("environment_seed", run.get("seed")),
        "planner_seed": run.get("planner_seed", run.get("seed")),
        "mode": run.get("mode"),
        "status": run.get("status", attempt_status),
        "outcome": run.get("outcome"),
        "manifest_readable": True,
        "git_clean": not bool(run.get("git_status")),
        "algorithm_completed": completion is not None,
        "return_success": home is not None,
        "planning_start_sim": planning_start,
        "completion_sim": completion,
        "home_reached_sim": home,
        "exploration_duration_sim": (completion-planning_start
                                     if completion is not None and planning_start is not None else None),
        "return_duration_sim": (home-completion
                                if home is not None and completion is not None else None),
        "exploration_distance_m": optional_float(
            at_completion.get("mission_distance") if at_completion else None),
        "final_mission_distance_m": optional_float(summary.get("mission_distance")),
        "free_coverage": optional_float(coverage.get("free_coverage")),
        "surface_coverage": optional_float(coverage.get("surface_coverage")),
        "coverage_valid": bool(coverage.get("valid", False)),
        "coverage_status": summary.get("coverage_status"),
        "t80_seconds": t80, "t80_censored": t80_censored,
        "t90_seconds": t90, "t90_censored": t90_censored,
        "t95_seconds": t95, "t95_censored": t95_censored,
        "collision_status": collision.get("status"),
        "collision_episodes": collision.get("episode_count"),
        "collision_free": (collision.get("episode_count") == 0 if collision_valid else None),
        "trajectory_status": alignment.get("status"),
        "resource_status": resources.get("status"),
        "global_planning_count": len(global_times),
        "global_planning_mean_ms": statistics.mean(global_times) if global_times else None,
        "global_planning_p95_ms": percentile(global_times, 95) if global_times else None,
        "exploration_local_planning_count": len(local_times),
        "exploration_local_planning_mean_ms": (statistics.mean(local_times)
                                                if local_times else None),
        "exploration_local_planning_p95_ms": (percentile(local_times, 95)
                                               if local_times else None),
        "executed_to_bspline_length_ratio_mean": optional_float(
            primary_alignment.get("executed_to_bspline_length_ratio", {}).get("mean")),
        "odom_to_bspline_mean_distance_mean": optional_float(
            primary_alignment.get("odom_to_bspline_mean_distance", {}).get("mean")),
        "exploration_cpu_mean": metric_value(resources, "exploration",
                                              "cpu_percent_one_core", "mean"),
        "exploration_cpu_p95": metric_value(resources, "exploration",
                                             "cpu_percent_one_core", "p95"),
        "exploration_rss_mean_mib": metric_value(resources, "exploration", "rss_mib", "mean"),
        "exploration_rss_peak_mib": metric_value(resources, "exploration", "rss_mib", "max"),
        "logger_cpu_mean": metric_value(resources, "logger", "cpu_percent_one_core", "mean"),
        "logger_rss_mean_mib": metric_value(resources, "logger", "rss_mib", "mean"),
        "simulator_cpu_mean": metric_value(resources, "simulator", "cpu_percent_one_core", "mean"),
        "simulator_rss_mean_mib": metric_value(resources, "simulator", "rss_mib", "mean"),
        "mean_rtf": optional_float(summary.get("rtf", {}).get("mean")),
        "mission_sim_duration": optional_float(summary.get("mission_sim_duration")),
        "mission_wall_duration": optional_float(summary.get("mission_wall_duration")),
    })
    return row


def rows_from_batch_state(state_path):
    state = load_json(state_path)
    rows = []
    for task in state["tasks"]:
        for attempt in task.get("attempts", []):
            result_dir = attempt.get("result_dir")
            if result_dir:
                rows.append(summarize_run(result_dir, task["task_id"],
                                          attempt.get("attempt"), attempt.get("status", "")))
            else:
                row = {field: None for field in RUN_FIELDS}
                row.update({
                    "run_id": "%s_attempt%02d" % (task["task_id"],
                                                    attempt.get("attempt", 0)),
                    "task_id": task["task_id"], "attempt": attempt.get("attempt"),
                    "environment_seed": task["environment_seed"],
                    "planner_seed": task["planner_seed"],
                    "status": attempt.get("status"),
                    "outcome": "MISSING_RESULT_DIR", "manifest_readable": False,
                })
                rows.append(row)
    return state, rows


def aggregate_rows(rows):
    readable = [row for row in rows if row["manifest_readable"]]
    coverage_valid = [row for row in readable if row["coverage_valid"]]
    collision_valid = [row for row in readable if row["collision_status"] == "VALID"]
    continuous = [
        "exploration_duration_sim", "return_duration_sim", "exploration_distance_m",
        "final_mission_distance_m", "free_coverage", "surface_coverage",
        "global_planning_mean_ms", "global_planning_p95_ms",
        "exploration_local_planning_mean_ms", "exploration_local_planning_p95_ms",
        "executed_to_bspline_length_ratio_mean", "odom_to_bspline_mean_distance_mean",
        "exploration_cpu_mean", "exploration_cpu_p95", "exploration_rss_mean_mib",
        "exploration_rss_peak_mib", "logger_cpu_mean", "logger_rss_mean_mib",
        "simulator_cpu_mean", "simulator_rss_mean_mib", "mean_rtf",
        "mission_sim_duration", "mission_wall_duration",
    ]

    def eligible_for_metric(name):
        if name in ("free_coverage", "surface_coverage"):
            return coverage_valid
        if name in ("executed_to_bspline_length_ratio_mean",
                    "odom_to_bspline_mean_distance_mean"):
            return [row for row in readable if row["trajectory_status"] == "VALID"]
        if (name.startswith("exploration_cpu") or name.startswith("exploration_rss") or
                name.startswith("logger_") or name.startswith("simulator_")):
            return [row for row in readable if row["resource_status"] == "VALID"]
        return readable
    thresholds = {}
    for name in ("t80", "t90", "t95"):
        attained = [row[name + "_seconds"] for row in coverage_valid
                    if not row[name + "_censored"] and row[name + "_seconds"] is not None]
        thresholds[name.upper()] = {
            "eligible_runs": len(coverage_valid),
            "attainment": rate_summary(len(attained), len(coverage_valid)),
            "censored_count": sum(bool(row[name + "_censored"]) for row in coverage_valid),
            "conditional_seconds": distribution_summary(attained),
        }
    return {
        "schema_version": 1,
        "attempt_count": len(rows),
        "readable_run_count": len(readable),
        "outcomes": dict(sorted(Counter(str(row["outcome"]) for row in rows).items())),
        "algorithm_completion": rate_summary(
            sum(bool(row["algorithm_completed"]) for row in readable), len(readable)),
        "return_success": rate_summary(
            sum(bool(row["return_success"]) for row in readable), len(readable)),
        "collision_free": rate_summary(
            sum(bool(row["collision_free"]) for row in collision_valid), len(collision_valid)),
        "coverage_valid": rate_summary(len(coverage_valid), len(readable)),
        "thresholds": thresholds,
        "continuous_metrics": {
            name: distribution_summary([row[name] for row in eligible_for_metric(name)])
            for name in continuous
        },
        "selection_notes": {
            "attempts": "all recorded attempts, including failures and retries",
            "rates": "all readable run manifests unless an eligible subset is stated",
            "threshold_times": "conditional on valid Coverage and threshold attainment; censored runs retained separately",
            "continuous_metrics": "non-null values from readable runs; Coverage, trajectory, and resource metrics additionally require their own VALID status",
        },
    }


def write_outputs(rows, output_dir, aggregate):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "runs.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=RUN_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows({key: "" if value is None else value for key, value in row.items()}
                         for row in rows)
    atomic_write_json(output_dir / "aggregate.json", aggregate)
