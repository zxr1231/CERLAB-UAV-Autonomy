import math
import unittest

from exploration_benchmark.r1_snapshot import FrozenVoxelMap
from exploration_benchmark.r1_visibility import (LegacyVisibilityConfig,
                                                  visible_set_sha256,
                                                  visible_unknown_voxels)


def _grid(dimensions=(7, 7, 3), resolution=1.0):
    count = dimensions[0] * dimensions[1] * dimensions[2]
    payload = bytearray(2 * count)
    return FrozenVoxelMap(
        version=4,
        resolution=resolution,
        map_min=(0.0, 0.0, 0.0),
        map_max=tuple(dimensions[i] * resolution for i in range(3)),
        dimensions=dimensions,
        p_min_log=-1.0,
        p_occ_log=0.5,
        payload=bytes(payload),
    )


def _with_voxels(grid, unknown=(), inflated=()):
    payload = bytearray(grid.payload)
    for index in unknown:
        payload[2 * grid.address(index)] = 0xFF
    for index in inflated:
        payload[2 * grid.address(index) + 1] = 1
    return FrozenVoxelMap(grid.version, grid.resolution, grid.map_min, grid.map_max,
                          grid.dimensions, grid.p_min_log, grid.p_occ_log,
                          bytes(payload))


def _config(grid, horizontal_fov=math.pi / 2, vertical_fov=math.pi / 2,
            dmin=0.0, dmax=5.0, planning_min=None, planning_max=None):
    return LegacyVisibilityConfig(
        horizontal_fov, vertical_fov, dmin, dmax,
        planning_min or grid.map_min,
        planning_max or grid.map_max,
    )


class R1VisibilityTest(unittest.TestCase):
    def test_stable_global_addresses_and_repeatability(self):
        grid = _with_voxels(_grid(), unknown=((4, 3, 1), (4, 4, 1), (1, 3, 1)))
        viewpoint = (3.5, 3.5, 1.5)
        expected = frozenset((grid.address((4, 3, 1)), grid.address((4, 4, 1))))
        first = visible_unknown_voxels(grid, viewpoint, 0.0, _config(grid))
        second = visible_unknown_voxels(grid, viewpoint, 0.0, _config(grid))
        self.assertEqual(first, expected)
        self.assertEqual(second, first)
        self.assertEqual(visible_set_sha256(first), visible_set_sha256(second))
        for address in first:
            self.assertEqual(grid.address(grid.index(address)), address)

    def test_inflated_wall_occludes_unknown_target(self):
        base = _grid((8, 3, 1))
        grid = _with_voxels(base, unknown=((6, 1, 0),), inflated=((4, 1, 0),))
        visible = visible_unknown_voxels(grid, (1.5, 1.5, 0.5), 0.0,
                                         _config(grid, dmax=6.0))
        self.assertNotIn(grid.address((6, 1, 0)), visible)

    def test_unknown_voxels_are_transparent_to_legacy_occlusion(self):
        grid = _with_voxels(_grid((8, 3, 1)), unknown=((4, 1, 0), (6, 1, 0)))
        visible = visible_unknown_voxels(grid, (1.5, 1.5, 0.5), 0.0,
                                         _config(grid, dmax=6.0))
        self.assertIn(grid.address((4, 1, 0)), visible)
        self.assertIn(grid.address((6, 1, 0)), visible)

    def test_yaw_boundary_is_inclusive_and_rear_target_is_excluded(self):
        grid = _with_voxels(_grid(), unknown=((4, 3, 1), (4, 4, 1), (1, 3, 1)))
        visible = visible_unknown_voxels(grid, (3.5, 3.5, 1.5), 0.0,
                                         _config(grid, dmax=5.0))
        self.assertIn(grid.address((4, 3, 1)), visible)
        self.assertIn(grid.address((4, 4, 1)), visible)
        self.assertNotIn(grid.address((1, 3, 1)), visible)

    def test_legacy_dmin_is_recorded_but_not_applied(self):
        grid = _with_voxels(_grid(), unknown=((4, 3, 1),))
        visible = visible_unknown_voxels(
            grid, (3.5, 3.5, 1.5), 0.0,
            _config(grid, dmin=1.5, dmax=2.0),
        )
        self.assertIn(grid.address((4, 3, 1)), visible)

    def test_vertical_fov_matches_legacy_z_envelope_not_angular_frustum(self):
        grid = _with_voxels(_grid((7, 7, 5)), unknown=((4, 3, 4),))
        # Elevation atan2(2, 1) is above 45 degrees, but DEP only applies a
        # z-envelope before its Euclidean distance check.
        visible = visible_unknown_voxels(
            grid, (3.5, 3.5, 2.5), 0.0,
            _config(grid, vertical_fov=math.pi / 2, dmax=3.0),
        )
        self.assertIn(grid.address((4, 3, 4)), visible)

    def test_planning_region_clips_unknown_targets(self):
        grid = _with_voxels(_grid(), unknown=((4, 3, 1), (5, 3, 1)))
        config = _config(grid, dmax=5.0, planning_max=(5.0, 7.0, 3.0))
        visible = visible_unknown_voxels(grid, (3.5, 3.5, 1.5), 0.0, config)
        self.assertIn(grid.address((4, 3, 1)), visible)
        self.assertNotIn(grid.address((5, 3, 1)), visible)

    def test_inflated_viewpoint_fails_closed(self):
        grid = _with_voxels(_grid(), unknown=((4, 3, 1),), inflated=((3, 3, 1),))
        visible = visible_unknown_voxels(grid, (3.5, 3.5, 1.5), 0.0,
                                         _config(grid))
        self.assertEqual(visible, frozenset())


if __name__ == "__main__":
    unittest.main()
