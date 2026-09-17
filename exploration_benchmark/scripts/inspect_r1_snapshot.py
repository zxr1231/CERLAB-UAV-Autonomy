#!/usr/bin/env python3
import argparse
import json

from exploration_benchmark.r1_snapshot import load_snapshot


def main():
    parser = argparse.ArgumentParser(description="Validate and summarize one CERLAB R1 snapshot")
    parser.add_argument("snapshot_directory")
    args = parser.parse_args()
    snapshot = load_snapshot(args.snapshot_directory)
    planner = snapshot["planner"]
    summary = {
        "directory": snapshot["directory"],
        "planning_sequence": planner["planning_sequence"],
        "map": snapshot["map"],
        "roadmap_nodes": len(planner["roadmap_nodes"]),
        "roadmap_edges": len(planner["roadmap_edges"]),
        "goal_candidates": len(planner["goal_candidates"]),
        "candidate_paths": len(planner["candidate_paths"]),
        "selected_candidate": planner["selected_candidate"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
