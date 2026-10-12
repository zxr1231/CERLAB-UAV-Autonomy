# I3-00: sensor-matched frozen camera evaluator, registered before implementation

2026-10-12. Isolated implementation only; no online selection/default/sensor change.
Model ID mapper_matched_frozen_shadow_v1, schema1. Exact reference is existing
sensor_shadow.py, NOT a new idealized FoV cone or full SLAM uncertainty model.

Pinhole rays in row-major v/u order with mapper pixel_skip2, filter margins, normalized
optical vectors; level-body yaw and body_to_camera homogeneous transform. Max Euclidean
range5m. Endpoints outside snapshot rejected (existing reference behavior, no clipping).
Endpoint voxel duplicates keep FIRST pixel ray. Forward DDA omits sensor cell, includes
endpoint, x/y/z strict comparisons with z/y ties identical reference. Known occupancy
stops ray before scoring; Unknown contributes within inclusive region boundaries.
Inflation is collision safety, not physical optical occlusion; do not change reference
set semantics. Prediction cannot know Unknown physical obstacle depths.

Independent per-path prefix union: raw=sum pose sets, marginal=pose set minus prefix,
unique=union, duplication=1-unique/raw. Each candidate owns separate history. Version
mismatch/invalid inputs/budget exhaustion invalidates ENTIRE result, no partial utility.
API accepts fixed pose samples; legacy polyline sampler semantics remain unmodified.
No Edge/map-results cache. Camera ray geometry may be precomputed once per evaluator.

Validation: deterministic synthetic occupancy/yaw/extrinsic/pixel/occlusion/boundary/
Unknown/inflation/repeated-history/budget fixtures; exact C++ versus Python addresses,
raw, marginal, union on ALL12 preregistered I2-06 prefixes, same0.25m/0.1rad odom samples.
Compare previous saved unions independently. No failed sample substitution.

Cost: one warmup+3 fixed repeats on all12 prefixes, timings exclude loading snapshots,
JSON and evaluator ray construction (each separately reported). Admission per-prefix
p95<=250ms and max<=500ms; also fixed30 independent candidate evaluations cycling12
prefixes, elapsed<=500ms for this workload probe. If exact parity passes but workload
budget fails: offline implementation complete, ONLINE cost admission NOT passed.
Do not increase thresholds after measurement. Three repeats not exploration repetitions.
Cooperative wall-time/voxel-operation/sample limits must fail closed. Planning budget
final allocation in I3-01 only after this gate; do not claim online runtime from offline
per-prefix timings alone. No core guided algorithm implementation in this bounded batch.

Backup protocol/code/reports and canonical handoff. Keep I1/I2 frozen data and commits.
