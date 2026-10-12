# I3-00 same-snapshot actual-route workload and budget audit

Registered before new timings. Source parent4ffa69c / evaluatorGP ece80ea. No kernel
optimization, online control change, new simulation or frozen data replacement.
V1/V2 30 executed-prefix probe failure500ms remains intact.

## Fixed data and candidate order

One existing floorplan1_static seed4/4 run at
EXP-I2-06-HELD-OUT-SEED4-V1/environment_seed_004/planner_seed_004/20261012T140548.
All38 global snapshots ordered by sequence, thirds1–13/14–26/27–38; choose both
endpoints of each third:1,13,14,26,27,38. No timing/gain-based selection.
Evaluate ALL stored shortcut candidates in ascending candidate id. These distance-
single routes are mandatory references, not informative/diverse alternatives.
No synthetic duplicate padding. Candidate counts1/3/5/10/15/30 are diagnostics;
count>Nactual explicitly unavailable, not substituted. Subsets omit Goals and therefore
cannot be used as fair deployment admission. Primary workload is ALL actual references.

Use map from each saved immutable global snapshot (exported AFTER online scoring),
and fixed start position/yaw from matching route_controls.jsonl. Snapshot.vehicle is
live odometry at export, so do NOT silently use it as fixed planning start. Confirm
first waypoint and logged fixed pose / scored motion consistency. Captured map may be
newer than original planning snapshot; report versions, not exact decision replay.
Validate manifest/FNV and record SHA256; never modify these files.

## Sampling and costs

Primary prospective sampler: route_translation_and_stationary_shortest_yaw_v1.
At start/corners/goal, stationary shortest-yaw rotation samples with max0.1rad steps;
straight3D segments follow segment heading with max0.25m steps, exact endpoints.
No ray/sample reduction. Body remains level/yaw-only, identical sensor5m camera model.
Corner rotations are a declared route-evaluation hypothesis, NOT reconstructed actual
B-spline motion. Estimated time uses original speed/angular speed/yaw penalty.
Compare calculated shortcut length/yaw/time to frozen scored metrics.

Translation-only sampling with instantaneous corner yaw is secondary to quantify yaw
cost, not a lower-precision replacement. Full raw paths separately described by length,
sample counts; primary timing uses final shortcut geometry actually scored by baseline.

For each of6 maps: load/check files outside timer; one warmup and3 repeats. Each repeat
creates one in-memory map copy (captured-snapshot preparation surrogate), constructs ONE
camera evaluator, evaluates actual candidates once in independent histories. Report
copy, model construction, per-route evaluation, full references, yaw-free diagnostic,
count-prefix cumulative costs, whole preparation+scoring. JSON disk/parsing excluded;
real mapper capture-lock, graph search, safety validation and optimizer not measured.
No claim full online planner <= this kernel preparation/scoring time.

## Fixed budget policy and admission

Budget500ms for preparation+camera scoring, same as prior batch threshold. Cannot be
increased after measurement. Warmups/repeats are compute repetitions, not new seed runs.
Primary cost admission requires all6 ALL-reference batches:3-repeat max<=500ms and
all finite/valid consistent results. Candidate subset successes do not override failure.

Test a cooperative500ms batch guard on each state: copy/build counted; before each
route pass remaining deadline to evaluateSamples. Timeout invalidates incomplete route
(no partial gain); if ANY mandatory reference unfinished, entire camera decision FALLBACK
(e.g. original Legacy path), never rank a partial Goal set. Valid already-scored results
may be logged but not used to call whole mandatory set complete. Optional routes only
AFTER all references complete, under same shared deadline; absent optional generation
in this dataset, do NOT claim optional-route budget admission. Report overshoot; check
<=25ms on this finite test (not hard real-time guarantee).

End condition: one6-state audit+tests+report. If mandatory cost fails, no cap alone can
solve fixed Goal-set scoring; record NO-GO and recommend a separately registered exact
empty-observation culling / new evaluation-definition decision, not endless optimization
or secretly reducing camera FoV, range, Goal set or route horizon. Do not implement that
optimization in this audit or proceed to guided construction. If cost passes, only
reference scoring admitted; actual extra-route budgets remain I3-01 work. Backup/handoff.
