# I1-02 validation: frozen-map C++ unique-gain evaluator

Date: 2026-09-22

Status: complete for the evaluator foundation. Online route selection remains Legacy;
frozen-fixture C++/Python agreement is the next I1-03 gate.

## Implementation

`global_planner::PathGainEvaluator` evaluates one immutable
`OccupancyMapSnapshot`. Its visible set uses stable global voxel addresses and mirrors
the frozen planner proxy:

- planner 2 m range and horizontal yaw cone;
- baseline vertical z scan envelope;
- planning ROI clipping;
- Unknown voxels are targets but do not occlude other Unknown voxels;
- inflated occupancy blocks visibility;
- viewpoint/target outside the frozen map fail closed;
- `dmin` remains unapplied, matching the existing planner behavior.

Polyline paths are sampled at the configured 0.25 m interval without duplicating
shared segment endpoints. Intermediate yaw follows the outgoing segment; the terminal
uses the existing best-yaw rule. Each candidate obtains an independent history set and
produces sample count, raw gain, unique gain, per-sample marginals, duplicate ratio,
estimated execution time and unique utility.

`unique_shadow` is now an evaluable mode. It captures one snapshot for all candidates,
computes the counterfactual Unique ranking and fills schema-4 fields, but leaves
`selection_gain_mode=legacy`. `unique_online` remains unavailable and fail-closed.

The evaluator rejects an expected map version that differs from its immutable
snapshot. Later live map updates do not invalidate the completed result because the
entire evaluation reads the recorded snapshot version, which is emitted as
`unique_map_version`.

Diagnostic snapshots include candidate raw/unique/marginal results when shadow
evaluation is active. No Edge cache was introduced.

## Verification

- `global_planner`, `autonomous_flight` and logging dependencies compile;
- three contract tests and three evaluator tests pass;
- evaluator fixtures cover stable addresses, Unknown transparency, inflated wall
  occlusion, repeated observation, raw/unique/marginal invariants, repeatability,
  invalid spacing and expected-version mismatch;
- all 85 exploration-benchmark Python tests pass;
- all return-home, seed, reachability and threshold-500 checks pass;
- no ROS/Gazebo process remains;
- no live `unique_shadow` exploration was run in I1-02. That requires I1-03 reference
  agreement before I1-04 live validation.

## Revisions

- `global_planner`: `219162f`;
- `autonomous_flight`: `e41b350`.

Next task: I1-03, which must compare C++ results against the Python 0.25 m reference on
the retained frozen fixtures and expand yaw/ROI/zero-length boundary tests.

