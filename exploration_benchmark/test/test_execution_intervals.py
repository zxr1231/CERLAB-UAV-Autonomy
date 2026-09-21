import unittest

from exploration_benchmark.execution_intervals import ExecutionIntervalTracker


class ExecutionIntervalTrackerTest(unittest.TestCase):
    def test_supersede_closes_previous_and_histories_do_not_cross(self):
        tracker = ExecutionIntervalTracker()
        self.assertIsNone(tracker.start(7, 2, 1.0, 10.0, "new_global_path",
                                        100, 20, (0, 0, 1), 0.0))
        tracker.observe_odom(1.1, (0, 0, 1), 0.0, 4.0)
        tracker.observe_odom(1.2, (0.5, 0, 1), 0.1, 0.5)
        closed = tracker.start(8, 2, 2.0, 11.0, "distance_progress",
                               110, 22, (0.5, 0, 1), 0.1)
        self.assertEqual(closed["trajectory_id"], 7)
        self.assertEqual(closed["end_reason"], "SUPERSEDED_BY_TRAJECTORY")
        self.assertEqual(closed["odom_count"], 2)
        self.assertEqual(closed["executed_distance"], 0.5)
        self.assertEqual(tracker.active["trajectory_id"], 8)
        self.assertEqual(tracker.active["odom_count"], 0)

    def test_explicit_close_and_no_active_close(self):
        tracker = ExecutionIntervalTracker()
        tracker.start(3, 1, 5.0, 2.0, "next_waypoint")
        closed = tracker.close(7.0, 4.0, "RETURNING_HOME", 12, 4)
        self.assertEqual(closed["duration_sim"], 2.0)
        self.assertTrue(closed["valid"])
        self.assertIsNone(tracker.close(8.0, 5.0, "again"))

    def test_time_reversal_is_retained_as_invalid(self):
        tracker = ExecutionIntervalTracker()
        tracker.start(1, 1, 10.0, 10.0, "initial")
        closed = tracker.close(9.0, 8.0, "clock_reset")
        self.assertFalse(closed["valid"])
        self.assertEqual(closed["duration_sim"], 0.0)
        self.assertIn("SIM_TIME_REVERSED", closed["errors"])

    def test_invalid_trajectory_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "positive"):
            ExecutionIntervalTracker().start(0, 1, 0, 0, "invalid")


if __name__ == "__main__":
    unittest.main()
