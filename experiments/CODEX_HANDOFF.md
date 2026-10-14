# CERLAB UAV autonomy — Codex handoff

Last updated: 2026-10-14. I3-03-01 (old G1-D0) COMPLETE: NO_USEFUL_CONDITIONING_SIGNAL. Counting correctness and <=50ms/256MiB preparation pass; K1 usefulness fails (zero wins; state26 positive delayed4→5). Report/local backup then stop. Next is a user-triggered research-scope decision; no P1/E2/core coding or GitHub push.

The historical executable prompt is `experiments/i3/I3_02A_START_PROMPT.md`; it has now been completed. Do not rerun it.

This is the canonical single-file handoff for a new Codex conversation. Read this
file first, then read the linked phase documents before changing code. Treat recorded
results as evidence with stated limits, not as guaranteed performance or novelty.

## User objective

Develop a simulation-first graduate-paper project on top of CERLAB-UAV-Autonomy for
an ordinary SCI/EI journal. The intended paper studies observation-opportunity-guided
route generation in the existing HIRE-style incremental PRM system. It is not trying
to claim that voxel union, ordinary K-shortest paths, a waypoint insertion or a cache
is independently new.

The current research structure is:

1. path-history-aware unique observation gain as the shared evaluator;
2. observation-opportunity-guided, budgeted alternative-route generation as the
   intended primary contribution;
3. observation-value-preserving shortcut as a supporting component if its need is
   experimentally demonstrated;
4. dependency-aware Edge evaluation only if final C++ profiling proves a bottleneck.

For a three-point SCI/EI paper presentation, see
`experiments/PAPER_CONTRIBUTIONS_DRAFT.md`: path-history observation evaluation,
observation-opportunity-guided route generation, and observation-value-preserving
simplification. The route generation is the intended main contribution; the other two
are tightly connected supporting method components. Their final claim strength
depends on the pending experiments.

Occupancy confidence, semantics, energy, dynamic prediction and loop closure are out
of the current scope. Do not add them to hide a failed hypothesis.

## Environment and project

```text
OS: Ubuntu 20.04
ROS: Noetic
Workspace: /home/zxr2/cerlab_benchmark_ws
Project: /home/zxr2/cerlab_benchmark_ws/src/CERLAB-UAV-Autonomy
Primary simulation world: floorplan2_dynamic_5.world
Research mode: simulation only
Rosbag: disabled; use CSV/JSON logs
```

Do not upgrade Ubuntu or ROS, reclone the project, replace the workspace, overwrite
personal files, configure PX4/QGroundControl, unlock a vehicle or run real flight.
Real hardware planning is deferred.

At this checkpoint no ROS, Gazebo, RViz or exploration instance is running.

## Git state at handoff

Backup policy updated by user (2026-10-13): ordinary “备份” requests mean LOCAL backup only. Push to GitHub after completing a major task such as I3-02, or when the user explicitly requests a push. Prior general push authorization does not mean every checkpoint should be pushed.

The user has authorized GitHub pushes. Local commits alone do not prove remote sync;
consult the latest backup README/remote receipt. A previous push was not executed
because automatic approval review hit a usage limit; report actual status explicitly.

```text
parent branch: feat/i3-camera-evaluator
I2-04 smoke source commit: e97291d431dba1344b4edcd59f9d4a1ff37520c5
I2-05 runner checkpoint: a8967e0
final documentation checkpoint: inspect git HEAD / local backup README
frozen I1 branch: feat/i1-unique-gain
frozen I1 commit: 10e9c3589e2f5895d53e354547a03bf8f6f238a2

global_planner:
  branch feat/i3-camera-evaluator
  commit 6ef0fa9 (isolated I3-03-01 bound diagnostic; online library unchanged)
autonomous_flight:
  branch feat/i2-route-logging
  commit 33422e2d5ff2c8e405013df5abb72f388351eb00
map_manager:
  branch feat/r2-execution-logging
  commit f6d2e925b47916a5cb3b72e011af6f3a17dbdd26
uav_simulator:
  branch feat/benchmark-v2
  commit cc8c8a6dce0214d9ba99a3189272f05dc8807d24
```

Before work, read any applicable `AGENTS.md`, run `git status` in the parent and
changed submodules, inspect running processes, and preserve user changes. Do not use
broad `pkill`; stop only process groups created for this project.

## Current operational baseline

The current baseline is not original endpoint-only DEP. Its class is named DEP but it
contains HIRE-style Frontier-guided sampling. Source review established:

- `calculateUnknown()` computes node/yaw unknown-voxel gains with a 2 m planner proxy;
- `findBestPath()` already recomputes and sums intermediate path-node gains;
- path nodes are summed without cross-node voxel-address deduplication;
- goals are prefiltered mainly by node gain;
- each goal normally receives one geometric-distance A* route;
- `shortcutPath()` is collision/geometric only and does not protect observation value;
- the PRM route can differ from shortcut, B-spline and executed odometry;
- history-dependent marginal gain must not be inserted as an ordinary additive
  negative A* edge cost.

The project already includes return-home behavior. Its operational near-completion
gate is `completion_gain_threshold=500`; this is a legacy reachable-gain threshold,
not 95% Coverage. Keep that gate on legacy gain during Innovation 1 so ranking and
stopping effects remain isolated.

## Benchmark v2: complete and frozen

The ten-seed HIRE-style baseline uses environment/planner seed pairs 1/1 through
10/10, fixed world, sensor, dynamics, start, Coverage denominator and stop rules.
All ten primary runs completed and returned home with zero recorded collisions.

Downstream reference aggregate:

```text
T80: 229.47 ± 25.74 s
T90: 282.96 ± 21.39 s
T95: 375.50 ± 34.19 s (documented seed 3/9/10 T95 repeat policy)
Exploration completion: 437.94 ± 48.54 s
Exploration distance: 181.41 ± 21.72 m
Final mission distance: 191.91 ± 23.07 m
Final accessible-free Coverage: 0.95757 ± 0.00414
Static-surface Coverage: 0.63578 ± 0.00842
Mean global-planning time across run means: 45.00 ms
Exploration CPU: 144.63 ± 1.02% of one logical core
Exploration RSS: 457.61 ± 6.25 MiB
Mean real-time factor: 0.99916
```

Authoritative files:

- `experiments/benchmark_v2/METRICS_SPEC.md`
- `experiments/benchmark_v2/FINAL_BASELINE_10SEED_2026-09-17.md`
- `experiments/benchmark_v2/STATUS.md`

