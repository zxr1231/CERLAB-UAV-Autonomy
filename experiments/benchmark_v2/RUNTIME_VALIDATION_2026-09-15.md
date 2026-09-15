# Benchmark v2 online provenance smoke — 2026-09-15

This development run validated the online pipeline before committing its logger-side
implementation. Its manifest correctly records a dirty working tree, so it is not a
formal benchmark result.

- Run: `EXP-BENCH-V2-DEV/seed_001/20260915T101600`
- Mode: headless smoke, seed 1, threshold 500, rosbag disabled
- Outcome: `HOME_REACHED`
- Planning-active simulation timestamp: 3.904 s
- Provenance messages: 612, exactly sequence 1 through 612
- Unique full-map sensor-observed voxels: 137,459
- Task-box observed voxels: 123,514 = 123.514 m³ raw known volume
- Accessible-free observed: 120,891 / 980,550 = 12.3289%
- Static-surface observed: 2,623 / 29,375 = 8.9294%
- Stream errors, duplicates, gaps, and cumulative-count mismatches: zero
- Free and surface Coverage monotonicity: passed
- T80/T90/T95: null with `censored=true`, as expected for the small smoke region
- Mean RTF: 0.999247
- Residual ROS/Gazebo processes: none

The first provenance message was received at sim 1.555 s, before the planning-active
origin. Valid sensor observations acquired during takeoff are therefore retained and
become initial Coverage at planning time zero. Direct artificial clearing is excluded
by construction: only the two calls to `updateOccupancyInfo()` inside
`raycastUpdate()` mark the tracker, while `setFree()` and `freeRegion()` do not call
it.

This run validates transport and accounting behavior. The Coverage values remain
provisional pending oracle visibility analysis of the accessible-free denominator.

## Clean-commit repeat

A second headless seed-1 smoke ran from parent commit `6e0f508` with an empty
`git_status` and schema version 2:

- Run: `EXP-BENCH-V2-CLEAN/seed_001/20260915T102048`
- Outcome: `HOME_REACHED`
- Mission simulation duration: 65.376 s
- Mission odometry distance: 16.359 m
- Planning-active timestamp: 3.961 s
- Provenance sequences: 1–1,074, contiguous
- Unique full-map sensor-observed voxels: 284,780, exactly reconciled
- Task-box observed: 245,600 = 245.600 m³
- Accessible-free observed: 240,474 / 980,550 = 24.5244%
- Static-surface observed: 5,126 / 29,375 = 17.4502%
- Mean RTF: 0.999228
- Manifest `measurement_status`: `PROVISIONAL_ACCESSIBLE_FREE_V1`
- Stream validity and monotonicity checks: passed
- Residual processes: none

The two smoke runs followed different short trajectories even with seed 1, so their
final provisional Coverage differs. They validate data integrity, not algorithm
performance or end-to-end deterministic replay.
