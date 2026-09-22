#!/usr/bin/env python3
"""Lightweight scalar, trajectory and planner-event logger; no rosbag."""
import csv
import json
import math
import threading
import time
from pathlib import Path

import rospy
from gazebo_msgs.msg import ContactsState
from map_manager.msg import ObservedVoxelDelta
from nav_msgs.msg import Odometry
from sensor_msgs.msg import PointCloud2
from std_msgs.msg import String

from exploration_benchmark.core import (TrajectoryAccumulator, atomic_write_json,
                                        duration_summary, value_summary)
from exploration_benchmark.collision_metrics import CollisionEpisodeAccumulator
from exploration_benchmark.coverage import CoverageAccumulator
from exploration_benchmark.execution_intervals import (INTERVAL_FIELDS,
                                                        ExecutionIntervalTracker)


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
        self.planning_start_sim = None
        self.state = "UNKNOWN"
        self.map_points = 0
        self.odom_count = 0
        self.map_count = 0
        self.planning_count = 0
        self.active_trajectory_id = 0
        self.active_global_sequence = 0
        self.latest_odom = None
        self.execution_intervals = ExecutionIntervalTracker()
        self.observation_delta_count = 0
        self.recorded_path_keys = set()
        self.global_times = []
        self.local_times = []
        self.return_times = []
        self.rtf_values = []
        self.trajectory = TrajectoryAccumulator(
            rospy.get_param("~odom_jump_threshold", 2.0),
            rospy.get_param("~odom_noise_threshold", 1e-4))
        self.previous_metric_sim = None
        self.previous_metric_wall = None
        self.coverage = None
        self.coverage_reported_errors = set()
        self.coverage_reported_thresholds = set()
        self.collisions = CollisionEpisodeAccumulator(
            rospy.get_param("~collision_quiet_period", 0.1))
        mask_path = rospy.get_param("~ground_truth_mask", "")
        metadata_path = rospy.get_param("~ground_truth_metadata", "")
        if bool(mask_path) != bool(metadata_path):
            raise RuntimeError("ground-truth mask and metadata must be configured together")
        if mask_path:
            self.coverage = CoverageAccumulator(mask_path, metadata_path)

        self.trajectory_file, self.trajectory_writer = self._csv(
            "trajectory.csv", ["sim_time", "wall_elapsed", "x", "y", "z", "yaw",
                               "vx", "vy", "vz", "distance_increment", "cumulative_distance",
                               "mission_distance", "trajectory_id", "execution_interval_id",
                               "global_sequence"])
        self.metrics_file, self.metrics_writer = self._csv(
            "metrics.csv", ["sim_time", "wall_elapsed", "mission_state", "map_points",
                            "cumulative_distance", "mission_distance", "odom_count",
                            "map_message_count", "rtf"])
        self.planning_file, self.planning_writer = self._csv(
            "planning.csv", ["sim_time", "wall_elapsed", "kind", "schema_version",
                             "sequence", "success", "recovery_used", "replan_reason",
                             "map_version", "depth_sequence", "trajectory_start_sim",
                             "start_x", "start_y", "start_z", "start_yaw",
                             "execution_snapshot_written", "execution_snapshot_name",
                             "total_ms", "frontier_ms", "roadmap_ms",
                             "prune_ms", "gain_update_ms", "goal_selection_ms",
                             "candidate_search_ms", "path_scoring_ms", "input_path_ms",
                             "update_path_ms", "bspline_ms", "roadmap_nodes",
                             "goal_candidates", "candidate_paths", "best_path_gain",
                             "gain_schema_version", "gain_mode", "selection_gain_mode",
                             "gain_sample_spacing", "unique_evaluator_available",
                             "unique_evaluation_status", "legacy_selected_candidate",
                             "unique_selected_candidate", "selected_raw_gain",
                             "selected_unique_gain", "selected_duplicate_ratio",
                             "unique_evaluation_ms", "unique_top1_changed",
                             "unique_score_margin", "gain_fallback_reason",
                             "dynamic_obstacles", "path_poses", "global_sequence",
                             "trajectory_id", "waypoint_index", "selected_path_length",
                             "selected_path_poses", "input_path_length",
                             "input_path_poses", "bspline_path_length",
                             "bspline_path_poses", "path_length", "raw_json"])
        self.execution_file, self.execution_writer = self._csv(
            "execution_intervals.csv", INTERVAL_FIELDS)
        self.coverage_file, self.coverage_writer = self._csv(
            "coverage.csv", ["sim_time", "wall_elapsed", "planning_elapsed",
                             "sequence", "raycast_id", "delta_count",
                             "new_unique_count", "observed_total_full_map",
                             "reconstructed_total_full_map", "observed_task",
                             "accessible_observed", "accessible_denominator",
                             "free_coverage", "surface_observed",
                             "surface_denominator", "surface_coverage",
                             "known_volume_m3", "valid", "errors"])
        self.collision_file, self.collision_writer = self._csv(
            "collisions.csv", ["episode_id", "phase", "start_sim", "end_sim",
                               "duration_sim", "wall_elapsed_recorded", "contact_pairs",
                               "max_force_n", "max_depth_m"])
        self.events_file = (self.output / "events.jsonl").open("x", encoding="utf-8")
        self.planned_paths_file = (self.output / "planned_paths.jsonl").open(
            "x", encoding="utf-8")
        self.observation_deltas_file = (self.output / "observation_deltas.jsonl").open(
            "x", encoding="utf-8")

        rospy.Subscriber("/CERLAB/quadcopter/odom", Odometry, self.odom_callback, queue_size=50)
        rospy.Subscriber("/dynamic_map/explored_voxel_map", PointCloud2, self.map_callback, queue_size=1)
        rospy.Subscriber("/dynamicExploration/mission_state", String, self.state_callback, queue_size=20)
        rospy.Subscriber("/dynamicExploration/planning_event", String, self.planning_callback, queue_size=100)
        rospy.Subscriber("/CERLAB/quadcopter/contacts", ContactsState,
                         self.collision_callback, queue_size=100)
        rospy.Subscriber("/dynamic_map/sensor_observation_delta", ObservedVoxelDelta,
                         self.observation_callback, queue_size=100)
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
            if self.closed:
                return
            sim_time = message.header.stamp.to_sec() or rospy.get_time()
            position = message.pose.pose.position
            velocity = message.twist.twist.linear
            yaw = self.yaw(message.pose.pose.orientation)
            increment, warning = self.trajectory.update(
                sim_time, (position.x, position.y, position.z))
            self.latest_odom = ((position.x, position.y, position.z), yaw)
            self.execution_intervals.observe_odom(
                sim_time, self.latest_odom[0], yaw, increment)
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
                "yaw": yaw,
                "vx": velocity.x, "vy": velocity.y, "vz": velocity.z,
                "distance_increment": increment,
                "cumulative_distance": self.trajectory.distance,
                "mission_distance": "" if self.mission_distance_start is None else
                                    self.trajectory.distance-self.mission_distance_start,
                "trajectory_id": self.active_trajectory_id,
                "execution_interval_id": self.active_trajectory_id,
                "global_sequence": self.active_global_sequence,
            })
            if self.odom_count % 30 == 0:
                self.trajectory_file.flush()

    def map_callback(self, message):
        with self.lock:
            if self.closed:
                return
            self.map_points = int(message.width) * int(message.height)
            self.map_count += 1

    def state_callback(self, message):
        with self.lock:
            if self.closed:
                return
            if message.data != self.state:
                old_state = self.state
                self.state = message.data
                self.event("MISSION_STATE", previous=old_state, current=self.state)
                if self.state in ("RETURNING_HOME", "HOME_REACHED"):
                    self.close_execution_interval("MISSION_STATE_" + self.state)
                if self.state == "EXPLORING" and self.mission_start_sim is None:
                    self.mission_start_sim = rospy.get_time()
                    self.mission_start_wall = self.wall_elapsed()
                    self.mission_distance_start = self.trajectory.distance
                if self.state == "HOME_REACHED" and self.mission_end_sim is None:
                    self.mission_end_sim = rospy.get_time()
                    self.mission_end_wall = self.wall_elapsed()

    def planning_callback(self, message):
        with self.lock:
            if self.closed:
                return
            try:
                payload = json.loads(message.data)
            except (TypeError, ValueError) as error:
                self.event("INVALID_PLANNING_EVENT", error=str(error), raw=message.data)
                return
            kind = payload.get("kind", "unknown")
            if (kind == "local" and payload.get("success") and payload.get("trajectory_id")):
                trajectory_id = int(payload["trajectory_id"])
                global_sequence = int(payload.get("global_sequence") or 0)
                pose = self.latest_odom
                closed = self.execution_intervals.start(
                    trajectory_id, global_sequence,
                    payload.get("trajectory_start_sim") or payload.get("sim_time", rospy.get_time()),
                    self.wall_elapsed(), payload.get("replan_reason", "unspecified"),
                    payload.get("map_version"), payload.get("depth_sequence"),
                    None if pose is None else pose[0], 0.0 if pose is None else pose[1])
                self.write_execution_interval(closed)
                self.active_trajectory_id = trajectory_id
                self.active_global_sequence = global_sequence
                self.event("EXECUTION_INTERVAL_STARTED", interval_id=trajectory_id,
                           global_sequence=global_sequence,
                           reason=payload.get("replan_reason", "unspecified"),
                           map_version=payload.get("map_version"),
                           depth_sequence=payload.get("depth_sequence"))
            total = payload.get("total_ms")
            if isinstance(total, (int, float)):
                {"global": self.global_times, "local": self.local_times,
                 "return": self.return_times}.get(kind, []).append(float(total))
            self.planning_count += 1
            fields = ["schema_version", "sequence", "success", "recovery_used",
                      "replan_reason", "map_version", "depth_sequence",
                      "trajectory_start_sim", "start_x", "start_y", "start_z",
                      "start_yaw", "execution_snapshot_written",
                      "execution_snapshot_name", "total_ms", "frontier_ms",
                      "roadmap_ms", "prune_ms", "gain_update_ms", "goal_selection_ms",
                      "candidate_search_ms", "path_scoring_ms", "input_path_ms",
                      "update_path_ms", "bspline_ms", "roadmap_nodes", "goal_candidates",
                      "candidate_paths", "best_path_gain", "dynamic_obstacles", "path_poses",
                      "gain_schema_version", "gain_mode", "selection_gain_mode",
                      "gain_sample_spacing", "unique_evaluator_available",
                      "unique_evaluation_status", "legacy_selected_candidate",
                      "unique_selected_candidate", "selected_raw_gain",
                      "selected_unique_gain", "selected_duplicate_ratio",
                      "unique_evaluation_ms", "unique_top1_changed",
                      "unique_score_margin", "gain_fallback_reason",
                      "global_sequence", "trajectory_id", "waypoint_index",
                      "selected_path_length", "selected_path_poses", "input_path_length",
                      "input_path_poses", "bspline_path_length", "bspline_path_poses",
                      "path_length"]
            row = {field: payload.get(field, "") for field in fields}
            row.update({"sim_time": payload.get("sim_time", rospy.get_time()),
                        "wall_elapsed": self.wall_elapsed(), "kind": kind,
                        "raw_json": message.data})
            self.planning_writer.writerow(row)
            self.planning_file.flush()
            if kind == "global":
                self.record_path("prm_raw", payload.get("sequence"),
                                 payload.get("raw_path_points"), payload)
                self.record_path("prm", payload.get("sequence"),
                                 payload.get("selected_path_points"), payload)
            elif kind == "local":
                self.record_path("input", payload.get("sequence"),
                                 payload.get("input_path_points"), payload)
                if payload.get("success"):
                    self.record_path("bspline", payload.get("trajectory_id"),
                                     payload.get("bspline_path_points"), payload)
            elif kind == "return":
                self.active_trajectory_id = 0
                self.active_global_sequence = 0
                self.record_path("return", payload.get("sequence"),
                                 payload.get("path_points"), payload)

    def record_path(self, kind, identifier, points, planning_payload):
        if not identifier or not isinstance(points, list):
            return
        identifier = int(identifier)
        key = (kind, identifier)
        if key in self.recorded_path_keys:
            self.event("DUPLICATE_PLANNED_PATH", kind=kind, identifier=identifier)
            return
        parsed = []
        try:
            for point in points:
                if len(point) != 3:
                    raise ValueError("point does not have three coordinates")
                parsed.append([float(value) for value in point])
        except (TypeError, ValueError) as error:
            self.event("INVALID_PLANNED_PATH", kind=kind, identifier=identifier,
                       error=str(error))
            return
        self.recorded_path_keys.add(key)
        length = sum(math.sqrt(sum((b[i]-a[i]) ** 2 for i in range(3)))
                     for a, b in zip(parsed, parsed[1:]))
        record = {
            "kind": kind,
            "id": identifier,
            "global_sequence": planning_payload.get("global_sequence"),
            "sim_time": planning_payload.get("sim_time", rospy.get_time()),
            "wall_elapsed": self.wall_elapsed(),
            "pose_count": len(parsed),
            "length": length,
            "points": parsed,
        }
        self.planned_paths_file.write(json.dumps(record, sort_keys=True) + "\n")
        self.planned_paths_file.flush()

    def write_execution_interval(self, row):
        if row is None:
            return
        serializable = dict(row)
        serializable["errors"] = json.dumps(serializable["errors"], sort_keys=True)
        self.execution_writer.writerow(serializable)
        self.execution_file.flush()
        self.event("EXECUTION_INTERVAL_ENDED", interval_id=row["interval_id"],
                   global_sequence=row["global_sequence"], reason=row["end_reason"],
                   duration_sim=row["duration_sim"], odom_count=row["odom_count"],
                   executed_distance=row["executed_distance"], valid=row["valid"])

    def close_execution_interval(self, reason, map_version=None, depth_sequence=None):
        row = self.execution_intervals.close(
            rospy.get_time(), self.wall_elapsed(), reason, map_version, depth_sequence)
        self.write_execution_interval(row)
        if row is not None:
            self.active_trajectory_id = 0
            self.active_global_sequence = 0

    def load_planning_start(self):
        if self.planning_start_sim is not None:
            return
        path = self.output / "planning_start.json"
        if not path.exists():
            return
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            sim_time = float(payload["sim_time"])
        except (OSError, ValueError, KeyError, TypeError) as error:
            message = "invalid planning_start.json: %s" % error
            if self.coverage is not None:
                self.coverage.invalidate(message)
            if message not in self.coverage_reported_errors:
                self.coverage_reported_errors.add(message)
                self.event("COVERAGE_INVALID", error=message)
            return
        self.planning_start_sim = sim_time
        if self.coverage is not None:
            self.coverage.set_planning_start(sim_time)
        self.event("PLANNING_ACTIVE", planning_start_sim=sim_time)

    def collision_phase(self):
        return "return" if self.state in ("RETURNING_HOME", "RETURN_BLOCKED",
                                           "HOME_REACHED") else "exploration"

    def record_collision_episodes(self, episodes):
        for episode in episodes:
            row = dict(episode)
            row["wall_elapsed_recorded"] = self.wall_elapsed()
            row["contact_pairs"] = json.dumps(row["contact_pairs"], sort_keys=True)
            self.collision_writer.writerow(row)
            self.collision_file.flush()
            self.event("COLLISION_ENDED", episode_id=episode["episode_id"],
                       phase=episode["phase"], start_sim=episode["start_sim"],
                       end_sim=episode["end_sim"])

    def collision_callback(self, message):
        with self.lock:
            if self.closed:
                return
            self.load_planning_start()
            sim_time = message.header.stamp.to_sec() or rospy.get_time()
            if self.planning_start_sim is None or sim_time < self.planning_start_sim:
                return
            pairs = []
            max_force = 0.0
            max_depth = 0.0
            for state in message.states:
                pair = " | ".join(sorted((state.collision1_name,
                                           state.collision2_name)))
                pairs.append(pair)
                force = state.total_wrench.force
                max_force = max(max_force,
                                math.sqrt(force.x ** 2 + force.y ** 2 + force.z ** 2))
                if state.depths:
                    max_depth = max(max_depth, max(float(value) for value in state.depths))
            completed, started = self.collisions.update(
                sim_time, self.collision_phase(), pairs, max_force, max_depth)
            self.record_collision_episodes(completed)
            if started:
                self.event("COLLISION_STARTED",
                           episode_id=self.collisions.active["episode_id"],
                           phase=self.collisions.active["phase"], pairs=pairs)

    def observation_callback(self, message):
        with self.lock:
            if self.closed:
                return
            self.load_planning_start()
            sim_time = message.header.stamp.to_sec() or rospy.get_time()
            self.observation_delta_count += 1
            self.observation_deltas_file.write(json.dumps({
                "sim_time": sim_time,
                "wall_elapsed": self.wall_elapsed(),
                "sensor_sequence": int(message.sequence),
                "raycast_id": int(message.raycast_id),
                "observed_total": int(message.observed_total),
                "delta_count": len(message.addresses),
                "addresses": [int(value) for value in message.addresses],
                "execution_interval_id": self.active_trajectory_id,
                "trajectory_id": self.active_trajectory_id,
                "global_sequence": self.active_global_sequence,
            }, sort_keys=True) + "\n")
            self.observation_deltas_file.flush()
            if self.coverage is None:
                return
            sample = self.coverage.ingest(message.sequence, message.observed_total,
                                          message.addresses, sim_time,
                                          message.raycast_id)
            row = dict(sample)
            row["wall_elapsed"] = self.wall_elapsed()
            row["planning_elapsed"] = ("" if sample["planning_elapsed"] is None
                                       else sample["planning_elapsed"])
            row["errors"] = json.dumps(sample["errors"], sort_keys=True)
            self.coverage_writer.writerow(row)
            self.coverage_file.flush()
            for error in sample["errors"]:
                if error not in self.coverage_reported_errors:
                    self.coverage_reported_errors.add(error)
                    self.event("COVERAGE_INVALID", error=error,
                               sequence=message.sequence)
            for name, threshold in (("T80", 0.80), ("T90", 0.90), ("T95", 0.95)):
                crossing = self.coverage.threshold_times[threshold]
                if crossing is not None and name not in self.coverage_reported_thresholds:
                    self.coverage_reported_thresholds.add(name)
                    self.event("COVERAGE_THRESHOLD", threshold=name,
                               planning_elapsed=crossing)

    def metric_timer(self, _event):
        with self.lock:
            if self.closed:
                return
            self.load_planning_start()
            sim_time = rospy.get_time()
            self.record_collision_episodes(self.collisions.advance(sim_time))
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
                "coverage": None if self.coverage is None else self.coverage.summary(),
            })

    def close(self):
        with self.lock:
            if self.closed:
                return
            self.closed = True
            self.load_planning_start()
            self.close_execution_interval("LOGGER_STOPPED")
            self.record_collision_episodes(self.collisions.advance(
                self.sim_end if self.sim_end is not None else rospy.get_time(), force=True))
            self.event("LOGGER_STOPPED")
            for stream in (self.trajectory_file, self.metrics_file,
                           self.planning_file, self.coverage_file, self.events_file,
                           self.planned_paths_file, self.collision_file,
                           self.execution_file, self.observation_deltas_file):
                stream.flush()
                stream.close()
            summary = {
                "schema_version": 3,
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
                "planned_path_count": len(self.recorded_path_keys),
                "execution_interval_count": self.execution_intervals.completed_count,
                "observation_delta_count": self.observation_delta_count,
                "collision": self.collisions.summary(),
                "planning": {
                    "global": duration_summary(self.global_times),
                    "local": duration_summary(self.local_times),
                    "return": duration_summary(self.return_times),
                },
                "rtf": value_summary(self.rtf_values),
                "coverage_status": ("UNAVAILABLE_NO_GROUND_TRUTH_MASK"
                                    if self.coverage is None else
                                    self.coverage.summary()["status"]),
                "coverage": None if self.coverage is None else self.coverage.summary(),
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
