"""Deterministic batch-matrix configuration and state helpers."""
import hashlib
import json

from exploration_benchmark.core import resolve_seeds, safe_component


TERMINAL_FAILURES = {"FAILED", "TIMEOUT", "PROCESS_ERROR", "USER_ABORT"}


def canonical_hash(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def parse_matrix_config(value):
    if int(value.get("schema_version", 0)) != 1:
        raise ValueError("matrix schema_version must be 1")
    experiment_id = safe_component(value["experiment_id"])
    mode = value.get("mode", "full")
    if mode not in ("smoke", "full"):
        raise ValueError("mode must be smoke or full")
    timeout = float(value.get("timeout", 900))
    repeats = int(value.get("repeats", 1))
    if timeout <= 0 or repeats <= 0:
        raise ValueError("timeout and repeats must be positive")
    pairs = value.get("seed_pairs")
    if not isinstance(pairs, list) or not pairs:
        raise ValueError("seed_pairs must be a non-empty list")
    gain_modes = value.get("path_gain_modes", ["legacy"])
    if (not isinstance(gain_modes, list) or not gain_modes or
            len(gain_modes) != len(set(gain_modes)) or
            any(item not in ("legacy", "unique_shadow", "unique_online")
                for item in gain_modes)):
        raise ValueError("path_gain_modes must be distinct supported modes")
    tasks = []
    seen = set()
    for pair in pairs:
        if isinstance(pair, dict):
            environment_seed, planner_seed = resolve_seeds(
                environment_seed=pair.get("environment_seed"),
                planner_seed=pair.get("planner_seed"))
        elif isinstance(pair, list) and len(pair) == 2:
            environment_seed, planner_seed = resolve_seeds(
                environment_seed=pair[0], planner_seed=pair[1])
        else:
            raise ValueError("each seed pair must be [environment, planner] or an object")
        for repeat in range(1, repeats + 1):
            for gain_mode in gain_modes:
                identifier = "env%03d_planner%03d_repeat%02d" % (
                    environment_seed, planner_seed, repeat)
                if "path_gain_modes" in value:
                    identifier += "_" + gain_mode
                if identifier in seen:
                    raise ValueError("duplicate matrix task: %s" % identifier)
                seen.add(identifier)
                tasks.append({
                    "task_id": identifier,
                    "environment_seed": environment_seed,
                    "planner_seed": planner_seed,
                    "repeat": repeat,
                    "path_gain_mode": gain_mode,
                    "status": "PENDING",
                    "attempts": [],
                })
    return {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "method": str(value.get("method", "hire_return_home_500")),
        "mode": mode,
        "timeout": timeout,
        "rviz": bool(value.get("rviz", False)),
        "disable_coverage": bool(value.get("disable_coverage", False)),
        "path_gain_modes": gain_modes,
        "tasks": tasks,
    }


def eligible_tasks(tasks, retry_failed=False):
    eligible = []
    for task in tasks:
        status = task["status"]
        if status in ("PENDING", "INTERRUPTED"):
            eligible.append(task)
        elif retry_failed and status in TERMINAL_FAILURES:
            eligible.append(task)
    return eligible


def recover_running_tasks(tasks):
    recovered = 0
    for task in tasks:
        if task["status"] == "RUNNING":
            task["status"] = "INTERRUPTED"
            if task["attempts"] and task["attempts"][-1].get("status") == "RUNNING":
                task["attempts"][-1]["status"] = "INTERRUPTED"
            recovered += 1
    return recovered
