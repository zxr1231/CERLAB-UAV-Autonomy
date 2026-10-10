# CERLAB UAV autonomy — Codex handoff

Last updated: 2026-10-10 at user-requested stop after seed2 collection.

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

The repositories are clean and their active branches are maintained in the user's
GitHub account. The user has authorized pushes for completed project work.

```text
parent branch: feat/i2-route-controls
I2-04 smoke source commit: e97291d431dba1344b4edcd59f9d4a1ff37520c5
I2-05 runner checkpoint: a8967e0
final documentation checkpoint: inspect git HEAD / local backup README
frozen I1 branch: feat/i1-unique-gain
frozen I1 commit: 10e9c3589e2f5895d53e354547a03bf8f6f238a2

global_planner:
  branch feat/i2-route-controls
  commit 99f3122feb84f854ec921f6421673e4b620f2e4c
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

**Current checkpoint: I2-05 collected8/12 trials; stopped after seed2 by user.**
Collection source remains067794787ede6654c8ddd76fd3681a7e45c46a9c, clean at
/home/zxr2/cerlab_benchmark_ws/src/CERLAB-UAV-Autonomy. DO NOT edit/commit its
source during this partial matrix. This updated documentation is in separate
worktree /home/zxr2/cerlab_i2_docs_checkpoint_20261010 on branch
`docs/i2-seed2-checkpoint-20261010`, so source/provenance stay fixed.

Current state files:
/home/zxr2/cerlab_benchmark_ws/results/EXP-I2-05-PAIRED-PILOT-V1/batch_state.json
and backup_controller_state.json. Controller ended with stopped_after_verified_backup;
no ROS11311 listener or running simulator remains. STOP_BACKUP_CONTROLLER exists.
Eight per-trial full archives/COMPLETE checksums verified under
/home/zxr2/下载/CERLAB_I2_Backups/I2_05_PAIRED_RUNS_2026-10-10/.
See I2_05_SEED2_CHECKPOINT_SUMMARY.json. No final3-seed conclusion yet.

Seed1: historical SUCCESS, distance_single USER_ABORT, generic SUCCESS, geometric
SUCCESS. User requested ending the single-route stalled run early after repeated
B-spline infeasibility; retain failure/censoring, do not replace or relabel900s timeout.
Seed2: distance_single SUCCESS, generic SUCCESS, geometric TIMEOUT, historical
SUCCESS. Geometric had HOME_REACHED near the deadline but lacked the runner's
extra waiting period; retain originalTIMEOUT and actual home event separately.

**Next action ONLY after user continuation:** inspect services/Git/backups; remove
STOP_BACKUP_CONTROLLER; launch the external backup_controller.py with a new user
service name (previous active unit was cerlab-i2-05-paired-backup-controller-v2,
now inactive). Keep source HEAD0677947. It validates existing backups then schedules
first pending seed3 generic_k_shortest, geometric_diverse, historical_legacy,
distance_single. No reruns of completed seed1/2 or automatic failure retry.
The external controller permits ONLY the existing user-aborted seed1 task via
CONTINUE_AFTER_USER_ABORT.json; other technical/measurement failures still halt.

After all12 terminal trials: run external summarize_pilot.py with workspace Python
path, audit observation/execution/provenance/censoring, create final summary in a
DOCS worktree or after collection source no longer needed, push and verify backup.
I2-06/held-out prediction-actual gate still precedes I3.

User preference: AFTER observation-opportunity guidance is implemented, switch NEW
experimental cohorts to parallel isolated ROS/Gazebo instances. Preregister uniform
concurrency, calibrate CPU/GPU/RTF and use the same parallel load for controls.
Do not mix current serial data as if measured under that parallel protocol.
Current matrix remains serial. See batch next_phase_preferences.json.

Seed2 checkpoint backup:
/home/zxr2/下载/CERLAB_I2_Backups/I2_05_SEED2_CHECKPOINT_2026-10-10/.

Local backup: `/home/zxr2/下载/CERLAB_I2_Backups/I2_05_ONLINE_2026-10-08/`
(completed on 2026-10-09 after the previous quota-related push interruption).

Final paper-scale ten-seed and multi-scene ablation is deferred until the full
proposed method is ready. The current three-part paper framing is in
`experiments/PAPER_CONTRIBUTIONS_DRAFT.md`; its second and third points remain
unimplemented hypotheses.

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

1. Start with the outcome and evidence; distinguish implemented, tested, experimentally
   supported and still unverified.
2. Read source/logs before repairing an error. Do not skip errors or blindly rebuild.
3. Use isolated feature branches/workspaces, preserve baseline and user data, and keep
   generated large results outside Git.
4. Do not start duplicate ROS/Gazebo instances. Do not stop unrelated ROS projects.
5. Do not automatically start rosbag. Use lightweight CSV/JSON.
6. After each bounded task, run appropriate tests, update this handoff, commit, push
   the user's GitHub repositories and create a verified local backup.
7. If context is nearly exhausted, stop at a clean checkpoint and update this file so
   a new conversation can resume from the first unfinished task.

## Ready-to-send instruction for a new conversation

```text
请先完整阅读：
/home/zxr2/cerlab_benchmark_ws/src/CERLAB-UAV-Autonomy/experiments/CODEX_HANDOFF.md

然后按其中“Immediate next task”继续。先核查 AGENTS.md、Git/submodule 状态和
运行进程，不要重复已完成的 Benchmark、R1 或 R2，不要修改冻结实验条件。
完成当前小任务后编译、测试、更新交接文档、提交并推送 GitHub，再制作本地备份。
如果我在任务中提问，回答后继续原任务，不要因此中断。
```
