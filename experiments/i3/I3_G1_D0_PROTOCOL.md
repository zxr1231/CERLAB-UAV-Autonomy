# G1-D0：参考条件观测上界的轻量诊断

2026-10-14，运行前登记。状态：协议完成，未实现/执行。
协议依据为用户确认的I3_GRILLING_CONSENSUS_2026-10-14.md。

## 1. 范围和固定输入

只使用旧I3-02A已保存的5个有效状态、14条完整评分路线及六快照，其中13为负控制。
通过INPUTS.json固定快照、原请求、全部pool/state、5reference和14full输出SHA。
不新增anchor/Edge候选、raycast、完整camera评分、seed或仿真。读取完整旧gain用于
事后诊断，不声称新的blind预测或held-out准确率。旧02A/E1全部数字与正式决定不变。

这个诊断语料的共同表示是：已知安全/motion可行、在最终参考一段插入单个PRM节点的
两段直连走廊。所有14条纳入，不按gain挑选。真实Edge是否存在不参与纳入或排序。
此表示只锁定D0诊断；不自动决定P1的几何母集，不重新开展失败的单点收益代理。

每个状态n=0/2/5/5/2。K=5会遍历全部已评分子集，不可能产生有意义的同池最终优势，
所以**主诊断固定为K=1的早期保留质量**；K=2和K=min(5,n)只作辅助曲线，不能替换K=1
挽救失败。未评分母集的value仍写unknown，不补算168条路线。

## 2. 主界定义

R为已保存reference的unique addresses。N为冻结快照planning region内、原camera语义
可计数的Unknown体素。Q=N\R。先确认R中的地址全在N中，输入epoch/config均一致。

对插入reference段(e)的两条新直连段取闭合轴对齐包围盒，每轴扩张：

```text
rho = range + ||body_to_camera_translation|| + sqrt(3)*resolution
```

所有changed-window旋转位置包含在这些段端点中；prefix/suffix不变由旧样本合同核查。
对map内体素中心计数，planning region边界按原camera中心包含语义，盒与map/region交
集之外不计数。浮点边界向外保守转换至离散索引；oracle检查不能容忍漏地址。

主实现固定**精确盒并集**，不使用sum(box_counts)来替代。两盒需最多3项；以后P1三盒
最多7项包含排除。用int64计数和一致的交集空集规则，结果必须在[0,|Q|]内。
N和Q使用同一种3D整数前缀计数表，范围限定为planning region有效体素索引网格；不
后验切换二维投影来降低成本。索引/表精确性先用小合成网格暴力计数验证。

```text
K_Q = |Q intersect box_union|
K_N = |N intersect box_union|
Ubar_Q = (|R| + K_Q) / T
Ubar_N = (|R| + K_N) / T
```

T仍为已登记motion估计时间。未知遮挡/FoV/yaw被忽略使界乐观，不允许称真实新增观测。
需要验证所有14路线V\R都在box_union且|V\R|<=K_Q、真实预测U<=Ubar_Q。
T<=1e-6、非法地址、非有限参数、配置或map版本不符为工程失败。

## 3. 三个公平访问规则

每状态共有同一14-route语料中的子集，观察次数K相同，最终使用同一个已保存精确U。

1. motion_order：按(T,L,anchor_id,reference_segment,record_id)升序。
2. unconditioned_bound：按Ubar_N降序，完全同分用motion_order的稳定键。
3. reference_conditioned_bound：按Ubar_Q降序，完全同分用同一稳定键。

排序不使用旧full gain/正例标签；先冻结排名文件，再读取旧完整收益标签作评价。
由于full gain早已公开且数据影响了方案设计，这只是防止工具偷偷oracle选点，不构成
新盲测。Geometry与条件界的排序变化率、top-K Jaccard都只能是辅助量。

