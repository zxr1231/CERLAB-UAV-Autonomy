#!/usr/bin/env python3
import argparse
import json

from exploration_benchmark.actual_observation import write_actual_observation


def main():
    parser = argparse.ArgumentParser(description="Build R2 actual observation sets")
    parser.add_argument("run_directory")
    parser.add_argument("--output-directory")
    args = parser.parse_args()
    summary = write_actual_observation(args.run_directory, args.output_directory)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
