#!/usr/bin/env python3
"""Lightweight scalar, trajectory and planner-event logger; no rosbag."""
import csv
import json
import math
import threading
import time
from pathlib import Path

import rospy
from nav_msgs.msg import Odometry
from sensor_msgs.msg import PointCloud2
from std_msgs.msg import String

from exploration_benchmark.core import (TrajectoryAccumulator, atomic_write_json,
                                        duration_summary, value_summary)


class BenchmarkLogger:
    def __init__(self):
        output_value = rospy.get_param("~output_dir", "")
        if not output_value:
            raise RuntimeError("~output_dir is required")
        self.output = Path(output_value).resolve()
        self.output.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.closed = False
        self.wall_start = time.monotonic()
        self.sim_start = None
        self.sim_end = None
        self.mission_start_sim = None
        self.mission_end_sim = None
        self.mission_start_wall = None
        self.mission_end_wall = None
        self.mission_distance_start = None
        self.state = "UNKNOWN"
        self.map_points = 0
        self.odom_count = 0
        self.map_count = 0
        self.planning_count = 0
        self.global_times = []
        self.local_times = []
        self.return_times = []
        self.rtf_values = []
        self.trajectory = TrajectoryAccumulator(
            rospy.get_param("~odom_jump_threshold", 2.0),
            rospy.get_param("~odom_noise_threshold", 1e-4))
        self.previous_metric_sim = None
        self.previous_metric_wall = None

        self.trajectory_file, self.trajectory_writer = self._csv(
            "trajectory.csv", ["sim_time", "wall_elapsed", "x", "y", "z", "yaw",
                               "vx", "vy", "vz", "distance_increment", "cumulative_distance",
                               "mission_distance"])
        self.metrics_file, self.metrics_writer = self._csv(
            "metrics.csv", ["sim_time", "wall_elapsed", "mission_state", "map_points",
                            "cumulative_distance", "mission_distance", "odom_count",
                            "map_message_count", "rtf"])
        self.planning_file, self.planning_writer = self._csv(
            "planning.csv", ["sim_time", "wall_elapsed", "kind", "sequence", "success",
                             "recovery_used", "total_ms", "frontier_ms", "roadmap_ms",
                             "prune_ms", "gain_update_ms", "goal_selection_ms",
                             "candidate_search_ms", "path_scoring_ms", "input_path_ms",
                             "update_path_ms", "bspline_ms", "roadmap_nodes",
                             "goal_candidates", "candidate_paths", "best_path_gain",
                             "dynamic_obstacles", "path_poses", "raw_json"])
        self.events_file = (self.output / "events.jsonl").open("x", encoding="utf-8")

        rospy.Subscriber("/CERLAB/quadcopter/odom", Odometry, self.odom_callback, queue_size=50)
        rospy.Subscriber("/dynamic_map/explored_voxel_map", PointCloud2, self.map_callback, queue_size=1)
        rospy.Subscriber("/dynamicExploration/mission_state", String, self.state_callback, queue_size=20)
        rospy.Subscriber("/dynamicExploration/planning_event", String, self.planning_callback, queue_size=100)
        self.timer = rospy.Timer(rospy.Duration(1.0), self.metric_timer)
        rospy.on_shutdown(self.close)
        self.event("LOGGER_STARTED")

    def _csv(self, name, fields):
        stream = (self.output / name).open("x", newline="", encoding="utf-8")
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        stream.flush()
        return stream, writer

    @staticmethod
    def yaw(quaternion):
        siny = 2.0 * (quaternion.w * quaternion.z + quaternion.x * quaternion.y)
        cosy = 1.0 - 2.0 * (quaternion.y ** 2 + quaternion.z ** 2)
        return math.atan2(siny, cosy)

    def wall_elapsed(self):
        return time.monotonic() - self.wall_start

    def event(self, name, **fields):
        payload = {"event": name, "sim_time": rospy.get_time(),
                   "wall_elapsed": self.wall_elapsed()}
        payload.update(fields)
        self.events_file.write(json.dumps(payload, sort_keys=True) + "\n")
        self.events_file.flush()

    def odom_callback(self, message):
        with self.lock:
            sim_time = message.header.stamp.to_sec() or rospy.get_time()
            position = message.pose.pose.position
            velocity = message.twist.twist.linear
            increment, warning = self.trajectory.update(
                sim_time, (position.x, position.y, position.z))
            self.odom_count += 1
            if self.sim_start is None:
                self.sim_start = sim_time
            self.sim_end = sim_time
            if warning:
                self.event(warning, x=position.x, y=position.y, z=position.z)
            self.trajectory_writer.writerow({
                "sim_time": "%.6f" % sim_time,
                "wall_elapsed": "%.6f" % self.wall_elapsed(),
                "x": position.x, "y": position.y, "z": position.z,
                "yaw": self.yaw(message.pose.pose.orientation),
                "vx": velocity.x, "vy": velocity.y, "vz": velocity.z,
                "distance_increment": increment,
                "cumulative_distance": self.trajectory.distance,
                "mission_distance": "" if self.mission_distance_start is None else
                                    self.trajectory.distance-self.mission_distance_start,
            })
            if self.odom_count % 30 == 0:
                self.trajectory_file.flush()

    def map_callback(self, message):
        with self.lock:
            self.map_points = int(message.width) * int(message.height)
            self.map_count += 1

    def state_callback(self, message):
        with self.lock:
            if message.data != self.state:
                old_state = self.state
                self.state = message.data
                self.event("MISSION_STATE", previous=old_state, current=self.state)
                if self.state == "EXPLORING" and self.mission_start_sim is None:
                    self.mission_start_sim = rospy.get_time()
                    self.mission_start_wall = self.wall_elapsed()
                    self.mission_distance_start = self.trajectory.distance
                if self.state == "HOME_REACHED" and self.mission_end_sim is None:
                    self.mission_end_sim = rospy.get_time()
                    self.mission_end_wall = self.wall_elapsed()

    def planning_callback(self, message):
        with self.lock:
            try:
                payload = json.loads(message.data)
            except (TypeError, ValueError) as error:
                self.event("INVALID_PLANNING_EVENT", error=str(error), raw=message.data)
                return
            kind = payload.get("kind", "unknown")
            total = payload.get("total_ms")
            if isinstance(total, (int, float)):
                {"global": self.global_times, "local": self.local_times,
                 "return": self.return_times}.get(kind, []).append(float(total))
            self.planning_count += 1
            fields = ["sequence", "success", "recovery_used", "total_ms", "frontier_ms",
                      "roadmap_ms", "prune_ms", "gain_update_ms", "goal_selection_ms",
                      "candidate_search_ms", "path_scoring_ms", "input_path_ms",
                      "update_path_ms", "bspline_ms", "roadmap_nodes", "goal_candidates",
                      "candidate_paths", "best_path_gain", "dynamic_obstacles", "path_poses"]
            row = {field: payload.get(field, "") for field in fields}
            row.update({"sim_time": payload.get("sim_time", rospy.get_time()),
                        "wall_elapsed": self.wall_elapsed(), "kind": kind,
                        "raw_json": message.data})
            self.planning_writer.writerow(row)
            self.planning_file.flush()

    def metric_timer(self, _event):
        with self.lock:
            sim_time = rospy.get_time()
            wall_time = self.wall_elapsed()
            rtf = ""
            if self.previous_metric_sim is not None:
                delta_wall = wall_time - self.previous_metric_wall
                delta_sim = sim_time - self.previous_metric_sim
                if delta_sim < 0:
                    self.event("SIM_TIME_RESET")
                elif delta_wall > 0:
                    rtf = delta_sim / delta_wall
                    self.rtf_values.append(rtf)
            self.previous_metric_sim = sim_time
            self.previous_metric_wall = wall_time
            self.metrics_writer.writerow({
                "sim_time": "%.6f" % sim_time,
                "wall_elapsed": "%.6f" % wall_time,
                "mission_state": self.state,
                "map_points": self.map_points,
                "cumulative_distance": self.trajectory.distance,
                "mission_distance": None if self.mission_distance_start is None else
                                    self.trajectory.distance-self.mission_distance_start,
                "odom_count": self.odom_count,
                "map_message_count": self.map_count,
                "rtf": rtf,
            })
            self.metrics_file.flush()
            atomic_write_json(self.output / "live_status.json", {
                "sim_time": sim_time, "wall_elapsed": wall_time,
                "mission_state": self.state, "map_points": self.map_points,
                "cumulative_distance": self.trajectory.distance,
                "mission_distance": None if self.mission_distance_start is None else
                                    self.trajectory.distance-self.mission_distance_start,
                "odom_count": self.odom_count, "planning_count": self.planning_count,
            })

    def close(self):
        with self.lock:
            if self.closed:
                return
            self.closed = True
            self.event("LOGGER_STOPPED")
            for stream in (self.trajectory_file, self.metrics_file,
                           self.planning_file, self.events_file):
                stream.flush()
                stream.close()
            summary = {
                "mission_state": self.state,
                "passed": self.state == "HOME_REACHED",
                "sim_start": self.sim_start,
                "sim_end": self.sim_end,
                "sim_duration": None if self.sim_start is None or self.sim_end is None else self.sim_end-self.sim_start,
                "mission_start_sim": self.mission_start_sim,
                "mission_end_sim": self.mission_end_sim,
                "mission_sim_duration": None if self.mission_start_sim is None or self.mission_end_sim is None else self.mission_end_sim-self.mission_start_sim,
                "mission_wall_duration": None if self.mission_start_wall is None or self.mission_end_wall is None else self.mission_end_wall-self.mission_start_wall,
                "wall_duration": self.wall_elapsed(),
                "map_points": self.map_points,
                "cumulative_distance": self.trajectory.distance,
                "mission_distance": None if self.mission_distance_start is None else self.trajectory.distance-self.mission_distance_start,
                "odom_count": self.odom_count,
                "map_message_count": self.map_count,
                "planning_event_count": self.planning_count,
                "planning": {
                    "global": duration_summary(self.global_times),
                    "local": duration_summary(self.local_times),
                    "return": duration_summary(self.return_times),
                },
                "rtf": value_summary(self.rtf_values),
                "coverage_status": "UNAVAILABLE_NO_VERIFIED_DENOMINATOR",
            }
            atomic_write_json(self.output / "summary.json", summary)


if __name__ == "__main__":
    rospy.init_node("exploration_benchmark_logger")
    try:
        BenchmarkLogger()
        rospy.spin()
    except Exception as error:
        rospy.logfatal("Benchmark logger failed: %s", error)
        raise
