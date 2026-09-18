# R1-06 checkpoint: sampling sensitivity, runtime and cache gate

Date: 2026-09-18

Status: complete. No online planner decision or completion condition was changed.

The exploration benchmark package compiles, all 55 regression tests pass, both
sensitivity-specific tests pass, and no ROS/Gazebo process was required or left
running. All study groups completed with zero snapshot failures.

## Sampling protocol

The same 25 gain-blind, state-decorrelated snapshots and 152 candidate routes from
R1-05 were recomputed independently at 0.25, 0.5 and 1.0 m. A convergence subset used
the first and last retained snapshot from each early/middle/late tertile (6 snapshots,
33 candidates) at 0.125 and 0.25 m.

### Full-set comparison against 0.25 m

| Spacing | Samples | Unique gain mean/median error | Top-1 agreement | Full-rank agreement | Rank correlation | Diagnostic time | Max RSS |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.25 m | 8613 | reference | 100% | 100% | 1.000 | 235.21 s | 37,780 KiB |
| 0.5 m | 4497 | 5.68% / 3.63% | 96% | 80% | 0.985 | 155.11 s | 37,420 KiB |
| 1.0 m | 2483 | 12.97% / 10.83% | 80% | 60% | 0.956 | 111.78 s | 36,928 KiB |

The maximum relative errors (66.7% at 0.5 m and 100% at 1.0 m) occur when the finest
reference gain is small, so mean/median and decision agreement are reported together.
One of 25 Top-1 decisions differs between 0.5 and 0.25 m; five differ at 1.0 m.

### 0.125 to 0.25 m convergence subset

At 0.25 m, all 6 Top-1 choices matched 0.125 m. Mean/median unique-gain error was
2.76% / 1.79%, full-rank agreement was 83.3%, and mean rank correlation was 0.994.
This is a bounded convergence check, not proof for every snapshot.

Decision:

- use **0.25 m** for formal R1/future paper diagnostic tables;
- 0.5 m may be used for development screening only and must be labelled;
- reject 1.0 m for route-ranking evidence;
- keep the 0.125 m subset as a convergence check rather than multiplying all formal
  computation by two.

With the selected 0.25 m model, the R1-05 pilot becomes: mean snapshot duplicate ratio
52.19%, selected-route duplicate ratio 67.15%, raw→unique full-order change 36%, and
raw→unique Top-1 change 16% (4/25). The four pure-dedup winner regrets were 7.48%,
7.83%, 0.34% and 5.95%; mean regret over all snapshots was 0.86%. This is stronger than
the provisional 0.5 m result, but remains one correlated run.

## Runtime and memory

At 0.25 m, candidate visibility evaluation consumed 181.85/235.21 s (77.3%); snapshot
validation/loading consumed 53.19 s (22.6%). At 0.5 m, evaluation consumed 98.16/155.11
s (63.3%) and validation/loading 56.79 s (36.6%). Memory stayed near 37 MiB across
spacings, so this pilot identifies compute time rather than RSS as the immediate issue.

These are offline Python timings with full hash/state validation. They do not predict
online C++ latency and cannot be compared directly with the existing planner's C++
planning time.

## Reuse and cache decision

At 0.5 m there were 4,497 sample occurrences but 2,649 unique pose/yaw samples, an
exact reuse fraction of 41.09%. Consecutive directed sampled-edge reuse was 42.53%
(4,345 occurrences, 2,497 unique). Candidate evaluation occupied 63.25% of offline
diagnostic wall time. Thus the predeclared illustrative gates—more than 30% scoring
share and more than 20% edge reuse—both pass in the offline proxy.

Decision: **retain Dependency-Aware Incremental Evaluation as a conditional later
prototype, but do not implement it yet and do not list it as a contribution.** The
guided route generator does not exist yet, and reuse/latency must be reprofiled in the
final C++ pipeline. Any future cache requires exact equality with full recomputation,
including map reset, direction/yaw, FoV, sampling interval and occlusion invalidation.

## Scientific conclusion

R1-06 confirms that the deduplication result is sampling-dependent. The 0.25 m result
supports retaining unique gain as the common evaluator and continuing to R1-07, while
the convergence and single-run limits prevent a performance or novelty claim. No
actual-observation correlation has been established.
