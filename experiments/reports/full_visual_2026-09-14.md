# Full visual exploration audit — 2026-09-14

## Protocol

- World: `floorplan2_dynamic_5.world`
- Mode: full exploration with Gazebo GUI and RViz
- Completion rule: reachable roadmap gain at or below 500, confirmed by the
  existing completion gate
- Current seed wiring: the same integer is passed to Gazebo and DEP
- Timeout: 1,200 wall seconds after planning starts
- Rosbag: disabled
- Coverage: unavailable because no verified explorable-space denominator exists

The table separates exploration from return. `Exploration time` ends when the state
first changes to `RETURNING_HOME`. Distance and map-point proxy are sampled at or
immediately before that transition.

## Results

| Run | Exploration outcome | Return outcome | Exploration time (sim s) | Distance at return start (m) | Map-point proxy at return start | Global/local events before return | Global mean / P95 (ms) | Mean RTF |
|---|---|---|---:|---:|---:|---:|---:|---:|
| seed 1 | completed | blocked; user stopped after diagnosis | 449.847 | 189.070 | 1,059,967 | 48 / 215 | 46.843 / 92.034 | 0.998767 |
| seed 2, run 1 | completed | home reached in 32.215 s | 423.761 | 181.684 | 1,063,770 | 38 / 173 | 49.584 / 92.656 | 0.998937 |
| seed 3 | completed | home reached in 14.045 s | 453.758 | 185.117 | 1,069,081 | 40 / 183 | 48.615 / 96.474 | 0.998876 |
| seed 2, run 2 | completed | home reached in 22.626 s | 454.414 | 198.567 | 1,066,453 | 37 / 212 | 46.163 / 89.065 | 0.998913 |

The three distinct-seed runs have the following exploratory statistics. These values
are development evidence from one scene, not paper-level confidence intervals.

| Metric | Mean | Sample standard deviation | Range | Coefficient of variation |
|---|---:|---:|---:|---:|
| Exploration time (sim s) | 442.455 | 16.307 | 423.761–453.758 | 3.69% |
| Distance at return start (m) | 185.290 | 3.696 | 181.684–189.070 | 1.99% |
| Map-point proxy at return start | 1,064,273 | 4,578 | 1,059,967–1,069,081 | 0.43% |
| Global planning events | 42.0 | 5.29 | 38–48 | 12.60% |
| Global planning mean time (ms) | 48.347 | 1.390 | 46.843–49.584 | 2.88% |
| Mean real-time factor | 0.998860 | 0.000086 | 0.998767–0.998937 | 0.009% |

All four runs reached the planner's near-completion condition. Three of four returned
home. Among the first run for each distinct seed, exploration completion was 3/3 and
return success was 2/3. The sample is too small to estimate a reliable success rate.

## Seed-2 repeatability

The repeated seed-2 run used the same world, code, configuration, Gazebo seed, DEP
seed, GUI mode, and stop rule. It reached exploration completion and home in both
runs, but was not an identical replay.

| Metric | Run 1 | Run 2 | Relative change |
|---|---:|---:|---:|
| Exploration time (sim s) | 423.761 | 454.414 | +7.23% |
| Distance at return start (m) | 181.684 | 198.567 | +9.29% |
| Map-point proxy at return start | 1,063,770 | 1,066,453 | +0.25% |
| Final mission distance (m) | 196.708 | 204.548 | +3.99% |
| Final map-point proxy | 1,064,646 | 1,069,152 | +0.42% |
| Global planning events before return | 38 | 37 | -2.63% |
| Local planning events before return | 173 | 212 | +22.54% |
| Global mean planning time (ms) | 49.584 | 46.163 | -6.90% |
| Mean RTF | 0.998937 | 0.998913 | -0.0024% |

The first recorded best-path gain was 1,922 in run 1 and 1,912 in run 2. The
configured seed controls explicit pseudo-random streams, but asynchronous depth,
odometry, map-update, and planning callbacks change the state at which random samples
are consumed. Fixed seeds therefore support controlled repeated trials; they do not
guarantee bitwise-identical end-to-end ROS/Gazebo trajectories.

## Seed-1 return failure

Seed 1 changed to `RETURNING_HOME` at simulation time 453.107 s after completing the
gain-based exploration criterion. A return path to home was produced, but B-spline
trajectory generation failed. The vehicle stopped near
`(-3.155, -6.086, 0.835)` while the state alternated through `RETURN_BLOCKED` and
`RETURNING_HOME`. The user stopped the run after the position remained unchanged
during repeated recovery attempts.

The final log contains 2,052 return events and 2,275 local events, versus 263 total
planning events before return. Those retry events must not be included in exploration
planning-load comparisons. This run is classified as:

- exploration: completed;
- return: failed/blocked;
- runner outcome: `USER_ABORT` as explicitly requested after diagnosis.

The return failure does not invalidate the seed-1 exploration measurements, but it
does show that mission-level return reliability is not yet robust.

## Interpretation and limits

The endpoint map-point proxy was consistent across these runs, while completion time,
path length, and local replanning count varied more. This is compatible with the
planner reaching a similar low-gain state through different trajectories. It is not
evidence of equal coverage because map-point count includes implementation-specific
map contents and has no verified denominator.

Global planning averaged about 48 ms in the three distinct-seed runs, with per-run
P95 values between 92 and 96 ms. Local planning before return had mean/P95 values of
2.320/29.672 ms for seed 1, 0.459/1.476 ms for seed 2, and 0.966/2.062 ms for seed 3.
Seed 1 therefore also contained substantially heavier local-planning outliers before
the return failure.

No process crash was observed. Collision count, CPU, and memory were not instrumented
in this dataset, so no numerical claim is made for them. GUI/RViz were enabled and
should be disabled for formal timing experiments. Before external-baseline studies,
the benchmark should split `environment_seed` from `planner_seed`, add a verified
coverage denominator, collision events, resource sampling, and headless batch runs
with at least ten seeds.