Never change FoV, velocity, acceleration, start, safety distance, map resolution,
Coverage definition, completion condition or seed set to make a new method look good.
Record simulation time, wall time and planner time separately. Retain failures and
censored thresholds.

## Phase R1: complete

R1 implemented immutable map/planner snapshots and offline raw/unique/marginal path
diagnostics without changing online selection.

Formal 0.25 m results from 25 state-decorrelated snapshots and 152 routes:

```text
mean candidate duplicate ratio: 52.19%
mean selected-route duplicate ratio: 67.15%
full-order change rate: 36%
Top-1 change rate: 16%
raw-choice unique relative regret: mean 0.86%, maximum 7.83%
```

H1 is supported as a one-scene pilot. This proves the structural problem can affect
ranking; it does not prove exploration improvement or novelty of voxel union.

Read:

- `experiments/r1/R1_FINAL_DECISION.md`
- `experiments/r1/R1_FINAL_SUMMARY.json`

## Phase R2: complete

R2 added stable global/trajectory/execution IDs, lightweight actual first-observation
voxel deltas, execution-start map snapshots, four predicted layers and alignment
metrics. Artificial `setFree`/takeoff clearing is excluded from actual observations.

The legacy 2 m planner proxy had poor exact agreement with the physical 5 m pinhole
depth camera. An offline mapper-matched frozen-map shadow evaluator was therefore
added. It matches intrinsics, extrinsics, image geometry, range and voxel traversal,
but cannot know where still-Unknown physical obstacles terminate future rays.

R2-06 controlled smoke, same odometry samples:

```text
legacy Jaccard 0.040, count Spearman 0.662
sensor-shadow Jaccard 0.714, count Spearman 0.965
```

R2-06 full seed-1 run:

```text
HOME_REACHED, no collision
final Coverage 96.260%
T80/T90/T95 223.926 / 354.530 / 488.120 s
exploration distance 232.165 m
24 execution intervals preselected; 19 comparable; 5 empty exclusions
overall shadow Jaccard 0.531 vs legacy 0.087
overall count Spearman 0.812 vs legacy 0.077
late shadow Precision 0.186 and Recall 0.991
```

The late-stage result is an explicit limitation: the shadow set becomes an optimistic
superset when unknown geometry controls real occlusion. H2 is conditionally supported
in early/middle exploration and is not fully proven.

Authoritative files:

- `experiments/r2/R2_FINAL_DECISION.md`
- `experiments/r2/R2_FINAL_SUMMARY.json`
- `experiments/r2/R2_06_VALIDATION.md`
- `experiments/r2/R2_06_FORMAL.json`

The R2 final decision is a conditional Go to Innovation 1. It does not authorize a
paper performance claim or immediate guided-route implementation.

## Retained data and backups

```text
Innovation-1 reference fixture:
/home/zxr2/cerlab_benchmark_ws/results/R2_FINAL_REFERENCE_20260922

R2 final archive and complete Git bundles:
/home/zxr2/下载/CERLAB_R2_Final_2026-09-22

Full R2 formal run retained for possible reanalysis:
/home/zxr2/cerlab_benchmark_ws/results/EXP-R2-06-SENSOR-SHADOW-SEED1-V1

R2 historical checkpoint backups retained:
/home/zxr2/下载/CERLAB_R2_Backups
```

The reference fixture contains 24 selected execution snapshots plus trajectory,
interval, actual-observation and shadow files. Do not delete the full run or historical
backups unless the user explicitly revisits data cleanup.

## Innovation 1 progress

I1-01 is complete. It added a versioned path-gain contract with `legacy`,
`unique_shadow` and `unique_online` names, 0.25 m sampling, schema-4 planning fields,
CSV columns and snapshot provenance. Default selection remains Legacy. Both unique
modes fail closed because the evaluator is not implemented yet. Compile, three new C++
tests, 85 Python tests, all return-home checks and a seed-1 small-ROI smoke passed.

Read `experiments/i1/I1_01_VALIDATION.md` and `experiments/i1/STATUS.md`.

I1-02 is complete. It added the immutable-snapshot C++ visible-set/path evaluator,
0.25 m polyline sampling, raw/unique/marginal metrics, independent candidate histories,
snapshot-version provenance and candidate metrics in diagnostic snapshots. Six C++
tests, 85 Python tests and all return-home checks pass. `unique_shadow` can now compute
counterfactual rankings; it still cannot control flight. `unique_online` remains
fail-closed.

Read `experiments/i1/I1_02_VALIDATION.md`.

I1-03 is complete. Across all 24 retained frozen snapshots, all 217 candidates and
13,131 path samples exactly match the Python reference for raw gain, unique gain,
per-sample marginals and final stable voxel-address sets. Weighted duplication is
65.252%. Nine C++ tests and 85 Python tests pass. The first sampled comparison exposed
only a null-versus-empty-array fixture serialization issue, which was fixed and
documented.

Read `experiments/i1/I1_03_VALIDATION.md` and
`experiments/i1/I1_03_CPP_PYTHON_AGREEMENT.json`.

I1-04 is complete. The full seed-1 shadow run reached home without collision; all
31 Unique evaluations were valid and counterfactual Top-1 changed 16/31 times. Change
rates persisted below 80%, from 80–95%, and above 95% Coverage. Unique evaluation
mean/p95/max was 47.57/101.90/112.22 ms. Global planning mean/p95 was 96.41/177.85 ms,
while RTF remained 0.99918. These costs must remain in later comparisons.

Read `experiments/i1/I1_04_VALIDATION.md` and
`experiments/i1/I1_04_SHADOW_SUMMARY.json`.

I1-05 is complete. A clean seed-1 small-ROI smoke used Unique selection on 10/10
global plans, changed the Legacy Top-1 twice, reached home without collision and kept
the completion gate on Legacy gain. All evaluations were valid, no normal fallback
occurred, Unique evaluation mean/p95 was 19.46/25.19 ms and RTF was 0.99928. Ten C++
selection/evaluator tests, 85 Python tests and all return-home checks pass.

Read `experiments/i1/I1_05_VALIDATION.md` and
`experiments/i1/I1_05_ONLINE_SMOKE.json`.

## I1 final result and immediate next task

