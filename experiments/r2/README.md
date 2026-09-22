# Phase R2 predicted-versus-actual observation validation

R2 validates whether predicted unique observation corresponds to sensor-observed new
voxels. It remains shadow mode: online route selection, dynamics, Benchmark v2
configuration and the legacy completion threshold 500 stay unchanged.

## Planning and execution identifiers

- `global_sequence`: one successful or failed global DEP planning attempt;
- `trajectory_id`: one local B-spline planning sequence, positive only on success;
- `execution_interval_id`: equal to the successful `trajectory_id` that activated the
  B-spline;
- an interval begins at `trajectory_start_sim` from the successful local planning
  event and ends when another B-spline supersedes it, the mission enters return/home,
  or the logger shuts down;
- odometry and observation deltas outside an active interval keep ID zero and are not
  silently assigned to a nearby plan.

Execution intervals describe activated B-splines, not completed global PRM routes. A
single global route can produce several local trajectories, and replanning can truncate
every level of the predicted route.

## Lightweight files

The Benchmark logger now records:

- `planning.csv`: schema version, global/local IDs, replan reason, map version, depth
  sequence and trajectory start time in addition to existing timing/path fields;
- `trajectory.csv`: odometry/yaw tagged with execution interval and global sequence;
- `execution_intervals.csv`: start/end reason, time, versions, odometry count,
  executed distance and endpoint poses;
- `observation_deltas.jsonl`: every sensor first-observation delta with its exact voxel
  addresses and active interval/global/trajectory IDs;
- `events.jsonl`: explicit interval start/end lifecycle events.

No rosbag is required. Artificial `setFree`/takeoff clearing does not call the sensor
observation tracker and therefore does not enter `ObservedVoxelDelta`; R2-03 will add
explicit consistency checks rather than relying only on this source inspection.

## Current boundary

R2-01 through R2-05 are complete. Actual observation sets are assigned by sensor
message timestamp, while callback-time interval IDs are retained for boundary audit.
Four predicted layers are built on execution-start snapshots and aligned with actual
sets. The legacy proxy shows useful count correlation for odom prefixes but weak exact
set overlap, so H2 remains unproven. See `R2_05_VALIDATION.md` before starting R2-06.
