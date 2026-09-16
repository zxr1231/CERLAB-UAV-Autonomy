#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from exploration_benchmark.aggregate import (aggregate_rows, distribution_summary,
                                             rate_summary, rows_from_batch_state)


class AggregateTest(unittest.TestCase):
    def test_distribution_and_wilson_rate(self):
        summary = distribution_summary([1, 2, 3])
        self.assertEqual(summary["mean"], 2)
        self.assertEqual(summary["median"], 2)
        rate = rate_summary(8, 10)
        self.assertEqual(rate["rate"], 0.8)
        self.assertLess(rate["wilson95_low"], 0.8)
        self.assertGreater(rate["wilson95_high"], 0.8)

    def test_censoring_and_failures_are_retained(self):
        rows = [
            {"manifest_readable": True, "outcome": "HOME_REACHED",
             "algorithm_completed": True, "return_success": True,
             "coverage_valid": True, "collision_status": "VALID",
             "trajectory_status": "VALID", "resource_status": "VALID",
             "collision_free": True, "t80_seconds": 10.0, "t80_censored": False,
             "t90_seconds": None, "t90_censored": True,
             "t95_seconds": None, "t95_censored": True},
            {"manifest_readable": True, "outcome": "TIMEOUT",
             "algorithm_completed": False, "return_success": False,
             "coverage_valid": True, "collision_status": "VALID",
             "trajectory_status": "VALID", "resource_status": "VALID",
             "collision_free": False, "t80_seconds": None, "t80_censored": True,
             "t90_seconds": None, "t90_censored": True,
             "t95_seconds": None, "t95_censored": True},
        ]
        for row in rows:
            for name in ("exploration_duration_sim", "return_duration_sim",
                         "exploration_distance_m", "final_mission_distance_m",
                         "free_coverage", "surface_coverage", "global_planning_mean_ms",
                         "global_planning_p95_ms", "exploration_local_planning_mean_ms",
                         "exploration_local_planning_p95_ms",
                         "executed_to_bspline_length_ratio_mean",
                         "odom_to_bspline_mean_distance_mean", "exploration_cpu_mean",
                         "exploration_cpu_p95", "exploration_rss_mean_mib",
                         "exploration_rss_peak_mib", "logger_cpu_mean",
                         "logger_rss_mean_mib", "simulator_cpu_mean",
                         "simulator_rss_mean_mib", "mean_rtf", "mission_sim_duration",
                         "mission_wall_duration"):
                row[name] = None
        aggregate = aggregate_rows(rows)
        self.assertEqual(aggregate["attempt_count"], 2)
        self.assertEqual(aggregate["algorithm_completion"]["rate"], 0.5)
        self.assertEqual(aggregate["collision_free"]["rate"], 0.5)
        self.assertEqual(aggregate["thresholds"]["T80"]["censored_count"], 1)
        self.assertEqual(aggregate["thresholds"]["T80"]["conditional_seconds"]["mean"], 10)
        self.assertEqual(aggregate["thresholds"]["T90"]["conditional_seconds"]["count"], 0)
        invalid_coverage = dict(rows[0])
        invalid_coverage["coverage_valid"] = False
        invalid_coverage["free_coverage"] = 0.99
        filtered = aggregate_rows([invalid_coverage])
        self.assertEqual(filtered["continuous_metrics"]["free_coverage"]["count"], 0)

    def test_missing_result_attempt_gets_a_row(self):
        with tempfile.TemporaryDirectory() as root:
            state = Path(root) / "batch_state.json"
            state.write_text(json.dumps({"tasks": [{
                "task_id": "env001_planner001_repeat01", "environment_seed": 1,
                "planner_seed": 1, "attempts": [{"attempt": 1,
                                                   "status": "INTERRUPTED"}]}]}))
            _, rows = rows_from_batch_state(state)
            self.assertEqual(len(rows), 1)
            self.assertFalse(rows[0]["manifest_readable"])
            self.assertEqual(rows[0]["outcome"], "MISSING_RESULT_DIR")

    def test_incomplete_result_directory_gets_unreadable_row(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            result = root / "incomplete"
            result.mkdir()
            (result / "run.json").write_text(json.dumps({"outcome": "PROCESS_ERROR"}))
            state = root / "batch_state.json"
            state.write_text(json.dumps({"tasks": [{
                "task_id": "env001_planner001_repeat01", "environment_seed": 1,
                "planner_seed": 1, "attempts": [{"attempt": 2,
                                                   "status": "PROCESS_ERROR",
                                                   "result_dir": str(result)}]}]}))
            _, rows = rows_from_batch_state(state)
            self.assertEqual(len(rows), 1)
            self.assertFalse(rows[0]["manifest_readable"])
            self.assertEqual(rows[0]["outcome"], "UNREADABLE_RESULT")


if __name__ == "__main__":
    unittest.main()
