#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from exploration_benchmark.core import (TrajectoryAccumulator, atomic_write_json,
                                        create_run_directory, duration_summary, percentile,
                                        value_summary)


class BenchmarkCoreTest(unittest.TestCase):
    def test_distance_and_noise(self):
        trajectory = TrajectoryAccumulator(jump_threshold=2.0, noise_threshold=0.01)
        self.assertEqual(trajectory.update(1, (0,0,0)), (0.0, None))
        self.assertEqual(trajectory.update(2, (0.001,0,0)), (0.0, None))
        increment, event = trajectory.update(3, (1.001,0,0))
        self.assertAlmostEqual(increment, 1.0)
        self.assertIsNone(event)
        self.assertAlmostEqual(trajectory.distance, 1.0)

    def test_time_reset_and_jump_are_not_distance(self):
        trajectory = TrajectoryAccumulator(jump_threshold=1.0)
        trajectory.update(10, (0,0,0))
        self.assertEqual(trajectory.update(9, (0.1,0,0))[1], "ODOM_TIME_RESET")
        self.assertEqual(trajectory.update(11, (5,0,0))[1], "ODOM_JUMP")
        self.assertEqual(trajectory.distance, 0.0)

    def test_percentiles(self):
        self.assertIsNone(percentile([], 95))
        self.assertEqual(percentile([1], 95), 1)
        self.assertAlmostEqual(percentile([1,2,3,4,5], 50), 3)
        summary = duration_summary([1,2,3])
        self.assertEqual(summary["count"], 3)
        self.assertEqual(summary["max_ms"], 3)
        self.assertEqual(value_summary([1,2,3])["mean"], 2)

    def test_unique_run_directory_and_safe_components(self):
        with tempfile.TemporaryDirectory() as root:
            path = create_run_directory(root, "EXP-001", 2, "20260910T120000")
            self.assertTrue(path.is_dir())
            with self.assertRaises(FileExistsError):
                create_run_directory(root, "EXP-001", 2, "20260910T120000")
            with self.assertRaises(ValueError):
                create_run_directory(root, "../bad", 2, "time")

    def test_atomic_json(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "result.json"
            atomic_write_json(path, {"passed": True})
            self.assertEqual(json.loads(path.read_text())["passed"], True)


if __name__ == "__main__":
    unittest.main()
