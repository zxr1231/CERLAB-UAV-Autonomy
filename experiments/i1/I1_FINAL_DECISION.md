# Innovation 1 final pilot decision

Date: 2026-10-08

## Decision

**No-Go for making `unique_online` the default exploration selector.** Keep the
path-history-aware Unique evaluator as a tested, feature-flagged research component
and keep the current Legacy selector as the operational default. Proceed with I2's
strong generic multi-route controls, but reassess predicted versus actual observation
on changed selections before implementing the proposed observation-guided route
generator in I3.

This is an engineering/research gate on a three-seed, one-scene pilot. It is not a
general impossibility claim about path deduplication and not a paper performance
claim. I1-06 is complete; no algorithm or Benchmark parameter was changed by this
decision.

## Frozen protocol and integrity

All six primary runs used the same parent commit `10e9c35`, identical submodule and
configuration hashes, empty Git status, seed pairs 1/1–3/3, the fixed floorplan2
world, 900 s timeout, headless mode, the same 980,550-voxel accessible-free Coverage
denominator, no rosbag and the Legacy gain threshold 500 for completion. Every primary
run reached HOME_REACHED with valid Coverage, trajectory, resource and collision
summaries and zero collision episodes. T80/T90/T95 are uncensored in all six runs.

The primary run for each task is the **first chronologically registered attempt that
actually completed with valid runner and measurement artifacts**. Matrix-wrapper
status alone can lag after a server restart. Seed-2 Legacy attempt 1 finished and
verified even though its wrapper was marked interrupted; the later valid repeat is
retained only for sensitivity analysis. All other interrupted or infrastructure-error
attempts remain in `batch_state.json` and on disk. No T95 replacement policy is used
in this pilot.

Reproduce the six-run audit with `experiments/analysis/summarize_i1_pilot.py` and the
batch state at
`/home/zxr2/cerlab_benchmark_ws/results/EXP-I1-06-PAIRED-PILOT-V1/batch_state.json`.
Its machine-readable output is `I1_06_PILOT_SUMMARY.json`.

## Paired outcomes

Differences are Unique-online minus Legacy; a negative T95 is faster, while a
negative actual-observation rate is worse.

| Seed | T80 Δ (s) | T90 Δ (s) | T95 Δ (s) | Completion Δ (s) | Explore distance Δ (m) | Actual accessible voxels/m Δ | Global planning mean Δ (ms) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | -35.90 | -40.79 | -124.07 | -7.20 | +9.67 | -170.24 | +44.53 |
| 2 | -1.17 | +30.45 | +48.56 | +63.98 | +8.16 | -266.48 | +49.63 |
| 3 | +21.91 | +50.75 | +50.14 | +122.93 | +54.21 | -1100.44 | +31.33 |

The mean paired T95 difference is -8.46 s, but its sample standard deviation is
100.13 s and its median is +48.56 s: seed 1's large improvement masks two slower
seeds. Unique-online flew farther in all three seeds (mean +24.01 m), obtained fewer
new accessible voxels per metre in all three (mean -512.38 voxels/m), and increased
mean global-planning time in all three (mean +41.83 ms). Actual observation per second
improved only in seed 1; it declined in seeds 2 and 3.

These actual-observation rates use the task-accessible sensor provenance count between
the planning start and exploration completion, divided by executed exploration
odometry distance or simulation time. Initial sensor observations are subtracted;
artificial takeoff clearing is excluded by the provenance stream. The exploratory
low-new interval measure considers valid exploration execution intervals with at
least 0.5 m executed distance and fewer than 100 first-observed full-map voxels per
metre. Its fraction improved in seeds 1 and 2 but worsened in seed 3; it does not
support a universal revisit-reduction claim.

Unique evaluation itself remained functional: 56/56, 257/257 and 45/45 global plans
used Unique selection with valid evaluation in seeds 1–3, with no logged fallback.
Real-time factors stayed near 0.999. The 257 plans in seed 2 versus 38 Legacy plans
are trajectory-dependent and warrant inspection; planning events are not independent
replicates.

## Gate interpretation and next work

I1 correctness is supported: the evaluator matched Python exactly on all 24 frozen
snapshots, 217 candidates and 13,131 path samples; online selection and return-home
engineering tests passed. The performance hypothesis that Unique-only online ranking
improves exploration is **not supported by this pilot**. The I1-KC5 downgrade criterion
is met because all three primary pairs have lower actual observation efficiency per
metre and longer flight, with two slower T95 runs.

Do not claim Unique-only as an independent performance contribution. Keep
`unique_online` available for controlled ablation, but leave `legacy` as default.
Before using this evaluator to justify I3's observation-guided route construction,
trace changed candidate choices through shortcut, B-spline and odometry and test
planner-model predicted versus actual observation ordering on held-out scene data.
The 2 m planner proxy and physical 5 m depth camera remain a known mismatch; R2's
mapper-matched shadow evaluator is an offline diagnostic, not a validated online
replacement. If this reassessment fails, revise the evaluator before route generation
instead of adding confidence, semantics, energy or cache modules.

I2 may now establish single-route, K-shortest and geometric-diversity controls with
fixed goals, candidate count, motion budget and computation budget. The proposed
route-generation mechanism in I3 remains conditional on the observation-model gate.
The three-point paper framing is in `../PAPER_CONTRIBUTIONS_DRAFT.md`; its second and
third points are still unimplemented hypotheses.
