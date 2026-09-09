# Exploration Return Home

This branch adds automatic return to the recorded takeoff XY/yaw at the configured takeoff altitude. It hovers after arrival and does not land.

Completion is a runtime condition: the selected path and every node in the current reachable sampled PRM have fresh information gain at or below the configured threshold. The current simulation default is 500 voxels. It is checked across at least three observations and five simulation seconds. A path-planning failure, empty roadmap, stale depth input, or gain above the threshold cannot alone trigger return. This event is not proof of ground-truth map coverage or a literal 98% measurement.

Return paths use known inflated-free connections, directly when possible and via the existing PRM otherwise. Failed return planning results in hover and retry. The original B-spline and dynamic-obstacle handling execute the path.

If globally prefiltered high-gain goals are disconnected, the planner connects the current pose to all nearby known-free PRM nodes and refreshes fallback candidates inside the reachable component. This recovery runs only after all normal candidates fail.

State topics:

- `/dynamicExploration/home`
- `/dynamicExploration/mission_state`
- `/dynamicExploration/return_path`

Mission states include `EXPLORING`, `CONFIRMING_COMPLETE`, `RETURNING_HOME`, `HOME_REACHED`, and explicit exploration/return blocked states.

Build and run from the containing catkin workspace:

```bash
bash src/CERLAB-UAV-Autonomy/scripts/build_return_home.sh
bash src/CERLAB-UAV-Autonomy/scripts/run_return_home.sh simulator
bash src/CERLAB-UAV-Autonomy/scripts/run_return_home.sh rviz
bash src/CERLAB-UAV-Autonomy/scripts/run_return_home.sh exploration
```

The exploration terminal retains the three official Enter prompts. `record_rosbag` and `enable_keyboard_control` remain false by default.

`return_home_smoke.launch` limits the planner ROI to 6×6×0.5 m without forcing completion. Two recorded runs naturally reached zero gain and returned. `return-smoke-001` flew 4.163 m from home and held for ten seconds with 0.01124 m maximum error. The final-binary run `return-smoke-002` flew 3.370 m from home and held with 0.01677 m maximum error. Both monitors reported `passed=true`. This validates the small-ROI simulation chain, not full-world coverage or real-flight safety.

Deterministic checks are available as:

```bash
source devel/setup.bash
rosrun autonomous_flight return_home_checks
```

All 22 checks pass. They cover completion gating, direct return, PRM detour, blocked/unknown/out-of-map home, remaining reachable gain, empty roadmap, already-at-home, multiple current-pose connectors, and disconnected global-goal recovery.

Full-range failures are retained. The first exposed a local-trajectory recovery gap; the second exposed disconnected global gain candidates; strict zero gain then ran for 1200 seconds without completing. Those findings produced the recovery fixes and the operational threshold of 500.

The subsequent full `floorplan2_dynamic_5` validation passed. It refreshed 338 reachable nodes, entered `CONFIRMING_COMPLETE` at simulation time 451.309 s, `RETURNING_HOME` at 456.845 s, and `HOME_REACHED` at 490.995 s. The UAV traveled as far as 12.287 m from home and held for ten seconds after return with 0.01033 m maximum error. Final explored-map topic size was 1,066,087 points; all critical nodes responded, no process crashed, and rosbag/keyboard control remained disabled. Raw monitor results are in `/home/zxr2/cerlab_return_ws/results/return-full-threshold-500-001/`.
