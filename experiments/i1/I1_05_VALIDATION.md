# I1-05 validation: feature-flagged Unique online selection

Date: 2026-09-23

Status: complete for engineering validation. Proceed to the paired three-seed I1-06
pilot; no exploration-performance claim is made from this small-ROI smoke.

## Selection and fallback

`unique_online` evaluates every candidate on one immutable snapshot and selects the
highest valid Unique utility. The already computed Legacy winner remains available.
Evaluation failure, absence of a valid candidate or an invalid candidate index keeps
the Legacy route and emits a stable fallback reason.

Only candidate ranking changes. Goal filtering, one geometric A* route per goal,
shortcut, dynamics and safety remain fixed. `bestPathGain` and reachable-roadmap
completion checks remain Legacy, preserving threshold 500.

Ten C++ evaluator/selection tests cover deterministic ties, invalid scores, no valid
candidate, out-of-range candidate and Legacy/shadow behavior. All 85 Python tests and
all return-home/threshold checks pass.

## Seed-1 small-ROI smoke

The clean source run `EXP-I1-05-UNIQUE-ONLINE-SMOKE-V1` reached HOME_REACHED with no
collision, crash or rosbag.

```text
global plans: 10
valid Unique evaluations: 10/10
selection_gain_mode=unique: 10/10
fallbacks: 0
Legacy/Unique Top-1 changes: 2/10
selected duplicate ratio mean: 67.08%
Unique evaluation mean/p95/max: 19.46 / 25.19 / 25.19 ms
global planning mean/p95/max: 39.49 / 83.98 / 83.98 ms
mission time/distance: 60.796 s / 13.103 m
mean RTF: 0.99928
trajectory alignment: VALID
```

Both changed decisions were executed through the normal selected-path → local
B-spline → odometry pipeline. The trajectory summary contains 20 trajectories with
odometry and six exploration trajectories with complete alignment metrics.

No normal-run fallback occurred. Fallback correctness is established by deterministic
tests rather than by intentionally corrupting a live map.

## Decision

I1-05 passes the engineering gate. I1-06 must run same-commit paired Legacy and
Unique-online modes for seed pairs 1/1, 2/2 and 3/3. Because simulation and planning
are asynchronous, the pairs are controlled repeated trials rather than identical
trajectories. Retain failures and compare Coverage, T80/T90/T95, distance, actual
observations, planning cost, resources, collision and success.

Do not add caching, retune the environment or change the Legacy completion gate.

