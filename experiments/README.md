# CERLAB研究工作入口

先读[总体交接](CODEX_HANDOFF.md)和[当前必读文档索引](ACTIVE_DOCUMENTS.md)。
当前Legacy默认配置保留；I3已关闭，A/B未立项。I4-01增量收益原型已完成，
正确性通过但成本门槛失败，停止且不自动进入I4-02。
历史报告里的下一阶段计划不自动构成当前授权。

| 需要查看什么 | 入口 |
|---|---|
| 固定指标、10seed与复测政策 | [Benchmark最终报告](benchmark_v2/FINAL_BASELINE_10SEED_2026-09-17.md)、[指标](benchmark_v2/METRICS_SPEC.md) |
| 各阶段正式结论及可复用组件 | [当前索引](ACTIVE_DOCUMENTS.md) |
| 最新方法取舍 | [I4-01最终报告](i4/I4_01_REPORT.md) |
| 原始数据是否已备份 | [备份审计](maintenance/HISTORICAL_GITHUB_BACKUP_AUDIT_2026-10-14.md)、[I3上传收据](i3/I3_GITHUB_SYNC_RECEIPT.json) |
| 此次整理/恢复旧文档 | [清理明细](maintenance/DOCUMENT_CLEANUP_2026-10-14.md) |

`benchmark_v2/`保留指标/地图mask/正式汇总；`r1/`至`i4/`保留正式决定、冻结协议/输入、
结果及复核证据；`analysis/`、阶段Python脚本保留复现工具。旧贡献草稿、完成阶段的启动
提示词/中途进展已压缩归档，避免与当前计划混淆。原始数据与历次正式备份继续保留。

历史地图点数是代理量，不可混作Benchmark Coverage；覆盖率分母、人工清空排除与
停止条件见冻结指标。I3数据在GitHub Release，其他阶段原始数据未全部上传。
