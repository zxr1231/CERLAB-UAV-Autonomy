# Benchmark v2 clean full-run validation

Date: 2026-09-16

## Run identity

- Parent commit: `c414604cab04f4728eda883db91e6b9a8cf88019`
- Environment seed / planner seed: `1 / 1`
- Mode: full floorplan2, RViz disabled, rosbag disabled
- Completion threshold: 500
- Manifest Git status: clean
- Outcome: `HOME_REACHED`
- Raw run:
  `/home/zxr2/cerlab_benchmark_ws/results/EXP-BENCH-V2-FULL-CLEAN-V2/environment_seed_001/planner_seed_001/20260916T102428`

## Coverage and timing

- Planning time origin: simulation time 4.221 s, recorded after the third confirmation.
- T80: 267.1108 s.
- T90: 329.2374 s.
- T95: 383.0436 s.
- Algorithm completion / return start: 450.719 s after planning activation.
- Return duration: 31.077 s.
- Mission simulation / wall duration: 482.171 / 482.575 s.
- Mean real-time factor: 0.99916.
- Final free Coverage: 944,895 / 980,550 = 0.96364.
- Final static-surface Coverage: 18,317 / 29,375 = 0.62356.
- Final known task volume: 963.237 m³.

All 6,258 Coverage rows were sequence-contiguous. Free and surface curves were
monotonic, and the received/reconstructed full-map provenance totals both equaled
1,190,646. The v2 mask content hash matched the committed artifact and both static
observability fractions were 1.0.

T95 preceded algorithm completion by 67.68 s. Final free Coverage was about 0.99
percentage points above 95%, quantifying the baseline's post-T95 long tail. Algorithm
completion remains a gain-threshold decision, not a ground-truth Coverage certificate.

## Motion, planning, safety, and resources

- Exploration distance at return start: 192.497 m.
- Final mission distance including return: 203.648 m.
- Global planning: 34 calls, mean 63.264 ms, p95 147.651 ms, max 174.867 ms.
- Exploration local planning: 203 calls, mean 0.654 ms.
- Return planning: one call, 0.525 ms.
- Collision messages after planning: 24,620; collision episodes: 0 (`VALID`).
- Exploration process tree: mean CPU 143.67% of one core; mean RSS 458.60 MiB.
- Simulator process tree: mean CPU 128.69%; mean RSS 851.16 MiB.
- Logger process tree: mean CPU 28.16%; mean RSS 152.47 MiB.
- Trajectory association status: `VALID`; 201 exploration B-splines were recorded,
  200 had associated odometry.

Logger load is reported separately and is not folded into the exploration-process
resource metric. Internal planning durations use steady wall clocks. The nontrivial
logger overhead is a limitation to retain when interpreting whole-system timing.

## Scope

This single seed validates the complete measurement pipeline and threshold behavior.
It is not a statistical performance result. Formal paper claims require the fixed
final commit, at least ten environment seeds, retained failures/censoring, and the
same protocol for every compared method.
