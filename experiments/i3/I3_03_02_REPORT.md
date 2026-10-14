# I3-03-02 最小观测引导原型：最终去留报告

2026-10-14。**决定：METHOD_NOT_SUPPORTED，关闭当前原型，不修订方法或追加复测。**

核心算法已实际编写、编译并完成本批扩大对照；没有以新诊断替代编码。工程正确性
通过，但扩展记录的优势不够稳定，500ms预算完成率也不支持准入。按用户“最后一次
测试”的要求到此止损；不换阈值、扩候选、加seed或回到旧开发状态追求正结果。

## 已实现的代码

- `global_planner/include/global_planner/opportunityRoutes.h`：可复用的两层有限束路线
  生成器；参考段→第一位置→第二位置→参考段出口，允许安全虚连接。motion、geometric
  与observation三种束选择；各候选独立可见集合，参考保持固定，记录new/lost/unique/time。
- `global_planner/test/opportunity_prototype_runner.cpp`：冻结快照运行入口，独立准备与
  完整相机精评分、deadline、memory guard、安全复验与reference回退。
- `cameraGainEvaluator.h/cpp`：可选每调用endpoint标记存储上限的重载及模型实际向量
  容量接口；既有接口、config/class布局、默认32MiB策略和光学数值不变。稀疏代理选择
  endpoint hash结构，避免每个小查询构建19.2MB dense marks；不缓存可见集合。
- `run_i3_03_02.py` / `summarize_i3_03_02.py`：固定全38事件、四核并行、公平截断统计和
  明确去留门槛；`plot_i3_03_02.py`只绘制最终已保存数据。

内部代理pixel skip32、姿态spacing1m/0.35rad，包含yaw/FoV/extrinsic/Occupied遮挡，
Unknown按冻结模型透明。最终完整评分始终pixel skip2、0.25m/0.1rad；没有改物理传感器。
第一层和第二层每层最多32次候选代理查询，另一次reference查询；束宽8，动作12000，
最多5条extra完整精评分。运动length/time<=1.25倍reference，extra yaw<=pi/2。

原型是实际生成代码：相对motion/diverse，观测组在26/27个状态改变第一层束，在21/21
个状态改变最终候选几何集合。三种多路线组都在28个状态输出含两个位置的路线，但
最终完整评分选中的改善路线全是一个位置；**第二层未带来最终选择收益**。

这是生成层原型，所有控制共同保留插入位置；没有部署observation-preserving shortcut、
B-spline或在线生成开关，在线默认Legacy及旧返航配置均未改。不能将本批当实际飞行效果。

## 一次冻结的扩大矩阵

输入为历史seed4/floorplan1静态运行全部38次全局规划事件。37有效、1负控制，未剔除
失败以美化结果；没有新seed、ROS/Gazebo或仿真实验。旧六状态中5有效，另32有效事件
作为主要扩展记录；所有事件来自同一轨迹，不是独立seed/scene实验。

4控制：reference-only / motion beam / geometry-diverse beam / observation beam。
2对照：操作受限但wall不限制的机制对照；独立全准备500ms的预算对照（生成50ms，
精评分475ms截止，最终预留25ms）。预算各warmup一次，固定测量3次，没有补跑。

共304独立进程任务，8个负控制跳过、148条机制记录、444条计时记录、148次warmup。
四worker固定不同物理核心0/2/4/6，各方法随事件轮换核心；独立文件和模型。仍共享
cache/memory/turbo，不声称绝无资源干扰或硬实时最坏情况。没有运行失败、重试或替换。

主要比较使用每状态K=min(三种多路线控制实际有效extra评分数)；K分布为0:3、1:3、
2:1、3:5、4:2、5:23。原cap结果也报告；本批两种统计最终结论相同。

## 主要效果：扩展32状态，等实际精评分数

数值均为冻结地图的预测unique/time效用。相对百分比是配对U差除以同状态reference U，
不是coverage、T95、真实新增观测或每条飞行的提升百分比。

| 观测组相对控制 | 胜 / 平 / 负 | 平均绝对U差 | 平均配对相对差 | 中位U差 |
|---|---|---:|---:|---:|
| motion beam | 1 / 29 / 2 | +5.045841 | +0.435580% | 0 |
| geometry-diverse beam | 1 / 31 / 0 | +0.042793 | +0.014940% | 0 |

