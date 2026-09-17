# Benchmark v2 baseline

## Version

- Parent branch: `feat/benchmark-v2`
- Parent base commit: `1716e467e93d338379cb4d0ab102ceb96d72b79d`
- `autonomous_flight`: `57e029b7313630ab903fa5125ab71a8939dda4a4`
- `global_planner`: `c4983761aa08c0e606ee3d56dd44c74ca5b60069`
- `map_manager`: `d8112b85f6ad4e2519b0f34740ff0f6c466bca24`
- `onboard_detector`: `4b4be99ea0697c0c617dd9c256507e94d83a307d`
- `remote_control`: `7e66ca4ad24944d6b168fb1964b298fac042ebd1`
- `time_optimizer`: `0854be3099be7a29fa2f3428a1c8e66da4b1f8ab`
- `tracking_controller`: `7f8f5d77556877169f31c978b3f3bdba0fcb62d2`
- `trajectory_planner`: `a84b491456e4f97d400627e1e2cd07392ac91333`
- `uav_simulator`: `299fcf3df40ecd7216e80f63d2f09166ab7d448a`

## Configuration hashes

| File | SHA256 |
|---|---|
| `floorplan2_dynamic_5.world` | `00e53bf50ddfae89746b4aed70dc60caa1cfdc6c3939c27a32e65eccd8e276a8` |
| `mapping_param.yaml` | `a0efc81649cce8f185ccca775a4820e1d4b23107c30d50868669f2eab215cd9a` |
| `exploration_param.yaml` | `5c937204fa4c1c0b3b6559ce471c52902dd547598aa6c2ea51929f735ee1e504` |
| `flight_base.yaml` | `d8a7878b53b4c22605a687e02fef3e631cb8968f935fd2e2c427cb8c90225997` |
| `start.launch` | `d267b7884c2ddaa40f2cd915bbd6df4ebd13721e1b43862f173a96e75d36d650` |

The baseline uses map resolution 0.1 m, map bounds
`[-20,20) × [-20,20) × [-0.1,2.9)`, DEP flight bounds
`[-20,20] × [-20,20] × [0.7,1.2]`, a 0.5 × 0.5 × 0.3 m robot,
5 m mapping ray length, 2 m DEP gain depth, return-home enabled, and
`completion_gain_threshold=500`.

## Revalidation on branch creation

- Incremental full-workspace Release build: passed.
- Benchmark accounting tests: 5/5 passed.
- Completion gate, return planning, reachability recovery, and seed checks:
  25/25 passed.
- Test-only ROS Master was stopped; no ROS/Gazebo process remained.
