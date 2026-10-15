# 阶段文档与重复上传文件清理

整理开始：2026-10-14；交接收尾完成：2026-10-15。用户要求只保留后续工作需要的阶段文件，并报告清理内容和空间收益。

## 已完成

- 活动目录归档22份过时文档：项目18份、下载4份；逐文件SHA核验后才移除原活动文件。
- 最新A/B审核结果移至下载/CERLAB_Research_Documents/current，不重复保存两份。
- 总体交接由约59KB精简到约12KB，保留当前结论、完整基线、复用入口、数据/
  GitHub范围及开发底线。旧全文保存在清理归档。
- 新建ACTIVE_DOCUMENTS.md，更新项目README、R1/R2/I1入口和下载文档README。
- 移除14个已远端核验的上传副本：4个tar.gz及10个临时Git bundle，合计379,695,142bytes。
  发布版仍在GitHub，全部原始数据与历次正式本地备份继续存在。
- 文档归档很小；主要空间收益来自这些上传副本。计入新归档、索引和校验记录后，
  文件占用净减少约362MiB（约380MB），精确统计见同名JSON。

## 归档的项目过程文档（18份）

路径相对experiments：

- PAPER_CONTRIBUTIONS_DRAFT.md（被后续负结果淘汰的三点贡献草稿）
- benchmark_v2/FORMAL_BASELINE_BATCH1_2026-09-16.md
- benchmark_v2/RUNTIME_VALIDATION_2026-09-15.md
- benchmark_v2/FULL_RUN_VALIDATION_2026-09-16.md
- r1/R1_06_PROGRESS.md
- i1/I1_04_PREP.md
- i1/I1_06_PROGRESS_2026-09-23.md
- i1/I1_06_PROGRESS_2026-10-08.md
- i1/I1_06_SEED3_LEGACY_2026-10-08.md
- i2/I2_05_SEED2_CHECKPOINT.md
- i3/I3_02A_START_PROMPT.md
- i3/I3_G1_D0_START_PROMPT.md
- i3/I3_BUDGET_POLICY_DRAFT.md
- i3/I3_02A_CLARIFICATIONS.md
- i3/I3_02E_DESIGN_REVIEW.md
- i3/I3_02E_REVISION_V2.md
- i3/I3_02E_REVISION_VALIDATION.md
- i3/I3_SCOPE_DECISION_2026-10-14.md

## 归档的下载文档（4份）与重排

- CERLAB_I3_02E_Astra_Audit_Prompt.md
- CERLAB_I3_02E_Astra_Audit_Report.md
- UAV_Exploration_Astra_Method_Review.md（已完成审核的原提案材料）
- CERLAB_Research_Documents/current/UAV_Autonomous_Exploration_Research_Roadmap_Revised.md
  （后续旧方向关闭，不能再作为当前路线图）

最新审核结果仍保留在：
`/home/zxr2/下载/CERLAB_Research_Documents/current/UAV_Exploration_A_B_Review_Result_2026-10-14.md`。
项目method_reviews中的权威审核副本保持不变。旧材料不代表新执行授权。

## 清理的重复上传副本

仅位于下载/CERLAB_I3_GitHub_Uploads/2026-10-14：

- I3_raw_results.tar.gz
- I3_local_backups.tar.gz
- I3_frozen_dependencies.tar.gz
- I3_git_bundles.tar.gz
- git_bundles/下parent、global_planner、autonomous_flight、map_manager、uav_simulator、
  trajectory_planner、onboard_detector、tracking_controller、time_optimizer、remote_control各.bundle。

四个归档先核对已发布资产大小/服务端SHA；10个bundle核对已发布Git归档内部manifest。
在移除payload前保存压缩ARCHIVE_FILE_INDEX.json.gz，文件名单、SHA与恢复说明仍在。
原SHA256SUMS保持上传时原样；再次本地校验需要先从Release下载已移除payload。

## 保留与验证

保留全部算法/分析/测试源码、启动和实验配置、各阶段正式决定/REPORT、结果JSON、
Benchmark指标及mask、输入注册与冻结协议；原始实验目录和历次正式本地备份未改动。
未删除任何已有目录、Git分支或标签，未改变冻结结论，未运行仿真/编译或上传新文件。

以下5份过程文档存在结构化协议/验证SHA引用，仍留原位置以保证复现：
I3_01A_SCOPE_REVIEW.md、I3_01A_SOURCE_AUDIT.md、I3_01D_METHOD_DECISION.md、
I3_02E_ASTRA_AUDIT.md、I3_02E_SOURCE_AUDIT.md。

验证覆盖：未授权修改的tracked文件SHA；上述硬引用SHA；原始5436文件的路径/大小/
mtime清单；6个正式本地备份树的同类清单；9个子模块无修改；当前入口Markdown链接。
正式旧报告中的历史软引用可通过归档manifest查找，不改写其冻结内容。

## 归档恢复与Git状态

核验归档目录：`/home/zxr2/下载/CERLAB_Document_Archives/CLEANUP_2026-10-14/`。
`documents_before_cleanup.tar.gz`含移除文档、整理前README和完整旧交接；内部FILE_MANIFEST
记录原路径/成员名/大小/SHA。`current_documents_after_cleanup.tar.gz`保存整理后入口。
解压到新目录，不覆盖现有文件。详细明细/统计见cleanup_plan与cleanup_receipt。

I3完整Release保持可恢复：
https://github.com/zxr1231/CERLAB-UAV-Autonomy/releases/tag/i3-complete-backup-2026-10-14

此次整理本地提交；没有补传历史数据，也不自动推GitHub。未来新Codex先读精简的
CODEX_HANDOFF.md和ACTIVE_DOCUMENTS.md，历史阶段提示词不再作为活动入口。
