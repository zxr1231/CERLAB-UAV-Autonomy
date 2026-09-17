"""Reader and integrity checks for CERLAB R1 diagnostic snapshots."""

import json
import struct
from pathlib import Path


MAP_HEADER = struct.Struct("<8sIQd3d3d3i2dQ")
MAP_MAGIC = b"CR1MAP1\0"


class SnapshotError(ValueError):
    pass


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

    raw = map_path.read_bytes()
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
    expected_count = dimensions[0] * dimensions[1] * dimensions[2]
    if voxel_count != expected_count:
        raise SnapshotError("voxel count does not match map dimensions")
    payload = raw[MAP_HEADER.size:]
    if len(payload) != voxel_count * 2:
        raise SnapshotError("map payload size mismatch")

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
