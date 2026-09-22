"""Frozen-map camera shadow evaluator for R2 predicted/actual calibration.

The evaluator mirrors the mapper's pinhole geometry, body-to-camera transform,
maximum Euclidean ray length and voxel traversal.  A frozen occupancy map cannot
reconstruct the depth of obstacles that are still unknown, so the model traces a
no-return ray until the first *known occupied* voxel.  That limitation is part of
the output provenance and must not be confused with an exact Gazebo-depth replay.
"""

from dataclasses import dataclass
import math
from pathlib import Path

import numpy as np
import yaml


@dataclass(frozen=True)
class CameraShadowConfig:
    fx: float
    fy: float
    cx: float
    cy: float
    image_cols: int
    image_rows: int
    filter_margin: int
    mapper_pixel_skip: int
    evaluation_pixel_skip: int
    raycast_max_length: float
    body_to_camera: tuple
    planning_min: tuple
    planning_max: tuple

    def __post_init__(self):
        if self.fx <= 0 or self.fy <= 0 or self.raycast_max_length <= 0:
            raise ValueError("camera focal lengths and range must be positive")
        if self.image_cols <= 0 or self.image_rows <= 0:
            raise ValueError("image dimensions must be positive")
        if self.filter_margin < 0:
            raise ValueError("filter margin cannot be negative")
        if self.mapper_pixel_skip <= 0 or self.evaluation_pixel_skip <= 0:
            raise ValueError("pixel skips must be positive")
        if len(self.body_to_camera) != 16:
            raise ValueError("body_to_camera must be a row-major 4x4 matrix")
        if len(self.planning_min) != 3 or len(self.planning_max) != 3:
            raise ValueError("planning region must contain three axes")

    @classmethod
    def from_yaml(cls, path, planning_min, planning_max,
                  evaluation_pixel_skip=None):
        values = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        fx, fy, cx, cy = values["depth_intrinsics"]
        mapper_skip = int(values["depth_skip_pixel"])
        return cls(
            float(fx), float(fy), float(cx), float(cy),
            int(values["image_cols"]), int(values["image_rows"]),
            int(values["depth_filter_margin"]), mapper_skip,
            int(evaluation_pixel_skip or mapper_skip),
            float(values["raycast_max_length"]),
            tuple(float(item) for item in values["body_to_camera"]),
            tuple(float(item) for item in planning_min),
            tuple(float(item) for item in planning_max),
        )

    def provenance(self):
        return {
            "model": "mapper_matched_frozen_shadow_v1",
            "depth_assumption": "no_return_until_first_snapshot_occupied",
            "unknown_obstacles_observable": False,
            "fx": self.fx, "fy": self.fy, "cx": self.cx, "cy": self.cy,
            "image_cols": self.image_cols, "image_rows": self.image_rows,
            "filter_margin": self.filter_margin,
            "mapper_pixel_skip": self.mapper_pixel_skip,
            "evaluation_pixel_skip": self.evaluation_pixel_skip,
            "raycast_max_length": self.raycast_max_length,
            "body_to_camera": list(self.body_to_camera),
            "planning_min": list(self.planning_min),
            "planning_max": list(self.planning_max),
        }


def _body_pose(position, yaw):
    cosine, sine = math.cos(yaw), math.sin(yaw)
    matrix = np.eye(4, dtype=np.float64)
    matrix[:3, :3] = ((cosine, -sine, 0.0),
                      (sine, cosine, 0.0),
                      (0.0, 0.0, 1.0))
    matrix[:3, 3] = position
    return matrix


def camera_pose(position, yaw, config):
    """Return camera origin and camera-to-map rotation for a level body pose."""
    body_to_camera = np.asarray(config.body_to_camera, dtype=np.float64).reshape(4, 4)
    map_to_camera = np.matmul(_body_pose(position, yaw), body_to_camera)
    return map_to_camera[:3, 3], map_to_camera[:3, :3]


def camera_unit_rays(config):
    """Return the configured sampled pinhole rays in the optical frame."""
    u = np.arange(config.filter_margin,
                  config.image_cols-config.filter_margin,
                  config.evaluation_pixel_skip, dtype=np.float64)
    v = np.arange(config.filter_margin,
                  config.image_rows-config.filter_margin,
                  config.evaluation_pixel_skip, dtype=np.float64)
    uu, vv = np.meshgrid(u, v)
    rays = np.column_stack(((uu.ravel()-config.cx)/config.fx,
                            (vv.ravel()-config.cy)/config.fy,
                            np.ones(uu.size, dtype=np.float64)))
    rays /= np.linalg.norm(rays, axis=1)[:, None]
    return rays


