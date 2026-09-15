# Benchmark v2 metric specification

Status: frozen draft for the floorplan2 prototype. Any semantic change must increment
the schema version and regenerate masks; old and new schemas must not be aggregated.

## Coordinate and grid convention

All evaluation masks use the map frame and exactly match `map_manager` indexing:

\[
i_k(p)=\left\lfloor\frac{p_k-o_k}{r}\right\rfloor,
\qquad
p_k(i)=o_k+(i_k+0.5)r.
\]

For the current configuration, `o=(-20,-20,-0.1)` m and `r=0.1` m. Map index bounds
are half-open. The task box contains voxel centers inside the outer collision AABB of
`Wall_0`, `Wall_2`, `Wall_4`, and `Wall_6`, with vertical bounds `[0,2.5]` m. This
separates the roughly 20 × 20 m building from the 40 × 40 × 3 m reserved map.

Static masks are generated only from the `floorplan2` collision geometry. The ground
plane is outside the vertical task interval, and the five moving persons are excluded
from the static denominator.

## Ground-truth sets

Let `G_task` be task-box voxels and `O_static` be voxel centers inside any static
floorplan collision box.

- `F_accessible`: the six-connected component of `G_task \\ O_static` containing the
  start position `(0,0,1)`. Its volume is the primary denominator.
- `S_static`: voxels in `O_static` with a six-neighbor in `F_accessible`. It represents
  observable static surfaces without counting wall interiors.
- `F_flight`: the start-connected subset within altitude `[0.7,1.2]` after box
  inflation by `ceil(robot_size/(2r))`. It is a feasibility mask for camera-pose
  generation, not a Coverage denominator.
- `F_observable`: the subset of `F_accessible` visible from at least one valid pose in
  `F_flight` under the mapping camera model. This remains a planned diagnostic until
  the oracle-visibility stage is implemented.

The mask generator must reject unsupported collision geometry rather than silently
dropping it. Each mask records source/config hashes, dimensions, counts, volumes, and
a canonical content hash.

## Actual observation provenance

`V_sensor(t)` is a monotonic union of voxel addresses actually processed by valid
depth raycasts up to simulation time `t`:

- a valid in-range depth marks traversed free voxels and its hit endpoint;
- zero depth or depth beyond the configured maximum marks only the truncated free ray;
- depth below the minimum is ignored, matching the current mapper;
- clipped map/range endpoints are not occupied hits;
- repeated rays and repeated frames do not increase the union.

Calls to `setFree()`, `freeRegion()`, or `freeRegions()` never set sensor provenance.
This excludes both the initial `free_range=[1,1,1]` cube and periodically cleared
dynamic-obstacle boxes. A later genuine ray through such a voxel may still mark it as
observed.

Actual observations accumulated during takeoff are valid. Coverage time has origin at
the third official confirmation (`PLANNING_ACTIVE`); the value at time zero may be
greater than zero because valid sensor observations can precede planning. The runner
must publish or record this time origin explicitly instead of inferring it from the
current `EXPLORING` state.

## Primary and secondary metrics

Primary free-space Coverage is

\[
C_{free}(t)=\frac{|V_{sensor}(t)\cap F_{accessible}|}{|F_{accessible}|}.
\]

Static-surface Coverage is reported separately:

\[
C_{surface}(t)=\frac{|V_{sensor}(t)\cap S_{static}|}{|S_{static}|}.
\]

For comparison with FALCON-style reporting, the benchmark also records actual known
volume inside the task box,

\[
V_{known}(t)=|V_{sensor}(t)\cap G_{task}|r^3,
\]

in cubic metres. `V_known` is not a percentage and is not substituted for
`C_free`.

T80, T90, and T95 are the first planning-relative times at which `C_free` crosses
0.80, 0.90, and 0.95. Linear interpolation is applied only between adjacent monotonic
samples. If a threshold is never reached, its value is `null` with
`censored=true`; timeout must not be inserted as the threshold time.

Algorithm completion, exploration completion, return start, return success, timeout,
collision, and process failure remain separate events. A return failure after the
algorithm completion event does not erase valid exploration measurements.

## Collision metric

The quadcopter collision mesh has a Gazebo contact sensor that publishes
`gazebo_msgs/ContactsState`. Collision measurement begins at `PLANNING_ACTIVE`;
contacts during spawn and takeoff are excluded. Consecutive contact messages belong
to one collision episode until there has been a 0.1 s simulation-time quiet period.
The primary safety values are whether any episode occurred and the episode count,
reported separately for exploration and return. Contact pairs, duration, maximum
reported wrench norm, and penetration depth are diagnostics. Wrench and penetration
values depend on the Gazebo/ODE contact solver and must not be compared with another
physics engine without calibration. A zero-collision run is valid only if contact
messages were received after planning began.

## Resource metric

At 1 Hz wall time after `PLANNING_ACTIVE`, the Runner reads Linux `/proc` for the
complete descendant trees rooted at its simulator, exploration, and logger launch
processes. The exploration tree is the primary algorithm resource scope; simulator
and logger loads are reported separately. CPU percentage is summed process CPU time
over wall time, where 100% equals one fully occupied logical core and multi-threaded
loads can exceed 100%. RSS is the sum of per-process resident pages; shared pages may
therefore be counted more than once. Formal comparisons disable RViz and use the same
host, build type, sampling interval, and background-process policy.

## Fair comparison rules

- Evaluation masks, sensor model, task box, dynamics, start pose, time origin, timeout,
  and environment seed set are identical for all algorithms.
- `environment_seed` and each algorithm's `planner_seed` are recorded separately.
- GUI/RViz are disabled for formal timing runs.
- Each scenario/algorithm uses at least ten environment seeds; failures are retained.
- Success rates are reported separately from conditional time/path statistics.
- PRM path, commanded B-spline, and executed odometry distance remain distinct.
- Collision episodes and resource scopes use the definitions above for every method.

## External reference check

FUEL defines completion as absence of frontiers and reports exploration time and
executed flight distance over repeated runs. FALCON defines the task as mapping the
accessible subspace of a bounded volume, uses a task bbox distinct from map bounds,
and reports Coverage in cubic metres. Its released `publishMapCoverage()` counts
non-Unknown voxels inside the task bbox and multiplies by voxel volume. Benchmark v2
retains that raw-volume metric while adding a fixed ground-truth denominator and
sensor provenance required by CERLAB's artificial clearing behavior.

Primary sources:

- FUEL paper: https://arxiv.org/abs/2010.11561
- FALCON paper: https://arxiv.org/abs/2407.00577
- FALCON map coverage implementation at commit `312eb4d`:
  https://github.com/HKUST-Aerial-Robotics/FALCON/blob/312eb4d32c6c7af1a482f94a0a204aa2bb150cca/falcon_planner/voxel_mapping/src/map_server.cpp#L817-L838
