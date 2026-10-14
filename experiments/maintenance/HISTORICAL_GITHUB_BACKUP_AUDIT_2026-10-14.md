# 历史研究工作 GitHub 备份完整性检查

2026-10-14。用户要求检查此前阶段是否也已全部上传。本次仅检查，不补传数据。

**结论：当前GitHub没有全部历史原始实验数据。此前阶段的代码、已提交报告/汇总已
同步；I3及其seed4依赖数据已完整上传；Benchmark、R1、R2、I1与I2其余数据未完整备份到远端。**

| 阶段 | 代码/已提交阶段报告 | 原始数据的当前远端状态 |
|---|---|---|
| Benchmark / Benchmark v2 | 已同步 | 有汇总、部分manifest/CSV及地图mask；完整运行日志/轨迹/失败/复测目录未全部上传 |
| R1 | 已同步 | snapshots/studies未完整上传 |
| R2 | 已同步 | full formal run、reference fixture及其他结果未完整上传 |
| I1 | 已同步 | 三seed配对pilot及smoke/shadow原始目录未完整上传 |
| I2 | 已同步 | seed4 held-out源运行已作为I3依赖上传；三seed四组pilot/其他smoke、admission、audit未完整上传 |
| I3 | 已同步 | 完整结果目录、历次本地备份、相关源输入及Git bundles已上传并校验 |

## 实际检查证据

1. 主仓库14条研究分支在检查开始时与对应本地HEAD一致。历史代码可经Git分支恢复，
   不等于原始实验文件在远端。
2. 主仓库Release列表只有`i3-complete-backup-2026-10-14`，含8个已核验附件。
   global_planner、map_manager、autonomous_flight、uav_simulator未发现其他Release归档。
3. 主仓库GitHub Actions artifacts数量为0。
4. 当前账户owned仓库为上述5个项目仓库，未发现另一个研究数据备份仓库。
5. 远端可达Git历史中，`results/`、`experiments/r1/snapshots/`、`experiments/r1/studies/`、
   `experiments/r2/results/`条目均为0；未发现tar.gz/tgz/zip/bundle等历史实验归档条目。
6. 对已上传I3归档内部manifest核查：raw包1850文件全部来自12个I3目录；依赖包357文件
   来自完整I2-06 seed4源运行；local-backups包2242文件来自I3备份目录，另含部分重复seed4
   输入，没有因此包含全部R1/R2/I1/I2历史数据。
7. 原始数据目录被项目`.gitignore`排除，普通git push不会上传这些目录。

本次确认的是目前远端可恢复范围，不推断曾被删除的资产。先前“GitHub已备份”不能
被解读为所有原始实验数据也已远端保存。当前新增审计文档仅本地提交，不在本次已上传阶段报告范围。

## 本地保留且尚需补齐的代表性内容

- `results/EXP-BENCH*`：24个目录，约195.43MiB，包括正式10seed V1/V2、3/9/10复测和失败/开发记录。
- `experiments/r1/snapshots`、`experiments/r1/studies`：约638.71MiB。
- `results/EXP-R2-06-SENSOR-SHADOW-SEED1-V1`：约2554.63MiB。
- `experiments/r2/results`与`results/R2_FINAL_REFERENCE_20260922`：合计约507.96MiB。
- `results/EXP-I1*`：5个目录，约226.64MiB；包含完整paired pilot。
- `results/EXP-I2*`：17个目录，约1911.36MiB；其中seed4源运行已远端保存，其他部分仍需补齐。
- 下载目录CERLAB_R1_Backups、CERLAB_R2_Backups、CERLAB_R2_Final_2026-09-22、CERLAB_I1_Backups、
  CERLAB_I2_Backups也没有被I3的“历次本地备份”包覆盖。

以上字节为本次查到的文件逻辑大小，可能含副本；不能直接当作去重后上传大小。并非整台电脑的穷尽清单。
本次没有删除文件、修改算法、启动实验或向GitHub写入新内容。数据仍在本机保留。

已完成I3备份：
https://github.com/zxr1231/CERLAB-UAV-Autonomy/releases/tag/i3-complete-backup-2026-10-14