I1-01 through I1-06 are complete. The paired matrix is
`experiments/i1/I1_06_MATRIX.json`; raw results and `batch_state.json` remain under
`/home/zxr2/cerlab_benchmark_ws/results/EXP-I1-06-PAIRED-PILOT-V1`.
All six primary runs used clean commit `10e9c35`, the same submodules, configuration,
Coverage denominator and seed pairs 1/1–3/3. All reached home with zero collision and
valid measurements. The primary policy chooses the first actually verified completed
attempt, even if its matrix wrapper was interrupted; later valid repeats remain
sensitivity data. In seed 2, this means Legacy attempt 1 is primary and attempt 4 is
an additional valid repeat. Failed attempts remain preserved.

Unique-online T95 differences versus Legacy were -124.07, +48.56 and +50.14 s in
seeds 1–3. Exploration distance increased by 9.67, 8.16 and 54.21 m. Actual task
sensor-new voxels per executed metre decreased in all three seeds by 170, 266 and
1100 voxels/m. Mean global planning cost increased in all three by 44.53, 49.63 and
31.33 ms. The mean T95 difference (-8.46 s) is dominated by seed 1; the median is
+48.56 s. These are three paired pilot runs in one scene, not a general statistical
claim.

**Final I1 decision:** do not enable Unique-online ranking as the default and do not
claim it independently improves exploration. The I1-KC5 downgrade criterion is met.
Keep the tested evaluator and explicit Unique flag for diagnostics/ablation; Legacy
remains the operational default and completion still uses Legacy gain 500. Read
`experiments/i1/I1_FINAL_DECISION.md`, `I1_FINAL_SUMMARY.json`, and
`I1_06_PILOT_SUMMARY.json` for exact evidence and limitations.

The current checkout may be `docs/i1-06-progress` to preserve the report. The frozen
experiment branch is `feat/i1-unique-gain` at `10e9c35`; preserve it and all raw runs.
No I1 seed remains pending.

At I1 close, I2 preparation was defined as establishing single-route, K-shortest and
geometric-diversity controls with a fixed Goal set, candidate cap, motion budget and
computation budget. Before implementing the proposed observation-guided routes in I3,
the plan also required tracing changed I1 selections through execution and checking
whether the 2 m planner Unique ranking predicts actual new observation on a held-out scene.
If that observation-model gate fails, correct the evaluator definition first. Do not
add cache, confidence or unrelated modules to hide the I1 result.

I2-00 has now closed the read-only I1 mismatch diagnosis. Across the three Unique
runs, 51 global plans changed Top-1; 50 linked to local execution but only 32 had at
least 0.5 m associated odometry. In seed 2, 222 near-identical plans occurred over
44.744 s at one goal while the UAV moved only 0.012 m net; 220 adjacent log entries
identified an unsafe local goal before replanning. The existing R2 matched-prefix
comparison showed the 2 m planner proxy agrees much less with actual sensor
observations than the 5 m mapper shadow, while frozen Unknown occlusion remains a
limitation. I1-03 still has exact 24-snapshot/217-candidate C++/Python agreement; no
reproducible evaluator implementation defect was found. No I1 data, conclusion or
algorithm code was changed. Read `experiments/i2/I2_00_DIAGNOSTIC_REPORT.md` and the
frozen protocol/JSON there.

I2-01 protocol is complete, NOT implemented: read
`experiments/i2/I2_01_GENERIC_ROUTE_PROTOCOL.md` and `I2_01_PROTOCOL.json`.
Historical Legacy stays default. New controls isolate deterministic single-distance,
Yen K-shortest and geometric diversity with identical multi-route pool/budgets;
Unique is shadow-only initially. Mandatory reference routes, post-shortcut collapse,
actual candidate deficits and compute costs must be reported. Source heap mutability
is a risk, not a demonstrated historical failure; common snapshot scoring is an
implementation prerequisite, not an existing feature.

I2-02 implements the isolated ROS-independent `routeSearch.h` solver in
`global_planner`, with deterministic Dijkstra and Yen, immutable directed graph,
loopless deduplication, reference/alternative pop counts and cooperative cutoff.
Six tests include a 300-graph exhaustive oracle and complete six-vertex fixtures.
Read `experiments/i2/I2_02_ROUTE_SEARCH_REPORT.md` and validation JSON. No online
integration or performance claim; historical search/default/config and I1 stay fixed.

I2-03 adds `routeCandidates.h`: common pool preparation, raw/simplified motion
limits, original-order geometric shortcut with snapshot callback, duplicate/rejection
counts, generic shortest and within-Goal directed-edge Jaccard diversity selection.
Mandatory references first, stable ties/round-robin/caps and cooperative cutoffs are
covered by nine tests. See `experiments/i2/I2_03_CANDIDATE_CONTROLS_REPORT.md` and
validation JSON. Selected counts are not actual scored counts; no online integration,
B-spline validation or observation benefit has been demonstrated.

I2-04 is complete: route modes are integrated behind historical_legacy default,
with common snapshot Legacy/Unique-shadow scoring, frozen original-A* comparison,
fresh-snapshot final safety check and route_controls.jsonl execution provenance.
The planner uses a worker thread: V1 found a live-map consistency defect, fixed in
c17fa0e. Keep V1 and V2 logs, not only the final pass. 3 snapshot + 7 search + 10
candidate C++ tests and 7 Python linkage tests pass. V2 four 35-second smoke runs
pass bounded checks, but remain TIMEOUT/FAILED in raw manifests (not full mission
success). Read I2_04_INTEGRATION_REPORT.md, I2_04_VALIDATION.json and smoke summary.

I2-05 first batch is complete (NOT the whole pilot). Preregistered ca557e6,
all 24 R2 execution-start snapshots x K6/12/24 =72 cases plus one fixed repeat.
Original K6 limits pass supply admission: 17/24 snapshots (early/middle/late 4/6/7),
1132 raw ->803 motion-feasible ->293 distinct ->292 selected, including 75 extras.
No live configuration, I1 data or V1 limits changed. Read I2_05_SUPPLY_REPORT.md,
protocol, validation and summary JSON. K12/24/relaxed constraints are diagnostics,
not deployed improvements; offline operation caps do not prove online feasibility.

A read-only I2-04 V2 audit found 12/27 scored-yaw mismatches with stored start yaw,
maximum 0.0183 rad. The initial integration read live currYaw_ and pose members
while mapping/odometry callbacks ran. Offline supply used fixed pose and was unaffected.
This new-control defect is now resolved by the following pose fix; I1 data stay frozen.

