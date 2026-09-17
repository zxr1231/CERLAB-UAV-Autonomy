# V2-05 trajectory association validation

Date: 2026-09-15

## Scope

This checkpoint verifies that the Benchmark v2 logger can distinguish and associate:

1. the selected global PRM path;
2. the local optimizer input path;
3. the sampled B-spline sent for execution;
4. odometry observed while that B-spline is active.

Return trajectories are retained but separated from the primary exploration
aggregate using `global_sequence`: positive values identify exploration paths and
zero identifies return-home paths. This prevents return motion from changing the
reported exploration-path metrics.

## Clean runtime check

- Parent commit: `fa4050a3d73c3dd8abccf9d681a8ee117716770b`
- `autonomous_flight` commit: `8940580`
- Environment seed / planner seed: `1 / 1`
- Mode: small-ROI smoke
- Outcome: `HOME_REACHED`
- Wall duration: 84.66 s
- Manifest Git status: clean
- Planning events: 10 global, 7 local, 1 return
- Path records: 10 PRM, 7 local inputs, 7 B-splines, 1 return
- Duplicate `(kind, id)` records: 0
- Phase split: 5 exploration B-splines, 2 return B-splines
- Trajectories associated with odometry: 5/5 exploration, 2/2 return
- Trajectory summary status: `VALID`
- Coverage validity: true (`PROVISIONAL_ACCESSIBLE_FREE_V1`)
- Residual ROS/Gazebo processes: 0

The raw run remains outside Git at:
`/home/zxr2/cerlab_benchmark_ws/results/EXP-BENCH-V2-TRAJ-CLEAN/environment_seed_001/planner_seed_001/20260915T204810`.

The smoke values verify instrumentation behavior only. They are not performance
evidence and must not be used as paper results.

## Tests

- Clean Release workspace build passed.
- Benchmark trajectory tests: 3 passed.
- Workspace test result summary after the change: 24 tests, 0 failures.
