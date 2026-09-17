# V2-06 collision and resource validation

Date: 2026-09-15

## Measurement design

The quadcopter collision mesh now has a 50 Hz Gazebo contact sensor. The logger
ignores contacts before `PLANNING_ACTIVE` and merges repeated messages into episodes
using a 0.1 s simulation-time quiet period. A zero-collision result is valid only
when post-start contact messages were received.

The Runner samples Linux `/proc` at 1 Hz after `PLANNING_ACTIVE`. It recursively
follows the process trees rooted at the simulator, exploration, and logger launch
PIDs. This is required because ROS launch gives child nodes their own process groups.
CPU 100% represents one logical core. RSS is summed across processes and can count
shared resident pages repeatedly.

## Positive contact check

A simulator-only check observed the spawned quadcopter mesh contacting
`ground_plane::link::collision`. The message contained collision names, total wrench,
contact positions, normals, and penetration depths. This contact occurred before
takeoff and is intentionally outside the benchmark measurement interval.

## Clean runtime check

- Parent commit: `082c55c25cab521977a723017cf8e6261ff0d9fb`
- `uav_simulator` commit: `cc8c8a6dce0214d9ba99a3189272f05dc8807d24`
- Environment seed / planner seed: `1 / 1`
- Mode: small-ROI smoke, RViz disabled
- Outcome: `HOME_REACHED`
- Wall duration: 90.26 s
- Run and logger schema: 3
- Manifest Git status: clean
- Post-start contact messages: 3,924
- Collision episodes: 0, status `VALID`
- Resource samples: 78 per component
- Negative CPU deltas: 0
- Exploration tree: 8 processes; mean CPU 121.79%; mean RSS 422.26 MiB
- Simulator tree: 11 processes; mean CPU 128.92%; mean RSS 864.26 MiB
- Logger tree: 2 processes; mean CPU 18.48%; mean RSS 99.13 MiB
- Coverage: valid, `PROVISIONAL_ACCESSIBLE_FREE_V1`
- Trajectory metrics: `VALID`
- Residual ROS/Gazebo processes: 0

Raw run:
`/home/zxr2/cerlab_benchmark_ws/results/EXP-BENCH-V2-V2-06-CLEAN/environment_seed_001/planner_seed_001/20260915T210811`

These smoke values validate measurement behavior. They are not algorithm performance
results and must not be used as paper evidence.

## Verification

- Clean Release workspace build passed.
- Workspace test summary: 29 tests, 0 failures.
- URDF-to-SDF conversion retained the contact sensor and its collision reference.
