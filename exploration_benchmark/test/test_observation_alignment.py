import math
import unittest

from exploration_benchmark.observation_alignment import (comparable_actual_set,
                                                          set_metrics, spearman,
                                                          staleness_band,
                                                          transition_metrics)
from exploration_benchmark.r1_snapshot import FrozenVoxelMap
from exploration_benchmark.r1_visibility import LegacyVisibilityConfig


class ObservationAlignmentTest(unittest.TestCase):
    def test_set_metrics(self):
        metrics = set_metrics({1, 2, 3}, {2, 3, 4, 5})
        self.assertEqual(metrics["intersection_count"], 2)
        self.assertAlmostEqual(metrics["precision"], 2/3)
        self.assertAlmostEqual(metrics["recall"], 0.5)
        self.assertAlmostEqual(metrics["jaccard"], 0.4)

    def test_transition_metrics(self):
        metrics = transition_metrics({1, 2, 3, 4}, {2, 3, 5})
        self.assertEqual(metrics["intersection_count"], 2)
        self.assertEqual(metrics["source_retention"], 0.5)
        self.assertAlmostEqual(metrics["target_novel_fraction"], 1/3)

    def test_actual_filter_requires_snapshot_unknown_roi_and_not_inflated(self):
        dimensions = (3, 2, 1); payload = bytearray(12)
        for address in (0, 1, 2, 3):
            payload[2*address] = 0xFF
        payload[2*2+1] = 1
        grid = FrozenVoxelMap(1, 1.0, (0, 0, 0), (3, 2, 1), dimensions,
                              -1.0, 0.5, bytes(payload))
        config = LegacyVisibilityConfig(math.pi/2, math.pi/2, 0, 2,
                                        (0, 0, 0), (1.9, 1.9, 1))
        comparable, out_of_map = comparable_actual_set({0, 1, 2, 3, 5, 99}, grid, config)
        self.assertEqual(comparable, {0, 1, 3})
        self.assertEqual(out_of_map, 1)

    def test_staleness_bands(self):
        self.assertEqual(staleness_band(0.0), "fresh")
        self.assertEqual(staleness_band(2.0), "fresh")
        self.assertEqual(staleness_band(2.01), "moderate")
        self.assertEqual(staleness_band(10.01), "stale")
        self.assertEqual(staleness_band(-1), "invalid")

    def test_spearman_handles_order_and_ties(self):
        self.assertAlmostEqual(spearman([1, 2, 3], [10, 20, 30]), 1.0)
        self.assertAlmostEqual(spearman([1, 2, 3], [30, 20, 10]), -1.0)
        self.assertIsNone(spearman([1], [2]))


if __name__ == "__main__":
    unittest.main()
