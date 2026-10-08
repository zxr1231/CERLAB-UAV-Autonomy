# I2-04 — Integration checkpoint and decision

Date: 2026-10-08. Status: implementation/contract tests and bounded smoke COMPLETE.
This is not an I2-05 pilot or evidence of exploration superiority.

## Implementation

- New /DEP/route_controls/mode and launch/runner switches: historical_legacy (default),
  distance_single, generic_k_shortest, geometric_diverse. New controls reject
  Unique-online; Legacy or Unique-shadow is allowed. YAML world/sensor/dynamics,
  completion500 and coverage definitions stay fixed.
- Stable sorted PRM position IDs, directed snapshot-validated graph, detached route
  nodes, original Goal prefilter unchanged. Ambiguous duplicate roadmap positions
  reject the adapter and explicitly log historical fallback. All-goals-unreachable
  uses existing recovery fallback; candidate supply failure is never completion.
- One immutable snapshot for graph/collision, ordinary shortcut, Legacy floating-grid
  node/yaw gain and Unique shadow. No substitution of voxel-centre union for Legacy.
  Scoring keeps intermediate-node sum, Goal best-yaw and motion-time formula.
- All mandatory routes/shortcut validation precede the 50 ms alternative deadline.
  New reuse APIs avoid hidden reference reruns after that deadline; per-Goal/global
  heap limits and cutoff logs remain. Scoring, map copying and serialization are
  charged in total planning time. Deadline is cooperative, not hard real-time.
- Original A* is compared using a FrozenRouteMap compatibility copy of the SAME
  captured map/graph. This audit copy is an extra cost, not free benchmark work.
  Temporary adjacency is cleared even on exceptions to avoid ownership cycles.
- Winner is rechecked using a newly captured complete map snapshot before release;
  unsafe winner is rejected. Both planning and validation versions are logged.
  Later map/obstacle changes still require existing local/B-spline safety handling.
- Lightweight route_controls.jsonl links global_sequence to existing raw PRM,
  simplified PRM, local input, B-spline, odometry and execution intervals. It stores
  graph/Goal IDs, protocol hash, routes, constraints/rejections, counts, cutoffs and
  candidate scores. Scored count comes from scoring, not requested K.

## Real defect found and fixed

V1 smoke showed versions changing during planning. Source confirms a dedicated
exploreReplanWorker_, despite main ros::spin(). Initial live-map A* comparison and
live final-check reads could observe mixed/new states. No collision was recorded,
but the consistency contract failed. c17fa0e replaces these with frozen comparison
and fresh snapshot safety validation. V1 remains intact; V2 is separate. Nothing
in I1-06 was rerun/replaced and no I1 evaluator correction is claimed.

## Validation

- Targeted catkin build: planner, exploration node and route tests pass.
- 3 real occMap/snapshot tests: collision/Unknown/bounds, frozen state under mutation,
  off-centre Legacy gains/yaw counts and selected score equality; all three new
  modes produce safe logged candidates. Frozen A* compatibility is checked.
- 7 distance/Yen and 10 candidate contract tests pass, including reference reuse.
- 4 execution-interval and 3 trajectory-metric Python checks pass; changed scripts
  compile. Sanitizers were NOT rerun for this integration task; do not reuse earlier
  isolated sanitizer evidence as proof for this changed code.
- V2 four sequential headless seed-1/1 runs, each bounded at 35 wall seconds after
  planning starts. All moved, zero measured collisions, no detected crash, valid
  resources/trajectory records, all four route layers and execution association.
  New mode shadow scores share the captured version, frozen A* comparisons match
  their map, and no rejected unsafe winner was executed in these samples.
- Outcomes remain TIMEOUT and run.json status FAILED as the original runner writes
  for an incomplete mission. Separate smoke audit passes its bounded criteria.
  No full mission success/T80/T90/T95 claim is made.

## Observations and implications

See I2_04_SMOKE_SUMMARY.json for exact logs and checks.

| Mode | global events | Raw / distinct / scored (ready events) | extra routes surviving | mean planner ms |
|---|---:|---:|---:|---:|
| historical Legacy | 4 | original path control | — | 54.906 |
| distance single | 4 | 11 / 11 / 11 | 0 | 128.917 |
| generic K-shortest | 4 (one recovery fallback) | 42 / 7 / 7 | 0 | 140.386 |
| geometric diverse | 5 | 54 / 9 / 9 | 0 | 126.597 |

All sampled RTF means are about 0.999. Mean times are smoke measurements only:
new controls also ran Unique shadow, graph/snapshot audit and extra logging; they
are not a controlled algorithm-efficiency comparison to default Legacy.
25 same-snapshot A* comparisons show maximum excess length 1.78e-15 m (rounding
scale), so these samples do not demonstrate a historical A* distance error.

Most alternatives fail raw time/yaw/length caps; additional candidates collapse
under ordinary shortcut. No extra candidate survives in these short early-phase
samples. This supports the need to audit actual candidate supply, not a claim that
geometric diversity or the proposed observation-guided method improves exploration.

## Next bounded task

I2-05 must first register a candidate-supply diagnostic across existing frozen
snapshots/planning phases. Check if useful alternatives survive motion limits and
ordinary shortcut. If all choices remain reference-only, do not spend a full three-
seed performance matrix comparing effectively identical candidate sets. Diagnose
whether this is early-scene geometry, pool/deadline insufficiency, raw motion proxy
or ordinary shortcut. Any protocol adjustment needs a new version before affected
experiments and the same settings for all multi-route controls. Do not tune to a
favorable T95, change frozen I1, or secretly introduce observation-preserving shortcut.
After that gate, register the same-commit/same-scoring pilot matrix. I3 still requires
the held-out predicted/actual ordering gate. Legacy remains operational default.

User repositories and local backup contain code/docs/evidence; raw V1/V2 logs remain
under cerlab_benchmark_ws/results and are included in the I2-04 result archive.
