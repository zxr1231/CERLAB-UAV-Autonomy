# CERLAB 项目交接：当前状态与工作入口

更新：2026-10-15，已完成上一轮文档整理的交接收尾。本文件是新Codex对话的主入口。阶段研究已经结束的部分只作复现依据，
历史文件里的“下一步”不能替代本文件和用户最新指令。清理前完整交接已压缩归档。

## 1. 当前结论与授权

- 目标为普通SCI/EI及后续研究生论文，优先仿真。
- Benchmark v2、R1、R2、I1、I2已完成；I3最终原型已实现、测试并关闭。
- **I3-03-02：METHOD_NOT_SUPPORTED。** 不再修改该方法、追加seed或复测追求正结果。
- A（执行前缀选路）/B（双时域协同）复核完成。A-lite工程较轻，但两者原样均未被认可
  为有明确差异的论文主方法。此前口头I4-01安排已撤回，I4未立项。
- 用户要求暂缓上传剩余原始数据；阶段文件与文档整理已完成，清单和恢复归档均已保留。
- 后续算法开发需要用户明确的新任务；当前没有正在运行的实验或自动待执行阶段。

当前必读文件见[ACTIVE_DOCUMENTS.md](ACTIVE_DOCUMENTS.md)，目录入口见[README.md](README.md)。

## 2. 环境、Git与运行保护

```text
Ubuntu 20.04 / ROS Noetic
研究工作空间：/home/zxr2/cerlab_benchmark_ws
项目：/home/zxr2/cerlab_benchmark_ws/src/CERLAB-UAV-Autonomy
原可运行工作空间：/home/zxr2/cerlab_ws（保留）
当前研究分支：feat/i3-opportunity-prototype
global_planner：0221483818fdbadf3dc64b3bf84ec3e286959bca
autonomous_flight：33422e2d5ff2c8e405013df5abb72f388351eb00
map_manager：f6d2e925b47916a5cb3b72e011af6f3a17dbdd26
uav_simulator：cc8c8a6dce0214d9ba99a3189272f05dc8807d24
```

父仓库HEAD请实际运行git log查询；上传后新增的历史备份审计/文档清理提交仅在本地。
I3代码和数据的远端快照不受这次文档整理影响。开始任务先读适用AGENTS.md，查Git/
submodule/进程，保留用户修改、冻结输入与失败。不要升级系统/ROS、重clone、覆盖个人
文件或删除已有目录；依赖安装前说明用途。不要启动重复ROS/Gazebo实例或宽泛pkill。

仅仿真。Orbvi/Jetson/PX4等实机计划未获运行授权，不刷飞控、不解锁、不执行真实飞行。
不自动开启rosbag。代码改动放研究分支/隔离工作空间，Legacy保持默认。

## 3. 当前运行基线与公平条件

基础为HIRE-style Frontier引导的增量PRM，类名仍为DEP。
`findBestPath()`已经累加中间节点收益；未知体素收益有重复计数，Goal预筛依赖节点收益，
每Goal通常一条距离A*路线。`shortcutPath()`为几何/碰撞简化。不能称首次路径收益、
首次体素union、普通K-shortest或普通cache为主要创新。路径history收益不能作为普通
可加负边权塞入A*。

默认Legacy＋返航，completion_gain_threshold=500；这个500是旧收益阈值，不是coverage
百分比，也不是500ms计算预算。Physical深度相机5m，旧planner proxy2m；5m shadow仍有
Unknown遮挡不可知的限制，不能当真实观测或完整SLAM不确定性。

Benchmark冻结scene/sensor/速度与加速度/start/安全距离/地图分辨率/seed/停止规则。
主场景floorplan2_dynamic_5.world。Coverage以task-accessible-free区域及冻结分母定义；
sensor provenance排除人工起飞清空。飞过已知自由区域不能一概算无效重访。分别记录
simulation time、wall time、planner time、实时率、失败/超时/未达到的T阈值。

10seed下游基线（均值±样本标准差，详见正式报告）：

| 指标 | 值 |
|---|---|
| T80 / T90 | 229.47±25.74 / 282.96±21.39 s |
| T95 | 375.50±34.19 s |
| 探索完成时间 | 437.94±48.54 s |
| 探索距离 | 181.41±21.72 m |
| 最终accessible-free Coverage | 0.95757±0.00414 |
| 全局规划均值 | 45.00 ms |
| 实时率均值 | 0.99916 |

