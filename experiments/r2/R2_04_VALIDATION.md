# R2-04 validation: four-layer predicted observation sets

Date: 2026-09-21

Status: complete for predicted-set construction. R2-05 will perform alignment and
overlap analysis; no correlation claim is made here.

## Data-path changes

The planner now retains each successful A* path before geometric shortcutting, in
parallel with the shortcut candidate. `findBestPath()` still receives and ranks the
same shortcut paths; the selected candidate index only identifies the corresponding
raw path for logging. Global events and fixed snapshots now contain both representations.

Local planning events also record the B-spline start position/yaw. Benchmark path logs
retain `prm_raw`, existing shortcut `prm`, local input and B-spline paths.

## Prediction definitions

All layers use the immutable map snapshot captured for their `global_sequence`, the
R1 `legacy_proxy_v1` visibility model, and formal 0.25 m spatial sampling.

- **PRM raw:** original A* node sequence, outgoing segment yaw and terminal best yaw;
- **PRM shortcut:** geometrically simplified selected route with the same yaw rule;
- **B-spline:** sampled B-spline polyline using the local-planning start yaw as the
  nominal held yaw, matching the controller's no-commanded-yaw-change behavior;
- **odom prefix:** actually executed positions and measured yaw, retained whenever
  translation exceeds 0.25 m or yaw changes by at least 0.1 rad, plus the terminal pose.

Each layer outputs sample count, predicted Unknown count, deterministic SHA-256 and the
full sorted address set. Missing snapshot, selected candidate, raw path, local plan,
B-spline or odometry fails the affected interval explicitly.

## Tests and regressions

Five new tests cover constant-yaw B-spline sampling, translation/yaw odom sampling,
path-history union, complete four-layer ID linkage and missing-snapshot failure. The
complete exploration benchmark suite has 68 passing tests. Modified global_planner,
exploration_benchmark and dependent autonomous_flight compile. All return-home checks
pass, including threshold 500 behavior.

## Live smoke

A fresh seed-1 no-GUI run captured 7 global snapshots and 23 completed local execution
intervals. All 23 intervals produced every predicted layer with zero construction
errors.

| Layer | Samples per interval min/median/max | Predicted voxels min/median/max |
|---|---:|---:|
| raw PRM | 4 / 23 / 30 | 1031 / 2197 / 2251 |
| shortcut PRM | 4 / 20 / 27 | 1031 / 2204 / 2298 |
| B-spline | 7 / 22 / 40 | 339 / 808 / 2395 |
| odom prefix | 3 / 4 / 33 | 0 / 38 / 3001 |

Later snapshots demonstrate real shortcut reduction: selected raw/shortcut waypoint
counts included 7/3, 5/2, 4/2 and 8/3, so the two PRM layers are not aliases. Prediction
construction took 54.24 wall seconds and about 99 MiB maximum RSS for the fixture.

The local-start map version exceeded its global snapshot version by 488 to 2,811,222
updates. This is retained evidence of map staleness, not silently corrected. R2-05 must
stratify or reject intervals whose prediction snapshot is too stale before interpreting
predicted/actual overlap.

R2-05 subsequently fixed this alignment problem by capturing a second immutable map at
each successful B-spline activation. Formal layer/actual comparison now uses the
execution-start snapshot; global snapshots remain useful for plan-time audit.

| Generated file | SHA-256 |
|---|---|
| `predicted_observation_summary.json` | `2a20d4ef7685a5096b6ddd3e64fef3df7b1d90d4086e52baacadf16b5f40b019` |
| `predicted_observation_sets.jsonl` | `bbd9fca3955d39f410aa6207acd6e6ec4459382a5dd78c4051c9c4a6a9abb981` |

## Limitations handed to R2-05

- nominal B-spline yaw is held at the plan-start yaw, while odom uses measured yaw;
- a single global snapshot may serve several later local trajectories and become stale;
- short odom intervals can have very small predicted sets;
- no Jaccard, precision, recall, layer-retention or predicted/actual calibration metric
  has yet been calculated;
- the smoke was manually stopped and is not a full exploration experiment.
