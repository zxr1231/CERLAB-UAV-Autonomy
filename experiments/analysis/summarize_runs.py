#!/usr/bin/env python3
"""Create a lightweight per-run table from CERLAB benchmark result folders."""
import argparse
import csv
import json
from pathlib import Path


FIELDS = [
    "run_id", "seed", "status", "outcome", "exploration_completed",
    "return_success", "return_blocked_count", "mission_start_sim",
    "confirming_complete_sim", "return_start_sim", "home_reached_sim",
    "exploration_duration_sim", "return_duration_sim",
    "distance_at_return_start", "map_points_at_return_start",
    "planning_events_at_return_start", "global_events_at_return_start",
    "local_events_at_return_start", "local_planning_mean_ms_at_return_start",
    "local_planning_p95_ms_at_return_start",
    "final_mission_distance", "final_map_points", "global_planning_count",
    "global_planning_mean_ms", "global_planning_p95_ms",
    "all_planning_event_count", "mean_rtf", "coverage_status",
]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def load_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def latest_at_or_before(rows, sim_time):
    eligible = [row for row in rows if row.get("sim_time") and
                float(row["sim_time"]) <= sim_time]
    return eligible[-1] if eligible else None


def state_times(events, state):
    return [float(event["sim_time"]) for event in events
            if event.get("event") == "MISSION_STATE" and
            event.get("current") == state]


def optional_float(value):
    return "" if value is None or value == "" else float(value)


def percentile(values, percentage):
    if not values:
        return ""
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentage / 100.0
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def summarize(run_dir):
    run_dir = Path(run_dir).resolve()
    run = load_json(run_dir / "run.json")
    summary = load_json(run_dir / "summary.json")
    events = load_jsonl(run_dir / "events.jsonl")
    trajectory = load_csv(run_dir / "trajectory.csv")
    metrics = load_csv(run_dir / "metrics.csv")
    planning = load_csv(run_dir / "planning.csv")

    returning = state_times(events, "RETURNING_HOME")
    home = state_times(events, "HOME_REACHED")
    confirming = state_times(events, "CONFIRMING_COMPLETE")
    return_start = returning[0] if returning else None
    home_time = home[0] if home else None
    confirmation = max((time for time in confirming
                        if return_start is None or time <= return_start), default=None)
    trajectory_at_return = (latest_at_or_before(trajectory, return_start)
                            if return_start is not None else None)
    metrics_at_return = (latest_at_or_before(metrics, return_start)
                         if return_start is not None else None)
    planning_at_return = ([row for row in planning if row.get("sim_time") and
                           return_start is not None and
                           float(row["sim_time"]) <= return_start])
    local_times_at_return = [float(row["total_ms"]) for row in planning_at_return
                             if row.get("kind") == "local" and row.get("total_ms")]
    mission_start = summary.get("mission_start_sim")
    global_metrics = summary.get("planning", {}).get("global", {})

    return {
        "run_id": "%s_seed_%03d_%s" % (run.get("mode", "unknown"), run["seed"],
                                         run_dir.name),
        "seed": run["seed"],
        "status": run["status"],
        "outcome": run["outcome"],
        "exploration_completed": return_start is not None,
        "return_success": home_time is not None,
        "return_blocked_count": len(state_times(events, "RETURN_BLOCKED")),
        "mission_start_sim": optional_float(mission_start),
        "confirming_complete_sim": optional_float(confirmation),
        "return_start_sim": optional_float(return_start),
        "home_reached_sim": optional_float(home_time),
        "exploration_duration_sim": optional_float(
            return_start - mission_start if return_start is not None and
            mission_start is not None else None),
        "return_duration_sim": optional_float(
            home_time - return_start if home_time is not None and
            return_start is not None else None),
        "distance_at_return_start": optional_float(
            trajectory_at_return.get("mission_distance")
            if trajectory_at_return else None),
        "map_points_at_return_start": (int(metrics_at_return["map_points"])
                                       if metrics_at_return else ""),
        "planning_events_at_return_start": len(planning_at_return),
        "global_events_at_return_start": sum(
            row.get("kind") == "global" for row in planning_at_return),
        "local_events_at_return_start": sum(
            row.get("kind") == "local" for row in planning_at_return),
        "local_planning_mean_ms_at_return_start": (
            sum(local_times_at_return) / len(local_times_at_return)
            if local_times_at_return else ""),
        "local_planning_p95_ms_at_return_start": percentile(
            local_times_at_return, 95),
        "final_mission_distance": optional_float(summary.get("mission_distance")),
        "final_map_points": summary.get("map_points", ""),
        "global_planning_count": global_metrics.get("count", ""),
        "global_planning_mean_ms": global_metrics.get("mean_ms", ""),
        "global_planning_p95_ms": global_metrics.get("p95_ms", ""),
        "all_planning_event_count": summary.get("planning_event_count", ""),
        "mean_rtf": summary.get("rtf", {}).get("mean", ""),
        "coverage_status": summary.get("coverage_status", ""),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("run_dirs", nargs="+")
    args = parser.parse_args()
    rows = [summarize(path) for path in args.run_dirs]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(output)


if __name__ == "__main__":
    main()
