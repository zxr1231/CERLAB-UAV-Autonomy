"""ROS-independent planning/execution interval bookkeeping for Phase R2."""

import math


INTERVAL_FIELDS = [
    "interval_id", "trajectory_id", "global_sequence", "start_sim", "end_sim",
    "duration_sim", "start_wall", "end_wall", "duration_wall", "start_reason",
    "end_reason", "start_map_version", "end_map_version", "start_depth_sequence",
    "end_depth_sequence", "odom_count", "executed_distance", "start_x", "start_y",
    "start_z", "start_yaw", "end_x", "end_y", "end_z", "end_yaw", "valid",
    "errors",
]


class ExecutionIntervalTracker:
    def __init__(self):
        self.active = None
        self.completed_count = 0

    @staticmethod
    def _pose(position, yaw):
        if position is None:
            return None
        values = tuple(float(value) for value in position)
        if len(values) != 3 or not all(math.isfinite(value) for value in values):
            raise ValueError("execution pose must contain three finite coordinates")
        yaw = float(yaw)
        if not math.isfinite(yaw):
            raise ValueError("execution yaw must be finite")
        return values + (yaw,)

    def start(self, trajectory_id, global_sequence, sim_time, wall_time, reason,
              map_version=None, depth_sequence=None, position=None, yaw=0.0):
        trajectory_id = int(trajectory_id)
        if trajectory_id <= 0:
            raise ValueError("trajectory_id must be positive")
        closed = self.close(sim_time, wall_time, "SUPERSEDED_BY_TRAJECTORY",
                            map_version, depth_sequence)
        pose = self._pose(position, yaw)
        self.active = {
            "interval_id": trajectory_id,
            "trajectory_id": trajectory_id,
            "global_sequence": int(global_sequence or 0),
            "start_sim": float(sim_time),
            "start_wall": float(wall_time),
            "start_reason": str(reason or "unspecified"),
            "start_map_version": (None if map_version is None else int(map_version)),
            "start_depth_sequence": (None if depth_sequence is None else int(depth_sequence)),
            "odom_count": 0,
            "executed_distance": 0.0,
            "start_pose": pose,
            "end_pose": pose,
            "last_odom_sim": None,
        }
        return closed

    def observe_odom(self, sim_time, position, yaw, distance_increment=0.0):
        if self.active is None:
            return False
        pose = self._pose(position, yaw)
        sim_time = float(sim_time)
        if self.active["odom_count"] > 0:
            increment = float(distance_increment)
            if math.isfinite(increment) and increment >= 0:
                self.active["executed_distance"] += increment
        else:
            self.active["start_pose"] = pose
        self.active["end_pose"] = pose
        self.active["last_odom_sim"] = sim_time
        self.active["odom_count"] += 1
        return True

    def close(self, sim_time, wall_time, reason, map_version=None, depth_sequence=None):
        if self.active is None:
            return None
        active = self.active
        self.active = None
        end_sim = float(sim_time)
        end_wall = float(wall_time)
        errors = []
        if end_sim < active["start_sim"]:
            errors.append("SIM_TIME_REVERSED")
        if end_wall < active["start_wall"]:
            errors.append("WALL_TIME_REVERSED")
        start_pose = active["start_pose"]
        end_pose = active["end_pose"]
        row = {
            "interval_id": active["interval_id"],
            "trajectory_id": active["trajectory_id"],
            "global_sequence": active["global_sequence"],
            "start_sim": active["start_sim"],
            "end_sim": end_sim,
            "duration_sim": max(0.0, end_sim-active["start_sim"]),
            "start_wall": active["start_wall"],
            "end_wall": end_wall,
            "duration_wall": max(0.0, end_wall-active["start_wall"]),
            "start_reason": active["start_reason"],
            "end_reason": str(reason or "unspecified"),
            "start_map_version": active["start_map_version"],
            "end_map_version": None if map_version is None else int(map_version),
            "start_depth_sequence": active["start_depth_sequence"],
            "end_depth_sequence": None if depth_sequence is None else int(depth_sequence),
            "odom_count": active["odom_count"],
            "executed_distance": active["executed_distance"],
            "start_x": None if start_pose is None else start_pose[0],
            "start_y": None if start_pose is None else start_pose[1],
            "start_z": None if start_pose is None else start_pose[2],
            "start_yaw": None if start_pose is None else start_pose[3],
            "end_x": None if end_pose is None else end_pose[0],
            "end_y": None if end_pose is None else end_pose[1],
            "end_z": None if end_pose is None else end_pose[2],
            "end_yaw": None if end_pose is None else end_pose[3],
            "valid": not errors,
            "errors": errors,
        }
        self.completed_count += 1
        return row
