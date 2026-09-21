# Phase R1 final decision

Date: 2026-09-21

## Decision

**Conditional GO: complete R1 and proceed to R2 shadow-mode predicted-versus-actual
observation validation.** Do not yet switch online route selection to unique gain and
do not begin the full guided-route implementation until the R2 gate is evaluated.

## What R1 established

1. The baseline structurally accumulates path-node gains without cross-node voxel
   deduplication; the issue is not based on an endpoint-only misreading.
2. A versioned immutable map/PRM/candidate snapshot and deterministic visible-Unknown
   set can be exported and replayed without changing online behavior.
3. Raw, unique and marginal path gains satisfy the required set invariants and use
   independent candidate histories.
4. In the formal 0.25 m diagnostic on 25 state-decorrelated snapshots and 152 routes,
   mean candidate duplicate ratio was 52.19%, selected-route duplicate ratio 67.15%,
   full ranking changed 36%, and Top-1 changed 4/25 times (16%).
5. Choosing the raw winner caused 0.86% mean and 7.83% maximum unique-utility regret in
   this pilot. This is enough to keep the evaluator, but not enough to claim exploration
   improvement.
6. The result depends on sampling interval. A 0.25 m interval is retained for formal
   diagnostics; 0.5 m is development-only and 1.0 m is rejected.
7. Offline scoring and exact edge/sample reuse exceed the provisional cache profiling
   gates, but these Python figures do not establish an online C++ bottleneck.

## Hypothesis and kill-criteria decision

| Item | R1 status | Decision |
|---|---|---|
| H1: repetition exists and can alter ranking | Pilot supported | Continue; KC1 not triggered, but repeat across layouts later |
| H2: predicted unique gain improves actual new observation | Not tested | Mandatory R2 gate before online selection claims |
| H3: guided routes beat generic alternatives | Not tested | Implement only after R2 evaluator gate |
| H4: observation-preserving shortcut helps | Not tested | Deferred until informative anchors/routes exist |
| H5: reuse and bottleneck justify cache | Offline proxy gate passed | Retain as conditional engineering work; reprofile final C++ pipeline |

KC1 is not triggered because Top-1 changes exceed the illustrative 5% continuation
threshold and several changes have nontrivial utility margins. This is a continuation
decision, not a statistical claim: all 25 snapshots belong to one trajectory in one
layout. KC2 remains unresolved because no actual-observation correlation was measured.

## Paper positioning after R1

- Unique path gain is the common evaluator and a supporting method component.
- Voxel union, marginal sets and generic multi-path generation are not independent
  primary contributions.
- The intended primary contribution remains baseline-route-conditioned,
  observation-opportunity-guided route generation under equal motion and computation
  budgets.
- Observation-preserving shortcut remains a necessary companion only if guided anchors
  are shown to carry observation value.
- Cache is omitted from contribution claims unless later exact C++ profiling and
  consistency tests support it.

## R2 scope

R2 remains diagnostic/shadow mode and must not change the flown route.

1. Freeze plan/execution intervals: snapshot, selected PRM/shortcut route, generated
   B-spline, odometry/yaw prefix, replan boundary and map versions.
2. Build actual newly observed voxel sets from the existing lightweight observation
   delta stream; exclude artificial takeoff-region clearing.
3. Evaluate the selected route at 0.25 m and separately evaluate the executed prefix,
   preserving the difference between PRM, shortcut, B-spline and odometry.
4. Report predicted set size, actual new set size, overlap/Jaccard, precision/recall,
   calibration error, per-meter/per-second observation, and planning/evaluation time.
5. Repeat over early/middle/late states and at least one held-out layout before making
   a general evaluator claim.

R2 must preserve the frozen world/FoV/dynamics/safety/seed rules, legacy completion
threshold 500, and no-rosbag policy. Use CSV/JSON and retain failures.

## R2 kill gate

Pause route-generation investment if the 0.25 m predicted unique gain does not provide
useful ordering or calibration for actual newly observed voxels on selected execution
prefixes, or if discrepancies are dominated by shortcut/B-spline/replan mismatch that
cannot be modelled reproducibly. Do not add confidence, semantics, energy, loop closure
or unrelated modules to hide a failed evaluator.

If R2 passes, proceed to observation-opportunity-guided candidate generation with
equal-goal/equal-candidate and equal-wall-time comparisons against the single shortest
route, generic/geometric alternatives, and naive marginal-coverage insertion.

## Engineering state

- branch: `feat/r1-observation-diagnostics`;
- R1 final pre-decision commit: `d6edfb7`;
- 55 exploration benchmark tests passed at R1-06;
- benchmark baseline, online scoring and completion behavior remain unchanged;
- R1 data and complete Git history are backed up by stage under
  `/home/zxr2/下载/CERLAB_R1_Backups/`.

R1 is now closed. Further work starts at R2-01 and requires explicit authorization.
