# R2-06 validation: mapper-matched prediction and exploration-stage study

Date: 2026-09-22

Status: complete for one seed and one scene. The sensor model calibration passed, but
late-stage overprediction prevents treating predicted unique gain as an exact
surrogate for actual new observations. H2 is conditionally supported, not proven.

## Evaluator correction

The R2-05 legacy proxy used the planner's 2 m range, horizontal yaw cone, vertical
z-envelope and inflated-occupancy line test. The mapper instead uses a 640x480 pinhole
depth camera, the configured body-to-camera extrinsic, two-pixel input stride and a
5 m Euclidean ray cap.

R2-06 adds an offline-only frozen-map shadow evaluator with those mapper parameters.
It uses the mapper's physical occupied state rather than the inflated collision map,
deduplicates maximum-range ray endpoints and evaluates on the immutable
execution-start snapshot. It never feeds online route selection or completion.

A frozen occupancy map cannot know the depth of obstacles that remain Unknown. The
shadow model therefore traces a no-return ray until the first snapshot-known occupied
voxel. This is an explicit upper-bound tendency, not an exact replay of Gazebo depth.

## Controlled calibration

The corrected R2-05 smoke was reevaluated at the same 0.25 m / 0.1 rad odometry
sampling used by the legacy proxy. All 14 intervals were retained.

| Odom-prefix model | Precision mean | Recall mean | Jaccard mean | Count Pearson | Count Spearman |
|---|---:|---:|---:|---:|---:|
| Legacy proxy | 0.314 | 0.043 | 0.040 | 0.847 | 0.662 |
| Mapper-matched shadow | **0.756** | **0.937** | **0.714** | **0.940** | **0.965** |

The improvement on identical poses shows that R2-05's low overlap primarily came from
sensor-model mismatch rather than timestamp/snapshot misalignment.

## Formal seed-1 run

- experiment: `EXP-R2-06-SENSOR-SHADOW-SEED1-V1`;
- result: `environment_seed_001/planner_seed_001/20260922T152615`;
- source commit at run start: `e697f8c`;
- environment/planner seed: 1/1;
- world, dynamics, FoV, safety and completion threshold: unchanged Benchmark v2;
- result: HOME_REACHED, no collision;
- final accessible-free Coverage: 96.260%;
- T80/T90/T95: 223.926 / 354.530 / 488.120 s;
- exploration distance: 232.165 m;
- execution intervals: 233.

Twenty-four intervals were selected before set scoring: eight evenly spaced execution
IDs from each execution-order tertile. Nineteen had a nonempty actual set that was
Unknown in the execution snapshot and inside the planner ROI. Five empty comparable
sets were retained as explicit exclusions. Stage labels are execution-order tertiles,
not equal-Coverage bins.

| Stage | Eligible | Model | Precision mean | Recall mean | Jaccard mean | Count Spearman |
|---|---:|---|---:|---:|---:|---:|
| Early | 7 | Legacy | 0.525 | 0.013 | 0.012 | 0.906 |
| Early | 7 | Shadow | **0.747** | **0.960** | **0.719** | **0.964** |
| Middle | 6 | Legacy | undefined | 0.000 | 0.000 | undefined |
| Middle | 6 | Shadow | **0.665** | **0.994** | **0.662** | **1.000** |
| Late | 6 | Legacy | **0.512** | 0.545 | **0.262** | 0.116 |
| Late | 6 | Shadow | 0.186 | **0.991** | 0.181 | **0.829** |
| Overall | 19 | Legacy | 0.518 | 0.177 | 0.087 | 0.077 |
| Overall | 19 | Shadow | **0.544** | **0.981** | **0.531** | **0.812** |

The middle legacy precision/correlation are undefined because all six legacy predicted
counts were zero.

## Interpretation

The mapper-matched evaluator is a defensible replacement for the legacy visibility
proxy in offline predicted/actual validation. It greatly improves exact-set overlap
and rank correlation overall and in the early/middle stages.

The late stage exposes a real limitation: shadow Recall remains high, but Precision
falls because a frozen map cannot predict where still-Unknown physical surfaces will
terminate the next depth rays. Several short late intervals therefore receive large
predicted supersets. The shadow count must not be presented as an unbiased estimate of
actual late-stage gain.

R2-06 supports continuing to R2-07. It does not yet justify deploying unique gain
online. R2-07 must decide whether the proposed method can use this evaluator with a
conservative late-stage treatment, and must preserve predicted-versus-actual metrics
as required validation rather than optimizing only predicted gain.

## Verification

- 85 Python tests pass;
- `exploration_benchmark` and `autonomous_flight` compile;
- opt-in snapshot launch arguments resolve for full and smoke launch files;
- the successful run used no RViz and no rosbag;
- no ROS/Gazebo process remained after the runner stopped;
- the sandbox-denied first attempt was retained as a failed run and was not substituted
  for the successful run.