T95采用用户已登记的seed3/9/10复测选择政策，原结果保留；不能把该政策倒用到新的
算法配对实验，也不能重跑直到有利。正式新对照需同版本/同条件，不能直接用旧汇总代替。

## 4. 已完成阶段与证据边界

| 阶段 | 最终结论 | 权威入口 |
|---|---|---|
| Benchmark v2 | 10seed完成、冻结指标与失败/复测记录 | [最终基线](benchmark_v2/FINAL_BASELINE_10SEED_2026-09-17.md)、[指标定义](benchmark_v2/METRICS_SPEC.md) |
| R1 | 重叠计数确实存在，有时改变排名；不是效率改善证明 | [最终决定](r1/R1_FINAL_DECISION.md)、R1_FINAL_SUMMARY.json |
| R2 | 5m匹配shadow比旧2m proxy更接近执行观测，但晚期Unknown遮挡仍过估 | [最终决定](r2/R2_FINAL_DECISION.md)、R2_06_VALIDATION.md |
| I1 | Unique-only三seed未稳定改善；3/3实际新增观测每米下降，Legacy保留 | [最终决定](i1/I1_FINAL_DECISION.md) |
| I2 | generic多路线没有稳定优势；早期pilot含反馈缺陷，失败及修复边界保留 | [最终决定](i2/I2_FINAL_DECISION.md)、[执行诊断](i2/I2_00_DIAGNOSTIC_REPORT.md) |
| I3 | 正确评价机制支持，主要生成原型不支持，关闭 | [最终原型报告](i3/I3_03_02_REPORT.md)、[状态](i3/STATUS.md) |
| A/B候选复核 | A-lite较易，A/B当前均未获论文立项认可 | [方法复核](method_reviews/A_B_METHOD_REVIEW_2026-10-14.md) |

R1：25状态/152路线，候选重复率52.19%，选中67.15%；Top1变化16%。
R2：19可比正式执行区间，shadow/旧proxy Jaccard0.531/0.087、count Spearman0.812/0.077，
晚期shadow precision0.186。已执行区间关联不能证明未选路线的反事实收益。

I2-00：51个改变选择中19个未执行到0.5m；seed2的222次近静止反馈主要触发于局部goal
unsafe，且当时Legacy/Unique同选。不能将其归因于收益排名或预设新时域方法能解决。
局部重规划可能保留全局目标；B-spline导出切线yaw不等于控制器执行yaw。

I3保留的重要结果（报告/协议/JSON仍在原路径）：

- I3-00：5m内核集合正确；完整多候选成本未过500ms。
- I3-01B：双路线供给/预算未准入。
- I3-01C：shortcut删预测观测，但直接恢复raw10/10违反运动条件且单位时间收益更低。
- I3-02A：单锚点proxy不支持；I3-02R仅事后segment信号，不是在线方法证明。
- I3-02E V2 E1：13/13精确合成正确；有限池价值不足，未进入E2。
- I3-03-01：AABB条件上界计数/成本通过，K1无优势、正例推迟，关闭该机制。
- I3-03-02：38旧状态（37有效/1负控制），304并行任务；扩展32状态对motion为1/29/2，
  对geometry为1/31/0；500ms完成54/111=48.65%，未过预登记门槛。28状态有两锚点
  输出，但0两锚点最终选中。仅模型预测收益，未测新的完整仿真T95/实际观测。

I3快照来自floorplan1_static、environment/planner seed4的一条历史轨迹；38状态相互相关，
不是38个独立seed，也不是Benchmark主场景的完整任务对比。

旧开发状态的局部正结果不能挽救扩展记录失败；不修改冻结数据、改门槛或补模块掩盖失败。
这些负结果不证明所有informative planning都不可能，也不允许将旧原型换名继续。

## 5. 源码复用入口

- `global_planner/include/global_planner/dep.cpp`：候选Goal、路线、Legacy/Unique选择、shortcut。
- 同目录`pathGainEvaluator.*`、`cameraGainEvaluator.*`：不可变地图上的路径收益/相机集合。
- 同目录`routeSearch.h`、`routeCandidates.h`、`routeSnapshot.h`：图搜索、控制组和安全快照。
- 同目录`opportunityRoutes.h`：已关闭I3原型，保留复现，不默认启用。
- `autonomous_flight/include/autonomous_flight/simulation/dynamicExploration.cpp`：执行/重规划/
  返航/日志；`trajectory_planner/.../bsplineTraj.*`：有状态局部优化接口，不是候选只读预演。
- `exploration_benchmark/`、`experiments/analysis/`：冻结评测、日志关联、汇总与复核工具。