I2-05 pose fix and online admission now pass. global_planner99f3122 adds a
mutex-protected odometry mailbox and one worker-owned start pose/yaw per plan.
New graph connectors, constraints and all candidate scores share it; historical
Legacy behavior remains. Five tests pass, including continuous odom updates during
fixed scoring. Two bounded240s seed1/1 runs with original K6/50ms limits pass.
Generic/diverse: 15/16 ready plans, 10/7 post35s plans with selected extras,
maximum yaw errors2.7e-15/1.8e-15rad, alternative max30.8/23.3ms, no recorded
collisions or fallbacks. Total planning means282.6/198.6ms, NOT 50ms. Read
I2_05_ONLINE_ADMISSION_REPORT.md, protocol, validation and summary. Raw runs remain
TIMEOUT/FAILED, not a full pilot or performance win. All previous data stay retained.

**Frozen I2-05 checkpoint: collected12/12 first attempts; all backed up.**
All per-run full archives/COMPLETE hashes verified; controller statusall_trials_backed_up.
No simulation/ROS master remains. Collection source0677947 stayed clean/frozen,
with global_planner99f3122/autonomous_flight33422e2. Source checkout may now advance
for final documentation; raw manifests always retain collection version0677947.

Read I2_05_PAIRED_REPORT.md, I2_05_PAIRED_SUMMARY.json and validation.
Statuses in seed order1/2/3:
- historical: SUCCESS/SUCCESS/SUCCESS; T95385.174/408.791/416.489s.
- single distance: USER_ABORT/SUCCESS/SUCCESS; T95censored/500.931/457.146s.
- generic K: SUCCESS/SUCCESS/TIMEOUT; T95511.322/423.078/censored.
- geometric: SUCCESS/TIMEOUT/SUCCESS; T95416.649/496.147/395.983s.
Seed1 single was user-stopped after B-spline infeasibility; keepUSER_ABORT.
Seed3 generic stayed at94.25% with repeated B-spline failure until900s; no retry.
Seed2 geometry reached home near deadline but failed runner dwell; keep rawTIMEOUT
and actualHOME event separately. Do not replace/exclude these first attempts.

N3 pilot: LegacyT95 mean403.485s/std16.318s; geometry436.260s/std52.884s.
Geometry has greater exploration distance in all3 seeds; ordinary multi-route controls
have no stable overall advantage here. This is NOT the proposed observation-guided
method; no main novelty/performance verdict or significance claim follows.
Supplemental sensor-only rates until stop include stalled time; read with success.

**Historical checkpoint (2026-10-10): I2-06 first-item contract/execution audit complete.**
Read `i2/I2_06_CONTRACT_EXECUTION_REPORT.md`, `I2_06_EXECUTION_AUDIT.json`,
`I2_06_VALIDATION.json` and the bounded protocol before resuming.

Confirmed an integration contract regression: detached new-control nodes discarded
scored-node gain feedback to live PRM. Fixed in global_planner3267e3d, separate branch.
Frozen counterexample RED: Legacy refreshes target999999→89; pre-fix adapter leaves999999.
GREEN:24 C++ tests pass (snapshot7/search7/candidates10); dependent flight targets build.
Scored intermediate/goal gains alone now sync; unscored nodes and A* state preserved.
Historical default unchanged. Post-fix online behavior/performance NOT tested.

Read-only12-trial audit: persistent terminal failures only in seed1 single2315calls/
470.339s and seed3 generic1963calls/435.483s; same input target each time, <.12m movement,
zero new accessible observations, depth/map still advancing. Generic optimizer message
is not direct proof of LBFGS nonconvergence. Failure-time occupancy/control points and
solver return status are unavailable; bounded execution diagnosis ends here.
Cannot attribute aggregate performance loss or stalls solely to missing feedback.
Keep I2-05 observed values/conclusions, but label all new-control V1 data PRE-FIX and
not clean isolation of route-generation effects. No replacement/retry for positives.

**I2 checkpoint: I2-00 through I2-06 COMPLETE (2026-10-12), conditional development decision.**
Read `i2/I2_FINAL_DECISION.md`, `I2_06_HELD_OUT_PROTOCOL.md/json`,
`I2_06_HELD_OUT_RESULTS.json`, `I2_06_POST_FIX_INTEGRATION.json` and validation.

Protocol committed BEFORE collection28d170f. One floorplan1_static seed4/4 headless
480wall-second trial, distance_single/Legacy selection/unique_shadow, repairedGP3267e3d.
RawTIMEOUT/FAILED retained, not complete-mission success; no new Coverage denominator
so NO Coverage/T80/T90/T95. No favorable retry.69 eligible execution intervals,12 IDs
preselected by order thirds (4each), all valid, two empty actual sets retained.

Legacy2m: per-metre Spearman0.435831, within-third concordance0.638889/18pairs,
medianJaccard0.111103 => FAIL complete gate (only overlap fails).
Mapper-matched5m: Spearman0.859649, concordance0.722222/18pairs,
medianJaccard0.841764 => PASS preregistered practical gate.
Single dependent static-scene run does not prove candidate counterfactual ranking,
exploration improvement or multi-seed significance. Early shadow n4 ranks weak:
Spearman0.20/concordance0.50; do not claim each stage is reliable. R2 unknown-occlusion
and level-body yaw limitations remain. Empty/empty Jaccard=1 retained; nonempty n10
shadow median0.818028/Legacy0.055410 are descriptive sensitivity, not gate replacement.

Online integration:38ready global plans with corrected feedback-policy logs,73/73local
success, no collision/adapter error, pose error3.55e-15rad, RTF0.998991. Mission distance
203.755m; diagnostic snapshots enabled, planning mean229.772ms includes diagnostic
costs; no repaired-vs-old causal performance comparison.1672014first-sensor addresses
integrityvalid, artificial clear excluded.47logged-ID/timestamp association mismatches
reported and canonical timestamp attribution used, not falsely claimed absent.

**Task defined at I2 close: I3-00 sensor-matched C++ evaluator (now V1 implemented below).**
Freeze a versioned contract matching existing5m mapper-shadow geometry; preserve old
Legacy/I1 proxy modes and physical settings. Cross-check frozen12 snapshots/prefixes
for exact addresses/raw/unique/marginal against Python and profile cost. Gate before
observation-guided route construction. Do not implement guided routes first with
unvalidated2m utility or silently replace old evaluator semantics/default.
After parity/cost admission, define guided-anchor/budget method and its execution /
observation-preserving-shortcut tests. Corrected paired comparison cohorts require
NEW registration; old12 pre-fix trials remain historical evidence, not cleanH3 controls.
No unrelated confidence/semantic/energy/loop-closure modules to hide failed hypotheses.

