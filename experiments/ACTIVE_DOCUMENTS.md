# 当前必读文档索引

更新2026-10-15。文档整理和交接收尾已完成。新任务首先只读总体交接和最新决定，按需要打开阶段证明，不必从旧
阶段提示词重新开始。所有历史下一步建议以用户新指令和最新交接为准。

## 当前工作

- [CODEX_HANDOFF.md](CODEX_HANDOFF.md)：当前状态、基线、Git/数据与后续工作底线。
- [最新选题建议](method_reviews/INCREMENTAL_GAIN_TOPIC_2026-10-15.md)：增量地图上的精确路径收益更新，推荐直接做核心原型，尚未实施。
- [选题最终决定](method_reviews/TOPIC_FINAL_DECISION_2026-10-15.md)：A/B不批准立项，本轮选择结束，无自动补测/再筛选任务。
- [A/B方法复核](method_reviews/A_B_METHOD_REVIEW_2026-10-14.md)：当前两候选工程/论文取舍。
- [I3最终报告](i3/I3_03_02_REPORT.md)：代码已实现但主方法未获支持，原型关闭。
- [历史GitHub备份审计](maintenance/HISTORICAL_GITHUB_BACKUP_AUDIT_2026-10-14.md)：剩余数据仍本地。
- [I3备份说明](i3/I3_GITHUB_BACKUP.md)：已上传数据/代码与远端收据。

## 冻结基线与测量

- [Benchmark v2最终基线](benchmark_v2/FINAL_BASELINE_10SEED_2026-09-17.md)：10seed/复测政策。
- [METRICS_SPEC](benchmark_v2/METRICS_SPEC.md)：Coverage、T80/T90/T95、轨迹/碰撞/资源口径。
- `benchmark_v2/BASELINE.md`、`OBSERVABILITY_AUDIT.md`、`ARTIFICIAL_CLEAR_VALIDATION.md`：
  场景/传感器与人工清空统计边界；config、mask、final_baseline表继续保留。

## 各阶段结果与复用

| 阶段 | 正式决定 | 对应机器结果 |
|---|---|---|
| R1 | [R1_FINAL_DECISION.md](r1/R1_FINAL_DECISION.md) | r1/R1_FINAL_SUMMARY.json |
| R2 | [R2_FINAL_DECISION.md](r2/R2_FINAL_DECISION.md) | r2/R2_FINAL_SUMMARY.json、R2_06_FORMAL.json |
| I1 | [I1_FINAL_DECISION.md](i1/I1_FINAL_DECISION.md) | i1/I1_06_PILOT_SUMMARY.json、I1_FINAL_SUMMARY.json |
| I2 | [I2_FINAL_DECISION.md](i2/I2_FINAL_DECISION.md) | i2/I2_05_PAIRED_SUMMARY.json、I2_06_HELD_OUT_RESULTS.json |
| I3 | [I3_03_02_REPORT.md](i3/I3_03_02_REPORT.md) | i3/I3_03_02_RESULTS.json、I3_03_02_VALIDATION.json |

I3相机精度/成本、shortcut损失、单锚点/E1/上界失败的正式REPORT与JSON仍在i3目录。
冻结PROTOCOL/CONTRACT、输入SHA注册、分析脚本及C++测试是复现依据，不能因失败删除。

## 历史文档归档

[本次清理清单](maintenance/DOCUMENT_CLEANUP_2026-10-14.md)列出全部移动/归档文件。
外部压缩归档保留原文件相对home路径和SHA256，旧文档引用的已归档过程文件可据清单查找。
正式报告中的历史引用不代表当前待执行阶段。下载文档统一入口为
`/home/zxr2/下载/CERLAB_Research_Documents/README.md`。
