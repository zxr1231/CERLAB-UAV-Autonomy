# V2 E1 完成：合成功能正确，固定走廊池局部价值未达门槛

2026-10-14。合同dc83800；采集parent6132b98 / global_planner32801ef。
只运行一次六状态离线批次。没有仿真、追加seed、扩大池或修改在线默认规划器。

## 正式结果与范围

保存的批次决定：**LIMITED_POOL_VALUE_FAIL**。
五个有效状态中四个有不同、安全且运动合格的候选，供给条件>=3通过；只有状态26有
预测单位估计时间收益高于reference的候选，未达到>=2状态局部价值条件。按V2结束
该固定几何池分支，不准入成本研究/E2，不自动开发观测引导生成或Edge cache。

候选合成功能验证通过：13条实际入池路线的完整地址集合、raw、unique、逐步marginal
与选择冻结后独立完整重算完全一致；五个reference与旧I3-01C保存结果一致。
这是离散冻结camera模型的正确性，不是实际飞行收益、主要创新成功或500ms预算通过。

## 供给与价值

共18874个枚举组合，均在每状态12000上限内，无截断。合格不同路线分别0/1/52/126/2，
按固定代价分层保留0/1/5/5/2，共13条。状态13在构图/相机之前跳过，零生成/零camera。

| 状态 | 原分层 | 枚举组合 | 合格/最终小池 | 小池最佳extra相对reference收益率 | 最终exact选择 |
|---|---|---:|---:|---:|---|
| 1 | early | 10 | 0/0 | 无extra | reference |
| 13 | early | 负控制跳过 | — | — | 不提交 |
| 14 | middle | 934 | 1/1 | -5.04% | reference |
| 26 | middle | 3760 | 52/5 | +4.73% | record3428 |
| 27 | late | 11520 | 126/5 | -2.20% | reference |
| 38 | late | 2650 | 2/2 | -7.81% | reference |

状态26的3428路线为 `[0,282,285,295,301]`，通过真实有向PRM Edge285→295。
新增2073、丢失40个预测Unknown体素，估计time从19.068s增至21.622s，U从568.188
增至595.086体素/s，约+4.734%。geometry选择3411但U更低并回退reference；new-only
与exact都选择3428。因此这个正例不构成exact相对new-only的独立优势。

状态38的两条Edge走廊不包含此前I3-02A无真实Edge限制下的正收益单锚点路线；两条U
均下降。不能将当前失败用于否定先前+0.58%的保存数字，也不能改表示补回有利路线。

五状态effective相对U均值：geometry=0，new-only和exact均约+0.947%。这只是固定池
描述值；exact本来就按同池完整U取最大，均值优于弱选择器不证明观测引导生成。
所有候选回退前退化及new/lost完整保留，未用回退后的0掩盖额外路线代价。

## 实现与验证

- 增加可选`CameraSharedBudget/evaluatePoseSets`：绝对deadline、跨查询累计pose/voxel
  限额、cancel、全有或全无pose集合。旧接口默认路径、光学ray/Unknown算术不变。
- 新增test-only Corridor fixture：有向Edge与连接段筛选、每Edge最短插入、固定5分层；
  带事件标签的window/suffix采样；使用reference pose sets与local corridor组合。
- 复用规范未变姿态，按完整候选顺序重新计算history/marginal；未用R减R_e。
- 分配跟踪仅链接独立fixture进程，不链接ROS规划节点；统计C++请求块与跟踪头，包含
  集合桶/节点、marks和暂存数组。分配前执行256MiB限额，输出JSON在可见scratch计量外。
- 12项新C++功能测试通过；5项原camera、10项原path evaluator、6项two-stage回归测试
  通过；23项相关Python测试通过，其中3项新增选择/门槛测试。
- 只读验证器重新核验全部source/context SHA、五个冻结selection、13候选效果与门槛。
  实现源码/协议/binary SHA已记录；正式批次无失败重采或阈值变更。

两轮编译：首轮只有misleading-indentation警告，未发生构建失败；修正排版并补测试后
第二轮无该警告。全部正式批次在冻结代码后执行，测试和构建日志均保存。

## 资源与统计缺口

tracked visibility allocation峰值22.34--32.64MiB，未触发256MiB限额。
它是C++分配请求容量，不是malloc arena或总RSS；模型/输入地图不在此限额范围内。
输入map payload报告39000000字节；依固定map/config推导光学模型逻辑payload6616416
字节。后者不包含vector扩容余量，不能称实测模型占用。

**本批没有采集整个fixture的峰值RSS和模型实际allocated capacity。** 这是V2资源记录
要求的元数据缺口，不能宣称协议所有资源记录项已完成。为遵守一次固定批次和负结果
退出条件，没有重跑候选或启动E2补齐。后续只有另行授权独立成本批次时，才能加完整
RSS/模型容量测量；当前价值失败不因补测而改变。

生成分项约14.5--31.8ms；compose子进程wall约262--1098ms。这些包含磁盘、JSON、
内存跟踪等fixture成本，control之间还共享离线输入，所以不能作为公平在线加速证据，
也不能直接判为50/500ms准入成功或失败。camera API的工程budget测试通过不等于
真实live-map锁、fresh safety、cleanup最坏时间得到证明。

## 停止与下一决策

完成的是正确性工具、固定池诊断与报告；未完成生成创新、E2或在线整合。
E1价值条件失败后，停止当前“每真实Edge最短插入＋5代价分层”的筛选分支。
不能通过扩大池、换阶段标签、追加seed、替换失败或改权重把这批变为成功。

下一步只做研究范围决策：是否另立一个在池确定前利用观测信息改变候选供给的明确
机制，或降低/关闭目前主张。局部精确评价器可保留为基础，但不能仅因它正确就将其
包装成主要创新。当前数据也不证明所有观测引导路线都不可行。

原始目录：`/home/zxr2/cerlab_benchmark_ws/results/EXP-I3-E1-FOUNDATION-V2/`。
结果：I3_02E1_RESULTS_V2.json；验证：I3_02E1_VALIDATION_V2.json。
本检查点仅本地提交和校验备份，不推送GitHub。
