# I3-02E V2 修订说明与当前决定

2026-10-13，用户授权按独立审核修订。仅修改研究文档，未实现算法或采集新实验。

## 生效文件

- I3_02E_METHOD_PROTOCOL_V2.md：执行合同。
- I3_02E_PROTOCOL_V2.json：结构化参数与判定。
- I3_02E_INPUTS_V2.json：已核验的六状态源SHA、stage和camera/context fingerprint。
- I3_02E_ASTRA_AUDIT.md：下载目录独立审核报告的原样快照；其中“尚未修订”描述属于审核时点。

V1的METHOD_PROTOCOL.md、PROTOCOL.json、SOURCE_AUDIT.md、DESIGN_REVIEW.md原样保留。
V2覆盖其未来执行指令，不覆盖历史事实。I3-02A/R报告、结果、代码均未修改。

## 审核问题到修订的对应

| 审核问题 | V2处理 |
|---|---|
| 几何生成后评分被叫作观测引导生成 | E1改为基础评价/受限池诊断，exact_net_rerank不再叫Proposed |
| oracle一致、同池最优不低于其他方法是必然性质 | 移入正确性/诊断；不再作为创新Go或“多条独立支持证据” |
| B_e集合差有误用风险 | 明确I_B/I_R，禁止R\R_e；允许精确union/引用计数 |
| window/yaw/近点合并不明确 | 事件分区、边界规范点、极短/垂直/±pi/端姿态、suffix history规则固定 |
| 评价5条但宣称2候选成本 | 明确reference1＋corridor<=5精评分、output<=1、oracle另计 |
| budget-aware API只写口号 | 统一绝对deadline、累计计数、256MiB可见scratch上限、invalid与整次控制回退、释放计费 |
| 相邻近点合并可能改真实Edge端点 | 只合并精确相等边界，近但不同点明确拒绝；实施前语义收紧需单独记录数量 |
| 每Edge最短位置筛掉有用插入 | 保留原固定筛池便于有限验证，但明确非收益支配；失败只关闭此分支 |
| 时间与安全被说得过强 | 改称估计motion time和离散freeLine检查，不宣称B-spline时间或严格连续安全 |
| 未锁输入和阶段标签 | registry保存源哈希/上下文fingerprint；沿用B阶段early=1/13、middle=14/26、late=27/38 |
| 未处理零参考gain/tie/invalid | U0=0可用、相对值null；exact sorting＋reference1e-9回退；invalid不可评分 |
| 真实Edge必要性未证明 | 仅作为有限表示；旧直连非Graph不推出必须via Edge |
| 交接旧版本与push模板 | 更新cde9ed0及V2入口；普通检查点只本地，大任务完成或明确授权才push |

## 决策分层

1. 工程正确性：采样、集合、raw/marginal/unique、同目标选择精确；失效不泄露结果。
2. 受限池局部价值：>=3非截断非空状态，>=2有正预测收益状态；不是论文效应证明。
3. 前两项通过：FOUNDATION_PASS_COST_STUDY_PENDING，只允许以后单独登记成本比较。
4. 生成创新仍未定义，不能由E1通过自动放行。需以后规定观测在池锁定前如何改变扩展/连接，
   与同预算同最终评价器的不同生成器比较。

E2跨阶段门槛如原样保留，early只有有效状态1；若1无候选就证据不足，不改14的阶段以放行。
这里提前揭示可达门槛的限制，不更改未来结果。资源上限是工程保护，不作为新贡献。

## 下一任务

下次收到执行指令后，从V2进行E1隔离接口/fixture实现、正确性测试、固定一次离线批次、
结果报告和本地备份后停止。先确认V2文档/registry/hash，不能运行旧V1协议或重跑I3-02A。
本次协议修订完成后停止，不自动开始上述实现。