保留正式协议/输入注册/结果JSON和分析测试脚本，不能因阶段结束而删除复现依赖。

## 6. 本地数据与GitHub备份边界

原始数据仍在本地，约6.55GB目录文件逻辑大小，含副本；尚未全部上传约5.21GB。

```text
/home/zxr2/cerlab_benchmark_ws/results/EXP-BENCH*
/home/zxr2/cerlab_benchmark_ws/results/EXP-I1*、EXP-I2*、EXP-I3*
/home/zxr2/cerlab_benchmark_ws/results/EXP-R2-06-SENSOR-SHADOW-SEED1-V1
/home/zxr2/cerlab_benchmark_ws/results/R2_FINAL_REFERENCE_20260922
项目experiments/r1/snapshots、r1/studies、r2/results
/home/zxr2/下载/CERLAB_R1_Backups、CERLAB_R2_Backups、CERLAB_R2_Final_2026-09-22
/home/zxr2/下载/CERLAB_I1_Backups、CERLAB_I2_Backups、CERLAB_I3_Backups
```

I3全部12结果目录、历次I3本地备份、seed4完整源运行111快照/日志、10仓库Git bundles
已远端核验。其余阶段代码/已提交报告已上传，但原始数据不全；原始数据被.gitignore
排除，git push不等于全数据备份。[历史备份审计](maintenance/HISTORICAL_GITHUB_BACKUP_AUDIT_2026-10-14.md)。

- [GitHub最新已上传I3分支](https://github.com/zxr1231/CERLAB-UAV-Autonomy/tree/feat/i3-opportunity-prototype)
- [I3完整Release](https://github.com/zxr1231/CERLAB-UAV-Autonomy/releases/tag/i3-complete-backup-2026-10-14)
- [上传收据](i3/I3_GITHUB_SYNC_RECEIPT.json)：代码tag快照cc47ef4，后续远端收据提交78c7e9f。

上次上传的临时压缩包/Git bundle副本此次整理后可从Release重新下载；本机原始数据和
历次正式备份不变。上传清单、SHA/远端收据保留在下载/CERLAB_I3_GitHub_Uploads/2026-10-14。

## 7. 文档整理与恢复

当前索引[ACTIVE_DOCUMENTS.md](ACTIVE_DOCUMENTS.md)。清理前文档及完整旧交接的核验归档：
`/home/zxr2/下载/CERLAB_Document_Archives/CLEANUP_2026-10-14/documents_before_cleanup.tar.gz`。
归档manifest记录旧路径/成员名/散列；恢复到新目录，勿覆盖当前目录。被归档的提示词/
贡献草稿/过程进展不再是当前执行指令。冻结协议硬引用的文档仍保留。

完整清理明细：[DOCUMENT_CLEANUP_2026-10-14.md](maintenance/DOCUMENT_CLEANUP_2026-10-14.md)。
下载文档入口：`/home/zxr2/下载/CERLAB_Research_Documents/README.md`。

整理结果：22份过时文档已核验压缩归档，1份当前审核结果重排，14份远端已验证的上传
临时副本移除，文件占用净减少约362MiB。原始5436文件、6个正式备份树和9个子模块
核验保持不变；源码/配置未改，正式协议与失败记录保留。整理后文档归档为同目录
`current_documents_after_cleanup.tar.gz`，内部manifest可逐文件核验。
文档整理与交接收尾只做本地提交，没有推送GitHub或补传历史数据。

## 8. 后续工作底线与沟通

最多一次有界方案定稿，然后核心实现与固定对照；若不能定义方法差异，明确停止/调整
研究问题，不新增连续独立诊断阶段。当前I3已完成最终去留测试，禁止方法修订复测。
普通SCI/EI允许渐进改进，但已有思想改名、改权重、union/cache/via point不自动成为贡献。
新颖性依据原始论文和作者代码；最终贡献需实际观测与任务证据，不承诺正结果或录用。

多个独立测试按用户偏好并行，隔离ROS Master/端口/输出与硬件资源；共享资源可能污染
固定计时口径时先说明并采用已登记的安排。中途提问简短回答后继续任务，不因此结束。
普通备份为本地校验备份；大任务完成或用户明确要求时才推GitHub。此次清理本地提交，
不补传历史原始数据，不自动推送。任务后更新本交接，保留未完成步骤和真实限制。

新对话提示：完整读本文件、当前文档索引，核查Git/进程后按用户新任务执行；不要重跑
已经关闭的I3、R1/R2诊断或自行启动I4。用户尚未选定下一论文主方法。
