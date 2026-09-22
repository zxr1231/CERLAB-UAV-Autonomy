import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

from exploration_benchmark.r1_snapshot import FrozenVoxelMap
from exploration_benchmark.sensor_shadow import (CameraShadowConfig, camera_pose,
                                                  camera_unit_rays,
                                                  visible_unknown_shadow,
                                                  voxel_line)
from exploration_benchmark.sensor_shadow_observation import select_stage_intervals


def _grid(dimensions=(8, 5, 3)):
    count = dimensions[0]*dimensions[1]*dimensions[2]
    return FrozenVoxelMap(1, 1.0, (0.0, 0.0, 0.0), tuple(map(float, dimensions)),
                          dimensions, -1.0, 0.5, bytes(2*count))


def _states(grid, unknown=(), occupied=()):
    payload = bytearray(grid.payload)
    for index in unknown:
        payload[2*grid.address(index)] = 0xFF
    for index in occupied:
        payload[2*grid.address(index)] = 1
    return FrozenVoxelMap(grid.version, grid.resolution, grid.map_min, grid.map_max,
                          grid.dimensions, grid.p_min_log, grid.p_occ_log,
                          bytes(payload))


def _config(body_to_camera=None):
    return CameraShadowConfig(
        1.0, 1.0, 0.0, 0.0, 1, 1, 0, 1, 1, 5.0,
        body_to_camera or (0, 0, 1, 0,
                           -1, 0, 0, 0,
                           0, -1, 0, 0,
                           0, 0, 0, 1),
        (0.0, 0.0, 0.0), (8.0, 5.0, 3.0))


class SensorShadowTest(unittest.TestCase):
    def test_stage_selection_is_even_and_independent_of_gain(self):
        rows = [{"interval_id": str(index), "global_sequence": "1", "valid": "true",
                 "odom_count": "3", "gain": str(100-index)} for index in range(1, 13)]
        self.assertEqual(select_stage_intervals(rows, 2),
                         {1: "early", 4: "early", 5: "middle", 8: "middle",
                          9: "late", 12: "late"})

    def test_camera_extrinsic_and_yaw_match_forward_body_axis(self):
        origin, rotation = camera_pose((1.0, 2.0, 1.0), math.pi/2, _config())
        np.testing.assert_allclose(origin, (1.0, 2.0, 1.0), atol=1e-12)
        optical_forward = np.matmul(rotation, np.asarray((0.0, 0.0, 1.0)))
        np.testing.assert_allclose(optical_forward, (0.0, 1.0, 0.0), atol=1e-12)

    def test_pixel_lattice_honors_margin_and_skip(self):
        config = CameraShadowConfig(10, 10, 2, 2, 6, 6, 1, 2, 2, 5,
                                    tuple(np.eye(4).ravel()), (0, 0, 0), (5, 5, 5))
        rays = camera_unit_rays(config)
        self.assertEqual(rays.shape, (4, 3))
        np.testing.assert_allclose(np.linalg.norm(rays, axis=1), np.ones(4))

    def test_voxel_line_omits_sensor_and_includes_endpoint(self):
        self.assertEqual(list(voxel_line((1.5, 1.5, 1.5), (4.5, 1.5, 1.5))),
                         [(2, 1, 1), (3, 1, 1), (4, 1, 1)])

    def test_known_occupied_stops_ray_but_unknown_is_observed(self):
        base = _grid()
        grid = _states(base, unknown=((2, 2, 1), (4, 2, 1), (6, 2, 1)),
                       occupied=((5, 2, 1),))
        config = _config()
        rays = np.asarray(((0.0, 0.0, 1.0),))
        visible = visible_unknown_shadow(grid, (1.5, 2.5, 1.5), 0.0, config, rays)
        self.assertIn(grid.address((2, 2, 1)), visible)
        self.assertIn(grid.address((4, 2, 1)), visible)
        self.assertNotIn(grid.address((6, 2, 1)), visible)

    def test_yaml_config_preserves_mapper_skip_separately(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"map.yaml"
            path.write_text("""depth_intrinsics: [10, 11, 3, 4]
image_cols: 8
image_rows: 6
depth_filter_margin: 1
depth_skip_pixel: 2
raycast_max_length: 5
body_to_camera: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
""", encoding="utf-8")
            config = CameraShadowConfig.from_yaml(path, (0, 0, 0), (1, 1, 1), 4)
            self.assertEqual(config.mapper_pixel_skip, 2)
            self.assertEqual(config.evaluation_pixel_skip, 4)


if __name__ == "__main__":
    unittest.main()
