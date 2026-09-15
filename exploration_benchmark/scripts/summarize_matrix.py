#!/usr/bin/env python3
import argparse
from pathlib import Path

from exploration_benchmark.aggregate import (aggregate_rows, rows_from_batch_state,
                                             write_outputs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-state", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    state, rows = rows_from_batch_state(Path(args.batch_state).resolve())
    aggregate = aggregate_rows(rows)
    aggregate["experiment_id"] = state.get("experiment_id")
    aggregate["batch_config_sha256"] = state.get("config_sha256")
    output = Path(args.output_dir).resolve()
    write_outputs(rows, output, aggregate)
    print(str(output))


if __name__ == "__main__":
    main()