预登记要求对两控制分别至少2个改善状态，平均U差>1e-9、中位差>=-1e-9。
平均/中位条件成立，但改善状态不足，**主要机制价值判据失败**。不能临时取消胜出
状态门槛，也不能把浮点正差当统计显著性。geometry是本批更有挑战性的对照，增益很小。

状态22相对motion较好，但与geometry完全相同；状态30相对geometry稍好，但与motion
完全相同。状态10/31观测组比motion差。说明许多改善来自多路线本身，并非特有观测引导。

旧五有效开发状态上，观测相对motion为2/3/0、均值+6.250117%，相对geometry为1/4/0、
均值+2.533813%；包含它们的37状态总体分别为3/32/2、2/35/0。这些数字完整保留，
不能替换32扩展状态的主要判据。状态26确实找到比reference约+12.6691%的模型路线，
但它是已反复使用的开发状态，且预算下未能提交，不能救回主要贡献。

## 500ms预算：不通过

| 方法 | 完整完成次数 / 111 | 完成率 |
|---|---:|---:|
| reference-only | 111 / 111 | 100.00% |
| motion beam | 72 / 111 | 64.86% |
| geometry-diverse beam | 69 / 111 | 62.16% |
| observation beam | 54 / 111 | **48.65%** |

reference-only评分数量不同，仅作为基准成本，不把这行当等候选数机制比较。
预登记观测完成率>=90%门槛未达到。观测组54次在生成50ms阶段截止，3次完整精评分
截止，全部回退reference，没有使用部分gain冒充有效选择。

扩展32状态下，按每事件3次计时中位effective U，观测相对motion与geometry都为
0胜/31平/1负，平均配对相对差均-0.131316%。离线少量好路线没有转化为预算下收益。
这里不等同碰撞/探索任务失败；它是生成/评分不完整后的安全reference回退率。

不受wall限制的生成中位/最大耗时：motion0.434/3.174ms，geometry0.463/6.150ms，
observation49.502/613.531ms。观测组budget总耗时中位194.646ms看起来更短，原因包含
大量提前停止，**不能宣传规划更快**。三个多路线组均有5extra完整评分成本问题。

## 正确性、资源与冻结证据

5项新C++、17项C++回归、4项统计测试通过；148组机制记录的reference/所选路线与
独立完整重算一致。旧状态1/14/26/27/38的reference逐地址、raw、unique与旧02A一致。
全部当前输入和旧D0来源SHA不变；negative无相机工作，所有有效提交路线安全，partial
结果仅作诊断不参与选择。新代码保留ray/Unknown语义，没有把Occupancy熵当SLAM不确定性。

分配跟踪峰值69.98MiB，进程最大RSS201.04MiB，256MiB工作区限额未触发。新dense模型
实际对象/向量容量7,946,032bytes，sparse模型4,812,592bytes；这些不含map、JSON、
ray traversal临时marks及库内存，后者在allocator/全进程RSS中另计。旧E1的未测容量记录
不改写，新模型元数据不能倒填为旧模型的实测值。

原始目录：`/home/zxr2/cerlab_benchmark_ws/results/EXP-I3-03-02-OPPORTUNITY-PROTOTYPE-V1/`。
输入目录：`/home/zxr2/cerlab_benchmark_ws/results/EXP-I3-03-02-PROTOTYPE-INPUTS-V1/`。
运行冻结parent `51f599f`、GP `0221483`，二进制/库/协议/input SHA在identity.json。
结果：I3_03_02_RESULTS.json / VALIDATION.json；图：原始目录final_comparison.png/pdf。

## 最终执行决定

**按当前方法、输入空间和预算，不支持将该观测引导原型继续作为主要创新推进。**
局部离线收益存在，不能因此宣称稳定优势、实时可用或SCI/EI贡献已成立；也不能由本批
单轨迹证明所有informative planning思想不可行。

当前原型结束：不自动继续校准、修订复测、扩大seed、加入cache/Confidence/语义或
开启在线仿真。代码和基础工具保留，Benchmark/R1/R2/I1/I2与旧负数据均可复用。
下一次如用户另行要求改变论文路线，应作为明确的新研究决策，不能把它伪装成当前
原型的又一轮“最后测试”。实际观测、coverage/T80/T90/T95和跨seed泛化本批均未验证。

本地备份：`/home/zxr2/下载/CERLAB_I3_Backups/I3_03_02_FINAL_2026-10-14/`，以README/
backup_receipt/SHA校验为准。本批不推GitHub，报告/交接/本地提交与备份完成后停止。
