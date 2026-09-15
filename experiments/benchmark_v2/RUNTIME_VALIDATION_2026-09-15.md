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
