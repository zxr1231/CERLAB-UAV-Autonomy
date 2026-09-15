# CERLAB Exploration Benchmark MVP

This package records lightweight simulation metrics without rosbag. It is based on the return-home baseline with `completion_gain_threshold=500`.

Implemented in this MVP:

- explicit DEP and Gazebo seeds;
- version/config manifest and ROS parameter dump;
- simulation and monotonic wall time with real-time factor;
- timestamped odometry trajectory and accumulated traveled distance;
- mission-state and failure events;
- steady-clock global, local B-spline, and return-path planning events;
- unique run directories and shutdown summaries.

Coverage is intentionally marked `UNAVAILABLE_NO_VERIFIED_DENOMINATOR`. The existing explored-map point count is recorded only as a map-size proxy because it includes artificial free regions.

After building and sourcing the workspace, run one small-ROI smoke experiment:

```bash
rosrun exploration_benchmark run_experiment.py \
  --experiment-id EXP-BENCH-SMOKE \
  --environment-seed 1 \
  --planner-seed 1 \
  --mode smoke \
  --timeout 240
```

Use `--mode full` for the configured full DEP region. RViz is disabled by default to reduce rendering effects; add `--rviz` for interactive debugging. The runner refuses to start if a ROS Master already exists and stops only the process groups it created.

Each run is written below the workspace `results/` directory as:

```text
EXP-ID/environment_seed_NNN/planner_seed_NNN/TIMESTAMP/
├── run.json
├── rosparams.yaml
├── metrics.csv
├── trajectory.csv
├── planning.csv
├── planned_paths.jsonl
├── trajectory_alignment.csv
├── trajectory_alignment_summary.json
├── coverage.csv
├── events.jsonl
├── runner_events.jsonl
├── planning_start.json
├── live_status.json
├── summary.json
├── runner_result.json
└── process logs
```

Run ROS-independent accounting tests with:

```bash
python3 exploration_benchmark/test/test_benchmark_core.py
```

The dated MVP runtime evidence and the limits of seed reproducibility are recorded in
[`VALIDATION.md`](VALIDATION.md).

Versioned experiment protocols, lightweight manifests, aggregate tables, and reports
are stored in the project-level [`experiments`](../experiments/README.md) directory.

Generate the Benchmark v2 floorplan2 ground-truth prototype with:

```bash
rosrun exploration_benchmark generate_ground_truth_mask.py \
  --world "$(rospack find uav_simulator)/worlds/floorplan2/floorplan2_dynamic_5.world" \
  --config "$(rospack find exploration_benchmark)/../experiments/benchmark_v2/config/floorplan2_static_v1.json" \
  --output-mask /tmp/floorplan2_static_v1.npz \
  --output-metadata /tmp/floorplan2_static_v1.metadata.json \
  --output-preview /tmp/floorplan2_static_v1.png
```

The committed mask is an offline evaluation artifact. It is not loaded by the
exploration planner and does not change map updates or path selection.

On `feat/benchmark-v2`, the runner loads this mask by default and records provisional
sensor-provenance coverage. Use `--disable-coverage` only for explicit compatibility
runs. Coverage remains provisional until the scenario's oracle visibility audit has
passed.

`--environment-seed` controls Gazebo and `--planner-seed` controls DEP. The legacy
`--seed N` remains available as shorthand for setting both to `N`; manifests always
record the two effective values separately.

Benchmark v2 assigns stable IDs to accepted local B-spline trajectories and records
the selected global PRM path, local optimizer input, sampled B-spline, and associated
odometry separately. `trajectory_alignment.csv` compares their lengths and geometric
deviations. Odometry remains assigned to the active local trajectory until it is
replaced or return planning begins; return-home motion is therefore excluded from
local B-spline execution metrics.
