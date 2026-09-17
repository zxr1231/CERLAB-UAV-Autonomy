# Phase R1 observation-gain diagnostics

R1 is an offline diagnostic phase. It does not change candidate selection, online
path scoring, trajectory generation, or mission completion. R1-01 and R1-02 establish
the frozen definitions and reproducible snapshot input required by later gain work.

## Frozen baseline

- parent baseline: `5579ce4` (`feat/benchmark-v2`);
- formal benchmark runtime baseline: `8230c80`;
- `global_planner`: `c498376`;
- `map_manager`: `fa9d45c`;
- R1 development branch: `feat/r1-observation-diagnostics` in the parent and modified
  submodules;
- world, start pose, FoV, speed/acceleration, safety distances, seeds, coverage mask,
  and benchmark stop definitions remain those of Benchmark v2.

The operational return condition remains the legacy `bestPathGain` plus
`reachableGainExhausted()` check with `completion_gain_threshold=500`. Future
`raw_gain` or `unique_gain` values must not feed this gate during R1.

## Frozen gain terms

- `legacy_gain`: the existing `findBestPath()` integer sum. Intermediate nodes use the
  heading of the next segment; the goal uses its best discrete yaw. This value retains
  the current interpolation and sampling behavior.
- `raw_gain`: the sum of visible-unknown set cardinalities produced by the new R1
  evaluator at all sampled poses. It may count the same global voxel more than once.
- `unique_gain`: the cardinality of the union of those same sets. It differs from
  `raw_gain` only by path-history deduplication.
- `marginal_gain[i]`: voxels first introduced by sample `i` relative to samples
  `0..i-1` of that candidate path.
- `duplicate_ratio`: `1 - unique_gain/raw_gain` when `raw_gain>0`; otherwise `0`.

Candidate histories are independent. An unselected candidate never modifies the
history of another candidate or the actual mission history. R1 uses these quantities
only in logs until a later phase is explicitly approved.

## R1 snapshot v1

The planner exporter is disabled by default. When enabled, it writes one directory per
eligible planning sequence. A snapshot contains:

- `map.bin`: map geometry, thresholds, map version, and one occupancy/inflation state
  pair per global voxel;
- `planner.json`: vehicle pose/yaw, sensor and motion parameters, planning ROI, sorted
  PRM nodes/edges, legacy node/yaw gains, candidate goals, shortcut candidate paths,
  the selected candidate index, and legacy selected-path gain;
- `manifest.json`: schema/version linkage and FNV-1a hashes. It is the completion
  marker and is committed with the directory by an atomic rename.

The map copies occupancy and inflation arrays while map writers hold the same snapshot
lock. The resulting value object cannot change after capture. `map_version` must agree
in all three files. The snapshot represents the mapper's discrete legacy state; it is
not proof that the legacy visibility model matches the physical depth camera.

Enable a bounded diagnostic collection before launching exploration:

```bash
mkdir -p /home/zxr2/cerlab_benchmark_ws/src/CERLAB-UAV-Autonomy/experiments/r1/snapshots
rosparam set /DEP/diagnostics/snapshot_enabled true
rosparam set /DEP/diagnostics/snapshot_directory /home/zxr2/cerlab_benchmark_ws/src/CERLAB-UAV-Autonomy/experiments/r1/snapshots
rosparam set /DEP/diagnostics/snapshot_stride 10
rosparam set /DEP/diagnostics/snapshot_max 12
```

The launch file loads `/DEP` parameters after shell-set parameters, so for actual data
collection these four values should be supplied by a dedicated R1 launch overlay or
set after launch and before planning. R1-02 does not start a collection run.

Validate a saved directory with:

```bash
source /opt/ros/noetic/setup.bash
source /home/zxr2/cerlab_ws/devel/setup.bash
rosrun exploration_benchmark inspect_r1_snapshot.py SNAPSHOT_DIRECTORY
```

The reader rejects missing manifests, changed payloads, invalid map states, truncated
payloads, dimension mismatches, and cross-file sequence or map-version mismatches.

## R1-01 and R1-02 acceptance

- baseline revisions and gain definitions are recorded;
- legacy completion threshold remains independent of future diagnostic gains;
- exporter is off by default and cannot overwrite an existing snapshot;
- map and planner data share a captured map version;
- deterministic node/edge ordering and payload hashes support repeatable loading;
- a synthetic round-trip test loads the same snapshot twice with identical output;
- corruption and incomplete-snapshot tests fail closed;
- no online scoring or trajectory code consumes snapshot data.

## R1-03 visible unknown voxel set

R1-03 adds the offline `legacy_proxy_v1` evaluator. Given one immutable map, position,
and yaw, it returns a `frozenset` of stable global voxel addresses. The implementation
deliberately mirrors the current DEP proxy before introducing any sensor-model change:

- target voxel must be Unknown and not inflated occupied;
- target center must lie in the planning ROI and within `dmax`;
- horizontal yaw difference must be at most half the configured horizontal FoV;
- vertical FoV supplies the same z scan envelope used by `calculateUnknown()` rather
  than a pinhole vertical-angle test;
- `dmin` is preserved in provenance but remains unapplied, matching current source;
- inflated occupied voxels block the target-to-viewpoint sampled line; Unknown voxels
  do not block it.

This is an explicit compatibility model, not a claim of physical camera fidelity. It
uses voxel centers rather than DEP's floating scan origin so that every observation has
one stable address. R1-04 must keep sampling-model differences separate from path
history deduplication.

Inspect one pose without changing planner behavior:

```bash
rosrun exploration_benchmark inspect_r1_visibility.py SNAPSHOT_DIRECTORY
```

Optional `--position X Y Z`, `--yaw RAD`, and `--list-addresses` arguments support
controlled fixtures. The default output includes the visible set size and a SHA-256
of sorted 64-bit addresses.
