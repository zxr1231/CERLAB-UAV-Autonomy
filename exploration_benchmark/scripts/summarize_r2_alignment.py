#!/usr/bin/env python3
import argparse
import json

from exploration_benchmark.observation_alignment import write_alignment


def main():
    parser = argparse.ArgumentParser(description="Align R2 predicted and actual sets")
    parser.add_argument("run_directory")
    parser.add_argument("snapshot_root")
    parser.add_argument("--output-directory")
    args = parser.parse_args()
    summary = write_alignment(args.run_directory, args.snapshot_root, args.output_directory)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
