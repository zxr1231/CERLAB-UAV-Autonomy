# CERLAB I3-02E 实现前独立审核

审核日期：2026-10-13。状态：审核完成；结论 B，须先修订协议，再进入有限基础验证。

## 续接入口

用户要求：本次只审核；可写独立审核文档；不修改源码、冻结实验及其协议，不运行实验。
若中断，下次先完整阅读本文件及同目录CERLAB_I3_02E_Astra_Audit_Prompt.md，
从下面未完成项继续。不要执行项目总交接中“直接实现E1”的旧指令。

当前主仓库HEAD：a5bed84f8063c6247695f86f4e41a87d4a6fb3aa。
global_planner：cde9ed05e107369504e6606ce45e43412f9cd86c。
分支feat/i3-camera-evaluator，起始Git状态干净；未找到适用AGENTS.md。

### 完成范围与续接状态

- 完整读取审核提示词、I3-02A/R报告、I3-02E四份协议/审查材料。
- 读取总交接历史和当前阶段，并核对版本与submodule。
- 重新定位dep.cpp::getBestViewCandidates/findBestPath、routeControls构图与参考生成、
  routeCandidates运动代价/shortcut及routeSnapshot安全检查。
- 初步发现：生成池不读取camera gain，因此当前是几何候选池的观测重排序；Proposed
  和full oracle同目标同候选，5/5一致和平均不低于其他同池控制有数学上的必然性。
- 已阅读DEP、HIRE、PIPE、FUEL、FALCON、TARE、EPIC、ETH active planning、t-BSP及2026 GP覆盖论文相关方法段，检查作者代码/仓库，证据深度见第9节。
- 已完成采样、集合合成、预算和I3-02R推论边界审核。
- 下文12节构成最终报告。审核没有待完成实验；本轮没有运行测试或生成新算法数据。

### 下一会话从哪里开始

本报告已经完成，不必重新开始文献与源码审核。下一步需用户安排“按第10节修订E协议”，
随后才实施第12节允许的基础验证。项目内旧交接尚未更新，因为本次明确禁止修改项目文件；
旧文档中的“直接实现E1”不代表本次审核放行。不要自动启动E1或E2。

### 核心发现摘要

1. I3-02E协议明确“池构造不读取camera gain”，与“观测机会引导生成”的命名有差距。
2. 对固定同池按完整U取argmax，与相同U的full oracle一致是实现正确性，不证明科研效果。
3. Proposed实质评分最多5条替代路线，不能因为最终输出只有1条就算参考+1的评分工作量。
4. B_e不能由R减去R_e得到；重叠体素仍可能被未改变姿态观察，必须重建不变姿态union。
5. RouteSnapshot::freeLine为离散点检测，不能宣称严格连续无碰撞。
6. “几条直连不属于原PRM”不推出“必须插入真实PRM Edge”；真实Edge约束须有独立动机。

## 1. Final Verdict

**B — 可以继续，但实现前必须修改若干定义。**

更准确的含义是：允许保留这条研究主线并准备一次有明确边界的工程可行性验证，
**不认可当前版本已构成“观测机会引导生成”的主要贡献，也不建议按现协议原样编码。**

问题真实、基础平台充分、连续路径观测评价值得保留。但当前E协议有三个直接影响结论的问题：

1. 候选池在读取观测之前就固定；所谓Proposed实际是几何候选上的精确收益重排序。
2. Proposed和oracle在同池优化同一U，oracle一致及平均优于弱选择器主要由定义保证。
3. 多达5条走廊都得到完整预测收益，实际信息评分工作量不能按“最后输出1条”计算。

这三个问题影响普通SCI/EI论文的论证完整性，并非按顶会标准苛求。修正定位与实验后，
本项目仍可能形成“一个明确方法贡献＋可靠评价机制＋执行验证”的渐进式论文；目前不能
保证已达到该水平。若坚持将现版本直接称为观测驱动生成，则该主张应评为C，暂缓开发。

## 2. Core Method Assessment

**当前方法真正研究的是：在同一目标和运动预算下，对少量几何生成的PRM局部绕行路线，
复用参考路线的观测集合并精确评价、选择预测观测收益率更高的路线。**

