# I2-05 first batch — Candidate supply diagnostic

Date: 2026-10-08. Offline supply gate PASSED. Full I2-05 pilot NOT complete.
Preregistered protocol: ca557e6, I2_05_SUPPLY_PROTOCOL.json. Native diagnostic runner:
global_planner 48d9a12. No online planner/config or frozen I1 results were changed.

## Inputs, implementation and checks

All 24 existing R2 execution-start snapshots were processed. Chronological thirds
contain eight snapshots each; these are stages within one historical run, not
independent seeds/scenes or measured Coverage stages. The historical export stores
undirected PRM pairs. Verified source 60ff159 inserts reciprocal neighbors and prunes
invalid nodes; reciprocal edges are reconstructed, independently collision checked
per direction, with directed synthetic-start connectors (historical 1.5 m limit).

Frozen Goal sets are preserved, not regenerated from new node gains. Terminal yaw
is recomputed on the captured map. Snapshot frames are execution-start states and
may differ from the state when historical goals/paths were planned; results describe
counterfactual supply on these frozen states, not strict historical decision replay.
236 frozen Goal instances include 217 reachable and 19 unreachable, no missing IDs.

Native code calls the tested I2 Dijkstra/Yen, motion/shortcut/dedup/selection components.
K=6 is PRIMARY with unchanged V1 limits. K=12/24 are diagnostics under identical
10k per-Goal / 100k global pop limits; no 50 ms wall deadline offline. Three constraint
cases share each generated pool. Relaxed cases explain bottlenecks and are not a
method selected for deployment. All 72 cases completed once; preselected
execution_000079 exactly repeated after removing elapsed time only.
Map/planner FNV hashes, versions, manifest SHA and output hashes passed. A corrupted
manifest was rejected without modifying original snapshots. 7 search and 10 candidate
regression tests pass. The negative check initially lacked sourced runtime libraries;
it was rerun in the correct ROS/workspace environment and reached integrity rejection.

## Fixed gate result

Preregistered admission: >=6/24 snapshots with a SELECTED extra route under original
K=6 constraints, including >=2 middle and >=2 late snapshots. Observed **17/24**,
with chronological early/middle/late **4/6/7**. It passes without any protocol tuning.

| Pool cap | Original constraints: positive snapshots | Selected extras | Post-only motion: extras | No-motion diagnostic: extras |
|---|---:|---:|---:|---:|
| 6 (primary) | 17/24 | 75 | 90 | 90 |
| 12 (diagnostic) | 19/24 | 95 | 111 | 112 |
| 24 (diagnostic) | 19/24 | 99 | 116 | 117 |

For primary K=6: **1,132 raw routes -> 803 motion-feasible -> 293 post-shortcut
unique -> 292 selected**, comprising 217 references and 75 extras. 510 motion-
feasible routes collapse under geometric shortcut. Raw rejection labels: length104,
time208, yaw279; labels overlap and cannot be summed as independent removals.
78/217 Goal searches hit a pop cutoff; these are truncated pools, not guaranteed
complete K-shortest lists. These diagnostics do not establish online 50 ms feasibility.

Larger pools give diminishing extra supply here. Removing raw constraints permits
15 more selected extras at K=6 but does not increase the 17 positive snapshots.
Original K=6 already supplies choices beyond the early 35-second smoke; there is no
basis to change its limits to chase a favorable result. Geometry selection lists
change in only 2/24 primary snapshots; the logged flag includes order changes, so
it is not evidence of different selected sets or better exploration.

## New online preflight finding

A read-only audit of I2-04 V2 logs found scored yaw inconsistent with the recorded
start yaw for 12/27 candidate records at >1e-3 rad, maximum 0.0183046105 rad.
The discrepancy is well above trigonometric rounding. Source findBestPath still
reads live currYaw_ during candidate scoring; route generation also reads live pose
members repeatedly. New controls require a shared frozen per-plan start pose/yaw.
This is an integration bookkeeping defect, not evidence that the proposed route
method is bad and not a correction/reinterpretation of frozen I1-06 results.
The offline runner already uses a constant recorded start/yaw, so its supply result
is unaffected. Runtime fairness is not fully established until this follow-up is fixed.
Read I2_05_POSE_CONSISTENCY_AUDIT.json and its reproducible audit script.

## Decision and bounded stop

This first batch ends at its preregistered boundary and preserves all results.
Supply is sufficient to continue I2, but it is only a necessary condition. There is
no new evidence of actual observation improvement, lower T95 or paper-level novelty.

Next I2-05 batch: freeze start position/yaw for new controls and verify callback
concurrency, preserve default Legacy and the original evaluator, then test candidate
survival under the unchanged online deadline on a bounded late-phase run/replay.
After those admission checks, preregister the same-commit/same-scoring four-mode
seed-1/2/3 paired matrix. Keep K=6 and V1 limits; K12/24 and relaxed cases remain
explanatory diagnostics. Do not change sensors/dynamics, run I1 again, implement
preservation secretly or launch the full matrix before the preflight defect is fixed.
I2-06 and held-out predicted/actual ordering remain required before I3.