New raw/analysis: /home/zxr2/cerlab_benchmark_ws/results/EXP-I2-06-HELD-OUT-SEED4-V1/.
New backup: /home/zxr2/下载/CERLAB_I2_Backups/I2_06_HELD_OUT_2026-10-12/ (registration,
collection full verified raw archive, final report/Git/analysis checkpoint).
Earlier audit: /home/zxr2/cerlab_benchmark_ws/results/EXP-I2-06-AUDIT-V1/;
earlier backup I2_06_FIRST_ITEM_2026-10-10 retained. No simulation remains.
At I2-06 close no I3 algorithm code had started.

Future user preference: AFTER observation-opportunity guidance is implemented, run
NEW cohorts in isolated parallel ROS/Gazebo instances. Register uniform concurrency,
calibrate CPU/GPU/RTF and controls' load; do not mix current serial results with them.

Raw batch: /home/zxr2/cerlab_benchmark_ws/results/EXP-I2-05-PAIRED-PILOT-V1/.
Per-trial backups: /home/zxr2/下载/CERLAB_I2_Backups/I2_05_PAIRED_RUNS_2026-10-10/.
Full matrix checkpoint: /home/zxr2/下载/CERLAB_I2_Backups/I2_05_PAIRED_FINAL_2026-10-10/.

Local backup: `/home/zxr2/下载/CERLAB_I2_Backups/I2_05_ONLINE_2026-10-08/`
(completed on 2026-10-09 after the previous quota-related push interruption).

Final paper-scale ten-seed and multi-scene ablation is deferred until the full
proposed method is ready. The current three-part paper framing is in
`experiments/PAPER_CONTRIBUTIONS_DRAFT.md`; its second and third points remain
unimplemented hypotheses.

## Current I3 checkpoint and immediate next task

I3-00 V1 isolated camera evaluator implemented on feature branch4f135f2. Read
`i3/I3_00_PROTOCOL.md`, `I3_00_REPORT.md`, validation, parity summary and batch cost.
15 C++ tests pass (5camera+10old evaluator), all12 I2-06 snapshots /239poses exact
per-pose addresses/raw/unique/marginal/union, including prior saved shadow unions.
No online/default/sensor/stop changes. New evaluator accepts fixed samples; route
sampling/integration and guided method remain pending.

One warmup+3 repeats: prefixp95=80.241ms,max81.281ms passes per-prefix budget.
Actual fixed30-candidate workload1178.820ms FAILS registered500ms batch budget.
Online cost admission NOT passed. Preserve failedV1 evidence; no threshold relaxation.
V1 backup complete and GitHub pushed; V1 failure retained. User requested continued
bounded performance protocol edc70d6, now completed (max2 interventions, no third).
Profile endpoint479.436ms /traversal592.887ms; intervention1 batch1042.562ms;
intervention2 compact frozen optical view/incremental addresses batch872.728ms.
Final15tests pass and all12/239 sets/raw/unique/marginal/saved unions exact.
Finalprefixp95=60.432ms,max65.747ms. Fixed30 probe still FAIL500ms; no admission.
Read `i3/I3_00_PERFORMANCE_REPORT.md`, protocol and results. No online or guided
method changes. Peak611.69MiB includes12full snapshots, not per-map online overhead.

The next same-snapshot workload/budget audit is now COMPLETE (protocolca76b50).
Read `i3/I3_00_SAME_SNAPSHOT_REPORT.md`, protocol/JSON/results/validation and
`I3_BUDGET_POLICY_DRAFT.md`.6 states1/13/14/26/27/38 of existing held-out run; all51
stored distance-reference routes,7862prospective poses. No kernel optimization.
Fixed planning pose/yaw from route_controls; map is later export snapshot, not exact
original-time replay. Explicit0.25m translation /0.1rad stationary shortest-yaw
sampling is a PROSPECTIVE hypothesis, not actual B-spline reconstruction.

All-reference prep+scoring maxima196/1676/1767/2788/3425/1871ms. Only state1passes500.
Camera prep about37ms; most cost full long routes, not short executed prefixes.
Candidate counts15/30 unavailable (no duplicate padding); lower-count prefixes omit
Goals and are ONLY diagnostics. Even translation-only secondary is1.04–2.41s in
non-start states, not an excuse to drop yaw samples. No all-Goal budget admission.
500ms cooperative guard rejected all incomplete Goal sets, maxovershoot0.218ms;
4sampler and2extreme-budget integration tests passed. Test tool only, not online.

Snapshot13 selected_candidate=-1 while eventproposal8 because final new-map safety
validation rejected/cleared bestPath. Confirmed SOURCE behavior, NOT exporter bug.
Retain rejected state in registered audit; distinguish proposal vs accepted/executed.
Optional posthoc selected-Legacy-proposal cost surrogates75–280ms include preparation,
not actual single-goal trials/admission. Exact duplicated pose fraction3–69% is only
reuse potential, not cache speedup or contribution. Do not conflate marginal0 with
empty visible set.

**I3-01A COMPLETE: explicit two-stage scope adopted for minimal offline probe only.**
Read `i3/I3_01A_SCOPE_REVIEW.md`, CONTRACT.json, SOURCE_AUDIT.md and VALIDATION.json.
CommonA is repaired distance_single generator + Legacy2m node/path gain/time scoring,
NOT historical_legacy A* equivalence. Keep historical system baseline separate.
A keeps originalprefilter/gain feedback/completion500; B only after existing completion
logic says continueEXPLORING. No new live mode/algorithm has been implemented.

B refines only one common safely selected Goal/terminalyaw, tau0 mandatory. First
registered target2final candidates (reference+1real distinct alternative), rawpool6,
old1.25motion ratios/+pi/2yaw, independent histories, camera5m exact model and full
0.25m/0.1rad prospective sampling. This is an explicitly narrower goal-comparison
scope, not passing old all-Goal budget or solving endpoint prefilter exclusions.
SharedB500ms includes preparation/reference/anchor queries/generation/shortcut/sampling/
scoring/finalvalidation/cleanup; gen50ms nested, scoringcutoff475ms, finalreserve25ms.
StageA/localoptimizer separate; no whole-planner500ms claim. Tight proposed pose drift
limits. Every incomplete2route attempt fallback; no padding or omitted failure denominator.
Equal caps != equal completed count: strictH3 requires matched actual2candidate cases.
Same simplifier required across generators; later preservation ablations must be common.