这个定义可实现，也可作为基础机制；“由参考路线遗漏的观测机会主动生成路线”尚未实现。

### 研究链条中哪些成立

- Baseline有节点累计重复、Unique-only未稳定改善、单锚点代理漏掉一条较优路线：已有证据支持。
- 连续路径的观测信息不能由单个anchor pose充分代表：I3-02A/02R支持这一有限判断。
- 因此必须使用真实有向PRM Edge作为创新对象：**不能由已有结果推出**。两点途经、任意安全
  连接、运动基元也可能表达同类走廊。真实Edge只能先作为有界候选表示，不能作为新颖性证据。
- 当前方法能提高实际探索效率：尚无证据，未来仍需执行轨迹和真实新增观测验证。

### I3-02R应如何解释

不修改它的数字及既有决定，但必须降低推论强度：

1. segment score使用已经完整评价过的候选marginal，结果不是一个低成本预测器的独立成功。
2. 若修改窗口覆盖参考的最后一段，其后没有suffix，窗口marginal之差扣除代价就与整路净值
   代数一致；此前状态26的正收益路线恰是最后一段修改，状态14/38则基本覆盖全路。
3. 对任何点x，anchor位于插入走廊上，所以 `dist(x,corridor) <= dist(x,anchor)`。
   “5m走廊覆盖比例高于5m锚点比例”在集合包含关系上本来就应成立。95.25%/97.31%具有
   描述价值，却不是证明“真实PRM Edge引导”独特有效的独立证据。
4. 净值 `D=T*(U-U0)` 与U相对参考的正负号一致，但跨不同T候选时，最大D不保证最大U。
   02R的排序一致只能保留为这14条已知候选上的观察。

这些边界可直接由[归因脚本](/home/zxr2/cerlab_benchmark_ws/src/CERLAB-UAV-Autonomy/experiments/analysis/run_i3_02r.py:60)
和[标签采样器](/home/zxr2/cerlab_benchmark_ws/src/CERLAB-UAV-Autonomy/experiments/analysis/i3_segment_attribution.py:4)核查。

## 3. What Is Actually New

| 部分 | 当前性质 | 合理贡献定位 |
|---|---|---|
| 参考路线条件下，识别遗漏观测并改变搜索/连接选择 | 尚未定义成可执行生成器 | 最值得保留的主要贡献候选 |
| prefix/suffix可见集复用、局部重算、精确合成 | 正确的局部评价分解；集合恒等式本身常规 | 若实现有明确成本优势，可作支撑方法/系统机制 |
| via Edge和两个安全连接 | 普通受限路径插入表示 | 算法组成部分，单独创新弱 |
| new/lost/时间统一排序 | 常规净效用比较 | 必要评价规则，不能靠改名算创新 |
| 保留走廊、不运行普通shortcut | 共享结构约束 | 尚非“观测价值保留简化算法” |
| 持久Edge缓存 | 尚未实现 | 先当工程优化；不能预先计入贡献或速度提升 |
| PRM→B-spline→实际观测对应验证 | 仍待完成 | 有价值的实验机制证据，不等于新规划理论 |

可以争取普通SCI/EI所需的一个主要贡献，但不应把“union、via Edge、cache”拆成三个独立创新。
即使最后采用精确重排序作为主要实现，也需要明确新增机制及强对照，单靠部署成熟组件并不足够。

## 4. Source/Protocol Consistency

### 已重新确认的源码事实

