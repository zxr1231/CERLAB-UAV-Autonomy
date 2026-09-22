# CERLAB UAV autonomy — Codex handoff

Last updated: 2026-09-22 after I1-01.

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
parent branch: feat/i1-unique-gain
parent starting commit for I1: 80f5e2f5b0a287348d2fc7dc9bca0eac0d7d11f6

autonomous_flight:
  branch feat/i1-gain-logging
  commit 3243c9f (I1-01)

global_planner:
  branch feat/i1-unique-gain
  commit 4b996cf (I1-01)

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

## Immediate next task: I1-02

Do not change candidate selection. Implement only the I1-02 evaluator foundation from
`experiments/r2/R2_FINAL_DECISION.md`:

1. Implement stable visible-Unknown voxel-address sets under the frozen planner model:
   2 m range, baseline yaw rule/z-envelope, Unknown transparency, inflated occlusion
   and planning ROI.
2. Sample candidate paths at the frozen 0.25 m interval and compute raw, unique,
   per-sample marginal, duplicate ratio and unique utility on one immutable snapshot.
3. Keep candidate histories independent and fail closed on map-version mismatch.
4. Populate the schema fields frozen by I1-01, but keep selection mode Legacy and keep
   both non-Legacy configuration modes unavailable until the relevant correctness gate.
5. Do not implement Edge cache, change A*, Goal selection, shortcut or completion.
6. Add focused unit fixtures, compile and test. I1-03 will perform the broader frozen
   offline-reference agreement study.
7. Update this handoff, commit/push changed repositories and create a verified backup.

After I1-01, follow I1-02 through I1-06 in the final R2 decision. The paired pilot uses
seed pairs 1/1, 2/2 and 3/3. Final paper-scale ten-seed and multi-scene ablation is
deferred until the full proposed method is ready.

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
