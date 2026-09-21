#!/usr/bin/env python3
import argparse
import json

from exploration_benchmark.predicted_observation import write_predicted_observation


def main():
    parser = argparse.ArgumentParser(description="Build R2 predicted observation sets")
    parser.add_argument("run_directory")
    parser.add_argument("snapshot_root")
    parser.add_argument("--output-directory")
    parser.add_argument("--spacing", type=float, default=0.25)
    parser.add_argument("--odom-yaw-spacing", type=float, default=0.1)
    args = parser.parse_args()
    summary = write_predicted_observation(
        args.run_directory, args.snapshot_root, args.output_directory,
        args.spacing, args.odom_yaw_spacing)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
