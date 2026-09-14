# Benchmark MVP validation

Validation was performed on Ubuntu 20.04 with ROS Noetic, using the headless
`return_home_smoke.launch` configuration and `completion_gain_threshold=500`. All
successful runs used parent commit `291c12b947f7ad39ade2fdff6b08be3758047d0a`
and the submodule commits recorded by each `run.json` manifest.

## Multi-seed smoke runs

| Seed | Run timestamp | Result | Mission sim time (s) | Mission odometry distance (m) | Final map-point proxy | Planning events | Mean RTF |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | 2026-09-14 15:13:47 CST | `HOME_REACHED` | 66.803 | 11.725 | 230,838 | 23 | 0.999185 |
| 2 | 2026-09-11 14:32:40 CST | `HOME_REACHED` | 49.372 | 9.238 | 191,109 | 18 | 0.999286 |
| 3 | 2026-09-11 14:37:56 CST | `HOME_REACHED` | 76.838 | 19.835 | 237,494 | 35 | 0.999240 |

These are smoke-test results, not paper performance results. The map-point field is
only a message-size proxy. It is not exploration coverage and cannot be used to
derive T80, T90, or T95 without a verified evaluation region and explorable-space
denominator.

## Repeated seed 1

An earlier seed-1 run on 2026-09-11 also reached `HOME_REACHED`. The first global
planning event in both runs selected a best path gain of 2,418, showing that the
configured seed reaches the DEP random generator. The full runs diverged afterward:

| Metric | 2026-09-11 run | 2026-09-14 run |
|---|---:|---:|
| Total odometry distance (m) | 10.915 | 12.616 |
| Global planning events | 10 | 13 |
| All planning events | 19 | 23 |
| Final map-point proxy | 194,383 | 230,838 |

The seed therefore controls the explicit DEP and Gazebo random streams but does not
make the complete ROS/Gazebo execution bitwise deterministic. Thread scheduling,
sensor/map callback order, and planning trigger timing remain uncontrolled. Formal
experiments must use multiple seeds and report distributions instead of treating one
seed as an identical replay guarantee.

## Preserved failures and cleanup

Failed run directories are retained beside successful runs. The MVP validation set
contains an early runner implementation error and odometry-readiness timeouts. Each
has `run.json` with `status=FAILED`, a `runner_result.json`, process logs, and a
`RUNNER_STOPPING` event. Post-run process audits found no remaining ROS Master,
Gazebo, exploration, controller, RViz, or benchmark logger processes.

One timeout on 2026-09-14 was caused by the restricted execution sandbox denying
network-interface enumeration before `roslaunch` started. A later cold-start timeout
registered the Gazebo odometry publisher without delivering the throttled readiness
topic. Both failures remain recorded; a subsequent clean diagnostic verified
advancing `/clock` plus real messages on `odom_raw` and `/odom`, followed by the
successful seed-1 repeat above.
