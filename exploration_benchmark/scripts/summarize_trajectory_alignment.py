#!/usr/bin/env python3
import argparse
import json

from exploration_benchmark.trajectory_metrics import write_run_metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir")
    args = parser.parse_args()
    print(json.dumps(write_run_metrics(args.run_dir), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
