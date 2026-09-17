# Benchmark v2 final 10-seed baseline

Date: 2026-09-17

## Protocol

- Parent commit: `8230c8065f9d462dc5d92f233fb402af359b28b4`
- Config: `config/floorplan2_dep_formal_10seed_v2.json`
- Config SHA256: `9c1d1e11b8b7f477bd768d891804abb828eeb37d875c5549143ebd43d186a8e2`
- Environment/planner seed pairs: 1/1 through 10/10
- Full floorplan2, headless, timeout 900 s, RViz off, rosbag off
- Method: current HIRE-guided DEP baseline, return-home gain threshold 500
- Coverage definition: `VALID_ACCESSIBLE_FREE_V2`

All ten primary runs recorded the same clean commit. All reached `HOME_REACHED`, had
valid Coverage/resource/trajectory summaries, and reported zero collision episodes.

## T95 repeat policy selected for the downstream baseline

Seeds 3, 9, and 10 had high original T95 values and were repeated with the identical
commit and protocol. Per project decision, only T95 is replaced; T80, T90, completion,
distance, Coverage, planning, resource, collision, and trajectory fields remain from
the original ten-run matrix.

| Seed | Original T95 s | Repeat T95 s | Downstream T95 s |
|---:|---:|---:|---:|
| 3 | 571.18 | 410.93 | 410.93 |
| 9 | 476.19 | 349.82 | 349.82 |
| 10 | 501.30 | 356.68 | 356.68 |

Original runs and the unmodified aggregate remain preserved. The downstream aggregate
records every replacement path and value in its JSON metadata.

## Per-seed downstream table

| Seed | T80 s | T90 s | T95 s | Completion s | Explore m | Final m | Free % | Surface % |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 253.86 | 289.19 | 324.44 | 383.01 | 156.33 | 171.54 | 95.74 | 63.50 |
| 2 | 176.80 | 260.64 | 410.37 | 483.55 | 207.09 | 221.43 | 96.31 | 62.88 |
| 3 | 244.86 | 330.82 | 410.93 | 479.11 | 177.87 | 181.06 | 95.09 | 63.59 |
| 4 | 213.00 | 271.58 | 371.09 | 427.13 | 188.95 | 203.50 | 95.96 | 64.07 |
| 5 | 245.23 | 284.70 | 344.13 | 395.49 | 167.22 | 180.94 | 96.37 | 64.39 |
| 6 | 204.38 | 266.19 | 358.49 | 373.81 | 152.44 | 153.52 | 95.84 | 64.59 |
| 7 | 238.21 | 259.04 | 421.11 | 443.14 | 186.52 | 201.03 | 95.56 | 63.93 |
| 8 | 218.69 | 277.95 | 407.97 | 402.18 | 166.63 | 175.77 | 95.21 | 61.64 |
| 9 | 240.14 | 294.00 | 349.82 | 508.79 | 220.38 | 225.95 | 95.86 | 63.41 |
| 10 | 259.50 | 295.43 | 356.68 | 483.25 | 190.69 | 204.31 | 95.63 | 63.77 |

## Final aggregate

- Exploration completion: 10/10; return success: 10/10.
- Collision-free: 10/10. Wilson 95% interval: 0.7225–1.0000.
- Coverage-valid: 10/10.
- T80: 229.47 ± 25.74 s (sample standard deviation).
- T90: 282.96 ± 21.39 s.
- T95 after the selected replacements: 375.50 ± 34.19 s.
- Original, unmodified T95: 418.63 ± 77.39 s.
- Exploration completion: 437.94 ± 48.54 s.
- Exploration distance: 181.41 ± 21.72 m.
- Final mission distance: 191.91 ± 23.07 m.
- Final free Coverage: 0.95757 ± 0.00414.
- Static-surface Coverage: 0.63578 ± 0.00842.
- Mean global-planning time across run means: 45.00 ms.
- Exploration process tree CPU: 144.63 ± 1.02% of one logical core.
- Exploration process tree RSS: 457.61 ± 6.25 MiB.
- Mean real-time factor: 0.99916.

## Integrity checks

- All ten primary runs used commit `8230c80` with an empty Git status.
- Provenance sequences start at one, are contiguous, and reconcile received and
  reconstructed totals in every run.
- Free and static-surface Coverage curves are monotonic in every run.
- Collision, resource, and trajectory summaries are `VALID` in every run.
- Collision episodes: 0 in every run.
- 2,218 of 2,224 exploration/return B-spline records had associated odometry; six
  short-lived replans had no odometry sample and remain explicitly represented.
- No ROS/Gazebo process remained after the primary matrix or repeat runs.

## Artifacts

- Original primary aggregate:
  `/home/zxr2/cerlab_benchmark_ws/results/EXP-BENCH-V2-DEP-FORMAL-10SEED-V2/aggregate_final`
- Downstream T95-only aggregate:
  `/home/zxr2/cerlab_benchmark_ws/results/EXP-BENCH-V2-DEP-FORMAL-10SEED-V2/aggregate_final_t95_retests`
- Committed review copies:
  `final_baseline/aggregate_original.json`,
  `final_baseline/aggregate_t95_retests.json`, and
  `final_baseline/runs_t95_retests.csv`.
- Repeat raw runs:
  `EXP-BENCH-V2-DEP-FORMAL-SEED3-REPEAT-V1`,
  `EXP-BENCH-V2-DEP-FORMAL-SEED9-REPEAT-V1`, and
  `EXP-BENCH-V2-DEP-FORMAL-SEED10-REPEAT-V1` under the workspace results directory.

Benchmark v2 now provides the frozen baseline required for innovation and ablation
experiments. Any compared method must use the same world, mask, sensor model, dynamics,
time origin, seed set, timeout, and aggregation policy.
