# Benchmark v2 implementation status

## Completed in the first atomic checkpoint

- V2-00: baseline verified and `feat/benchmark-v2` created from `1716e46`.
- V2-01: metric sets, time origin, Unknown/provenance semantics, censoring, and fair
  comparison rules frozen in `METRICS_SPEC.md`.
- V2-02 floorplan2 prototype: direct SDF box parsing, full pose composition,
  deterministic voxelization, six-connected free-space extraction, static surface
  mask, robot-size box inflation, reachable flight-center mask, deterministic NPZ,
  canonical content hash, and top-down PNG preview.
- External method check: FUEL and FALCON papers plus FALCON's released map coverage
  implementation were inspected from primary sources.
- V2-03 producer checkpoint: `map_manager@da5facb` tracks the monotonic union of
  voxel addresses touched by sensor raycasts and publishes timestamped incremental
  deltas with sequence, raycast ID, and cumulative total. Direct `setFree()` and
  `freeRegion()` calls bypass the tracker.
- V2-03 consumer checkpoint: the logger loads the fixed mask, reconstructs the union
  from deltas, rejects sequence/count/duplicate errors, and records `coverage.csv`.
- V2-04 implementation: the runner records the third-confirmation simulation timestamp
  in `planning_start.json`; provisional free/surface Coverage and censored interpolated
  T80/T90/T95 are implemented. Clean full-run validation remains pending.
- V2-05 implementation: stable global-planning and local-trajectory IDs associate the
  selected PRM path, local optimizer input, sampled B-spline, and executed odometry.
  Per-trajectory length ratios and point-to-polyline deviations are generated without
  including return-home odometry.
- V2-07 completed: Runner CLI, result paths, simulator launch, DEP launch, and schema-2
  manifests now separate `environment_seed` and `planner_seed`; legacy `--seed`
  remains a shorthand for equal values.

## Floorplan2 static mask v1

- Shape: `201 × 201 × 25` voxels at 0.1 m resolution.
- Discrete task volume: 1,010.025 m³.
- Accessible static-free denominator: 980,550 voxels = 980.550 m³.
- Static occupied: 29,475 voxels = 29.475 m³.
- Static surface: 29,375 voxels = 29.375 m³.
- Reachable inflated flight-center space in z=[0.7,1.2]: 172,885 voxels.
- Unreachable static-free voxels: 0.
- Accessible XY boundary touches: 0, confirming a closed rasterized outer wall.
- Canonical content SHA256:
  `23c85015a99be3ea585e4a407b6a2e6654eb7263bbb64ad2f4ba319e8f8a43da`.
- Deterministic NPZ file SHA256:
  `c782566ede82d4fdc3928c3d9d73a94a1578a33d6382866e4b8923279dc0e930`.

## Verification

- Clean-environment Release build passed with `CMAKE_PREFIX_PATH=/opt/ros/noetic`.
- Benchmark core tests: 5 passed.
- Ground-truth generator tests: 7 passed.
- Existing return/completion/seed checks: 25 passed before prototype changes; the
  prototype does not link to those components.
- Sensor-observation tracker gtest: 2 cases passed; all dependent planner and flight
  targets rebuilt successfully.
- Coverage accumulator tests: 4 passed. Combined Catkin result: 20 tests, 0 failures.
- Headless seed-1 smoke reached `HOME_REACHED`; 612 provenance messages were
  contiguous, 137,459 unique full-map addresses reconciled exactly, free/surface
  curves were monotonic, and no process remained.
- A clean-commit schema-2 smoke at parent `6e0f508` also reached `HOME_REACHED`.
  Its manifest had an empty Git status and matching final `measurement_status`;
  sequences 1–1,074 were contiguous, 284,780 addresses reconciled exactly, and all
  Coverage invariants passed.
- Split-seed smoke at parent `9bbeffb` reached `HOME_REACHED`: result path and
  manifest recorded environment seed 1 and planner seed 2, Gazebo ran with
  `--seed 1`, `/DEP/random_seed` was 2, legacy `seed` was null, and provenance
  remained valid through sequence 1,584.
- V2-05 development smoke reached `HOME_REACHED`: 13 selected PRM paths, 15 local
  inputs, 15 B-splines, and one return path were recorded exactly once with unique
  IDs. All 15 B-splines associated with odometry; the offline alignment summary was
  `VALID`. A final clean-commit smoke remains pending.
- Real mask regenerated twice with byte-identical NPZ and PNG outputs.
- Array partition, disjointness, subset, shape, dtype, and stored-hash checks passed.
- No ROS/Gazebo processes remained.

## Explicitly pending

- `F_observable` oracle visibility mask and validation.
- Artificial-clear integration assertion beyond source-path and tracker tests.
- Full-run T80/T90/T95 behavior and logger overhead.
- Clean full-run validation of Coverage, T80/T90/T95, and the planning-active time
  origin.
- Collision and resource metrics.
- Batch seed matrix, statistics, and multi-run seed-pair validation.

The pipeline now outputs provisional Coverage. Until oracle visibility and a clean
full-run validation are complete, these values must not support paper claims;
existing historical map point counts remain proxies.

Draft PRs:

- Parent Benchmark v2: https://github.com/zxr1231/CERLAB-UAV-Autonomy/pull/3
- Sensor provenance producer: https://github.com/zxr1231/map_manager/pull/1
