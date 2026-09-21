# R2-01 / R2-02 validation

Date: 2026-09-21

Status: complete. Logging only; no online decision changed.

## Implemented

- map mutation version exposed through a locked read;
- global/local planning events upgraded to schema 3 with map version and depth sequence;
- successful local events include trajectory start time and explicit replan reason;
- reasons currently distinguish new global path, next waypoint, static collision,
  dynamic collision, distance progress, dynamic-obstacle periodic replanning and local
  dynamic-collision retry;
- ROS-independent execution interval tracker with fail-closed time validation;
- odometry tagged by active interval/global sequence;
- every `ObservedVoxelDelta` recorded even when no Benchmark coverage mask is loaded;
- active interval association stored on every delta;
- interval summaries and start/end events flushed incrementally;
- shutdown callbacks ignore messages after file closure.

The full exploration benchmark regression contains 59 passing tests. Modified
map_manager, exploration_benchmark and dependent autonomous_flight packages compile.

## Live smoke

The first smoke exposed a planning CSV header mismatch. It produced interval/delta
data but planning rows failed, so that directory is retained as a failed fixture and
excluded. After fixing the header, a fresh seed-1 no-GUI smoke produced:

- 51 planning rows, all schema 3;
- 43 closed execution intervals, all marked valid;
- 1,416 observation-delta messages;
- 1,315 deltas associated with an active execution interval;
- 443,700 associated first-observation addresses;
- observed replan reasons: `new_global_path`, `next_waypoint`, and
  `dynamic_obstacle_periodic`;
- interval termination by B-spline replacement and controlled logger shutdown.

Unassociated deltas are retained with interval ID zero. They primarily cover startup,
takeoff, rotations or gaps without an active successful local trajectory; R2-03 must
define whether each category enters the actual-observation denominator.

Passing-fixture hashes:

| File | SHA-256 |
|---|---|
| `execution_intervals.csv` | `95c79a52279b62d6b71659dc8664a031ffa890326880bea9fce4b5acea3772a7` |
| `observation_deltas.jsonl` | `dda913502f38d5a1495ef2655b2b11fd497323426d10fdab089ad39328499566` |
| `planning.csv` | `6b8d1a3a2ec9c318311ef5cfabb2631066c012795ea32b59b30a96bd00577f1f` |
| `summary.json` | `c505f4747f080b98173990082cb7d461adfb4638002b3123703fbd9d5076e0c5` |

## Remaining limitations

- callback arrival order at a trajectory boundary still requires an R2-03 boundary
  audit using message timestamps;
- logger shutdown leaves end map/depth versions empty because no final planner event is
  available; the interval remains valid and is labelled `LOGGER_STOPPED`;
- replan reasons describe the trigger for local planning, not a guarantee that the
  previous B-spline was unsafe;
- the smoke was stopped manually and is not a completed exploration experiment;
- no predicted set, actual set union, Jaccard, precision, recall or correlation has yet
  been computed.
