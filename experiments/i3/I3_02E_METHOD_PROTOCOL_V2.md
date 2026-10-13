# I3-02E V2：局部走廊集合合成与受限候选价值验证

2026-10-13，实施前修订。当前状态：协议完成，未实现、未采集E1数据。
本文件与I3_02E_PROTOCOL_V2.json、I3_02E_INPUTS_V2.json共同构成当前执行合同。
a5bed84中的四份E文档原样保留为V1，不能继续使用其“主要方法准入”解释。
依据：[独立审核](I3_02E_ASTRA_AUDIT.md)。变更清单见I3_02E_REVISION_V2.md。

## 1. 本批回答什么

E1验证：在固定几何池内，局部可见集重算能否与完整路线精确一致，以及该受限池有没有
值得继续做计算成本验证的候选。**这是评价器基础批次，不是观测机会引导生成。**
union、via Edge、精确argmax和普通缓存均不单独算主要创新。
I3-02A失败与I3-02R的事后诊断原样保留。02R的相关性受共享完整marginal和窗口覆盖率
影响；“距走廊比距锚点近”有几何包含关系，不证明真实PRM Edge的必要性。

## 2. 固定输入与环境

沿用1/13/14/26/27/38，原snapshot、request、result的SHA见INPUTS_V2。负控制13只做
元数据核验，不构图、生成或调用camera。其余全部留在分母，不替换seed/状态。
沿用I3-01B预先划分：early=1/13，middle=14/26，late=27/38；不是Coverage阶段。
地图为已保存export snapshot，pose/goal/yaw来自已记录request，不是假装原时刻在线重放。

INPUTS_V2锁定完整camera JSON、motion model、planning region、start pose/yaw、terminal
yaw、accepted与goal，以及map/planner/manifest/request字节。结构化fingerprint使用
UTF-8 JSON，sort_keys=True、separators=(',',':')、ensure_ascii=False、allow_nan=False。
快照SHA充当本离线批次地址空间epoch；在线以后需额外reset generation。不得仅用version或
瞬态Graph ID跨快照复用。原物理sensor、FoV、速度/加速度、任务区、安全距离与停止条件不变。

## 3. 几何池：保留V1的受限假设

用真实有向PRM Edge u→v及安全连接p_e→u、v→p_(e+1)替换参考的一段。
排除含临时start ID0的Edge，不对有向Graph自动对称化。按(e,u,v)枚举，每状态最多12000
对；每对包括被拒绝者，只有尚有组合未访问才算truncated。边本身和连接段均重新核验。
沿用RouteSnapshot::free/freeLine的已知未膨胀自由语义。该检查是离散采样，不宣称严格
连续体素安全；本批不改变所有历史控制的安全语义。

每个Edge仅保留安全、运动合格路线中估计time最低的插入位置；同分取e较小者。按
(time,length,u,v,e)排序并使用等长位置序列1e-6去重，保留排序靠前者；不宣称连续曲线
或可见集合等价。n>5取floor(j*(n-1)/4),j=0..4；否则全部保留。相同池用于所有评分控制。
不读取camera决定池，不扩大池。该筛选可能漏掉有观测价值的位置，不存在收益支配保证。

### 规范点与重复规则（V2显式收紧）

- 参考节点与其坐标/yaw不得更改；不删参考共线点或重采样原参考。
- u与p_e、v与p_(e+1)若坐标逐分量完全相等，可合并为同一个边界姿态，保留原Graph
  Edge端点ID作为provenance；与边界仅接近但不精确相等（距离<=1e-6）则拒绝为
  NEAR_BOUNDARY_AMBIGUITY，不能挪动边界点让ray结果变化。
- u/v与窗口外参考节点非相邻重复（距离<=1e-6）、u/v之间距离<=1e-6、其他零长度段均拒绝。
- 去除精确相邻重复后，若替换链每点到原段距离<=1e-6且链长减原段长<=1e-6，拒绝为
  NO_GEOMETRIC_CHANGE。这是固定表示筛选，不是可见集合相等的证明。
- 原参考本身有相邻退化段或输入非有限时为INVALID_CONTEXT，保留错误；不偷偷修参考。

运动使用既有公式T=L/v+yawPenalty*sum(abs(remainder(delta_yaw,2*pi)))/angularSpeed。
保持start/terminal yaw，重新算整条候选。L/T<=参考的1.25倍，额外yaw<=pi/2，边界包含。
这是估计代价，不是实际加速/B-spline时间。T<=1e-6、L<=1e-6参考拒绝为DEGENERATE_REFERENCE；
candidate同样拒绝。负数或非有限motion参数拒绝，yawPenalty允许0，速度/角速度必须>0。