**Historical registration for I3-01B (now completed; see current checkpoint below).**
Read `I3_01B_MINIMAL_PROTOCOL.md/json`; use6 unchanged cases1/13/14/26/27/38;13is
mandatory skip-negative (proposal8 rejected), remaining5 require exported-map/raw/graph
revalidation. Reuse recordedA goal/pose, not rerun/camera-select a new Goal; map epoch
is later export, not original decision replay. Isolated fixture tests only.
Reference-only / generic /diverse controls, operation-limited supply diagnostic then
actual inclusive500ms/nested50ms trials, warmup+3repeats, predeterminedorder. No guided
or new core optimization/simulation. Require>=3valid refs spanning3strata and>=3paired
actual2candidate states with middle+late represented; missing supply INCONCLUSIVE,
adequate supply but costsafety failure NO-GO. One batch; no favorable case/seed replacement.
Report and backup before any I3-02. Opportunities still need own later cost/H3 validation.
No new novelty/performance rating from current protocol. 500ms is registered engineering
budget, not universal hard UAV standard; any future change needs independent rationale.
I3-01A standalone archive was deferred by user; its documents/commits are included
in the I3-01B checkpoint. Do not claim the separate I3_01A directory exists.

**Historical checkpoint: I3-01B COMPLETE, NOT admitted.**
Read I3_01B_REPORT.md, RESULTS.json, VALIDATION.json and unchanged registered protocol.
One6-state batch, sourceparent74cd188 /GP86ee511,6 C++ tests pass. Five valid references
all finish within500ms; negative13never entersB or submits a path. Multi-route:
1/14/26/38 have no distinct feasible alternative;27has one but its evaluation fails
475ms scoring cutoff (total~478ms, correct fallback). Zero paired states complete2
candidates under all repetitions. Overall INCONCLUSIVE_SUPPLY plus real cost failure
at27; neither passes dual-route admission nor disproves research novelty/H3.
28raw ->15motion-feasible ->6distinct including5references:10feasible extras,9geometric
collapses,1distinct extra.13raw candidates fail motion constraints; reason tags overlap.
State27operation cap10000produces4raw, not6, not proof no other routes exist.
Completed scores match full same-model oracle; timed tests do not reuse oracle scores.
No simulation or camera-kernel/default/online changes. Do not repeat/fill candidates.

**Current checkpoint: I3-01C COMPLETE, NO DIRECT RAW-RETENTION ADMISSION.**
Read experiments/i3/I3_01C_REPORT.md, RESULTS.json and VALIDATION.json.
Preregistered197e24c; batch toolingb4045ee / fixture155d65b; camera kernel unchanged.
All15fixed-pool paths evaluated,60outputs including yaw-sampling sensitivity.
All10extras lose material predicted visibility after shortcut (9.17–33.31%,
median17.10%), but all10raw-as-final routes violate time/yaw limits and all primary
raw utilities are lower than final reference. Direct-retention leads0; required2
states, actual0. Secondary sampling still has0leads; one utility classification
is yaw-sensitive. No actual-flight benefit or online500ms admission established.
4accounting tests and reference/fixture/source-hash checks pass. Frozen I1/I2/B
results remain unchanged. No new simulation, evaluator kernel or default changes.

**Historical checkpoint: I3-02A COMPLETE, PROXY_NOT_SUPPORTED.**
Read experiments/i3/I3_02A_REPORT.md, RESULTS.json and VALIDATION.json. Protocol was
registered at b641c96; isolated implementation parent6e2ef68 / global_plannercde9ed0.
The fixed batch scanned3498/3498 edge-node pairs and formed14 small-pool routes across
five valid states;13 remained a zero-call negative control. Reference camera outputs
exactly match I3-01C in all five states. Eight new C++, six existing two-stage and
15 related Python tests pass. Online dep.cpp and camera kernel are unchanged.

Oracle supply has useful routes at26 and38, but Residual-cost selects a useful route
only at38 (required>=2). At26 it misses route636, whose complete predicted rate is
+6.48%; its single-anchor proxy sees only12 new voxels. Residual-cost equals Geometry
at every nonempty state. Naive marginal selects worse routes. Formal result is
PROXY_NOT_SUPPORTED and method-difference evidence is also absent. No I3-02B timing
protocol, I3-03, online simulation, performance or novelty admission follows.

**Current checkpoint: I3-02R COMPLETE, SEGMENT SIGNAL ONLY.**
Read I3_02R_PROTOCOL.md, REPORT.md, RESULTS.json and VALIDATION.json. Registered433a2c9,
implemented2a4b369. Read-only analysis uses the same14 saved I3-02A candidates with
zero camera evaluations/new candidates/simulation and leaves PROXY_NOT_SUPPORTED intact.
Changed-window segment score matches full-oracle candidate/reference choices5/5;
Spearman/sign agreement are1.0. It selects636 at26 (+6.48%) and197 at38 (+0.58%).
For these useful routes95.25%/97.31% of added voxels are within5m of the inserted
corridor, while only41.84%/56.05% are within5m of the anchor.

This is post-hoc mechanism evidence, not a deployable selector: it consumes saved
full-route path-history marginals, and the changed window spans25.1--97.3% of poses
(median76.1%). It neither solves the500ms failure nor supplies an observation-driven
generator. Do not rebrand it as an algorithm/performance result.

**Historical checkpoint: I3-02E V1 DESIGN, superseded for future execution by V2 below.**
Read I3_02E_SOURCE_AUDIT.md, I3_02E_METHOD_PROTOCOL.md, I3_02E_PROTOCOL.json and
I3_02E_DESIGN_REVIEW.md. Final reference segments are often shortcut lines rather than
Graph edges. The new representation replaces one reference segment with connector ->
real directed PRM Edge -> connector, preserves that short corridor, and uses the same
representation for Geometry/Naive/Proposed controls. At most12000 geometry pairs and
5 scored corridors per state are fixed before camera values.

Reference pose sets form R and unchanged B_e; the changed corridor C includes entry,
three translations and exit yaw. Proposed set is exactly B_e union C, with both new
and lost voxels and full motion time. A full route oracle is allowed only after frozen
selection. Current CameraGainEvaluator lacks a budget-aware all-or-nothing pose-set
batch API; implementing/testing that isolated interface is an E1 prerequisite and all
its cost counts. No persistent Edge cache is assumed.

