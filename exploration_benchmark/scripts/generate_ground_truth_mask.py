#!/usr/bin/env python3
"""Generate deterministic CERLAB ground-truth mask artifacts."""
import argparse
import json
from pathlib import Path

from exploration_benchmark.ground_truth import (build_masks, file_sha256,
                                                topdown_image,
                                                write_deterministic_npz,
                                                write_json, write_rgb_png)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--world", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-mask", required=True)
    parser.add_argument("--output-metadata", required=True)
    parser.add_argument("--output-preview", required=True)
    args = parser.parse_args()

    world = Path(args.world).resolve()
    config_path = Path(args.config).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    arrays, metadata, grid = build_masks(world, config)
    output_mask = Path(args.output_mask).resolve()
    output_preview = Path(args.output_preview).resolve()
    write_deterministic_npz(output_mask, arrays)
    write_rgb_png(output_preview, topdown_image(arrays, grid, config["home_position"]), scale=4)
    metadata.update({
        "world_path": str(world),
        "world_sha256": file_sha256(world),
        "config_path": str(config_path),
        "config_sha256": file_sha256(config_path),
        "mask_path": str(output_mask),
        "mask_file_sha256": file_sha256(output_mask),
        "preview_path": str(output_preview),
        "preview_sha256": file_sha256(output_preview),
    })
    write_json(args.output_metadata, metadata)
    print(json.dumps({
        "mask": str(output_mask),
        "metadata": str(Path(args.output_metadata).resolve()),
        "preview": str(output_preview),
        "content_sha256": metadata["mask_content_sha256"],
        "counts": metadata["counts"],
        "volumes_m3": metadata["volumes_m3"],
        "xy_boundary_touch": metadata["accessible_free_touches_xy_boundary"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
