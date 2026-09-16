# Formal baseline batch 1 — seeds 1–3

Date: 2026-09-16

## Fixed protocol

- Parent commit: `a29c1a84716fda15d1af56f10ce179b52bcc2204`
- Config: `config/floorplan2_dep_formal_batch1_v1.json`
- Config SHA256: `e8969b5271e011ab26c04100de04d29ed1efba070b4c6dc5655f122642fa9d0a`
- Method: current HIRE-guided DEP baseline with return-home threshold 500
- Seed pairs: 1/1, 2/2, 3/3
- Full floorplan2, timeout 900 s, headless, RViz off, rosbag off
- Audited Coverage status: `VALID_ACCESSIBLE_FREE_V2`

All three manifests recorded the exact commit above and an empty Git status.

## Per-run results

| Seed | T80 s | T90 s | T95 s | Completion s | Explore m | Final m | Final free | Surface | Outcome |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 213.36 | 299.51 | 367.09 | 384.53 | 159.72 | 167.25 | 0.9582 | 0.6409 | HOME_REACHED |
| 2 | 241.76 | 288.36 | 388.06 | 395.00 | 165.81 | 173.47 | 0.9535 | 0.6282 | HOME_REACHED |
| 3 | 232.95 | 300.32 | 410.72 | 423.16 | 177.09 | 178.12 | 0.9525 | 0.6312 | HOME_REACHED |

## Preliminary three-seed aggregate

- Exploration completion: 3/3; return success: 3/3.
- Collision-free: 3/3. The Wilson 95% lower bound is only 0.4385 because n=3.
- T80: mean 229.35 s, sample standard deviation 14.54 s.
- T90: mean 296.06 s, sample standard deviation 6.68 s.
- T95: mean 388.62 s, sample standard deviation 21.82 s.
- Exploration completion: mean 400.89 s, sample standard deviation 19.98 s.
- Exploration distance: mean 167.54 m, sample standard deviation 8.82 m.
- Final mission distance: mean 172.95 m, sample standard deviation 5.45 m.
- Final free Coverage: mean 0.95475, sample standard deviation 0.00302.
- Global planning mean across run means: 50.15 ms.
- Exploration process tree: mean CPU 145.51% of one core; mean RSS 455.19 MiB.
- Mean real-time factor across runs: 0.99907.

T95 preceded algorithm completion by 17.44, 6.94, and 12.44 s respectively. This
confirms a smaller post-T95 tail in these runs while preserving the distinction between
Coverage threshold crossing and the gain-based completion gate.

## Integrity checks

- Coverage rows: 5,756 / 5,707 / 5,924; every sequence starts at 1 and is contiguous.
- Free and surface curves are monotonic in all runs.
- Final received and reconstructed provenance totals match in all runs:
  1,180,885 / 1,175,214 / 1,175,474.
- Collision, resource, and trajectory summaries are `VALID` in all runs.
- Collision episodes: 0 / 0 / 0.
- No ROS/Gazebo process remained after the matrix.

Local outputs:

- Batch state: `/home/zxr2/cerlab_benchmark_ws/results/EXP-BENCH-V2-DEP-FORMAL-BATCH1-V1/batch_state.json`
- Aggregate: `/home/zxr2/cerlab_benchmark_ws/results/EXP-BENCH-V2-DEP-FORMAL-BATCH1-V1/aggregate_v1`

## Interpretation limit

This is the first formal subset, not the final baseline dataset. At least seven more
environment seeds are required to reach the specified minimum of ten. No comparison
or improvement claim should use this n=3 aggregate as final evidence.