**Historical checkpoint: audit B addressed by I3-02E V2, now implemented/tested below.**
Read i3/I3_02E_REVISION_V2.md, METHOD_PROTOCOL_V2.md, PROTOCOL_V2.json and INPUTS_V2.json.
I3_02E_ASTRA_AUDIT.md is the immutable audit snapshot; its pre-revision status is historical.
All four V1 E documents and earlier negative data are preserved. E1 is now exact local
visibility composition and LIMITED GEOMETRIC POOL VALUE, not observation-guided generation.
The latter remains undefined/unimplemented. Exact argmax matching the same oracle and
dominating weaker same-pool selectors are correctness/definition properties, not novelty.

**Current checkpoint: V2 E1 COMPLETE, LIMITED_POOL_VALUE_FAIL.**
Read i3/I3_02E1_REPORT_V2.md, RESULTS_V2.json and VALIDATION_V2.json.
Collection parent6132b98 / global_planner32801ef, one registered6-state batch:
18874 pairs,13 fixed-pool corridors, no truncation. Pools1/14/26/27/38=0/1/5/5/2.
Four nonempty states pass supply>=3; only26has positive predicted-U (required>=2),
so value fails. Candidate3428 at26 is [0,282,285,295,301], real Edge285->295:
new2073/lost40, U+4.734%; new-only and exact both choose it. Other states keep reference.
Do not restore prior non-Edge anchor candidate197 at38 to improve the result.

13/13 candidate address/raw/unique/per-pose marginal outputs exactly match independent
full recomputation after choices are checkpointed. All5reference outputs match old
I3-01C.12new C++ tests+21existing regression tests and23Python tests pass.
Optional shared pose-set API uses unchanged optical ray arithmetic, absolute deadline,
counter/cancel checks and all-or-nothing output. Allocation tracker is linked into
isolated fixtures only; live planner defaults/dep.cpp are unchanged. Scratch peaks
22.34--32.64MiB under256MiB. Engineering FUNCTIONAL parity passes, but process peakRSS
and model allocated capacity were not collected: explicit resource-metadata gap,
not full resource-recording compliance. No repeat or E2 was run to fill it. One-shot
fixture process times are not fair deployed-speed or500ms admission evidence.

**Historical scope decision: I3_SCOPE_DECISION_2026-10-14.md and TRACE.json; future rules superseded by confirmed grilling consensus below.**
Read-only saved records prove per-Edge min-time excluded0 candidates in this corpus.
Old positive26/636 and38/197 have no allowed existing nonstart Graph arcs and no exact
E1 path match; they were excluded by representation. E1 qualified-not-scored counts
are0/0/47/121/0. We did NOT score them and cannot claim they contain useful routes.

One remaining hypothesis is reference-conditioned observation UPPER-BOUND search,
not more via-point/Edge variants. Keep same finite E1 mother sets0/1/52/126/2 and
<=5 exact alternative evaluations. Reference R defines residual Unknown Q=N minus R;
conservative range/extrinsic/voxel-padded corridor boxes produce optimistic new-voxel
counts and Ubar=(|R|+K)/estimatedTime. Ubar changes visit/retention order BEFORE full
scoring. Exact B_e union C determines actual model utility. No negative A* edge weights,
no persistent cache/free preprocessing. Old E1 failure remains, not superseded.

**Historical registration: user-confirmed grilling consensus Q1--Q8, G1-D0 registered. Completed below.**
Read i3/I3_GRILLING_CONSENSUS_2026-10-14.md, I3_G1_D0_PROTOCOL.md/JSON and INPUTS.json.
The eight decisions prioritize actual observation/exploration benefit as eventual paper
evidence; old reused5states do not solely decide the whole line. Real Graph Edge becomes
an implementation option, not a scientific necessity. No change to old E1/02A results.
The old “must find a state27positive” gate and optional box-sum approximation are no
longer future execution requirements. Main bound uses exact union (<=7 queries for3boxes).

**Historical D0 execution instructions (now completed; DO NOT rerun):**
Use I3_G1_D0_START_PROMPT.md. D0 uniformly uses all14 previously scored02A safe single-
waypoint corridors (sizes0/2/5/5/2) and original6snapshots,13negative. This is retrospective
development diagnosis, not an independent experiment or revival of failed anchor proxy.
No new geometry/visibility/seed/simulation; never supplement168unscored Edge routes.
Compute exact union counts for N and Q=N minus R, freeze motion/N-bound/Q-bound ranking,
then read saved precise labels. K1 is the primary early-value check; K2/5auxiliary cannot
rescue failure (K5covers the whole already-scored subset). Require an effective-U strict
signal versus each control, no-later known-positive retention vs motion, nonlower5-state
means, plus per-bound index/build/query/sort<=50ms and256MiB scratch. The50ms is a NEW
diagnostic overhead target under eventual500ms, not a deployment admission result.

Correct bound/changed ranking alone is insufficient. Once-only diagnostic then, ONLY
if all gates support it, separately register one P1prototype with common predeclared safe
corridors and real full500ms budgets plus equal actual scoring-count mechanism comparison.
No automatic P1/E2/core coding. Any D0/P1failure stops THIS mechanism, pauses core coding
and triggers a research-scope decision, not a universal proof against informative planning.
Process RSS and allocation counts must be recorded in D0; new model capacity must be
measured before later P1 (D0constructs no model). Preserve all old metadata gaps/failures.
This turn only registered protocols; after a future D0, report/local commit/verified
backup and stop. No GitHub push for this small checkpoint.

**Current: I3-03-01 (G1-D0) COMPLETE, NO_USEFUL_CONDITIONING_SIGNAL.**
Read i3/I3_03_01_REPORT.md, RESULTS.json and VALIDATION.json. Isolated integer prefix
counting tool/tests complete; one six-state batch over all14 old alternatives, zero
new routes/camera evaluations/seed/simulation.6 C++ +5 Python tests and74 frozen file
hashes pass. Exact counts/containment/upper inequalities14/14pass. N/Q preparation
max12.946/13.308ms; counted workspace max8.12MiB, process RSS max57.93MiB. Model
not constructed; its old actual capacity remains not_measured. No500ms admission.

