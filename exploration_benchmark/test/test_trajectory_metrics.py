#!/usr/bin/env python3
import csv
import json
import tempfile
import unittest
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from exploration_benchmark.trajectory_metrics import (point_to_polyline_distances,
                                                      polyline_length,
                                                      write_run_metrics)


class TrajectoryMetricsTest(unittest.TestCase):
    def test_polyline_length_and_distances(self):
        line = [[0, 0, 0], [2, 0, 0]]
        self.assertEqual(polyline_length(line), 2.0)
        distances = point_to_polyline_distances([[1, 1, 0], [3, 0, 0]], line)
        np.testing.assert_allclose(distances, [1.0, 1.0])

    def test_run_association_excludes_cross_id_increment(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            paths = [
                {"kind": "input", "id": 7, "global_sequence": 2,
                 "points": [[0, 0, 0], [2, 0, 0]]},
                {"kind": "bspline", "id": 7, "global_sequence": 2,
                 "points": [[0, 0, 0], [1, 0, 0], [2, 0, 0]]},
            ]
            (root/"planned_paths.jsonl").write_text(
                "".join(json.dumps(item)+"\n" for item in paths))
            fields = ["sim_time", "x", "y", "z", "trajectory_id"]
            with (root/"trajectory.csv").open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
                writer.writeheader()
                writer.writerows([
                    {"sim_time": 1, "x": 0, "y": 0, "z": 0, "trajectory_id": 7},
                    {"sim_time": 2, "x": 1, "y": 0, "z": 0, "trajectory_id": 7},
                    {"sim_time": 3, "x": 2, "y": 0, "z": 0, "trajectory_id": 7},
                ])
            summary = write_run_metrics(root)
            self.assertEqual(summary["trajectory_count"], 1)
            with (root/"trajectory_alignment.csv").open() as stream:
                row = next(csv.DictReader(stream))
            self.assertEqual(float(row["executed_length"]), 2.0)
            self.assertEqual(float(row["bspline_to_input_length_ratio"]), 1.0)
            self.assertEqual(float(row["odom_to_bspline_max_distance"]), 0.0)


if __name__ == "__main__":
    unittest.main()
