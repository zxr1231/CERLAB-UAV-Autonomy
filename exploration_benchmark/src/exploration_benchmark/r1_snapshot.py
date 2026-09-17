"""Reader and integrity checks for CERLAB R1 diagnostic snapshots."""

import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path


MAP_HEADER = struct.Struct("<8sIQd3d3d3i2dQ")
MAP_MAGIC = b"CR1MAP1\0"


class SnapshotError(ValueError):
    pass


@dataclass(frozen=True)
class FrozenVoxelMap:
    """Immutable discrete map loaded from one R1 snapshot."""

    version: int
    resolution: float
    map_min: tuple
    map_max: tuple
    dimensions: tuple
    p_min_log: float
    p_occ_log: float
    payload: bytes

    @property
    def voxel_count(self):
        return self.dimensions[0] * self.dimensions[1] * self.dimensions[2]

    def in_bounds(self, index):
        return all(0 <= index[axis] < self.dimensions[axis] for axis in range(3))

    def address(self, index):
        if not self.in_bounds(index):
            raise IndexError("voxel index outside frozen map")
        x, y, z = index
        return x * self.dimensions[1] * self.dimensions[2] + y * self.dimensions[2] + z

    def index(self, address):
        if address < 0 or address >= self.voxel_count:
            raise IndexError("voxel address outside frozen map")
        yz = self.dimensions[1] * self.dimensions[2]
        x, remainder = divmod(address, yz)
        y, z = divmod(remainder, self.dimensions[2])
        return x, y, z

    def position(self, index):
        if not self.in_bounds(index):
            raise IndexError("voxel index outside frozen map")
        return tuple((index[axis] + 0.5) * self.resolution + self.map_min[axis]
                     for axis in range(3))

    def position_to_index(self, position):
        return tuple(int(math.floor((position[axis] - self.map_min[axis]) /
                                    self.resolution)) for axis in range(3))

    def occupancy_state(self, address):
        if address < 0 or address >= self.voxel_count:
            raise IndexError("voxel address outside frozen map")
        value = self.payload[2 * address]
        return value - 256 if value >= 128 else value

    def is_unknown(self, address):
        return self.occupancy_state(address) == -1

    def is_inflated(self, address):
        if address < 0 or address >= self.voxel_count:
            raise IndexError("voxel address outside frozen map")
        return self.payload[2 * address + 1] == 1


def fnv1a64(path):
    value = 0xCBF29CE484222325
    with Path(path).open("rb") as stream:
        while True:
            chunk = stream.read(65536)
            if not chunk:
                break
            for byte in chunk:
                value ^= byte
                value = (value * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return f"{value:016x}"


def _parse_map(raw):
    if len(raw) < MAP_HEADER.size:
        raise SnapshotError("truncated map header")
    values = MAP_HEADER.unpack_from(raw)
    magic, schema, version, resolution = values[:4]
    map_min = values[4:7]
    map_max = values[7:10]
    dimensions = values[10:13]
    p_min_log, p_occ_log, voxel_count = values[13:]
    if magic != MAP_MAGIC or schema != 1:
        raise SnapshotError("unsupported map binary schema")
    if resolution <= 0 or any(dimension <= 0 for dimension in dimensions):
        raise SnapshotError("invalid map geometry")
    expected_count = dimensions[0] * dimensions[1] * dimensions[2]
    if voxel_count != expected_count:
        raise SnapshotError("voxel count does not match map dimensions")
    payload = raw[MAP_HEADER.size:]
    if len(payload) != voxel_count * 2:
        raise SnapshotError("map payload size mismatch")
    return FrozenVoxelMap(version, resolution, tuple(map_min), tuple(map_max),
                          tuple(dimensions), p_min_log, p_occ_log, payload)


def load_frozen_map(directory):
    """Load the immutable voxel arrays after validating the snapshot manifest."""
    snapshot = load_snapshot(directory)
    map_path = Path(directory) / snapshot["manifest"]["map_file"]
    return _parse_map(map_path.read_bytes())


def load_snapshot(directory):
    directory = Path(directory)
    manifest_path = directory / "manifest.json"
    if not manifest_path.is_file():
        raise SnapshotError("snapshot has no manifest commit marker")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "cerlab-r1-snapshot-v1" or not manifest.get("complete"):
        raise SnapshotError("unsupported or incomplete snapshot manifest")

    map_path = directory / manifest["map_file"]
    planner_path = directory / manifest["planner_file"]
    if fnv1a64(map_path) != manifest["map_fnv1a64"]:
        raise SnapshotError("map hash mismatch")
    if fnv1a64(planner_path) != manifest["planner_fnv1a64"]:
        raise SnapshotError("planner hash mismatch")

    frozen_map = _parse_map(map_path.read_bytes())
    version = frozen_map.version
    resolution = frozen_map.resolution
    map_min = frozen_map.map_min
    map_max = frozen_map.map_max
    dimensions = frozen_map.dimensions
    p_min_log = frozen_map.p_min_log
    p_occ_log = frozen_map.p_occ_log
    voxel_count = frozen_map.voxel_count
    payload = frozen_map.payload

    occupancy_counts = {"unknown": 0, "free": 0, "occupied": 0}
    inflated_count = 0
    for offset in range(0, len(payload), 2):
        state = struct.unpack_from("<b", payload, offset)[0]
        inflated = payload[offset + 1]
        if state == -1:
            occupancy_counts["unknown"] += 1
        elif state == 0:
            occupancy_counts["free"] += 1
        elif state == 1:
            occupancy_counts["occupied"] += 1
        else:
            raise SnapshotError("invalid occupancy state")
        if inflated not in (0, 1):
            raise SnapshotError("invalid inflated state")
        inflated_count += inflated

    planner = json.loads(planner_path.read_text(encoding="utf-8"))
    if planner.get("schema") != "cerlab-r1-planner-v1":
        raise SnapshotError("unsupported planner schema")
    if planner.get("planning_sequence") != manifest.get("planning_sequence"):
        raise SnapshotError("planner and manifest sequence mismatch")
    if planner.get("map_version") != version or manifest.get("map_version") != version:
        raise SnapshotError("map version mismatch across snapshot files")

    return {
        "directory": str(directory),
        "manifest": manifest,
        "planner": planner,
        "map": {
            "version": version,
            "resolution": resolution,
            "min": list(map_min),
            "max": list(map_max),
            "dimensions": list(dimensions),
            "p_min_log": p_min_log,
            "p_occ_log": p_occ_log,
            "voxel_count": voxel_count,
            "occupancy_counts": occupancy_counts,
            "inflated_count": inflated_count,
        },
    }