def voxel_line(start, end):
    """Yield voxel indices after the start voxel through the end voxel.

    This is the forward counterpart of CERLAB's ``RayCaster``.  Axis ties use the
    same z/y preference as the C++ implementation.  The sensor voxel is omitted,
    matching the mapper's reverse endpoint-to-camera traversal.
    """
    start = np.asarray(start, dtype=np.float64)
    end = np.asarray(end, dtype=np.float64)
    current = np.floor(start).astype(np.int64)
    terminal = np.floor(end).astype(np.int64)
    if np.array_equal(current, terminal):
        return
    delta_index = terminal-current
    step = np.sign(delta_index).astype(np.int64)
    direction = end-start
    t_delta = np.full(3, math.inf, dtype=np.float64)
    t_max = np.full(3, math.inf, dtype=np.float64)
    for axis in range(3):
        if step[axis] == 0 or direction[axis] == 0:
            continue
        boundary = current[axis] + (1 if step[axis] > 0 else 0)
        t_max[axis] = (boundary-start[axis])/direction[axis]
        t_delta[axis] = abs(1.0/direction[axis])
    safety = int(np.abs(terminal-current).sum())+3
    for _ in range(safety):
        # Equivalent tie behavior to: x<y, then winner<z, else z; y<z else z.
        if t_max[0] < t_max[1] and t_max[0] < t_max[2]:
            axis = 0
        elif t_max[1] < t_max[2]:
            axis = 1
        else:
            axis = 2
        current[axis] += step[axis]
        t_max[axis] += t_delta[axis]
        yield tuple(int(value) for value in current)
        if np.array_equal(current, terminal):
            return
    raise RuntimeError("voxel traversal exceeded deterministic safety bound")


def _in_planning_region(position, config):
    return all(config.planning_min[axis] <= position[axis] <=
               config.planning_max[axis] for axis in range(3))


def visible_unknown_shadow(grid, viewpoint, yaw, config, unit_rays=None):
    """Predict first-observed unknown addresses from one body pose.

    Pixel rays that end in the same maximum-range voxel are collapsed.  CERLAB's
    mapper also suppresses duplicate ray endpoints within a depth frame.  Rays stop
    before a voxel already known occupied in the frozen snapshot; inflated free
    voxels do not occlude the physical depth camera.
    """
    unit_rays = camera_unit_rays(config) if unit_rays is None else unit_rays
    origin, rotation = camera_pose(viewpoint, yaw, config)
    if not grid.in_bounds(grid.position_to_index(origin)):
        return frozenset()
    directions = np.matmul(unit_rays, rotation.T)
    endpoints = origin[None, :] + directions*config.raycast_max_length
    endpoint_indices = np.floor((endpoints-np.asarray(grid.map_min))/grid.resolution).astype(np.int64)
    valid = np.all((endpoint_indices >= 0) &
                   (endpoint_indices < np.asarray(grid.dimensions)), axis=1)
    endpoint_indices = endpoint_indices[valid]
    endpoints = endpoints[valid]
    if not len(endpoints):
        return frozenset()
    # Keep one deterministic representative per endpoint voxel, mirroring the
    # mapper's per-frame duplicate-endpoint suppression for max-range rays.
    _, representatives = np.unique(endpoint_indices, axis=0, return_index=True)
    origin_voxel = (origin-np.asarray(grid.map_min))/grid.resolution
    visible = set()
    for representative in np.sort(representatives):
        endpoint_voxel = (endpoints[representative]-np.asarray(grid.map_min))/grid.resolution
        for index in voxel_line(origin_voxel, endpoint_voxel):
            if not grid.in_bounds(index):
                break
            address = grid.address(index)
            state = grid.occupancy_state(address)
            if state == 1:
                break
            if state == -1 and _in_planning_region(grid.position(index), config):
                visible.add(address)
    return frozenset(visible)


def visible_shadow_union(grid, samples, config):
    rays = camera_unit_rays(config)
    result = set()
    for sample in samples:
        result.update(visible_unknown_shadow(
            grid, sample["position"], float(sample["yaw"]), config, rays))
    return result