## 4. 唯一采样与集合分解

沿用twoStageFixture::sample合同：先初始pose；每非零平移段前以std::remainder最短yaw
旋转，ceil(abs(delta)/0.1)步；平移ceil(length/0.25)步；最后terminal yaw旋转。
朝向atan2(dy,dx)，严格垂直段dx=dy=0使用固定yaw=0，不能新增自由yaw优化。
±pi同分保持std::remainder及原输入符号，不额外包角或替换旧样本；跨语言oracle必须一致。
连续重复pose仅按旧append的1e-12位置和angleDistance判定去重，不能用几何1e-6代替。

使用同一带事件标签的采样器生成完整候选姿态，随后按规范边界取changed window：

1. B的prefix保留抵达p_e时的pose（e=0为初始pose），窗口从其后转入新方向的样本开始；
2. 窗口包含最多三段的所有旋转与平移，含p_(e+1)到下一参考方向的旋转；末段则含terminal旋转；
3. suffix从下一原参考段的平移样本开始；初始重复端pose被append跳过时，不手动补回；
4. 精确重叠边界导致空连接段时跳过该连接，依事件而非固定节点索引划分。原单锚点标签器
   不可直接用于两节点走廊。

定义索引I_B为参考不变prefix/suffix，I_R为其补集。实现必须验证候选未变pose与参考
position/yaw逐项匹配（1e-12诊断容差），并真正复用同一规范姿态值，不能重新浮点近似
生成后假定ray地址相同。完整oracle仍独立按同合同重算；任何地址不一致为工程FAIL。

```text
B_e = union V(q), q indexed by I_B
R_e = union V(q), q indexed by I_R
R = B_e union R_e
C = union V(q), q in candidate changed window
V_candidate = B_e union C
new = C minus R
lost = (R_e minus B_e) minus C
U = |V_candidate| / T
D = |V_candidate| - |R| - U0*(T-T0)
```

**禁止B_e=R minus R_e。** 允许直接union、分段prefix/suffix集合或精确引用计数；选择
数据结构不改变合同，所有分配和构建计入。端姿态可在局部计算中重复，但union、raw与
marginal统计必须依据去重后的完整pose序列。

E1要求重建每姿态visible-set序列，raw=sum|V(q)|，marginal=该pose相对前缀新增地址数。
候选独立history，从复用集合重新计算suffix marginal，不能直接复用参考marginal数值。
与oracle逐地址/逐marginal/raw/unique比对；JSON完整地址可保存，线上不把序列化算作收益。
此精确性只属于冻结地图shadow和指定姿态，不外推actual observation或B-spline。

## 5. 控制与数值合同

三种同池规则改名为：

- geometry_with_u_fallback：min(time,length,u,v,e)，再用所选路线U与reference比较；
- new_only_with_u_fallback：max|C\R|，同分取(time,length,u,v,e)，再共同U回退；
- exact_net_rerank：全池精确U最大，再与reference比较。旧proposed_net_corridor名称停止用于V2。

extra之间用精确数值严格排序，U完全相同取(time,length,u,v,e)最小，避免epsilon比较器
破坏排序传递性。只有U_best>U0+1e-9才替代reference，其余回退；1e-9仅数值容差。
U0=0合法：报告绝对收益与选择；相对比例为null，另报有效比例分母，不制造epsilon分母。
无池时extra=null/回退参考，仍属于五状态分母；valid=false的结果不可当作gain=0的候选。
D只作净值/正负诊断，不拿argmax D替代argmax U。

同池oracle argmax一致是实现检查；exact_net_rerank不低于同池两弱规则是定义性质。
这两项不作为科研效果或生成创新门槛。后续生成比较必须允许各方法输出不同候选、使用
相同母集/预算/最终评价器；不能声称本批已验证Generic K或观测驱动生成。

## 6. 预算API合同与成本账

新接口限test-only fixture及所需可选budget API，不改变相机光学内核/部署默认行为。
预算对象必须包含一个共享steady_clock绝对deadline、累计pose/voxel访问计数、内存计数；
各pose/走廊不能重置预算。E1无500ms准入时deadline可为infinity，但单元测试必须覆盖
已过期deadline、访问数/pose上限、分配上限和中途取消。

