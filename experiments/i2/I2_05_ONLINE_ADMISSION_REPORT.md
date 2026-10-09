# I2-05 second batch — Fixed start pose and online admission

Date: 2026-10-08. Status: pose fix and online admission COMPLETE/PASSED.
The full I2-05 paired pilot remains pending. User requested backup after this task.

## Change and scope

New controls copy one coherent position/yaw/stamp/sequence from a mutex-protected
odometry mailbox at candidate-generation entry. The worker owns this per-plan copy.
Graph start node, synthetic start connectors, motion constraints, recorded start yaw
and Legacy-formula candidate time/score use the same copy. Callback updates cannot
change the values midway through new-control scoring.

Historical_legacy keeps its original callback and live-yaw selection behavior.
No I1 data, evaluator formula, world/sensor/dynamics, coverage or V1 K/budget limit
was changed. This fixes the new integration's 12/27 yaw mismatch previously found
(max0.0183 rad), not an I1-06 conclusion. Map snapshot and pose are recorded separately;
this is not an atomically synchronized SLAM state. It does not claim thread safety
for every historical frontend/visualization member or predict future dynamic safety.

Source: global_planner99f3122; smoke parent0e8874f. Protocol601b92b was committed
before new online results: I2_05_ONLINE_ADMISSION_PROTOCOL.json.

## Tests and online result

Targeted catkin builds of dynamic_exploration_node, test_dep_node and
return_home_checks pass (the last consumer build completed during backup recovery
on 2026-10-09). Five snapshot/pose
checks pass, including 20,000 mailbox updates with coherent-pair reads, invalid pose
rejection, fixed scores/start geometry under continuous actual odomCB updates, and
historical live-yaw semantics once the new snapshot is disabled.

Two sequential headless seed1/1 runs use original K6, motion constraints, 50ms
incremental alternative deadline and Unique-shadow with Legacy selection. Each is
bounded at 240 wall seconds after planning begins. No user Goal or rosbag is used.
Both pass the preregistered admission checks; all raw TIMEOUT/FAILED outcomes remain.
The run duration is not a full mission-success or T95 experiment.

| Metric | Generic K-shortest | Geometric diverse |
|---|---:|---:|
| Ready global plans | 15 | 16 |
| Post-35s plans with selected extras | 10 | 7 |
| Max scored-yaw reconstruction error, rad | 2.665e-15 | 1.776e-15 |
| Incremental alternatives p95, ms | 30.300 | 21.506 |
| Incremental alternatives max, ms | 30.804 | 23.263 |
| Total global planning mean, ms | 282.592 | 198.613 |
| Total global planning p95, ms | 371.399 | 260.065 |
| RTF mean | 0.999236 | 0.999212 |
| Historical fallback / adapter errors | 0 / 0 | 0 / 0 |
| Recorded collisions | 0 | 0 |

Raw/simplified geometry and yaw constraints agree with the stored frozen pose;
shadow scoring shares the map version, final validation is logged, all four route
layers/execution linkage and collision/resource/trajectory records are valid.
No rejected unsafe winner was executed in the samples. Original pre-fix logs and
previous offline supply data remain preserved.

The 50ms allowance applies only to incremental route generation/selection/validation;
TOTAL planning includes frontend, snapshot and frozen-A* audit copy, Legacy scoring,
Unique shadow and logging. Total means near200–283ms are material overhead, not a
50ms whole-planner claim. These two runs are admissions, not evidence that diversity
improves observation, distance or T95. No sanitizer pass is claimed for this change.

## Decision and next checkpoint

Offline supply and online budget/consistency gates pass without tuning K6/V1 limits.
Proceed next to preregister the same-commit, same-scoring, four-mode seed1/2/3 paired
pilot (historical Legacy, distance-single infrastructure control, generic K, geometric
diversity), with failures retained. Review audit-only overhead before freezing that
matrix; any logging/feature change must be fixed for every applicable control and
measured rather than hidden. Do not use these short-run times as algorithm wins.

I2-06 decision/held-out prediction-vs-actual ordering still precedes I3. Current batch
ends with verified GitHub/local backup as requested. No ROS/Gazebo instance remains
from the bounded checks. Read CODEX_HANDOFF.md for the first unfinished task.

## Backup recovery on 2026-10-09

Original temporary test/build logs were unavailable. The same-code five pose tests
were rerun successfully on an isolated master and saved durably under the admission
batch backup_recovery_validation_20261009 directory. Original validation hashes
and all simulation outcomes are retained; no simulation was rerun.
