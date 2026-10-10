# I2-06 第一项：收益反馈接口修复与冻结实验执行诊断

2026-10-10。**本项完成；I2-06 整体未完成。** 用户要求完成本项后备份停止；
独立场景预测／实际观测排序门槛尚未预注册、采集或通过，不能进入 I3。

## 结论

1. 确认并修复了新 route controls 的实现缺陷：克隆节点评分后未向原 PRM 写回
   `numVoxels/yawNumVoxels`，破坏了 Legacy 的“评分 → 后续目标筛选”反馈。
2. 12 次冻结首轮实验中，seed1 distance_single 和 seed3 generic_k_shortest 的
   长期停滞是持续局部轨迹失败、反复选中相同输入目标；不是进程退出或深度回调停止。
3. **尚未证明上述接口缺陷导致了停滞或 T95 差异。** 不改写 I2-05 数值、失败、
   删失、结论，也不重跑原 seed 追求正结果。既有“无稳定优势”是旧版本的观测事实；
   不能把它当作排除接口混杂后的纯多路线效果，更不能判定观测引导方法成败。
4. 已修复、已编译、24 个 C++ 测试通过；**修复后的在线效果尚未验证**。

## 1. 固定反例与最小修复

源码：`global_planner/include/global_planner/dep.cpp` 中的
`updateInformationGain/getBestViewCandidates/findBestPath`，以及 `routeControls.cpp`。

- 更新器只刷新新节点和历史轨迹附近的有限邻居，不是每轮刷新全部 PRM。
- 目标预筛选读取 live PRM 的缓存收益；Legacy 候选持有这些节点，路径评分直接刷新它们。
- 新控制生成 detached 节点，虽然沿用了相同的预筛选函数和路径收益公式，但评分只修改
  克隆。于是“预筛选代码未变”不代表“预筛选输入更新机制未变”。
- 固定地图反例：原目标缓存设为 999999，Legacy 评分刷新为 89；修复前新控制评分后
  仍为 999999。RED 测试的 XML、日志保留，证明不是根据运行结果猜测出的缺陷。

修复：每轮建立克隆 → 原节点映射，仅在实际路径评分后同步收益字段；不回写 A* 的
`g/f/parent`、邻接关系或新节点标志。合成起点和未评分节点不更新；历史模式／fallback
不启用该映射；规划起止和 fallback 清理映射。日志增加
`gain_feedback_policy=scored_nodes_to_roadmap_v1`。仍以本轮固定快照计算新控制收益，
**没有宣称与 Legacy 的实时地图读取时刻完全相同**。

修复提交：`global_planner` 分支 `fix/i2-06-gain-feedback`，
`3267e3d74bbdb8480ac6ea8ac9f7c26662c45e75`。

验证：
- `route_snapshot_test` 7/7：三个控制模式目标写回、中间节点写回、未评分节点保持、
  A* 状态保持、fallback 不写回，以及已有快照／位姿一致性检查。
- `route_search_test` 7/7；`route_candidates_test` 10/10。
- `dynamic_exploration_node`、`test_dep_node`、`return_home_checks` 依赖目标编译成功。
- 没有修改运动、FoV、停止阈值、evaluator 几何模型、B-spline 权重或原始工作空间。

## 2. 12 次冻结实验只读诊断

输入：`EXP-I2-05-PAIRED-PILOT-V1` 的全部 12 次首轮实验，采集源 `0677947`、
旧 global_planner `99f3122`。分析脚本逐项记录输入 SHA256，分析前后核对；
结果写入新的 `EXP-I2-06-AUDIT-V1`，原始目录不写入。

“持续末段失败”：最后一次成功的局部规划后，全部局部调用都失败，至少 5 次且
距最后 odometry 至少 30 秒。其余 10 次没有这种末段失败，但仍可能有短暂失败。

| 项目 | seed1 distance_single | seed3 generic_k_shortest |
|---|---:|---:|
| 原始状态 | USER_ABORT | TIMEOUT |
| 连续末段局部失败 | 2315 | 1963 |
| 末段持续仿真时间（s） | 470.339 | 435.483 |
| 期间实际飞行距离（m） | 0.0465 | 0.1144 |
| `updatePath` 成功次数 | 2315 | 1963 |
| 输入路径长度范围（m） | 7.331–7.384 | 4.624–4.679 |
| 同一输入目标占比（厘米取整） | 100% | 100% |
| 深度序号推进 | 14073 | 12885 |
| 地图消息计数推进 | 4690 | 4350 |
| accessible 新增观测计数 | 0 | 0 |
| 最后 60s 位置包围盒对角线（m） | 0 | 0 |