固定工程内存上限：可见集合/marks/索引/合成scratch合计256MiB，allocator或等效分配计数
在分配前检查，包含容器容量与节点/桶分配；不只是4*地址数。map输入和光学模型另报字节，
总RSS/峰值另外记录。该上限是实现前保护性工程常数，不是性能结论；触发即RESOURCE_FAIL，
本批不得临时提高。可流式释放不再需要的集合，不得凭无效结果释放后继续评分。

输出结构至少含valid/failure_reason、context fingerprint、完整pose sets或精确分段等价
结构、union/raw/marginal和资源计数。异常/取消/超时返回valid=false、无可用地址/收益，
统计计数可以保留。单个参考或任何本控制必需走廊不完整，整次控制记incomplete并回退，
不能用已完成子集偷偷声称全池最佳。已安全验证reference不可用时不提交任何路线。

E2只保留计划约束，不能在本轮自动运行：

```text
t_B：snapshot/准备开始，整阶段500ms
t_G：几何池开始，deadline=min(t_G+50ms,t_B+475ms)
t_score_deadline=t_B+475ms（中断正在进行的评分）
t_final_deadline=t_B+500ms（包括安全检查、失效处理和释放）
```

所有分配/模型构建/union/排序/复制/最后提交都检查剩余时间；内核现有末次check之后的
排序和析构仍要计入外层wall clock。25ms预留不保证锁等待完成；超时记录并拒绝提交，
不是硬实时最坏情况证明。fresh map检查必须区分冻结fixture检查与真正在线新地图检查。

资源计数分别保存：pair_enumerated<=12000、motion_feasible、routes_constructed、
pool_size<=5、coarse_observation_queries=0、reference_exact_evaluations=1、
corridors_exact_evaluated<=5、routes_exact_scored<=6（含reference）、extra_output<=1。
独立full-recompute oracle最多6条，专列oracle成本；不能把5条精评分说成参考+1条。

E1共享集合的离线描述成本不用于公平部署比较。后续Geometry+回退只计算自身需要的
reference和所选路线；new-only/exact各自承担全部所需观测查询，不能接收另一个控制的
免费集合。合成与全路重算的计时对照则严格使用同输入池、独立准备和同输出。

## 7. E1执行顺序与结论

一次固定批次，不做新仿真、新seed或候选补齐。先实现/编译并通过必要测试，再冻结代码。
生成与筛选日志先保存；计算reference与每走廊集合并冻结三规则选择；随后独立全路重算
做正确性oracle。跨状态或中断恢复先核对代码/协议/binary/hash，完成项禁止重采。
记录失败attempt，不因效果负面修评价器；只修可复现接口/工程错误且保留证据。

### 工程门槛（必须全部通过）

六状态/负控制有效，输入和原记录hash不变；完整pose与集合合成正确；raw、逐步marginal、
union地址与oracle一致；同U/tie下全五状态选择相同；上下文/资源失败正确拒绝；安全语义不变。
任一不满足为ENGINEERING_FAIL或RESOURCE_FAIL，不能转成科研失败或有利重跑。

### 受限池开发价值条件（不是创新准入）

至少3个非截断状态有不同可行extra；至少2个状态有U>U0+1e-9的候选。仅这两项作为
继续准备成本验证的实用条件，保留V1数量以避免再针对02A结果调阈值。未满足分别为
LIMITED_POOL_SUPPLY_FAIL / LIMITED_POOL_VALUE_FAIL，停止本池，不加seed或扩大12000/5。
报告Geometry/new-only差异、所有效应量和相对均值，但“至少胜1次”“均值不低”不再当
独立创新门槛。所有参考/候选实际得分和回退前退化必须保留。

工程与局部价值均满足：FOUNDATION_PASS_COST_STUDY_PENDING。
这个状态只允许以后登记合成vs全路重算的成本协议，**不自动运行E2，不准入生成创新**。
工程正确但没有局部价值不证明所有观测引导方案不可能；无实际加速则仅保留基础评价用途。

E2若以后单独登记，预算完成至少3有效状态且覆盖既定early/middle/late，3次均完成该
控制所需全部工作，报告所有失败；无池不填充。早期只有状态1可有效，因此若状态1无供给，
不能满足这条跨阶段门槛，明确为固定样本证据不足，不能后验把14改成early。

## 8. 结束与以后研究

E1完成即报告/本地备份/停止。不得自动进入E2、I3-03、在线B-spline或持久cache。
真正观测引导生成另需一个有限查询的协议：在候选池锁定前，观测残差改变扩展/连接选择，
与相同母集、预算、最终精确评价器的几何生成器比较。此机制在V2仍标为未定义。
本次不追加无关模块，不改冻结I1/I2/02A/02R的数字或结论。