| 事实 | 源码证据 | 审核结果 |
|---|---|---|
| 中间节点与Goal均重新计算并计收益，路径朝向影响收益，按估计时间归一化 | [dep.cpp::findBestPath](/home/zxr2/cerlab_benchmark_ws/src/CERLAB-UAV-Autonomy/global_planner/include/global_planner/dep.cpp:1037) | 一致；不能宣称首次考虑路径收益 |
| Goal按节点gain优先队列和相对最高gain阈值预筛，受min/max数量控制 | [getBestViewCandidates](/home/zxr2/cerlab_benchmark_ws/src/CERLAB-UAV-Autonomy/global_planner/include/global_planner/dep.cpp:891) | 一致；固定Goal细化不解决被预筛掉的目标 |
| 冻结pose/map、临时排序ID、有向Graph和距离搜索 | [routeControls.cpp](/home/zxr2/cerlab_benchmark_ws/src/CERLAB-UAV-Autonomy/global_planner/include/global_planner/routeControls.cpp:34)、[routeSearch.h](/home/zxr2/cerlab_benchmark_ws/src/CERLAB-UAV-Autonomy/global_planner/include/global_planner/routeSearch.h:28) | 一致；distance_single不可冒充原始DEP/HIRE历史A* |
| 现有shortcut按直连可行性删点 | [routeCandidates.h](/home/zxr2/cerlab_benchmark_ws/src/CERLAB-UAV-Autonomy/global_planner/include/global_planner/routeCandidates.h:46) | 一致，未使用观测保留判据 |
| Unknown/越界在free判定中不自由 | [routeSnapshot.h](/home/zxr2/cerlab_benchmark_ws/src/CERLAB-UAV-Autonomy/global_planner/include/global_planner/routeSnapshot.h:37) | 一致，但freeLine是离散采样检测 |
| 相机ray遇已知Occupied停止，Unknown继续并计入集合 | [cameraGainEvaluator.cpp](/home/zxr2/cerlab_benchmark_ws/src/CERLAB-UAV-Autonomy/global_planner/include/global_planner/cameraGainEvaluator.cpp:114) | 预测模型一致，不能消除未知真实遮挡 |
| 当前batch无逐姿态集合返回，单姿态visibleUnknown无外部deadline | [cameraGainEvaluator.h](/home/zxr2/cerlab_benchmark_ws/src/CERLAB-UAV-Autonomy/global_planner/include/global_planner/cameraGainEvaluator.h:27) | E1需要新增接口合同，现成代码还不满足 |

### 文档不一致与过强表述

- [E协议第23—30行](/home/zxr2/cerlab_benchmark_ws/src/CERLAB-UAV-Autonomy/experiments/i3/I3_02E_METHOD_PROTOCOL.md:23)
  明确先以time选择每Edge插入位置并固定5分层，且“不读取camera gain”。这与02R建议的
  “先残余观测机会，再选择少量高分边构造路线”不同。
- “不属于Graph的直连段”只证明shortcut和Graph边不是同一表示；不能推出必须通过真实Edge。
- `measure()`用 `length/v + yawPenalty*yaw/angularSpeed`，这是估计代价，未显式包含加速、
  动力学转弯、优化失败或执行暂停。协议中的“完整执行时间”应改为“既定运动模型估计时间”。
- `freeLine()`每map resolution检查离散点，且循环为`i<steps`，不能宣称连续段所有穿过体素
  都检查过。沿用它可保持实验语义一致，但严格安全需要以后共同的线段遍历验证；此次未运行
  反例实验，不据源码风险改写以前的零碰撞记录。
- `sameGeometry()`要求点数相同后逐点比较，并非连续曲线等价。共线分段与同曲线不同采样需要
  单独定义，不能声称现函数覆盖全部几何重复。
- 总交接开头global_planner仍写155d65b，实际为cde9ed0；结尾仍有“小任务就push”的旧模板，
  与用户当前“普通备份只本地”冲突。将来修订交接时一并修正，本次没有修改它。

## 5. Candidate Generation Audit

### 判定：当前是观测重排序，不是观测机会驱动生成

设几何、地图安全和代价筛选生成固定池P。当前流程是：

```text
geometry/map/motion → P（最多5条） → 对P的全部成员求精确U → argmax U
```

参考遗漏观测仅在P已经确定后出现，既不改变可访问Edge、不改变插入位置，也不决定
哪些候选值得完整构造。因此不能把“最终选中了信息丰富路线”当成“观测驱动生成”。

### 最小必要调整：先拆清楚两个研究问题

**推荐眼下先把E1收敛为工程基础批次：** 名称改为“局部走廊集合合成和候选价值验证”，
保留现固定池作为明确的受限表示；通过仅表示有价值候选及精确复用可实现，不放行主要创新。
这不要求现在另写一套更复杂的生成器，也避免继续通过换点/换边和重命名获得表面进展。

若继续保留“观测引导生成”作为主要贡献，则在后续单独协议中必须先定义以下接口：

