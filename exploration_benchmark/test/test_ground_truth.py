#!/usr/bin/env python3
import hashlib
import tempfile
import unittest
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from exploration_benchmark.ground_truth import (GridSpec, OrientedBox,
                                                adjacent_to,
                                                canonical_mask_sha256,
                                                dilate_box, flood_fill,
                                                parse_static_boxes,
                                                voxelize_boxes,
                                                write_deterministic_npz)


class GroundTruthTest(unittest.TestCase):
    def test_sdf_pose_composition_and_rotated_box(self):
        sdf = """<sdf version='1.7'><world name='default'>
          <model name='room'><pose>1 2 0 0 0 1.5707963267948966</pose><static>1</static>
            <link name='wall'><pose>2 0 0 0 0 0</pose>
              <collision name='box'><pose>0 0 0.5 0 0 0</pose>
                <geometry><box><size>2 1 1</size></box></geometry>
              </collision>
            </link>
          </model></world></sdf>"""
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "world.sdf"
            path.write_text(sdf)
            box = parse_static_boxes(path, ["room"])[0]
        np.testing.assert_allclose(box.center, [1, 4, 0.5], atol=1e-12)
        np.testing.assert_allclose(box.rotation.dot([1, 0, 0]), [0, 1, 0], atol=1e-12)

    def test_unsupported_collision_geometry_fails_closed(self):
        sdf = """<sdf version='1.7'><world name='default'>
          <model name='room'><static>true</static><link name='object'>
            <collision name='sphere'><geometry><sphere><radius>1</radius></sphere></geometry>
            </collision></link></model></world></sdf>"""
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "world.sdf"
            path.write_text(sdf)
            with self.assertRaisesRegex(ValueError, "unsupported collision geometry"):
                parse_static_boxes(path, ["room"])

    def test_voxelize_one_cell(self):
        grid = GridSpec(np.zeros(3), 1.0, np.zeros(3, dtype=int), (4, 4, 4))
        box = OrientedBox("m", "l", "c", np.array([1.5, 2.5, 0.5]),
                          np.eye(3), np.array([0.9, 0.9, 0.9]))
        mask = voxelize_boxes([box], grid)
        self.assertEqual(int(mask.sum()), 1)
        self.assertTrue(mask[1, 2, 0])

    def test_flood_fill_respects_barrier(self):
        allowed = np.ones((5, 3, 1), dtype=bool)
        allowed[2, :, :] = False
        reached = flood_fill(allowed, (0, 1, 0))
        self.assertEqual(int(reached.sum()), 6)
        self.assertFalse(reached[4, 1, 0])

    def test_box_dilation_is_separable(self):
        mask = np.zeros((5, 5, 3), dtype=bool)
        mask[2, 2, 1] = True
        dilated = dilate_box(mask, (1, 2, 0))
        self.assertEqual(int(dilated.sum()), 15)
        self.assertTrue(dilated[1, 0, 1])
        self.assertFalse(dilated[0, 2, 1])

    def test_surface_uses_six_neighbors(self):
        free = np.zeros((3, 3, 3), dtype=bool)
        free[1, 1, 1] = True
        occupied = np.ones_like(free)
        surface = occupied & adjacent_to(free)
        self.assertEqual(int(surface.sum()), 6)

    def test_deterministic_archive_and_content_hash(self):
        arrays = {
            "b": np.array([True, False]),
            "a": np.array([[1, 2], [3, 4]], dtype=np.uint8),
        }
        with tempfile.TemporaryDirectory() as root:
            first = Path(root) / "first.npz"
            second = Path(root) / "second.npz"
            write_deterministic_npz(first, arrays)
            write_deterministic_npz(second, dict(reversed(list(arrays.items()))))
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with np.load(first) as loaded:
                np.testing.assert_array_equal(loaded["a"], arrays["a"])
        expected = canonical_mask_sha256(arrays)
        self.assertEqual(len(expected), 64)
        self.assertEqual(expected, canonical_mask_sha256(dict(arrays)))


if __name__ == "__main__":
    unittest.main()
