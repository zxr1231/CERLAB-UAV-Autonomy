# I2-03 — Geometric candidate controls

Date: 2026-10-08. Isolated implementation; no online exploration experiment.
Branch: `feat/i2-route-controls` in parent and global_planner.
Protocol: I2_GENERIC_ROUTES_V1; original JSON/limits unchanged.

## Implemented

`routeCandidates.h` prepares a single immutable feasible pool for either selection
method. API has no gain/observation field. Goal terminal yaw is an externally frozen
per-Goal input, shared by all alternatives; selection never queries best-yaw gain.
Live PRM stable IDs, snapshot callback and terminal-yaw export remain I2-04 work.

Raw route structure/directed edges and known-free lines are validated, then the
original DEP greedy geometric shortcut order is reproduced using a caller-supplied
snapshot line-check adapter. This is ordinary geometric shortcut, NOT the later
observation-preserving proposal. Prepared candidates record raw and simplified
length, total yaw and estimated time (length/speed + yawPenalty*yaw/angularSpeed).
Wrapped angular distance is mathematically the baseline shortest angular difference;
exact floating-point correspondence to its acos implementation remains an integration
check, especially at motion-limit boundaries. Finite valid dynamics are required.

Both raw and simplified metrics are limited against their corresponding reference
by length <= 1.25x, time <= 1.25x and yaw <= reference + pi/2. Tests also use explicitly
looser limits to isolate geometry from constraints; those are not experiment configs.
Zero-length references admit no extra routes. A failed reference cannot be replaced
silently by an alternative. Unsafe or invalid candidates retain rejection records.

Raw sequences are deduplicated; simplified ordered position sequences are deduplicated
within each Goal with Euclidean endpoint tolerance 1e-6 m. Counts distinguish input
raw generation, motion-feasible routes (including later duplicates), and distinct
post-shortcut routes. Selection counts are named `selectedPerGoal`, not claimed
actual scoring: actual scored counts must come from I2-04 scoring integration.

Generic selects the shortest simplified feasible route; geometric selects maximum
minimum directed-edge-set Jaccard distance to already selected routes of the SAME
Goal. Distance then lexicographic stable raw node sequence breaks ties. Both use the
same prepared pool/caps. Reference routes are reserved first in stable Goal-ID order;
remaining slots are assigned round-robin. Global caps too small to keep mandatory
references are configuration errors. No duplicate padding or invented candidates.

These details clarify previously unspecified tie/reference/distance conventions;
no outcome-dependent protocol tuning took place. A common pool can yield different
selected routes while keeping the same actual selected count. It can also collapse
to one route after shortcut; that deficit is a recorded outcome, not a hidden failure.

Cooperative cutoff callbacks are checked at alternative start, line-check loops,
before candidate commitment and during selection scans. Expiry discards partial
candidates but retains mandatory references. No callback can preempt a single slow
map-line check/allocation; hard real-time behavior is not claimed. Pool/search cap
and end-to-end deadline wiring remain integration work.

## Verification

Nine correctness tests cover:

- Shared Yen pool, contrasting generic/geometric choices, no pool mutation and
  no observation input.
- Raw duplicates and shortcut collapse with stage counts and honest route deficit.
- Independent raw/simplified length, time and yaw rejection; a route passing raw
  length can fail after shortcut makes the reference shorter.
- Directed Jaccard, endpoint geometry tolerance and ordered route shape.
- Stable Goal order/round-robin/global cap and mandatory references.
- Collision/reference failure, zero-length reference and invalid dynamics.
- Equal-cost/equal-diversity tie broken by stable raw sequence.
- Mid-candidate cutoff cannot commit a partial route.
- Geometric shortcut order on visible/blocked segments.

Catkin and sanitizer results are recorded in I2_03_VALIDATION.json. I2-02's six solver
checks are run once as a dependency regression. No new ROS seed or full simulation
was started. Leak detection remains disabled because of sandbox ptrace limitations.

## Limitations and next task

This establishes internal candidate-selection contracts, NOT actual exploration
improvement or safe flight. Jaccard is graph-edge diversity and can overstate spatial
diversity of nearby routes with different IDs. Snapshot consistency is a required
caller contract, not established by mock line checks. Geometry dedup uses a stable
pool order because tolerance equality is not transitive. Cross-Goal duplicate goals
and map/reset/version checks must be handled by the live adapter. B-spline feasibility,
actual travel, actual observation and candidate counts remain untested online.

Historical planner, defaults, sensor/dynamics settings and frozen I1 evidence remain
unchanged. Next I2-04: snapshot-consistent graph/collision/scoring adapter, explicit
feature flags, log schema linkage and disabled-feature compatibility, followed by
bounded simulation safety smoke. Only then preregister I2-05 pilot runs. No I3 guided
routing or observation-preserving shortcut is introduced in this task.