1. 相同的有限几何可行母集S，以及候选查询/光线遍历/CPU与wall预算；不能无限全图光线评价。
2. 观测残差或其有依据的界在“最后5条完整评价路线”确定之前改变扩展、连接或保留决策。
3. 插入位置不能先被纯最小time不可逆淘汰；需明确保留多位置的有界规则，或承认该限制。
4. 输出的生成候选再由统一精确评价器评分。Geometry/Generic用各自生成器，但同一最终评价器。
5. 消融“有/无参考集合残差条件”，验证它是否改变候选供给及真实净收益，而不只是改变数字。

没有这些定义就不具备生成创新；添加一个未经分析的残差权重或再扩大池均不是合格修订。
本报告不规定一组看过结果后的新数值，也不授权运行新母集搜索。

### 候选池偏差

- 同一Edge在不同位置插入，可能删去不同参考观测且连接段观测完全不同；最低time并不支配
  其他插入位置的U。此预筛可能不可恢复地删除最佳路线。
- 5分层只覆盖代价分布，不覆盖观测区域、拓扑或yaw分布。
- 12000覆盖了当前最大11520的已知fixture，是知晓开发集规模后的设计常数；可以作为明确
  工程上限，但不是数据无关的复杂度证明。组合次数也不等于相同raycast/碰撞检查工作量。
- 若此池失败，可停止该固定实验分支；不能推出整个观测引导方向或所有Edge表示不可能。

## 6. Exactness Audit

### 公式在固定离散观测模型下成立

令参考的未变姿态索引集合为I_B，改变窗口索引为I_R。对姿态q和冻结地图M定义V_M(q)：

```text
B_e = union_{i in I_B} V_M(q_i)
R_e = union_{i in I_R} V_M(q_i)
R   = B_e union R_e
C   = union_{q in candidate changed window} V_M(q)
V_candidate = B_e union C
```

只要候选其余姿态完全相同，这个集合恒等式就是精确的；它不是新的信息理论。

**B_e不能取R\R_e。** 例如B={a,b}、R_e={b,c}、C={c,d}，正确候选为{a,b,c,d}；
从R删除R_e会错删仍由B观察到的b。可用不变姿态直接union、分段prefix/suffix union，
或精确引用计数实现；不必预先强制使用内存开销最大的逐姿态unordered_set方案。

由集合定义还得到：`new=C\R`，`lost=(R_e\B_e)\C`。Naive-new与Proposed主要区别在
是否考虑lost和时间，不应把Naive-new描述成与E1完全不同的观测模型。

### 编码前必须补齐的边界

1. 固定唯一采样器，并比较完整带yaw的姿态序列，而非只比较路径节点。参考平移段必须保持
   相同的`ceil(length/0.25)`与插值规则；若改为全路等弧长采样，suffix采样相位可能改变。
2. changed window包含入口处从原入射yaw到新方向的旋转、所有连接/Edge的旋转平移、出口
   到下一原边或terminal yaw的旋转；初始pose和边界端姿态须明确归属。集合允许重复端姿态，
   但raw/marginal不能任意双计。
3. 相邻1e-6合并只能使用明确的规范点，不能修改窗口外的p_e/p_(e+1)；近似点合并、共线删点
   都可能改变ray落在哪个体素。不能从几何近似相同推出可见地址严格相同。
4. 浮点yaw相差2π、±π转向同分、极短/垂直段、reference仅两点、u等于连接端点等均要有
   唯一规则。I3-02R的单锚点索引标签不能直接用于新增两个节点的E走廊。
5. 合成后的unique集合可以直接求U，但raw和逐步marginal仍须按完整候选顺序重建；不能
   复用旧suffix的marginal数值，因为它依赖新的prefix观测历史。
6. map epoch/reset、version、地址布局、分辨率、相机外参、FoV、range、region、ray采样和
   pose合同必须一致。单独version数值或瞬态Edge ID不足以跨地图复用。
7. 固定snapshot中的Unknown透明性不能替代真实遮挡；预测可见Unknown计数也不等同于
   Shannon互信息或完整SLAM不确定性。