Primary K1 effective-relative means motion=N=Q=+0.115377% over5validstates. Q strictly
better than either control in0states; record636 at26moves4→5, violating no-later gate.
K2same; K5exhausts old pool and cannot rescue. Changed ranks at26/27are not usefulness.
This stops the reference-conditioned AABB-count ranking mechanism and core coding.
It does not kill all informative planning, alter old02A/E1/I1 or admit automatic P1.
Implementation frozen parent46787af / GP6ef0fa9; final commit recorded in backup receipt.
Raw: /home/zxr2/cerlab_benchmark_ws/results/EXP-I3-03-01-BOUND-DIAGNOSTIC-V1/.
Backup: /home/zxr2/下载/CERLAB_I3_Backups/I3_03_01_2026-10-14/.

**Immediate next task, only after user starts it: research-scope decision.**
Do not automatically start I3-03-02 (G1-P1), E2, online guided-route coding or new seeds.
Decide whether to drop this bound's ranking role and formulate a materially different
bounded hypothesis, or narrow the paper objective. Do not tune boxes/K/weights or add
confidence/semantics/energy/loop closure to disguise the failed discriminator. Any new
implementation needs a separate fixed protocol; preserve all current/frozen negatives.
This completed task ends after verified local backup, without a GitHub push.
Raw: /home/zxr2/cerlab_benchmark_ws/results/EXP-I3-E1-FOUNDATION-V2/.
Local backup: /home/zxr2/下载/CERLAB_I3_Backups/I3_E1_V2_2026-10-14/.
No GitHub push for this checkpoint; user asked backup and stop after E1.

Raw: /home/zxr2/cerlab_benchmark_ws/results/EXP-I3-01C-OBSERVATION-LOSS-V1/.
Backup target: /home/zxr2/下载/CERLAB_I3_Backups/I3_01C_2026-10-13/.
Read its README and remote_sync_receipt.json for verified backup/push status.

Raw: /home/zxr2/cerlab_benchmark_ws/results/EXP-I3-01B-TWO-STAGE-V1/.
Backup: /home/zxr2/下载/CERLAB_I3_Backups/I3_01B_2026-10-12/ (phase date12, backup completion13; README records actual remote sync).
User explicitly requests continue authorized task after answering mid-task questions;
do not end the task merely to answer status. Finish current backup then report outcome.
Raw: /home/zxr2/cerlab_benchmark_ws/results/EXP-I3-00-CAMERA-PARITY-V1/.
Backup: /home/zxr2/下载/CERLAB_I3_Backups/I3_00_V1_2026-10-12/.
V2 raw: /home/zxr2/cerlab_benchmark_ws/results/EXP-I3-00-CAMERA-PERFORMANCE-V2/.
V2 backup: /home/zxr2/下载/CERLAB_I3_Backups/I3_00_V2_2026-10-12/.
Same-snapshot raw: /home/zxr2/cerlab_benchmark_ws/results/EXP-I3-00-SAME-SNAPSHOT-V1/.
Backup: /home/zxr2/下载/CERLAB_I3_Backups/I3_00_SAME_SNAPSHOT_2026-10-12/.

## Innovation-1 isolation rules

- Unique gain changes candidate ranking only behind a feature flag.
- Goal generation/prefilter, one A* route per goal and original shortcut stay fixed.
- Legacy route remains the fallback.
- Candidate histories are independent.
- No Edge cache during Innovation 1.
- Default legacy mode must reproduce current route and completion behavior.
- Cross-check selected C++ sets/counts against the frozen offline 0.25 m reference.
- Trace changed selections through shortcut, B-spline and odometry.
- Report actual observation per metre/second, planning time, CPU/RSS and real-time
  factor, not predicted gain alone.

Apply the kill/downgrade criteria in `R2_FINAL_DECISION.md`. Unique-only may be neutral
in global T95 and remain useful as infrastructure, but then it must not be advertised
as an independent performance contribution.

## Literature and claim boundary

The final novelty audit found close prior mechanisms in DEP/HIRE, PIPE, ETH active 3D
planning, TARE, FALCON, FUEL, t-BSP, EPIC, a 2026 GP coverage method and earlier
informative shortcutting. Read the audit before wording contributions:

`/home/zxr2/下载/CERLAB_Research_Documents/current/CERLAB_Final_Innovation_Audit_2026-09-17.md`

The paper must not claim:

- that HIRE uses endpoint gain only;
- first path information gain or first voxel union;
- ordinary K-shortest paths as the contribution;
- a via point plus two A* calls as sufficient novelty;
- generic caching as an algorithmic contribution;
- Occupancy entropy as full SLAM uncertainty;
- performance, significance or generality before paired multi-seed/multi-scene tests.

The intended primary claim, if H3 later passes, is a baseline-route-conditioned,
observation-opportunity-guided route construction method under fixed motion and
computation budgets, with observation preservation through simplification/execution.

## Working protocol for the next Codex

User preference updated2026-10-14: run multiple future tests in parallel, with separate
ROS Masters/ports/output directories when simulations are involved. If shared hardware
would interfere with frozen timing/resource comparisons, explain it first and use resource
isolation or a separately registered measurement arrangement; do not silently alter a
frozen protocol. The current D0 batch retains its pre-registered sequential timing.

1. Start with the outcome and evidence; distinguish implemented, tested, experimentally
   supported and still unverified.
2. Read source/logs before repairing an error. Do not skip errors or blindly rebuild.
3. Use isolated feature branches/workspaces, preserve baseline and user data, and keep
   generated large results outside Git.
4. Do not start duplicate ROS/Gazebo instances. Do not stop unrelated ROS projects.
5. Do not automatically start rosbag. Use lightweight CSV/JSON.
6. After each bounded task, run appropriate checks, update this handoff, commit locally
   and create a verified local backup. Push only after a major task such as I3-02 is
   complete, or when the user explicitly requests a push.
7. If context is nearly exhausted, stop at a clean checkpoint and update this file so
   a new conversation can resume from the first unfinished task.

## Ready-to-send instruction for a new conversation

```text
请先完整阅读：
/home/zxr2/cerlab_benchmark_ws/src/CERLAB-UAV-Autonomy/experiments/CODEX_HANDOFF.md

然后按其中“Immediate next task”继续。先核查 AGENTS.md、Git/submodule 状态和
运行进程，不要重复已完成的 Benchmark、R1 或 R2，不要修改冻结实验条件。
完成当前小任务后进行适当检查、更新交接文档、本地提交与校验备份；大任务完成或明确要求时再推送GitHub。
如果我在任务中提问，回答后继续原任务，不要因此中断。
```
