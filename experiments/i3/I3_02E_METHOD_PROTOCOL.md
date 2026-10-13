# I3-02E：参考路线条件下的观测机会Edge/短走廊协议

2026-10-13；状态：方法与下一批离线协议已定义，尚未实现或运行。I3-02A的
`PROXY_NOT_SUPPORTED`不变，I3-02R只提供事后路段信号。

## 方法对象

固定Stage A安全接受的同一Goal、最终参考路线`tau0`、start pose/yaw、terminal yaw和
immutable map snapshot。枚举参考段`(p_e,p_(e+1))`与当前Graph中不含临时start ID0的
有向Edge`u->v`，构造：

```text
tau(e,u,v) = tau0 prefix + [p_e,u,v,p_(e+1)] + tau0 suffix
```

相邻重复点以1e-6合并；非相邻重复节点/位置、零长度或无几何变化拒绝。`u->v`必须在
Graph中；两条连接段和完整候选必须通过同一`RouteSnapshot::freeLine`。Unknown不自由。
保留`u->v`及连接段，不再调用普通shortcut。所有对照都用同一候选表示。

完整候选按既定速度、角速度、yaw penalty和terminal yaw重新计算length/time/yaw；相对
`tau0`必须同时满足length/time<=1.25及额外yaw<=pi/2。不是用平移距离代替执行时间。

## 有界几何池

枚举顺序固定为参考段index升序，再`u`、`v`升序；每状态最多12000对，达到上限且仍有
组合则标记截断。当前固定fixture最大11520，不应截断。保存所有重叠拒绝原因。

对每个有向Edge只保留最终time最小的插入位置；同time按参考段index。之后按time、
length、u、v、段index排序并以1e-6整条位置序列去重。若合格数<=5全部进入共同池；
否则取排序索引`floor(j*(n-1)/4), j=0..4`。池构造不读取camera gain、不得补齐或换样。

## 精确参考条件走廊评价

参考路线使用既定5m mapper-shadow、0.25m平移/0.1rad原地最短yaw采样。一次请求内获得
每个参考姿态的可见Unknown地址集合，形成`R=V(tau0)`。对插入位置e，将参考姿态分为：

- `B_e`：不会因替换改变的prefix/suffix姿态union；
- `R_e`：从`p_e`转向原参考段、沿原段运动，并在`p_(e+1)`转向下一参考段或terminal
  yaw的changed window。

候选走廊`C(e,u,v)`从抵达`p_e`时的yaw开始，完整采样`p_e->u->v->p_(e+1)`，并包含
出口处转向下一参考段或terminal yaw。完整候选预测集合定义为：

```text
V_hat(tau) = B_e union C(e,u,v)
new  = V_hat(tau) minus R
lost = R minus V_hat(tau)
U(tau) = |V_hat(tau)| / T(tau)
D(tau) = |V_hat(tau)| - |R| - U(tau0)*(T(tau)-T(tau0))
```

最终排序使用`U(tau)`；只有严格高于参考1e-9才选择额外路线，同分保留参考。必须同时
记录new/lost/D，禁止只累计新增体素。候选history相互独立，不能把D作为普通负边权放入
A*。离线必须将`V_hat`地址与整条候选完整重算逐地址比较；不一致为工程失败。

下一实现需要budget-aware、all-or-nothing pose-set batch接口。超时不得泄露部分集合或
参与排序。request-local参考pose reuse计入准备/参考成本；没有跨规划持久Edge cache。

## 同池对照

每状态最终都是参考+最多1条额外路线；共同几何池最多5条：

| 控制 | 从共同池选额外路线的规则 |
|---|---|
| Geometry-edge | 最小最终time，再length/u/v/段index |
| Naive-new | 最大`|C minus R|`，忽略lost和运动代价；同分按time等稳定键 |
| Proposed-net-corridor | 最大完整`U(tau)`，使用`B_e union C`；同分保留参考/稳定键 |
| Full-route oracle | 完整路线5m重算，只在选择checkpoint后做离线正确性/上界验证 |