8. 精确性只针对所定义的PRM折线姿态。在重新shortcut、B-spline全局优化、滚转俯仰变化、
   地图更新或只执行路径前缀后，不再自动成立。必须后续对actual observation单独验证。

## 7. Budget Audit

### 500ms：高风险，尚不能确认可行，也不能由旧结果断言绝不可能

已有报告中：I3-01B状态27单参考整阶段约270ms；I3-02A单条完整候选相机分项最高约280ms；
I3-02R的变化窗口姿态占比中位76.1%。这使“参考＋最多5走廊”尤其在长路线状态下有明显风险。
精确复用可能节省重复计算，但保留pose sets、构造B_e、union、排序和释放又引入成本。

以上是不同旧测量的风险证据，不能直接相加当作E1/E2实测时间，也不能按pose比例外推
相机耗时。完整30候选曾失败并不排除极少候选未来成功。必须实测同一批新实现。

应报告的总账：

```text
snapshot获取/复制/锁等待 + 模型建立 + 几何池/安全检查
+ reference可见集合 + 所有查询过的机会/走廊
+ B_e构建与集合合成 + 完整精评分 + 选择
+ 最后安全验证 + 超时丢弃与内存释放
```

500ms仍是已登记的Stage B工程预算，Stage A和局部优化另报；它不是整机规划总耗时，
也不是所有UAV必须满足的通用理论阈值。保留当前预算，不为了放行而改变物理设置。

### 接口合同尚不充分

现`evaluateSamples()`开始时建立自己的计时起点，构造函数不含外部deadline；末次
`work.check()`后还有地址复制、排序、统计和结果返回。外层必须在提交前再次检查整阶段时间。
`visibleUnknown()`无外部budget，不能循环调用它后声称有严格475ms截止。

新接口至少需要：统一绝对deadline、累计samples/voxel visits、scratch字节限额、全有或
全无结果、明确valid/map/config标识、超时后零可用得分、内存清理计费。不能每个pose重置
475ms，也不能把一次走廊未完成的部分集合当作低收益候选排序。

50ms应明确只覆盖哪段操作；排序、去重、路线拼接与碰撞检测若属于生成就必须包括。
475ms应中断正在进行的评分，而不只是“此后不开始新评分”。25ms是预留量，不是fresh
map锁等待和检查必定完成的证明。所有超时仍进入分母，回退前重新验证参考安全。

必须把真正成本单位分开：枚举组合数、构造路线数、粗观测查询数、精确评分路线数、
最终提交路线数。**评价5条然后输出1条，不等于只评价1条。**

## 8. Control Fairness Audit

### 同池比较适合评价器，异池同规则比较才适合生成器

| 要回答的问题 | 应固定什么 | 允许变化什么 |
|---|---|---|
| 集合合成是否正确/更快 | 完全相同候选和同一观测模型 | 合成评价 vs 全路重算 |
| 评分规则有何作用 | 完全相同候选池、运动约束 | Geometry / new-only / net-U |
| 观测是否改善生成 | 同Goal、可行母集、预算、输出数、最终精确评价器 | 候选扩展/保留规则和最终候选内容 |
| 是否改善探索 | 同场景、物理配置、seed、终止规则 | 整个规划方法，统计失败/RTF/执行观测 |

当前E1只覆盖前两行。为了测生成，不能同时要求所有方法最终生成完全相同候选；应共享
母集、资源上限和最终评价规则。Generic K与几何多样路线不应沿用历史有缺陷的I2结果
充当新方法公平对照。

Geometry-edge在选择阶段无需camera，但协议要求它最终与参考做U回退，所以它实际上
仍需参考及所选路线的camera评分。建议称为“Geometry＋共同安全收益回退”，并将纯几何
无camera控制单独标注，不能混为同一时延指标。

离线分析允许复用集合节省重复工作；部署成本比较必须独立从同状态开始，不能将Proposed
算出的所有集合免费送给其他控制，也不能故意让Geometry支付无用的五候选评分成本。
同预算表示相同上限和实际成本透明，不要求强迫每个方法烧满同样CPU时间。

所有走廊法应共同保留via Edge，若后续改用观测保留shortcut，则各生成器共享相同实现。
当前“禁止shortcut”只证明结构保留，尚未证明B-spline会按其观察或证明简化贡献。