每K的effective U=max(reference U,已访问K个不同候选的U)，reference改善容差1e-9。
记录raw候选效应、访问顺序、第一次遇到已知较优路线的位置、平均相对U和最优遗憾。
没有候选的状态保留reference。U0=0时相对指标null，绝对U仍报告，不加epsilon分母。
若任一有效状态U0=0导致五状态相对均值不可评，记INCONCLUSIVE_QUALITY_METRICS，不
悄悄减少分母判PASS。当前固定语料的reference gain均已知非零，此规则仍显式保存。

## 4. 成本和资源：先证明值得构建

从同一预加载map开始，对N/Q各独立计数构建、全部诊断box查询和排序，单次测量；
不做warmup或性能调优重跑。分别记录table构建/query/sort和全准备wall、内存峰值。
磁盘/JSON读取单列，reference camera成本使用旧记录说明为未重新测量，因此不能
宣布500ms部署准入。引入参考R不应被当作免费在线信息。

**D0固定工程目标：** 每个界控制一次完整count-table构建+全部box查询+排序<=50ms，
其全部额外scratch<=256MiB；这是在500ms总体目标下预先分配的诊断预算，不是新的物理
速度限制，也不是原几何generation50ms的同一个计时区间。两段未来都需计入总500ms。
只要任一有效状态超过诊断目标，D0工程成本条件不通过；不因结果临时提高50ms。
无候选状态不建立索引，实际计数工作为0，不能用填充工作假装一次有候选测量。

分配跟踪必须包含表容量/临时数组/引用索引；map/model存储和全进程RSS另报真实测量
与未涉及项。D0不构造新的camera model，旧模型实际容量仍记not_measured，而不是再次
用逻辑payload冒充实测；P1采集前必须补齐模型容量和全进程峰值RSS。

计数/排名不是ray评分：D0新增精确camera queries=0。不得将已有gain标签的读取耗时
称作新算法精评分速度。以后P1部署主对照是同500ms cap、独立准备；等实际精评分数
另作机制对照，不能仅用同cap5说明公平，也不能故意让几何法付出无用的表成本。

## 5. 预先冻结的诊断决定

按顺序报告全部条件，不以一个PASS掩盖另一项失败：

- 正确性：输入/地址/精确计数/包含关系/上界在全部14已评分路线成立。失败为
  BOUND_ENGINEERING_FAIL，允许修复可复现工具错误并保留记录，不调界达到有利结果。
- 廉价性：上面每状态/每界<=50ms与256MiB目标成立；不成立为BOUND_PREPARATION_FAIL。
- 有用性（固定K=1）：条件界至少1状态比motion_order的effective U高、至少1状态比
  unconditioned_bound高；五状态平均effective相对U不低于二者；两个已知有正例状态
  均不比motion_order首次遇到正例更晚。缺任一条件为NO_USEFUL_CONDITIONING_SIGNAL。
- 无正例的状态保留，不根据已知state26/38的效应大小再另设百分比。1e-9是数值容差，
  不是论文效应；这些开发集判据不能独占整个研究方向的终止权。
- 全部成立仅为DIAGNOSTIC_SIGNAL_ONLY，可单独登记一次P1。不是主要创新、探索改善、
  实际观测或实时预算的证明，不能自动进入P1/E2。

一次诊断有负结果就停止该上界机制和核心编码，保留整套基础成果，然后做主线决策。
不为挽救D0改精确union为sum、改变K、盒膨胀、input、50ms、cap或追加场景。
不是证明全部信息规划不可能，不覆盖已有02A/E1结论。

## 6. 授权和结束点

本次仅登记D0合同。下一次用户明确启动D0后，实施隔离计数/排名工具及必要测试、
一次固定诊断、报告、更新交接并本地备份后停止。不新装依赖，不启动ROS/Gazebo。
P1只在D0有用信号后单独冻结；其公共安全走廊定义、未参与设计的验证输入和失败规则
另行登记，不能继承历史真实Edge限制或state27专属生死门槛，也不能自动挑新seed。
