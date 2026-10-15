# 当前候选选题定稿：不批准 A/B 为论文主方法

日期：2026-10-15。状态：**DECISION_COMPLETE_NO_APPROVED_TOPIC**。
核查基准：父仓库 f0cff66，global_planner 0221483，autonomous_flight 33422e2。
本任务只作最终去留决定；无算法修改、编译、仿真或新实验数据。

## 1. 最终决定

本次限定比较现有两个候选：A（执行前缀感知的候选排序，含 A-lite）和
B（短期观测与长期探索协调）。**两个都不批准为新的 SCI/EI 论文主方法，不启动 I4。**
这是一项已经结束的否决决定，不是“等再诊断一次才能决定”。不再保留自动筛选、
补测、调参或给这两项增加模块的待办。I3 原型继续维持 METHOD_NOT_SUPPORTED。

我没有找到同时满足“明确方法差异、当前缺陷证据、实现可控”三项要求的新方案。
不能为了兑现“下次就编码”而把工程适配写成论文创新。此次未选出可进入核心开发的题目，
也不代表无人机探索方向不存在可研究问题。

不要求实现前证明性能一定提高；允许实验有风险。这里未通过的是**方法差异的定义**，
不是因为没有预先获得正结果，也不是用顶会标准否定渐进改进。

## 2. 两个候选的明确取舍

| 候选 | 确定可实现的内容 | 尚不能支撑立项的原因 | 决定 |
|---|---|---|---|
| A / A-lite | 根据当前运动与转向状态，估计共同时间窗内观测，重排现有候选；无效则 Legacy 回退 | 动力学、yaw、有限时域和轨迹观测已有明确先例；匹配 CERLAB 先转向再平移仍是执行适配，未定义超出这些思想的机制 | 不作为论文主方法实施 |
| B | 在 A 上保留全局目标或加入长短期协调 | A 已有远程回退；加权融合未形成独立机制；全局引导局部访问已有更完整方法，实施和归因成本更高 | 不实施 |

不能用新名称、额外 alpha、按速度改变时间窗、换成真实 B-spline 预演自动解决上述问题。
本次也不把“失败记忆/黑名单”“普通缓存”等临时替代点列为新选题，避免更名后继续循环。

## 3. 本地证据及因果边界

- [I3 最终报告](../i3/I3_03_02_REPORT.md)：扩展32状态下，观测引导对几何多路线
  为1胜31平0负；预算完整率54/111。已实现的原型不支持继续，不能由少数正例复活。
- [I2 执行诊断](../i2/I2_00_DIAGNOSTIC_REPORT.md)：51次改变选择中19次未执行到0.5m。
  这说明需要区分预测与执行，但不证明远期收益导致失败，也不证明短前缀排序优越。
- 同报告的222次重复规划中，两种排序始终选择同一目标，日志直接触发是局部目标不安全。
  尚不能据此把收益重排当成停滞修复，更不能把黑名单修复直接称为论文算法。
- 本次重读 `autonomous_flight/include/autonomous_flight/simulation/dynamicExploration.cpp`
  的 `replanCheckCB()`：接收全局结果会停止并处理路点；执行途中仍可能只局部重规划，
  全部路点完成后才申请新的全局路径。局部更新不等于全局后半程必然作废。
- 当前 `bsplineTraj` 为有状态规划接口；对所有候选预演真实轨迹不是小改评分公式。
  该工程代价本身不增加论文创新性。具体接口见[前次源码审核](A_B_METHOD_REVIEW_2026-10-14.md)。

## 4. 原始论文和作者代码的最终核查

本次联网日期2026-10-15，检索包含2025–2026；以下区分全文/源码与摘要证据。
没有穷尽全部论文，不作“确定撞车”或“保证没有类似工作”的声明。

| 原始来源 | 本次核查范围与事实 | 对候选的影响 |
|---|---|---|
| [FUEL 论文](https://arxiv.org/abs/2010.11561)；[作者 manager 源码](https://raw.githubusercontent.com/HKUST-Aerial-Robotics/FUEL/main/fuel_planner/exploration_manager/src/fast_exploration_manager.cpp) | 源码111–143全局tour/局部精化；207–255计入yaw时间下界、远目标截取路径、使用当前运动状态生成轨迹及yaw规划 | A的执行约束与B的分层协调不是空白；不声称FUEL采用同一个前缀gain公式 |
| [FALCON 全文](https://arxiv.org/html/2407.00577v2) | §V-B以带访问次序约束的SOP把局部frontier插入全局引导；式1–7估算含运动与yaw的时间成本；§V-C生成B-spline | B需要区别于具体全局约束机制，单纯短长时域融合不足；A的运动时间估算也不能单独作为差异 |
| [Active 3D Planning](https://arxiv.org/abs/1909.09548)；[作者评价器](https://raw.githubusercontent.com/ethz-asl/mav_active_3d_planning/master/active_3d_planning_core/src/module/trajectory_evaluator/simulated_sensor_evaluator.cpp) | 本次读论文摘要与评价器；轨迹可见体素、可选父链去重；父链去重不是默认开启 | 轨迹可见集合与history去重是可复用基础，不能作为A新增主贡献 |
| [Goel/Corah/Michael 原文入口](https://publications.ri.cmu.edu/fast-exploration-using-multirotors-analysis-planning-and-experimentation) | 本次机构摘要：动力学动作、滚动时域信息增益、时域长度及重规划频率实验；此前核查记录保留 | 有限执行时域结合信息收益不是新的研究空白；不据摘要断言与A完全相同 |
| [Kinodynamic Trajectory Planning for Efficient UAV Exploration and Reconstruction of Unknown Environments](https://researchportal.ulisboa.pt/en/publications/kinodynamic-trajectory-planning-for-efficient-uav-exploration-and/) | 2026 RA-L，DOI 10.1109/LRA.2025.3641147；仅作者机构摘要，涉及kinodynamic RRT、IMG及yaw优化，未核全文/代码 | 近期近邻提醒，不能只用“动力学+观测”主张创新；本条不单独作为否决依据 |

这些工作不证明 A/B 与任一论文逐项完全相同。否决依据是：当前候选说明没有给出
在这些先例之外、能明确实现和单独消融的新增机制，而不是“别人也用了相同关键词”。

## 5. 不再追加的工作

不重跑 I3；不做 A/B 的试探seed；不先写一堆评价器再决定算法；不添加
Confidence、语义、能耗或回环；不调整旧数据、门槛和停止规则来得到正结果。
因为没有批准算法，本次不虚构候选数、H、权重或通过率，写出一份看似完整的实验协议。

保留 Legacy+返航500、Benchmark v2、评价器、执行日志和所有负结果。这些是已完成的
工程与研究资产，但不等于已经具备足以投稿的方法贡献。

## 6. 后续执行状态

**当前没有自动待执行的创新算法任务。** 本次选择工作结束，不再自动开启新一轮选题。
如果后续单独授权工程改进，A-lite可以作为工程功能实现，但应明确它没有通过论文立项，
不能用工程测试替代新颖性定义。若要求继续以方法论文为目标，需要一项由用户另行确认的
研究问题变更；本文件不把该条件变成循环审核待办，也不建议立即追加实验。

本次交付：本决定、总体交接/索引更新、本地提交与校验备份。未推送GitHub。