Full-route重算放在checkpoint之后是正确工程安排，但它仍与Proposed共享同一camera模型
和同一优化目标。因此是**独立调用的实现校验**，不是独立的真实观测oracle。

## 9. Novelty Risk

### 风险分级

| 方面 | 风险 | 理由 |
|---|---|---|
| 首次路径收益/union/历史去重 | High | 已有论文与作者代码明确覆盖 |
| 两途经点＋真实Edge＋三个安全段 | High | 常规受限路线插入表示；换表示未证明方法差异 |
| 当前“观测引导生成”命名 | High | 观测不参与生成和5候选筛选 |
| 精确局部合成和预算化实现 | Medium | 可形成实用配套机制，需测真实节省与严格一致性 |
| 完整方法达到普通SCI/EI的潜力 | Medium–High | 有明确问题和平台，但主要生成机制及闭环效果未证实 |
| 冻结负结果与可追溯性 | Low | 现有记录基本完整；不能把这一优点当成创新证明 |

### 原始论文/代码对照

本次实际联网查找至2026-10-13可获得的材料。以下只概括已核实的机制，不从“未见相同公式”
推出首次提出。每项均与原文方法或作者代码相连。

| 工作 | 直接重合的机制与差异 | 本次证据深度 | 对本项目风险 |
|---|---|---|---|
| DEP | 增量PRM、节点gain预筛、最短路径候选与路径gain/time；原论文已非终点-only。E的差别只能放在连续去重与受限路线修改。 | [原文§IV-C](https://arxiv.org/pdf/2010.07429)，本机衍生实现另核；未证明本机就是原始DEP复现 | High |
| HIRE | Frontier启发式增量采样、路径中间点按运动yaw累计gain/time和B-spline；禁止重述为新路径收益。 | [原文§IV-D](https://arxiv.org/html/2309.09121)，本机dep.cpp/routeControls | High |
| PIPE | 给各frontier构造A*路径，沿路径累积可见区域并集并按收益/路径代价选目标；使用预测地图。当前E也偏向已生成路径的观测重排序。 | [原文§IV-C/E](https://arxiv.org/html/2503.07504v2)、[作者process_path/score_frontiers_pathwise](https://raw.githubusercontent.com/castacks/pipe-planner/init-import/scripts/sim_utils.py) | High |
| ETH Schmid等 | 持久轨迹树、gain/cost/value与重连复用；框架代码可删除父链已见体素。原论文假设gain独立，代码去重选项默认false，不能混称全部实验用了去重。 | [原文§III](https://arxiv.org/html/1909.09548v2)、[作者computeGain](https://raw.githubusercontent.com/ethz-asl/mav_active_3d_planning/master/active_3d_planning_core/src/module/trajectory_evaluator/simulated_sensor_evaluator.cpp) | High |
| TARE | 按残余表面覆盖选视点，更新重叠覆盖，再构造局部路线。代码先计算导航/已选视点覆盖，再选尚未覆盖的视点，是非常接近的条件化观测思想。目标与表示不是本E的固定Goal体素走廊，但足以否定“残余覆盖引导路线”这一宽泛首次主张。 | [原文§IV-A/B](https://www.roboticsproceedings.org/rss17/p018.pdf)、[作者LocalCoveragePlanner](https://raw.githubusercontent.com/caochao39/tare_planner/master/src/tare_planner/src/local_coverage_planner/local_coverage_planner.cpp) | High |
| FALCON | 以全局覆盖序列为引导，把frontier代表视点用SOP插入并优化遍历时间。与“基准路径上加入观测位置”的故事相近；尚未确认同样的B_e/C差分集合与单PRM Edge约束。 | [原文§V-B](https://arxiv.org/html/2407.00577v2)、[作者仓库](https://github.com/HKUST-Aerial-Robotics/FALCON)目录/README；本次未完成核心cpp逐函数读取 | High |
| FUEL | 增量frontier结构、全局ATSP、局部视点细化、轨迹；代码shortenPath按碰撞/Unknown保留必要点。适合系统对照，非本E的精确局部集合修改。 | [原文§IV/V](https://arxiv.org/html/2010.11561v1)、[作者manager/shortenPath](https://raw.githubusercontent.com/HKUST-Aerial-Robotics/FUEL/main/fuel_planner/exploration_manager/src/fast_exploration_manager.cpp) | Medium |
| EPIC | 点云/自由球拓扑、frontier可达视点与覆盖评分、ATSP及局部轨迹；与RGB-D体素模型不同，不等于固定Goal短走廊。 | [原文§V-B](https://arxiv.org/html/2410.14203v2)、[作者仓库](https://github.com/Robotics-STAR-Lab/EPIC)目录/README；未做完整函数审计 | Medium |
| t-BSP | PRM上生成k-diverse shortest paths，评价SLAM belief图信息；并非Unknown可见体素覆盖，却已覆盖“PRM多路径＋信息选择”的宽泛组合。 | [原文候选生成/实验](https://arxiv.org/html/1903.00927v1)；未核实配套作者实现 | Medium |
| Jakkala等2026 GP覆盖规划 | 将估计不确定性约束转为覆盖，按边际覆盖/路线增量选择位置，并用nearest insertion近似新增路程。任务模型不同，但“新增观测/额外绕行”机制风险高。 | [原文附录B/C](https://arxiv.org/html/2602.05198v1)、[作者仓库](https://github.com/itskalvik/uncertainty-guaranteed-ipp)及benchmark入口；核心GreedyCover/GCBCover位于SGP-Tools，未完整核算法实现 | High |

近期补充：已查看2026年9月WOLF原文的预测frontier生成与预算化融合机制，其world-model
路线与当前静态可见集走廊不同，并不要求本项目加入学习模块。[WOLF原文§III-C](https://arxiv.org/html/2609.23656)

**对重点检索问题的回答：** 已确认许多工作具有“未覆盖区域/边际收益＋基准路线或覆盖路线
插入＋代价限制”的实质机制。此次没有确证完全相同的“固定Goal、单真实PRM Edge、B_e∪C
精确替换”的完整算法；这只说明精确重合仍不确定，不能据此宣称该组合新颖。

检索限制：FALCON部分GitHub源码请求返回加载错误，EPIC本次只核到论文方法与作者仓库
层级；2026 GP工作的核心库和t-BSP代码未逐函数核查。其他检索命中未读到足够原文的
工作没有用来支持具体重合断言。未穷尽截至今日所有论文，也不把搜索页日期当发表时间。

## 10. Required Changes Before Implementation

以下是编码前必改项，不是要求现在部署另一套大系统：

| 必改项 | 具体文件 | 修改要求 |
|---|---|---|
| 收敛E1主张 | I3_02E_DESIGN_REVIEW.md、METHOD_PROTOCOL.md | 改为精确局部评价/受限候选基础验证；保留生成贡献为尚未定义 |
| 拆开正确性与科研门槛 | METHOD_PROTOCOL.md、PROTOCOL.json | oracle一致、argmax不低于同池其他选择器归入正确性/诊断，不当创新Go |
| 定义姿态分解 | METHOD_PROTOCOL.md | 写出I_B/I_R、端点yaw、规范点、重复处理、suffix不变判据、B_e不得集合相减 |
| 明确计费单位 | PROTOCOL.json、预算说明 | 分别限制枚举、粗查询、精评分、输出，承认最多5替代精评分；固定共用deadline |
| 定义接口失败语义 | METHOD_PROTOCOL.md | deadline/内存/无效结果/清理/全部候选中断回退，不只写all-or-nothing口号 |
| 限定池失败解释 | SOURCE_AUDIT.md、DESIGN_REVIEW.md | per-Edge最短插入不是收益支配，真实Edge必要性只是待验证设计，失败不外推全部主线 |
| 明确冻结输入与时间分层 | PROTOCOL.json | 引用原snapshot/request SHA与camera/config fingerprint；明确早中晚划分依据，不看本批结果再定 |
| 固定选择数值合同 | METHOD_PROTOCOL.md、PROTOCOL.json | U0=0、T≈0、1e-9为比较容差、所有同分键、非有限输入、相邻合并后的Edge身份 |
| 更新续接指令 | CODEX_HANDOFF.md、STATUS.md | 暂缓原样E1，修正旧commit与push模板，保留原版本与本审核对照 |

不应覆盖a5bed84所登记的旧协议，应另存修订版并列明改动理由。此时E1尚未采集，允许
实施前修订；不能在修订批次看完结果后再改条件。建议将“是否继续生成创新”设为独立
决策，不让基础评价验证通过自动推出普通SCI/EI创新足够。

## 11. E1 Acceptance and Kill Criteria

### 推荐保留的工程门槛

- 六个固定状态全部留档，13为零生成/零camera负控制；五个有效状态不替换。
- 全部实际评价候选的合成地址与完整重算一致；同U和同tie规则下的最优选择也必须一致。
  这里是工程PASS，失败应定位实现/定义，不能解释为研究假设被否。
- 共用snapshot/config、独立候选history、预算失效不泄露结果、语义一致的安全检测。
- raw、unique、marginal的验证范围分别说明；如果只合成unique集合，不声称重建了全部序列。

### 推荐保留但降级为开发集诊断的价值门槛

- 至少3个状态有真实不同、安全、运动合格的候选；至少2个状态有正预测U改进。
  保留当前条件可控制工作量，但只称“此固定池有局部价值”，不称方法稳定有效。
- 与Geometry/Naive至少1状态严格差异可作为评分规则诊断；不能称生成创新通过。
- 报告每状态的绝对new/lost、时间增量、U变化、最佳可得U及被筛选阶段，不能只给均值。
- 1e-9是浮点比较容差，不是有科研意义的改善阈值。现阶段不根据已知0.58%和6.48%
  反设一个“恰好能通过”的百分比。论文效应门槛需在新的独立批次前另登记。

### 需要删除其“科研准入”含义的条件

若P为固定池，Proposed严格用完整U，则：

```text
U_proposed = max(U_reference, max_{tau in P} U(tau))
```

同池Geometry/Naive最终选择都是P中的路线或reference，所以在相同模型下：

```text
U_proposed >= U_geometry_effective
U_proposed >= U_naive_effective
```

这是逐状态成立的定义性质，五状态均值不低于两者无需实验才能知道。“有2个正候选状态”
在精确argmax正确时也自动意味着Proposed会选中至少2个。因此不能将这些相关/必然条件
累计描述成多条相互独立的创新支持证据。

### 预算及退出

- E1通过仅允许登记精确合成 vs 全路重算的同输入成本比较，并准备E2；不自动执行E2。
- E2保留50/475/500ms及实际完成数要求，但明确只在固定状态上的有限工程准入；3次计时
  不是实时最坏情况证明，未通过的状态必须报告。
- 几何池供给/收益失败：关闭当前固定表示/筛选分支，不加池、不补seed追正结果。
- 合成精确却无成本收益：降为正确性基础，不宣称增量加速贡献。
- 未来生成器在同一最终评价器与预算下不能改善候选质量：关闭“观测引导生成”主张。
- 预测改进无法转化成actual observation或被执行层持续抹掉：记录limitation并停止主要
  性能主张，不能添加Confidence/语义/能耗掩盖失败。

## 12. Final Development Decision

**不建议原样开始I3-02E1；建议先完成第10节的协议修订，再做一次收敛后的基础验证。**

修订后可实施：隔离的pose-set预算接口、规范的changed-window分解、B_e/C精确合成、
固定几何池生成和同池评分诊断。仍禁止自动进行在线整合或新seed性能实验。

对论文主线的判断是：**有真实问题和可复用成果，值得有限继续；主要贡献尚未闭合。**
普通SCI/EI可以接受成熟框架上的非平凡改进，但必须证明具体机制带来了什么，而不能靠
“point换edge、几何候选再排序、同目标oracle一致”凑成创新。下一步最有价值的是把
“评价怎么更省且正确”和“观测怎么改变候选生成”分清楚，各自用能证伪的实验回答。

### 审核交付与未做事项

本报告按用户要求单独保存在下载目录。项目源码、实验记录、原协议、总交接和Git提交
未修改；未编译、未运行新实验、未启动ROS/Gazebo、未推送GitHub。
本次报告已完成，后续无需重复本轮审核；从“协议修订”开始，不能直接照旧交接运行E1。
