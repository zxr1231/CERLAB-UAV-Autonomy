#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from exploration_benchmark.coverage import CoverageAccumulator


class CoverageAccumulatorTest(unittest.TestCase):
    def make_accumulator(self, root):
        root = Path(root)
        accessible = np.ones((2, 2, 2), dtype=bool)
        surface = np.zeros_like(accessible)
        surface[0, 0, 0] = True
        surface[1, 1, 1] = True
        mask = root / "mask.npz"
        np.savez(mask, accessible_free=accessible, static_surface=surface)
        metadata = {
            "shape": [2, 2, 2],
            "map_shape": [4, 3, 2],
            "global_index_min": [1, 1, 0],
            "voxel_volume_m3": 0.001,
            "mask_content_sha256": "test-mask",
        }
        metadata_path = root / "metadata.json"
        metadata_path.write_text(json.dumps(metadata))
        return CoverageAccumulator(mask, metadata_path)

    @staticmethod
    def address(x, y, z):
        return x * 3 * 2 + y * 2 + z

    def test_address_mapping_union_and_threshold_interpolation(self):
        with tempfile.TemporaryDirectory() as root:
            accumulator = self.make_accumulator(root)
            first = accumulator.ingest(
                1, 2, [self.address(0, 0, 0), self.address(1, 1, 0)], 5.0, 4)
            self.assertTrue(first["valid"])
            self.assertEqual(first["observed_task"], 1)
            self.assertEqual(first["accessible_observed"], 1)
            self.assertEqual(first["surface_observed"], 1)
            accumulator.set_planning_start(10.0)

            remaining = [self.address(x, y, z) for x in (1, 2)
                         for y in (1, 2) for z in (0, 1)
                         if (x, y, z) != (1, 1, 0)]
            second = accumulator.ingest(2, 9, remaining, 20.0, 5)
            self.assertEqual(second["accessible_observed"], 8)
            self.assertEqual(second["free_coverage"], 1.0)
            self.assertEqual(second["known_volume_m3"], 0.008)
            summary = accumulator.summary()
            self.assertAlmostEqual(summary["thresholds"]["T80"]["seconds"],
                                   (0.80 - 0.125) / (1.0 - 0.125) * 10.0)
            self.assertFalse(summary["thresholds"]["T95"]["censored"])

    def test_preplanning_coverage_crossing_is_time_zero(self):
        with tempfile.TemporaryDirectory() as root:
            accumulator = self.make_accumulator(root)
            addresses = [self.address(x, y, z) for x in (1, 2)
                         for y in (1, 2) for z in (0, 1)]
            accumulator.ingest(1, 8, addresses, 4.0)
            accumulator.set_planning_start(6.0)
            for name in ("T80", "T90", "T95"):
                self.assertEqual(accumulator.summary()["thresholds"][name]["seconds"], 0.0)

    def test_sequence_gap_and_total_mismatch_invalidate_stream(self):
        with tempfile.TemporaryDirectory() as root:
            accumulator = self.make_accumulator(root)
            sample = accumulator.ingest(2, 99, [self.address(1, 1, 0)], 1.0)
            self.assertFalse(sample["valid"])
            self.assertTrue(any("sequence gap" in item for item in sample["errors"]))
            self.assertTrue(any("count mismatch" in item for item in sample["errors"]))

    def test_repeated_address_invalidates_stream_without_double_counting(self):
        with tempfile.TemporaryDirectory() as root:
            accumulator = self.make_accumulator(root)
            address = self.address(1, 1, 0)
            accumulator.ingest(1, 1, [address], 1.0)
            sample = accumulator.ingest(2, 1, [address], 2.0)
            self.assertFalse(sample["valid"])
            self.assertEqual(sample["reconstructed_total_full_map"], 1)


if __name__ == "__main__":
    unittest.main()
