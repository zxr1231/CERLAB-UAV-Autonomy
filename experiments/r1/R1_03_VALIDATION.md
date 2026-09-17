# R1-03 checkpoint: visible unknown voxel set

Date: 2026-09-17

Status: complete for the fixed-snapshot evaluator and one live export/read smoke test.
No online decision path consumes the result.

Implemented:

- immutable map access by global `(x,y,z)` index and stable linear address;
- address/index/voxel-center conversions;
- yaw-aware horizontal FoV and planning ROI filtering;
- DEP-compatible vertical z envelope and Euclidean `dmax` check;
- DEP-compatible inflated-occupied line sampling from target to viewpoint;
- explicit Unknown-transparent behavior and unapplied legacy `dmin`;
- deterministic visible-set SHA-256;
- CLI evaluation of the captured vehicle pose or a supplied pose/yaw.

Correctness tests cover:

1. stable addresses, inverse address conversion, repeat result and hash;
2. an inflated wall blocking an Unknown target;
3. an Unknown intermediate voxel not blocking a farther Unknown target;
4. inclusive yaw/FoV boundary and rear-target rejection;
5. current `dmin` behavior;
6. current vertical envelope behavior;
7. planning-region clipping;
8. fail-closed behavior for an inflated viewpoint.

The three R1-02 format tests remain in the focused suite. All 11 focused tests pass;
the complete `exploration_benchmark/test` regression contains 41 passing tests.

## Live smoke result

A seed-1, `floorplan2_dynamic_5`, no-GUI run exported exactly one snapshot from
planning sequence 1. It contained 4,800,000 map voxels, 7 roadmap nodes, 9 edges, 7
goals and 4 shortcut candidate paths; selected candidate ID was 0. The evaluator found
409 visible Unknown voxels at the captured vehicle pose. Two independent evaluations
returned the same set hash:

`59b749e3804ad8214b6ce2bb7f4f3d388b2f237432631c82e1d7f8d2f77b4721`.

The measured end-to-end Python command took about 5.02 wall seconds and 33,764 KiB
maximum RSS. This includes manifest hashing and scanning a 4.8-million-voxel payload;
it is a smoke measurement, not R1-06 profiling. The local snapshot is ignored by Git
and preserved in the R1-03 backup. Its lightweight metadata is recorded in
`R1_03_LIVE_SMOKE.json`.

The first launch exposed a stale dependent binary after `occMap` changed layout:
`map_manager` and `global_planner` had been rebuilt, but `autonomous_flight` still used
the old ABI and aborted during initialization. Rebuilding `autonomous_flight` and its
dependent libraries resolved it; the repeated launch, export, and evaluation passed.
This was a build-artifact mismatch, not an algorithm result.

Scientific boundary: `legacy_proxy_v1` is a controlled discrete evaluation model. It
does not reproduce the physical camera intrinsics/extrinsics and does not claim that
Unknown-space transparency is physically correct. Its purpose is to isolate set
deduplication from simultaneous sensor-model changes. A later calibration experiment
must compare it with actual observation; R1-03 itself establishes no exploration
improvement.

R1-04 may now compute per-sample sets and raw/unique/marginal path diagnostics. It must
not feed those results into online path selection or the completion threshold.
