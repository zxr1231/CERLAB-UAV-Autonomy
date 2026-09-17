#!/usr/bin/env python3
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from exploration_benchmark.collision_metrics import CollisionEpisodeAccumulator


class CollisionMetricsTest(unittest.TestCase):
    def test_repeated_contacts_form_one_episode(self):
        accumulator = CollisionEpisodeAccumulator(quiet_period=0.1)
        completed, started = accumulator.update(1.0, "exploration", ["uav|wall"], 2, 0.01)
        self.assertTrue(started); self.assertEqual(completed, [])
        completed, started = accumulator.update(1.05, "exploration", ["uav|wall"], 3, 0.02)
        self.assertFalse(started); self.assertEqual(completed, [])
        self.assertEqual(accumulator.advance(1.14), [])
        episode = accumulator.advance(1.16)[0]
        self.assertAlmostEqual(episode["duration_sim"], 0.05)
        self.assertEqual(episode["max_force_n"], 3)
        self.assertEqual(accumulator.summary()["episode_count"], 1)
        self.assertEqual(accumulator.summary()["message_count"], 2)

    def test_quiet_gap_starts_a_new_episode(self):
        accumulator = CollisionEpisodeAccumulator(quiet_period=0.1)
        accumulator.update(1.0, "exploration", ["uav|wall"])
        completed, started = accumulator.update(1.2, "return", ["uav|person"])
        self.assertTrue(started); self.assertEqual(len(completed), 1)
        accumulator.advance(1.3, force=True)
        self.assertEqual(accumulator.summary()["episode_count_by_phase"],
                         {"exploration": 1, "return": 1})

    def test_no_messages_is_not_a_valid_zero_collision_measurement(self):
        accumulator = CollisionEpisodeAccumulator()
        self.assertEqual(accumulator.summary()["status"], "NO_CONTACT_MESSAGES")
        accumulator.update(1.0, "exploration", [])
        self.assertEqual(accumulator.summary()["status"], "VALID")


if __name__ == "__main__":
    unittest.main()
