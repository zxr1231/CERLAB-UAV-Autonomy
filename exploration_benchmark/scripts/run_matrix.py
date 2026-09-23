#!/usr/bin/env python3
"""Run a resumable, serial matrix of isolated CERLAB benchmark trials."""
import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

from exploration_benchmark.batch import (canonical_hash, eligible_tasks,
                                         parse_matrix_config, recover_running_tasks)
from exploration_benchmark.core import atomic_write_json


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def load_json(path):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream)


def find_result_path(stdout, results_root):
    results_root = Path(results_root).resolve()
    for line in reversed(stdout.splitlines()):
        candidate = Path(line.strip())
        if not candidate.is_dir():
            continue
        candidate = candidate.resolve()
        try:
            candidate.relative_to(results_root)
        except ValueError:
            continue
        if (candidate / "run.json").is_file():
            return candidate
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--workspace", default="/home/zxr2/cerlab_benchmark_ws")
    parser.add_argument("--results-root", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--max-tasks", type=int)
    args = parser.parse_args()
    if args.max_tasks is not None and args.max_tasks <= 0:
        parser.error("--max-tasks must be positive")

    config_path = Path(args.config).resolve()
    raw_config = load_json(config_path)
    matrix = parse_matrix_config(raw_config)
    config_hash = canonical_hash(raw_config)
    workspace = Path(args.workspace).resolve()
    results_root = (Path(args.results_root).resolve() if args.results_root else
                    workspace / "results")
    batch_root = results_root / matrix["experiment_id"]
    state_path = batch_root / "batch_state.json"

    if state_path.exists():
        state = load_json(state_path)
        if state.get("config_sha256") != config_hash:
            raise RuntimeError("existing batch_state.json has a different config hash")
        recover_running_tasks(state["tasks"])
    else:
        state = {
            "schema_version": 1,
            "experiment_id": matrix["experiment_id"],
            "method": matrix["method"],
            "config_path": str(config_path),
            "config_sha256": config_hash,
            "created_utc": utc_now(),
            "updated_utc": utc_now(),
            "tasks": matrix["tasks"],
        }

    scheduled = eligible_tasks(state["tasks"], args.retry_failed)
    if args.max_tasks is not None:
        scheduled = scheduled[:args.max_tasks]
    plan = {
        "experiment_id": matrix["experiment_id"],
        "config_sha256": config_hash,
        "total_tasks": len(state["tasks"]),
        "scheduled_tasks": [task["task_id"] for task in scheduled],
        "skipped_tasks": [task["task_id"] for task in state["tasks"]
                          if task not in scheduled],
    }
    if args.dry_run:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0

    batch_root.mkdir(parents=True, exist_ok=True)
    state["updated_utc"] = utc_now()
    state["last_plan"] = plan
    atomic_write_json(state_path, state)
    runner = Path(__file__).resolve().with_name("run_experiment.py")
    for task in scheduled:
        command = [
            sys.executable, str(runner),
            "--workspace", str(workspace),
            "--results-root", str(results_root),
            "--experiment-id", matrix["experiment_id"],
            "--environment-seed", str(task["environment_seed"]),
            "--planner-seed", str(task["planner_seed"]),
            "--mode", matrix["mode"],
            "--timeout", str(matrix["timeout"]),
            "--path-gain-mode", task.get("path_gain_mode", "legacy"),
        ]
        if matrix["rviz"]:
            command.append("--rviz")
        if matrix["disable_coverage"]:
            command.append("--disable-coverage")
        attempt = {"attempt": len(task["attempts"]) + 1, "status": "RUNNING",
                   "start_utc": utc_now(), "command": command}
        task["attempts"].append(attempt)
        task["status"] = "RUNNING"
        state["updated_utc"] = utc_now()
        atomic_write_json(state_path, state)
        try:
            completed = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        except KeyboardInterrupt:
            attempt.update({"status": "INTERRUPTED", "end_utc": utc_now()})
            task["status"] = "INTERRUPTED"
            state["updated_utc"] = utc_now()
            atomic_write_json(state_path, state)
            return 130
        result_path = find_result_path(completed.stdout, results_root)
        outcome = None
        if result_path is not None:
            try:
                outcome = load_json(result_path / "run.json").get("outcome")
            except (OSError, ValueError):
                outcome = "INVALID_RUN_MANIFEST"
        status = "SUCCESS" if completed.returncode == 0 and outcome == "HOME_REACHED" else (
            outcome if outcome in ("TIMEOUT", "PROCESS_ERROR", "USER_ABORT") else "FAILED")
        attempt.update({
            "status": status,
            "end_utc": utc_now(),
            "returncode": completed.returncode,
            "result_dir": None if result_path is None else str(result_path),
            "outcome": outcome,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        })
        task["status"] = status
        state["updated_utc"] = utc_now()
        atomic_write_json(state_path, state)

    counts = {}
    for task in state["tasks"]:
        counts[task["status"]] = counts.get(task["status"], 0) + 1
    state["status_counts"] = counts
    state["updated_utc"] = utc_now()
    atomic_write_json(state_path, state)
    print(str(state_path))
    return 1 if any(task["status"] in ("FAILED", "TIMEOUT", "PROCESS_ERROR",
                                       "USER_ABORT", "INTERRUPTED")
                    for task in state["tasks"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
