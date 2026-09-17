#!/usr/bin/env python3
import argparse
import json

from exploration_benchmark.r1_snapshot import load_frozen_map, load_snapshot
from exploration_benchmark.r1_visibility import (LegacyVisibilityConfig,
                                                  visible_set_sha256,
                                                  visible_unknown_voxels)


def main():
    parser = argparse.ArgumentParser(description="Evaluate one visible-unknown set")
    parser.add_argument("snapshot_directory")
    parser.add_argument("--position", nargs=3, type=float,
                        help="viewpoint x y z; defaults to the captured vehicle pose")
    parser.add_argument("--yaw", type=float,
                        help="viewpoint yaw in radians; defaults to captured yaw")
    parser.add_argument("--list-addresses", action="store_true")
    args = parser.parse_args()

    snapshot = load_snapshot(args.snapshot_directory)
    planner = snapshot["planner"]
    grid = load_frozen_map(args.snapshot_directory)
    position = args.position or planner["vehicle"]["position"]
    yaw = planner["vehicle"]["yaw"] if args.yaw is None else args.yaw
    config = LegacyVisibilityConfig.from_planner(planner)
    visible = visible_unknown_voxels(grid, position, yaw, config)
    result = {
        "model": "legacy_proxy_v1",
        "map_version": grid.version,
        "position": list(position),
        "yaw": yaw,
        "visible_unknown_count": len(visible),
        "visible_set_sha256": visible_set_sha256(visible),
    }
    if args.list_addresses:
        result["visible_unknown_addresses"] = sorted(visible)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
