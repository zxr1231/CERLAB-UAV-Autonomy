# I1-01 validation: path-gain contract, modes and logs

Date: 2026-09-22

Status: complete. This task changed interfaces and observability only; candidate
ranking and the legacy completion threshold remain unchanged.

## Frozen configuration

The `/DEP/path_gain` namespace defines:

```yaml
schema_version: 1
mode: legacy
sample_spacing: 0.25
```

Recognized modes are `legacy`, `unique_shadow` and `unique_online`. I1-01 exposes all
three names but sets `unique_evaluator_available=false`; requesting either unique mode
fails during DEP construction. This prevents a declared but unimplemented method from
silently running as Legacy.

The active Legacy mode records `selection_gain_mode=legacy`, and completion continues
to read the existing `bestPathGain` with threshold 500.

## Schema

Global planning events advance from schema 3 to schema 4 and freeze fields for:

- gain schema/configured/selection mode and 0.25 m sampling;
- evaluator availability and status;
- Legacy and Unique selected candidate IDs;
- raw/unique gain, duplicate ratio and evaluation time;
- Top-1 change, score margin and fallback reason.

Uncomputed Unique values are JSON `null` and empty CSV cells. They are never encoded
as zero or false. Diagnostic snapshots also record the path-gain contract and the
explicit Legacy completion mode.

## Verification

- `global_planner`, `autonomous_flight` and `exploration_benchmark` compile;
- three C++ contract tests pass, including invalid schema/spacing and fail-closed
  unimplemented modes;
- all 85 exploration-benchmark Python tests pass;
- all return-home, seed, reachability and threshold-500 checks pass;
- development smoke `EXP-I1-01-CONTRACT-SMOKE`, seed 1/1, reached HOME_REACHED with
  zero collision and no rosbag;
- all 461 global rows used schema 4, `gain_mode=legacy`,
  `selection_gain_mode=legacy`, spacing 0.25 and evaluator unavailable;
- every uncomputed Unique field decoded as JSON null and an empty CSV value;
- smoke global-planning mean/p95 were 11.034/14.563 ms in the small-ROI smoke. These
  are engineering checks and must not be compared with the full-map formal baseline;
- no ROS/Gazebo process remained after the runner stopped.

## Revisions

- `global_planner`: `4b996cf` on `feat/i1-unique-gain`;
- `autonomous_flight`: `3243c9f` on `feat/i1-gain-logging`.

Next task: I1-02. Implement the planner-consistent visible-set/path evaluator while
keeping online selection Legacy.

