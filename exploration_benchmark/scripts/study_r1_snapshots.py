#!/usr/bin/env python3
import argparse
import json

from exploration_benchmark.r1_snapshot_study import run_snapshot_study


def main():
    parser = argparse.ArgumentParser(description="Run and aggregate an R1 snapshot study")
    parser.add_argument("snapshot_root")
    parser.add_argument("output_directory")
    parser.add_argument("--spacing", type=float, default=0.5)
    parser.add_argument("--min-position-delta", type=float, default=1.0)
    parser.add_argument("--min-map-version-delta", type=int, default=500000)
    parser.add_argument("--no-keep-final", action="store_true")
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()
    summary = run_snapshot_study(
        args.snapshot_root, args.output_directory, args.spacing, not args.no_resume,
        args.min_position_delta, args.min_map_version_delta, not args.no_keep_final)
    concise = {
        "snapshots": len(summary["rows"]),
        "failures": len(summary["failures"]),
        "aggregate": summary["aggregate"],
    }
    print(json.dumps(concise, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
