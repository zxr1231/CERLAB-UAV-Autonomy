# I4-01 GitHub备份已完成：代码分支与受权限保护的草稿附件

2026-10-15，按用户“把刚才做的备份GitHub”的授权执行。算法结论仍为
PROTOTYPE_COST_GATE_FAIL；未修改算法、重跑实验或启动I4-02。

## 入口与版本

- [主仓库I4分支](https://github.com/zxr1231/CERLAB-UAV-Autonomy/tree/feat/i4-incremental-gain)
- [global_planner I4分支](https://github.com/zxr1231/global_planner/tree/feat/i4-incremental-gain)
- [数据备份草稿Release](https://github.com/zxr1231/CERLAB-UAV-Autonomy/releases/tag/untagged-08b22dddb25d3eed4e69)

仓库已核实为PUBLIC，代码/报告分支公开。原始数据附件保持draft=true，未公开发布；
查看草稿需登录有相应权限的GitHub账号（本次为zxr1231管理员）。这是完成的草稿备份，
不是上传中或遗漏附件。不要因未在公开Release列表中看到它而重复上传。

主仓库代码/数据冻结tag：`i4-01-backup-2026-10-15`，指向
`78816187d6145bde6474cf3ef30cc39603ec630e`；global_planner为
`5dfadc01cbd2d17e75bffca03aa13eaa617081e7`。两个分支已与远端核验。
后续主仓库分支包含本上传收据/交接提交，冻结tag及两个Git bundle不重写。

## 已校验附件

Release ID：413376318。共10个附件，182,653,717 bytes（约174.19MiB）。

| 附件 | 内容 |
|---|---|
| artifacts.tar.gz | I4固定输入、完整回放输出、所需冻结源快照、测试/失败日志、文档与研究二进制 |
| FILE_MANIFEST.json | 334个归档文件的来源、成员名、大小及SHA256 |
| parent.bundle / global_planner.bundle | 两个研究仓库可达Git历史 |
| parent_verify.log / global_planner_verify.log | 本地Git bundle验证记录 |
| SHA256SUMS | 原备份附件校验清单 |
| backup_receipt.json | 本地备份收据，创建时github_push=false是历史状态 |
| RESTORE.md / submodules.txt | 恢复说明与未修改子模块版本 |

归档334成员已在本地逐个核对SHA256；10个GitHub附件的服务器digest、状态和字节数
全部与本地匹配。artifacts.tar.gz的SHA256为
`fa9a02cbbb6a50e1956d7d6ec846d009506c73c030be4e785f4da5db818e97f8`。

上传核验见[I4_GITHUB_SYNC_RECEIPT.json](I4_GITHUB_SYNC_RECEIPT.json)。额外本地元数据：
`/home/zxr2/下载/CERLAB_I4_GitHub_Uploads/2026-10-15/`。
原本地备份：`/home/zxr2/下载/CERLAB_I4_Backups/I4_01_2026-10-15/`，未删除或重写。
没有补传其它阶段尚未上传的历史原始数据。

## 发布边界

自动审批拒绝将该Release从草稿公开发布：本次授权未明确包含公开原始研究数据，
且当时尚未核实仓库可见性。随后只读核实仓库为PUBLIC，保留草稿并完成附件校验，
没有绕过拒绝。公开发布不属于本次已完成动作，需另有明确授权后处理。
