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
  --seed 1 \
  --mode smoke \
  --timeout 240
```

Use `--mode full` for the configured full DEP region. RViz is disabled by default to reduce rendering effects; add `--rviz` for interactive debugging. The runner refuses to start if a ROS Master already exists and stops only the process groups it created.

Each run is written below the workspace `results/` directory as:

```text
EXP-ID/seed_NNN/TIMESTAMP/
├── run.json
├── rosparams.yaml
├── metrics.csv
├── trajectory.csv
├── planning.csv
├── events.jsonl
├── runner_events.jsonl
├── live_status.json
├── summary.json
├── runner_result.json
└── process logs
```

Run ROS-independent accounting tests with:

```bash
python3 exploration_benchmark/test/test_benchmark_core.py
```
