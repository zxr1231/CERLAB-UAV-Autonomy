"""ROS-independent benchmark accounting helpers."""
import json
import math
import os
from pathlib import Path


class TrajectoryAccumulator:
    def __init__(self, jump_threshold=2.0, noise_threshold=1e-4):
        self.jump_threshold = float(jump_threshold)
        self.noise_threshold = float(noise_threshold)
        self.last_time = None
        self.last_position = None
        self.distance = 0.0

    def update(self, sim_time, position):
        sim_time = float(sim_time)
        position = tuple(float(value) for value in position)
        event = None
        increment = 0.0
        if self.last_time is not None:
            if sim_time < self.last_time:
                event = "ODOM_TIME_RESET"
            else:
                displacement = math.sqrt(sum((a-b) ** 2 for a, b in zip(position, self.last_position)))
                if displacement > self.jump_threshold:
                    event = "ODOM_JUMP"
                elif displacement >= self.noise_threshold:
                    increment = displacement
                    self.distance += displacement
        self.last_time = sim_time
        self.last_position = position
        return increment, event


def percentile(values, percent):
    values = sorted(float(value) for value in values)
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    rank = (len(values) - 1) * float(percent) / 100.0
    lower = int(math.floor(rank))
    upper = int(math.ceil(rank))
    if lower == upper:
        return values[lower]
    return values[lower] + (rank-lower) * (values[upper]-values[lower])


def duration_summary(values):
    values = [float(value) for value in values]
    if not values:
        return {"count": 0, "mean_ms": None, "p95_ms": None, "max_ms": None}
    return {
        "count": len(values),
        "mean_ms": sum(values) / len(values),
        "p95_ms": percentile(values, 95),
        "max_ms": max(values),
    }


def value_summary(values):
    summary = duration_summary(values)
    return {"count": summary["count"], "mean": summary["mean_ms"],
            "p95": summary["p95_ms"], "max": summary["max_ms"]}


def safe_component(value):
    value = str(value)
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
    if not value or value in (".", "..") or any(char not in allowed for char in value):
        raise ValueError("unsafe result path component: %r" % value)
    return value


def create_run_directory(results_root, experiment_id, seed, timestamp):
    path = (Path(results_root) / safe_component(experiment_id) /
            ("seed_%03d" % int(seed)) / safe_component(timestamp))
    path.mkdir(parents=True, exist_ok=False)
    return path


def atomic_write_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(str(temporary), str(path))
