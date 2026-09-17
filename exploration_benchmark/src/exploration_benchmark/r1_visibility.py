"""Visible-unknown voxel sets for frozen CERLAB R1 snapshots."""

import hashlib
import math
import struct
from dataclasses import dataclass


@dataclass(frozen=True)
class LegacyVisibilityConfig:
    horizontal_fov: float
    vertical_fov: float
    dmin: float
    dmax: float
    planning_min: tuple
    planning_max: tuple

    def __post_init__(self):
        scalar_values = (self.horizontal_fov, self.vertical_fov, self.dmin, self.dmax)
        if not all(math.isfinite(value) for value in scalar_values):
            raise ValueError("visibility parameters must be finite")
        if len(self.planning_min) != 3 or len(self.planning_max) != 3:
            raise ValueError("planning region must contain three axes")
        region_values = tuple(self.planning_min) + tuple(self.planning_max)
        if not all(math.isfinite(value) for value in region_values):
            raise ValueError("planning region must be finite")
        if not 0 < self.horizontal_fov <= 2 * math.pi:
            raise ValueError("horizontal FoV must be in (0, 2*pi]")
        if not 0 < self.vertical_fov < math.pi:
            raise ValueError("vertical FoV must be in (0, pi)")
        if self.dmin < 0 or self.dmax <= 0 or self.dmin > self.dmax:
            raise ValueError("invalid sensor distance bounds")
        if any(self.planning_min[i] > self.planning_max[i] for i in range(3)):
            raise ValueError("invalid planning region")

    @classmethod
    def from_planner(cls, planner):
        sensor = planner["sensor_model"]
        region = planner["planning_region"]
        if sensor.get("visibility_model") != "legacy_inflated_occupied_line":
            raise ValueError("snapshot visibility model is not supported by legacy_proxy_v1")
        config = cls(
            float(sensor["horizontal_fov"]),
            float(sensor["vertical_fov"]),
            float(sensor["dmin"]),
            float(sensor["dmax"]),
            tuple(float(value) for value in region["min"]),
            tuple(float(value) for value in region["max"]),
        )
        return config


def _angle_difference(first, second):
    return abs((first - second + math.pi) % (2 * math.pi) - math.pi)


def _inflated_at_position(grid, position):
    index = grid.position_to_index(position)
    if not grid.in_bounds(index):
        return True
    return grid.is_inflated(grid.address(index))


def _legacy_line_occluded(grid, target, viewpoint):
    """Mirror occMap::isInflatedOccupiedLine(target, viewpoint)."""
    if _inflated_at_position(grid, target) or _inflated_at_position(grid, viewpoint):
        return True
    delta = tuple(viewpoint[i] - target[i] for i in range(3))
    distance = math.sqrt(sum(value * value for value in delta))
    if distance <= 0:
        return False
    steps = int(distance / grid.resolution)
    direction = tuple(value / distance for value in delta)
    for step in range(1, steps):
        position = tuple(target[i] + step * grid.resolution * direction[i]
                         for i in range(3))
        if _inflated_at_position(grid, position):
            return True
    return False


def visible_unknown_voxels(grid, viewpoint, yaw, config):
    """Return stable global addresses visible under DEP's frozen legacy proxy.

    This intentionally preserves two baseline behaviors: ``dmin`` is recorded but is
    not applied, and vertical FoV defines a z scan envelope rather than a true angular
    frustum. Unknown voxels do not occlude other unknown voxels.
    """
    viewpoint = tuple(float(value) for value in viewpoint)
    if len(viewpoint) != 3 or not all(math.isfinite(value) for value in viewpoint):
        raise ValueError("viewpoint must contain three finite coordinates")
    if not math.isfinite(yaw):
        raise ValueError("yaw must be finite")
    if _inflated_at_position(grid, viewpoint):
        return frozenset()

    z_range = config.dmax * math.tan(config.vertical_fov / 2.0)
    bounds_min = (viewpoint[0] - config.dmax,
                  viewpoint[1] - config.dmax,
                  viewpoint[2] - z_range)
    bounds_max = (viewpoint[0] + config.dmax,
                  viewpoint[1] + config.dmax,
                  viewpoint[2] + z_range)
    index_min = []
    index_max = []
    for axis in range(3):
        lower = max(bounds_min[axis], config.planning_min[axis], grid.map_min[axis])
        upper = min(bounds_max[axis], config.planning_max[axis], grid.map_max[axis])
        if lower > upper:
            return frozenset()
        first = int(math.ceil((lower - grid.map_min[axis]) / grid.resolution - 0.5))
        last = int(math.floor((upper - grid.map_min[axis]) / grid.resolution - 0.5))
        index_min.append(max(0, first))
        index_max.append(min(grid.dimensions[axis] - 1, last))
    if any(index_min[axis] > index_max[axis] for axis in range(3)):
        return frozenset()

    visible = set()
    max_distance_squared = config.dmax * config.dmax
    half_horizontal_fov = config.horizontal_fov / 2.0
    for x in range(index_min[0], index_max[0] + 1):
        for y in range(index_min[1], index_max[1] + 1):
            for z in range(index_min[2], index_max[2] + 1):
                index = (x, y, z)
                address = grid.address(index)
                if not grid.is_unknown(address) or grid.is_inflated(address):
                    continue
                target = grid.position(index)
                delta = tuple(target[i] - viewpoint[i] for i in range(3))
                if sum(value * value for value in delta) > max_distance_squared + 1e-12:
                    continue
                horizontal_norm = math.hypot(delta[0], delta[1])
                if horizontal_norm <= 1e-12:
                    continue
                target_yaw = math.atan2(delta[1], delta[0])
                if _angle_difference(target_yaw, yaw) > half_horizontal_fov + 1e-12:
                    continue
                if _legacy_line_occluded(grid, target, viewpoint):
                    continue
                visible.add(address)
    return frozenset(visible)


def visible_set_sha256(addresses):
    digest = hashlib.sha256()
    for address in sorted(addresses):
        digest.update(struct.pack("<Q", address))
    return digest.hexdigest()
