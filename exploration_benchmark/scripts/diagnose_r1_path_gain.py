#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from exploration_benchmark.r1_path_gain import diagnose_snapshot_paths


def main():
    parser = argparse.ArgumentParser(description="Diagnose raw/unique/marginal path gain")
    parser.add_argument("snapshot_directory")
    parser.add_argument("--spacing", type=float, default=0.5,
                        help="spatial sample interval in meters (default: 0.5)")
    parser.add_argument("--output", help="optional JSON output path")
    args = parser.parse_args()
    report = diagnose_snapshot_paths(args.snapshot_directory, args.spacing)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
