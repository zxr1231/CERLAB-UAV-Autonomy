#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from exploration_benchmark.r1_sensitivity import compare_sampling_studies


def main():
    parser = argparse.ArgumentParser(description="Compare R1 path sampling intervals")
    parser.add_argument("--study", nargs=2, action="append", metavar=("SPACING", "DIR"),
                        required=True, help="repeat for each spacing")
    parser.add_argument("--output")
    args = parser.parse_args()
    studies = {float(spacing): directory for spacing, directory in args.study}
    result = compare_sampling_studies(studies)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