Geometry-edge和Naive-new先按各自规则确定一个额外路线，再用完整合成收益与参考比较；
额外路线不严格优于参考时回退参考。各控制的`effective utility`即该最终参考/额外选择的
收益率，不能用共同池中另一个oracle候选替换自己选错的路线。

Generic K-shortest和Geometric-diverse保留为后续H3对照，不在第一批重跑。第一批只回答
Edge/走廊表示是否提供候选、合成是否精确、观测/代价联合规则是否区别于简单对照。

## I3-02E1 固定离线批次

仍使用状态1/13/14/26/27/38及原SHA；13为安全拒绝负控制，零枚举/零camera调用。
五个有效状态全纳入，不增加seed，不称held-out。一次批次：

1. 实现隔离candidate/pose-set fixture和必要测试，不修改在线`dep.cpp`默认路径；
2. 生成共同几何池，保存全部组合、拒绝、per-Edge最佳、去重和分层记录；
3. 计算参考pose集合及五条以内走廊集合，冻结三个控制选择；
4. 选择checkpoint后才做完整路线oracle，验证地址、收益和选择；
5. 报告组件wall time/voxel visits/pose数/峰值scratch，但不宣称500ms准入；
6. 输出后结束，不自动运行预算批次或仿真。

工程测试至少覆盖：有向Edge方向；start Edge排除；Unknown/膨胀安全；重复节点/位置；
12000边界；每Edge最小time插入；5分层索引；yaw wrap/terminal yaw；changed-window边界；
同计数不同集合；new/lost；独立history；map/config/version变化；budget中断全有或全无；
组合集合与完整路线地址精确一致；状态13零工作。

## 预注册决定

- 任一输入/hash、采样或集合精确性失败：`ENGINEERING_FAIL`，修复前不解释方法。
- 不截断且共同池非空的有效状态少于3：`EDGE_CORRIDOR_SUPPLY_FAIL`。
- 完整oracle中有严格高于参考收益率的候选状态少于2：`NO_USEFUL_EDGE_CORRIDOR_SUPPLY`。
- Proposed在有用状态中选中正收益路线的状态少于2，或五状态未全部匹配共同池full-oracle
  的参考/候选决定：`CORRIDOR_EVALUATOR_NOT_SUPPORTED`。
- Proposed有效结果必须至少1状态严格优于Geometry-edge、至少1状态严格优于Naive-new，
  且五状态平均effective relative utility分别不低于二者；否则
  `NO_DISTINCT_EDGE_OPPORTUNITY_SIGNAL`。同一状态可同时满足两项。
- 全部通过只得到`ADMIT_I3_02E2_BUDGET_PROBE`，不是在线/论文准入。

I3-02E2若获准，必须用同一实现、无离线可见集重用，warmup+3次，计入snapshot/模型、
reference pose sets、最多5走廊评价、集合合成、选择、fresh safety和cleanup。几何池形成
仍在嵌套50ms内；475ms停止新评分，25ms留最终验证，总Stage B<=500ms。至少3个有效
状态（早/中/晚且中晚各>=1）三次全部完成参考+实际额外候选才通过；供给不足不能填充。

若E1价值失败，停止该表示，不扩大池/改分层/增加seed。若E1通过而E2仅因可见性评价
成本失败，先用profiling证明具体复用率与瓶颈，再单独登记依赖感知Edge缓存；缓存必须
exact且其构建/失效成本计入，不能作为免费前提。无法做到则关闭当前主线。

## 科研边界

该机制仍建立在visible-set union、via corridor和已有PRM上，不能仅凭组件组合声称新颖。
论文主张只有在后续同预算下稳定优于Generic K/Geometry/Naive、预测与实际观测一致、
B-spline可执行且多seed/多场景成立时，才能表述为参考路线条件下的观测机会路线构造。
I3-02E不进行新的文献新颖性审核，也不改变I1/I2/I3已有负结果。
