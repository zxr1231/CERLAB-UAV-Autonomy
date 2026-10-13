# I3-02R：既有单锚点结果的路段归因与研究方向决定

2026-10-13，分析前登记。只读取I3-02A已经保存的参考、14条固定小池候选、采样姿态、
marginal gain和visible voxel地址；不调用相机评价器、不生成候选、不增加seed、不修改算法。
本批用于解释代理失配并决定是否值得另立新方法协议，不改变I3-02A的
`PROXY_NOT_SUPPORTED`结论。

## 固定输入与路段标签

输入是`EXP-I3-02A-SINGLE-ANCHOR-V1`的五个有效状态和状态13负控制。必须验证原协议、
summary、batch、所有选择checkpoint、快照及I3-01B源文件hash；参考/候选采样数必须与
marginal长度相同。用与既有0.25m/0.1rad sampler完全相同的顺序重建带标签姿态，并以
位置/yaw 1e-12逐项匹配保存输入，否则为`ATTRIBUTION_ENGINEERING_FAIL`。

候选在参考边e插入锚点，定义changed window：从参考顶点p_e处转向插入incoming边开始，
包括incoming/outgoing的转向与平移；到下游参考顶点p_{e+1}后，继续包含转向下一条原参考
边的原地旋转，若e为最后一边则包含terminal yaw旋转。下游原边的平移不包含。参考changed
window同样包含被替换原边的转向/平移，以及其末端到下一原边或terminal yaw的旋转。
初始共同姿态不包含。其余分为unchanged prefix/suffix。该边界显式纳入插点导致的进入/
退出朝向变化，不能将后继整段观测事后吸收到proxy。

## 预定义诊断量

对每条候选，使用保存的path-history marginal序列计算：

```text
M_c = candidate changed-window marginal sum
M_0 = reference replaced-window marginal sum
S_segment = M_c - M_0 - U0 * (T_c - T0)
D_oracle = |V(candidate)| - |V(reference)| - U0 * (T_c - T0)
downstream_residual = D_oracle - S_segment
```

`S_segment`只是假设能够复用参考prefix history的局部路段代理；本批没有实现这种在线
复用，也没有测成本。每状态从参考开始，只有`S_segment>1e-9`才选择得分最大的额外路线；
否则选参考。同分按time、length、anchor ID、edge、record ID。选择前保存checkpoint，
但这些marginal本身来自此前完整路线计算，故只能做机制诊断，不能冒充无oracle的新实验。

用14条候选计算`S_segment`与`D_oracle`的Spearman（平均秩，若常数则不可评），同时报告
绝对误差、符号一致率、候选/参考分类和各状态选择。路线相关，不能把14条当独立统计样本。

对每个状态的full-oracle最优有效选择固定为：在参考和小池候选中最大unique/time，
<=1e-9同分保留参考。此前结果已公开，因此这不是held-out准确率。机制支持要求：

1. 五个有效状态全部选择与full-oracle有效选择一致；即1/14/27选择参考，26/38选择
   对应最高收益候选；
2. 14条候选的Spearman>=0.7且S_segment/D_oracle符号一致率>=0.8；
3. 在状态26必须区别于Geometry并选择真正正净收益路线；状态38不得退化。

任一失败即`CLOSE_CURRENT_SINGLE_ANCHOR_MECHANISM`。全部满足最多为
`SEGMENT_SIGNAL_ONLY_REQUIRES_NEW_OPPORTUNITY_GENERATOR`：只允许讨论一个全新预注册的
“参考路线遗漏观测区域→候选走廊”生成机制，仍不放行I3-02B计时、I3-03或在线仿真。

## 空间描述（不作通过门槛）

对full-oracle正收益候选的新增体素，使用冻结map的地址→体素中心转换，报告到锚点、
incoming/outgoing线段的距离分布、5m范围比例、6邻域连通分量数和最大分量比例。
这只能判断新增观测是否形成空间集中的走廊邻近区域；距离不包含FoV/遮挡，不能反推
锚点可见性或作为新的选择器。不得看到空间结果后添加阈值或重写门槛。

结果无论正负都更新报告/交接并本地备份后停止。不得重跑I3-02A或通过新代理搜索正结果。
