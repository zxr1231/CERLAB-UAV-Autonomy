# Floorplan2 static observability audit

Date: 2026-09-16

## Purpose

This audit checks whether the fixed accessible-free and static-surface denominators
contain voxels that cannot be observed from any feasible camera pose. It is independent
of the tested exploration trajectory and does not use a final online map.

## Oracle model

- Candidate body positions: every voxel in `flight_reachable`, z=0.7–1.2 m.
- Body attitude: level roll/pitch with nested uniform yaw sets of 32, 64, and 128.
- Camera transform and intrinsics: exact values from `mapping_param.yaml`.
- Image sampling: margin 2 and vertical pixel stride 2.
- Ray length: 5.0 m, matching `raycast_max_length`.
- Occlusion: deterministic traversal against vertically extruded static floorplan
  occupancy. The generator fails closed if this geometric assumption is violated.
- Dynamic people: excluded because they are transient and already excluded from the
  static denominator.

Arbitrary yaw lets a sampled horizontal camera ray align with each tested azimuth.
The vertical check uses the nearest pixel row and requires its ray to intersect the
target voxel. A visible static surface is the first occupied surface reachable without
another occupied voxel between it and a candidate camera pose.

## Result

| Yaw samples | Observable accessible free | Added from previous |
|---:|---:|---:|
| 32 | 980,550 | 980,550 |
| 64 | 980,550 | 0 |
| 128 | 980,550 | 0 |

- `observable_free = accessible_free`: 980,550 voxels, 980.550 m³.
- `observable_static_surface = static_surface`: 29,375 voxels, 29.375 m³.
- Unobservable accessible free: 0.
- Unobservable static surface: 0.

The v2 mask therefore validates the existing denominators without changing their
counts. This does not mean one trajectory will reach 100% Coverage, and it is not a
model of occupancy confidence, localization uncertainty, dynamic occlusion, sensor
noise, or complete SLAM uncertainty.

## Reproducibility

- Config: `config/floorplan2_static_observable_v2.json`
- Mask content SHA256: `4769621c2dcd395cd2083375fc0bf456aff4447382eba1caa6e15bee1e3201c5`
- NPZ SHA256: `58a21ffbe6bfc7168d3eb9de8762632b82aac702b5c4129e5a73f92565142bc1`
- PNG SHA256: `7883417495abe53d237f7c91452e0b5b7d583b2a486843e466508a50684cba28`

Two independent generations produced byte-identical NPZ and PNG files. Array subset,
partition, equality, and zero-complement assertions passed.

## Online integration check

A clean smoke at parent `d6acf4e` loaded the v2 artifact by default and reached
`HOME_REACHED` in 80.78 s wall time. The manifest was clean and recorded the v2
content hash. Final Coverage status was
`PROVISIONAL_ACCESSIBLE_FREE_V2_OBSERVABILITY_AUDITED`, with:

- `observability_audited=true`;
- observable free/surface fractions 1.0 / 1.0;
- 1,040 contiguous provenance updates and no Coverage error;
- valid collision, resource, and trajectory measurements;
- 3,420 post-start contact messages, zero collision episodes;
- no residual ROS/Gazebo process.

The smoke final free Coverage was 0.2146 because it uses the small ROI. T80/T90/T95
correctly remained censored and null.