两个末段均有不同 global sequence，说明确实在反复请求全局路径，不是单次调用卡死。
地图版本也持续推进；这只能证明处理继续，不能证明有新信息或地图正确。
Coverage 日志按观测增量记录，停滞时可能没有新行；分析采用最后计数前向保持，
没有将“缺少新行”误当成未采集传感器。

整轮日志的 `optimizer_failure/optimizer_timeout/A* failure` 计数分别是
seed1 single **2317/2/1**、seed3 generic **1971/2/0**。文字日志没有逐条 sequence
关联，不能把这些整轮计数硬分配到每一个末段调用。全部 12 轮未见 `process has died`
消息；这只是日志证据，不是对所有异常退出方式的穷尽证明。

## 3. 执行层原因能解释到哪里

`autonomous_flight/.../simulation/dynamicExploration.cpp::plannerCB` 将当前 odometry
和当前路径目标组成两点局部输入，再生成分段直线样本交给 B-spline；并非一次把整条
PRM 路线完整传入优化器。失败且没有可继续执行的轨迹时，再请求全局规划。
没有失败目标记忆，允许重复选中同一目标。这解释了现有日志呈现的失败循环机制。

`trajectory_planner/.../bsplineTraj.cpp::optimizeTrajectory` 在优化轨迹仍有碰撞时
继续引导／调整惩罚，超时或重试超限返回 false；外层统一打印“optimizer not finding
 a solution”。`optimize()` 的 L-BFGS 返回码没有直接用于这项成功判断。因此：

- 不能把这条报错等同于已证明的 L-BFGS 数值不收敛。
- 日志证明 `updatePath` 成功、输入距离不为零，不支持“输入太短／未建立路径”的解释。
- `updatePath → clear` 会清空动态障碍数组，不能声称旧障碍数组必然残留；末段动态
  障碍计数曾达到 2，也不能笼统声称末段没有动态障碍。
- 旧实验没有失败时刻的 occupancy snapshot、优化控制点、逐次碰撞或求解器状态。
  无法还原具体障碍、精确失败分支或修复效果。此处达到本次诊断结束条件。

不在本轮调 B-spline 参数、增加失败规避策略或重放原 seed。这些若未来确需修改，
应有独立协议和实验，不能混入本次收益反馈修复。

## 4. 距离搜索对照

新控制的日志包含同一固定地图上的原 A* 与最短距离参考对照：共 25622 个可比目标，
433 个原 A* 路径长出超过 1 微米，最大差值 0.4648m，全部比较的平均差值 0.001258m。
长期失败期间的重复规划占比很高，样本不是独立样本，均值也不是因果效应。

原 A* 与距离参考并非处处严格等价，但这些数据不能解释任务级的大幅距离／T95 差异。
路线模式还包含固定快照、位姿锁定及本次发现的收益反馈差异；框架对照是必要的。

## 5. 恢复时从这里继续

本轮只完成 I2-06 第一项并备份。剩余：
1. 先预注册唯一独立场景／seed／有限采集时间及预测-实际**单位代价排序**检查，
   明确样本资格、阶段取样、门槛和不足样本的处理；尚未注册，不能声称已通过。
2. 修复版本有限在线检查可与新独立场景采集合并，但必须单列接口健康证据和模型门槛。
   旧 floorplan2 Coverage mask 不适用于新世界，未经新分母验证不得报告 Coverage/T95。
3. 门槛分析、I2 最终决策和后续 I3 是否放行。相关性检查是已执行前缀上的证据，
   不是未执行候选路线的真实反事实排序验证。

新版本不得覆盖冻结 I1-06/I2-05 数据；如以后需要修复后的成对对照，单独注册新 cohort。

复现第一项：
```bash
python3 experiments/analysis/audit_i2_execution.py \
  --batch-root /home/zxr2/cerlab_benchmark_ws/results/EXP-I2-05-PAIRED-PILOT-V1 \
  --output-directory /tmp/i2-06-readonly-reproduction
```

机器可读结果：`I2_06_EXECUTION_AUDIT.json`、`I2_06_VALIDATION.json`。
原始诊断证据：`/home/zxr2/cerlab_benchmark_ws/results/EXP-I2-06-AUDIT-V1/`。
