#!/usr/bin/env python3
import argparse
import json

from exploration_benchmark.sensor_shadow_observation import (
    write_sensor_shadow_comparison, write_sensor_shadow_observation)


def main():
    parser = argparse.ArgumentParser(description="Build/compare R2 camera shadow predictions")
    parser.add_argument("run_directory")
    parser.add_argument("snapshot_root")
    parser.add_argument("mapping_config")
    parser.add_argument("--output-directory")
    parser.add_argument("--spacing", type=float, default=0.1)
    parser.add_argument("--yaw-spacing", type=float, default=0.05)
    parser.add_argument("--evaluation-pixel-skip", type=int)
    args = parser.parse_args()
    prediction = write_sensor_shadow_observation(
        args.run_directory, args.snapshot_root, args.mapping_config,
        args.output_directory, args.spacing, args.yaw_spacing,
        args.evaluation_pixel_skip)
    comparison = write_sensor_shadow_comparison(
        args.output_directory or args.run_directory, args.snapshot_root,
        args.output_directory)
    print(json.dumps({"prediction": prediction, "comparison": comparison},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
