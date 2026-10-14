# I3 完整 GitHub 备份

2026-10-14，用户明确要求将此前 I3 的所有工作备份到自己的 GitHub。
目标主仓库：https://github.com/zxr1231/CERLAB-UAV-Autonomy
目标Release：https://github.com/zxr1231/CERLAB-UAV-Autonomy/releases/tag/i3-complete-backup-2026-10-14

**完成状态：GitHub备份已发布并核验。** 两个仓库各两条I3分支与备份tag均匹配；
四个归档和三份说明附件共7个文件的服务端大小/SHA256与本地一致，归档内4470文件
逐个核验，覆盖主仓库和9个子模块Git历史。上传核验见`I3_GITHUB_SYNC_RECEIPT.json`；
最终收据另作为Release附件。随后的branch提交仅补充备份完成记录，tag保持冻结。

本备份是研究检查点，保留全部负结果。I3-03-02仍为METHOD_NOT_SUPPORTED，当前原型关闭。
不是算法性能发布，也没有新增仿真/研究数据。GitHub上传完成状态以远端Release、branch/tag
和上传收据为准，不能以本文件的存在代替远端核验。

## Git 内容

- 主仓库：`feat/i3-camera-evaluator`、`feat/i3-opportunity-prototype` 两条I3分支与完整祖先历史。
- 用户global_planner fork：相同两条I3分支，含相机内核、隔离工具和最终两层束原型。
- 固定依赖：autonomous_flight / map_manager / uav_simulator对应用户fork分支。
- 当前 `.gitmodules` 的map_manager链接修正为用户fork，匹配已有研究提交；算法未变。
- Release标签固定一个完整代码/文档快照；随后上传核验记录可在最新研究分支读取。

主仓库的子模块条目仅保存commit指针，具体源码必须通过子模块或下面Git bundles恢复。
历史旧commit的 `.gitmodules` 可能仍指向原作者map_manager；离线bundle不受此链接影响。

## Release 附件（已上传核验）

| 文件 | 覆盖内容 |
|---|---|
| `I3_raw_results.tar.gz` | 全部12个EXP-I3结果/输入目录，逐次原始输出、失败、日志、统计、图、checkpoint |
| `I3_local_backups.tar.gz` | 下载/CERLAB_I3_Backups中的全部阶段备份、旧bundle、补丁、二进制、输入与校验材料 |
| `I3_frozen_dependencies.tar.gz` | I3输入注册/原始记录引用的完整seed4源运行，含全部111快照及执行关联日志 |
| `I3_git_bundles.tar.gz` | 主仓库与9个子模块的Git bundles、当前commit/branch/remote清单与bundle verify输出 |
| `SHA256SUMS` | 上述归档和manifest的SHA256 |
| `UPLOAD_MANIFEST.json` | 源目录、逐文件清单/散列、数量、archive大小/散列和代码检查点 |
| `RESTORE.md` | 文件验证、离线恢复与路径说明 |
| `REMOTE_SYNC_RECEIPT.json` | 上传完成后提供的真实远端核验收据 |

原始数据通过Release附件存储，不把体积较大的实验文件放入Git历史。Git提交中的RESULTS/
VALIDATION报告和Release原始数据相互对应，已关闭的假设与未验证项如实保留。

## 完整性与恢复边界

每个数据归档含内部逐文件SHA清单，生成后重新读归档逐文件验证。上传后核对远端branch/
tag、资产大小和服务端digest；如服务端不提供digest，下载回读后核对SHA。
归档不是Ubuntu/ROS全系统镜像；ROS依赖和构建环境仍按既有冻结环境使用。
恢复时解压到新目录，保留已有工作空间和个人文件，不直接覆盖当前实验数据。

本次上传临时文件与最终收据保留在：
`/home/zxr2/下载/CERLAB_I3_GitHub_Uploads/2026-10-14/`。
前序各本地备份保持不动。未经新增任务指令不运行新算法或实验。
