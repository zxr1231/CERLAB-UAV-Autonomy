# I2-06 held-out executed-prefix gate — preregistered 2026-10-12

Register and commit BEFORE collection. One first attempt only; no selection or tuning
based on outcome, no rerun of frozen I1/I2 pilots. This is a model/integration diagnostic,
not a performance comparison, Coverage benchmark or unexecuted-route ranking oracle.

## Collection

- World: floorplan1/floorplan1_static.world, separate held_out_floorplan1.launch copied
  from frozen deployed start.launch with only active world changed. Default unchanged.
- Gazebo seed4; planner seed4. Corrected global_planner3267e3d.
- Mode distance_single, Legacy selection + unique_shadow diagnostic; return gain500.
- Sensor/mapping/dynamics/start/region identical to existing config; headless, no bag.
- Timeout480 wall seconds after official confirmations / planning begins, or standard
  runner HOME_REACHED+10s if sooner. TIMEOUT retained as bounded collection status.
- Execution-start immutable snapshots and normal CSV/JSON delta provenance enabled.
  Keep all raw snapshots. No new coverage mask: disable Coverage, no T80/T90/T95.
- Observe corrected feedback policy log, ready safe routes, valid matched yaw context,
  sensor/trajectory activity, collisions, planning costs, CPU/RSS and RTF separately.
  This does not quantify the repair's effect against old trials.

## Selection (before looking at information outcomes)

Read execution_intervals.csv after collection. Eligible: valid, global_sequence>0,
odom_count>=2, executed_distance>=0.5m, duration>0. Matched execution-start snapshot
must exist; report missing snapshots as telemetry error, not silently replace samples.
Sort by interval_id and divide these eligible intervals into three equal-order thirds
(early/middle/late are order strata, NOT Coverage strata). Choose up to4 evenly spaced
IDs per third using existing select_stage_intervals; do not replace selected empty
actual sets or failed predictions. Freeze selected IDs before raycasting/actual scoring.
At least8 selected valid comparisons and at least2 per third are required. Hover/yaw-only
intervals are retained in raw data but outside this per-metre primary gate.

## Prediction and actual observation

Same odometry prefix sampled at0.25m or0.1rad, including first/final pose, for BOTH:
1. Legacy2m FoV/yaw/occlusion voxel-centre model, identical prior offline evaluator.
2. Existing frozen mapper-matched5m camera shadow: actual intrinsics/extrinsics/pixel
   lattice/margin/mapper pixel skip2; no new approximation or parameter adjustment.
Both use each interval's execution-start snapshot. Camera shadow has no knowledge of
physical obstacles that were Unknown; level-body yaw approximation is retained.

Actual sets from canonical timestamp-aligned FIRST SENSOR observation deltas, artificial
setFree excluded; integrity check delta sequence/observed_total/global union. Apply same
existing R2 comparable-actual mask: snapshot Unknown, noninflated, in planner region.
Keep actual-empty intervals as zero gain; no R2-style empty-set exclusion in this gate.
For each model compute set precision/recall/Jaccard and actual/predicted count per actual
executed metre. No inference of actual observation for an unexecuted candidate.

## Fixed practical admission thresholds (diagnostic, not statistical significance)

For EACH model independently require ALL:
- At least8 comparisons and2 per order third, no telemetry/set/snapshot integrity errors.
- Overall Spearman(predicted voxels/m, actual voxels/m) >=0.30, nondegenerate ranks.
- Within-third actual utility ordering concordance >=0.60 across at least9 pairs with
  unequal actual utility: predicted tie earns0.5; actual tie omitted; pool pair counts
  across thirds. This mitigates trivial global exploration-stage or length trends.
- Median set Jaccard >=0.25 (empty/empty convention1 reported, not dropped).

Also report count correlations, per-second correlations, each-third statistics,
zero-actual prevalence, paired legacy-vs-shadow changes and all exclusions; these
secondary diagnostics do not override the primary thresholds. With one dependent run,
no confidence interval interpreted as multi-scene/seed significance. No threshold tuning.

## Development decision

- Legacy passes: retained2m evaluator may proceed to bounded I3 methodology, subject
  to execution/unknown-occlusion limitation and fair corrected controls.
- Legacy fails but mapper-shadow passes: conditional support ONLY for sensor-aware
  definition; first port/validate that already-defined geometry in C++ against frozen
  held-out sets before guided route implementation. Do not claim2m online utility validated.
- Both fail with sufficient valid samples: NO-GO for current observation-guidance
  claim; record limitation and reassess bounded method definition, no unrelated modules.
- Insufficient samples / telemetry failure: INCONCLUSIVE, no admission, no favorable
  rerun in this protocol. State the exact missing evidence and propose a separate next task.

No automatic I3 implementation in this task. Finish report, update handoff, push and
make a hash-verified backup including new raw data. Keep prior results immutable.
