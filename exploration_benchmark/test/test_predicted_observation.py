import csv
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from exploration_benchmark.execution_intervals import INTERVAL_FIELDS
from exploration_benchmark.predicted_observation import (build_predicted_observation,
                                                          sample_constant_yaw_polyline,
                                                          sample_odom_prefix,
                                                          visible_union)


def _write_run(root):
    interval = {field: "" for field in INTERVAL_FIELDS}
    interval.update({"interval_id": 7, "trajectory_id": 7, "global_sequence": 1,
                     "start_sim": 1, "end_sim": 2, "duration_sim": 1,
                     "executed_distance": 1, "odom_count": 3,
                     "start_reason": "test", "end_reason": "test",
                     "valid": True, "errors": "[]"})
    with (root / "execution_intervals.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=INTERVAL_FIELDS)
        writer.writeheader(); writer.writerow(interval)
    planning_fields = ["kind", "success", "trajectory_id", "start_yaw", "map_version"]
    with (root / "planning.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=planning_fields)
        writer.writeheader(); writer.writerow({"kind": "local", "success": "True",
                                               "trajectory_id": 7, "start_yaw": 0.25,
                                               "map_version": 12})
    (root / "planned_paths.jsonl").write_text(json.dumps({
        "kind": "bspline", "id": 7, "points": [[0, 0, 1], [1, 0, 1]]}) + "\n")
    trajectory_fields = ["sim_time", "x", "y", "z", "yaw", "execution_interval_id"]
    with (root / "trajectory.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=trajectory_fields)
        writer.writeheader()
        writer.writerows([
            {"sim_time": 1, "x": 0, "y": 0, "z": 1, "yaw": 0,
             "execution_interval_id": 7},
            {"sim_time": 1.5, "x": 0.3, "y": 0, "z": 1, "yaw": 0.2,
             "execution_interval_id": 7},
            {"sim_time": 2, "x": 1, "y": 0, "z": 1, "yaw": 0.2,
             "execution_interval_id": 7},
        ])


class PredictedObservationTest(unittest.TestCase):
    def test_constant_yaw_polyline_sampling(self):
        samples = sample_constant_yaw_polyline([[0, 0, 0], [1, 0, 0]], 0.7, 0.25)
        self.assertEqual(len(samples), 5)
        self.assertTrue(all(sample.yaw == 0.7 for sample in samples))

    def test_odom_sampling_preserves_translation_rotation_and_terminal(self):
        rows = [
            {"sim_time": 0, "x": 0, "y": 0, "z": 0, "yaw": 0},
            {"sim_time": 1, "x": 0.1, "y": 0, "z": 0, "yaw": 0.2},
            {"sim_time": 2, "x": 0.4, "y": 0, "z": 0, "yaw": 0.21},
            {"sim_time": 3, "x": 0.41, "y": 0, "z": 0, "yaw": 0.22},
        ]
        samples = sample_odom_prefix(rows, 0.25, 0.1)
        self.assertEqual([sample["sim_time"] for sample in samples], [0, 1, 2, 3])

    def test_visible_union_deduplicates_across_samples(self):
        samples = [{"position": (0, 0, 0), "yaw": 0},
                   {"position": (1, 0, 0), "yaw": 0}]
        def visibility(_grid, position, _yaw, _config):
            return {1, 2} if position[0] == 0 else {2, 3}
        self.assertEqual(visible_union(object(), object(), samples, visibility), {1, 2, 3})

    def test_builds_all_four_layers_with_matching_ids(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); run = root / "run"; snapshots = root / "snapshots"
            run.mkdir(); (snapshots / "snapshot_000001").mkdir(parents=True)
            _write_run(run)
            snapshot = {
                "planner": {
                    "selected_candidate": 0,
                    "candidate_paths": [{
                        "id": 0,
                        "raw_waypoints": [
                            {"position": [0, 0, 1], "yaw": 0},
                            {"position": [0.5, 0.5, 1], "yaw": math.pi/4},
                            {"position": [1, 0, 1], "yaw": 0}],
                        "waypoints": [
                            {"position": [0, 0, 1], "yaw": 0},
                            {"position": [1, 0, 1], "yaw": 0}],
                    }],
                    "sensor_model": {"horizontal_fov": 1.57, "vertical_fov": 1.57,
                                     "dmin": 0.3, "dmax": 2,
                                     "visibility_model": "legacy_inflated_occupied_line"},
                    "planning_region": {"min": [-2, -2, 0.7], "max": [2, 2, 1.2]},
                },
                "map": {"version": 10},
                "manifest": {"map_file": "map.bin"},
            }
            def fake_union(_grid, _config, samples, visibility_fn=None):
                return set(range(len(samples)))
            with mock.patch("exploration_benchmark.predicted_observation.load_snapshot",
                            return_value=snapshot), mock.patch(
                                "exploration_benchmark.predicted_observation.load_frozen_map",
                                return_value=object()), mock.patch(
                                    "exploration_benchmark.predicted_observation.visible_union",
                                    side_effect=fake_union):
                result = build_predicted_observation(run, snapshots)
            self.assertEqual(result["status"], "VALID")
            self.assertEqual(result["valid_interval_count"], 1)
            self.assertEqual(set(result["intervals"][0]["layers"]),
                             {"prm_raw", "prm_shortcut", "bspline", "odom_prefix"})

    def test_missing_snapshot_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); run = root / "run"; snapshots = root / "snapshots"
            run.mkdir(); snapshots.mkdir(); _write_run(run)
            result = build_predicted_observation(run, snapshots)
            self.assertEqual(result["status"], "INVALID")
            self.assertIn("missing snapshot", result["errors"][0])


if __name__ == "__main__":
    unittest.main()
