# R2-05 validation: alignment, overlap and execution preservation

Date: 2026-09-22

Status: engineering alignment passed; the current legacy visibility proxy did not pass
the scientific exact-set agreement gate. H2 remains unproven.

## Alignment correction

The first R2-04 fixture used the global-plan map snapshot. Global planning is followed
by orientation motion before B-spline activation, and later local trajectories reuse
the same global route. Consequently, no interval passed the strict fresh-map analysis
rule: global-plan to execution delay was commonly 3–10 s and map-version drift reached
2.8 million updates.

R2-05 therefore adds an immutable `execution_NNNNNN` snapshot immediately after every
successful B-spline activation. This is an alignment correction independent of metric
outcomes. The snapshot records its capture kind, execution ID and originating global
planning sequence. The four layers are recomputed on this same execution-start map.

In the corrected smoke, all 14 execution snapshots had a local-event map-version delta
of zero. Thirteen intervals passed the analysis rule; one lacked a nonempty comparable
actual/odom prediction and was retained but excluded from aggregate metrics.

## Comparable actual set

For each execution snapshot, actual first-observation addresses are retained only when
they were Unknown in that snapshot, lie inside the planner ROI, and are not inflated
occupied. On average, 15.09% of the physical sensor's interval observations meet this
comparison support. Startup observations remain outside execution intervals.

Metrics are defined as:

- precision = predicted/actual intersection divided by predicted set size;
- recall = intersection divided by comparable actual set size;
- Jaccard = intersection divided by set union;
- count Pearson/Spearman across eligible execution intervals;
- transition retention and Jaccard for raw→shortcut→B-spline→odom-prefix.

## Corrected smoke result

| Layer versus actual | Precision mean / median | Recall mean / median | Jaccard mean / median | Count Pearson / Spearman |
|---|---:|---:|---:|---:|
| raw PRM | 0.398 / 0.410 | 0.242 / 0.112 | 0.092 / 0.054 | -0.449 / -0.626 |
| shortcut PRM | 0.442 / 0.455 | 0.231 / 0.113 | 0.094 / 0.051 | -0.418 / -0.571 |
| B-spline | 0.582 / 0.794 | 0.052 / 0.016 | 0.049 / 0.013 | 0.158 / -0.066 |
| odom prefix | 0.314 / 0.090 | 0.046 / 0.006 | 0.043 / 0.005 | **0.841 / 0.632** |

The odom-prefix count correlation is encouraging because it compares the actually
executed pose/yaw prefix. Exact-set overlap remains weak and variable. Full PRM routes
are negatively count-correlated with short execution intervals, confirming that a
complete planned route cannot be treated as if it were executed before replanning.

## Layer preservation

| Transition | Source retention mean / median | Jaccard mean / median | Target novel fraction mean |
|---|---:|---:|---:|
| raw PRM → shortcut | 0.773 / 0.857 | 0.758 / 0.846 | 0.021 |
| shortcut → B-spline | 0.312 / 0.074 | 0.281 / 0.070 | 0.244 |
| B-spline → odom prefix | 0.578 / 0.624 | 0.263 / 0.248 | 0.485 |

Raw→shortcut loses about 22.7% of the raw predicted set on average in this smoke, which
supports keeping observation preservation as a method concern. Shortcut→B-spline loss
cannot be attributed solely to smoothing because each local B-spline normally covers
only the next portion of the global route. B-spline→odom differences combine partial
execution, measured yaw, tracking deviation and replanning.

## Scientific decision

The alignment/logging pipeline is correct enough to proceed, but the legacy proxy is
not yet a physically matched observation predictor. The planner uses `dmax=2 m`, a
z-envelope rather than vertical angular FoV, body-position viewpoints and inflated-line
occlusion; the mapper uses a 5 m depth camera, camera extrinsics and pinhole intrinsics.
Low Jaccard/recall cannot be interpreted as a failure of unique gain alone.

R2-06 must begin with a sensor-matched shadow evaluator using the mapper's camera
extrinsics, intrinsics/range and ray semantics. It must compare that evaluator with the
legacy proxy on the same execution-start snapshots before running early/middle/late
validation. Do not change online route selection or retune the environment.

## Verification

- five alignment unit tests and five predicted-set tests pass;
- the full exploration benchmark suite has 73 passing tests;
- global_planner, exploration_benchmark and dependent autonomous_flight compile;
- return-home and threshold-500 checks pass;
- 14 corrected execution snapshots, actual sets, predicted sets and alignment records
  completed without integrity errors.

| Generated file | SHA-256 |
|---|---|
| `observation_alignment_summary.json` | `d9c2e74b6504be33c36abeba047c1e9bd1d54aa09758c09b12dae4b7a99b415e` |
| `observation_alignment_intervals.json` | `7a077653a7c9d10e6af57da26affdfdb571bc9f56050adf0df6dbb6699d92ac5` |
| `predicted_observation_summary.json` | `149d6b4db4bb8ca33cb2117b2d94390fae0213d91cd73951cabd9835ed0afa5a` |
| `predicted_observation_sets.jsonl` | `09ae26dd0219baf8d46d6b86e081a630d9d4cbcc5b5dc9970f293734b82bc95d` |

These are smoke results, not independent statistical evidence.
