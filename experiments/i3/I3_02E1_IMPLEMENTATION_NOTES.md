# V2 E1 实现前工程说明

2026-10-14，正式批次未运行。V2池、公式、门槛、输入和物理配置保持不变。

1. 内存限制通过仅链接到corridor_fixture_runner/test的operator new/delete分配跟踪实现，
   不链接到规划ROS节点。统计C++请求块容量、桶/节点、数组及跟踪头；malloc内部空闲管理
   和RSS不是该数值，RSS另列。先判定请求块容量再malloc，256MiB上限不调高。
   模型/地图在guard外，分别报存储量；guard涵盖pose结果、marks、索引、union及输出数值
   暂存，JSON序列化在guard外单列。只允许在这个已计量fixture内声称scratch上限得到执行。
2. 可选evaluatePoseSets使用原visible光学算术，新shared budget只加deadline/cancel/累计
   pose与voxel检查。旧evaluateSamples/visibleUnknown行为继续使用原默认合同。
3. 整个控制必需查询失败，fixture非零退出并不输出可用评分，Python批次记工程/资源失败；
   本阶段不提交路径，不声称执行了在线fresh-map回退。negative13在构图/地图加载前跳过。
4. E1只有分项一次观察，deadline默认infinity，接口单元测试用有限deadline/访问/内存
   限额验证失效；没有warmup+3预算测试，不自动进入E2。
5. old optical path不变通过旧kernel输出/parity测试和旧reference结果验证。Oracle在各控制
   checkpoint保存后独立重新生成完整route poses再评价；未变姿态在合成中按规范值复用。
6. fixture总phase时间只作描述。result buffer序列化/释放另记外部进程wall；不能以该
   分项时间冒充含全部准备/锁/fresh safety的Stage B成本。

任何新增实现错误先保留日志再定位，未通过正确性前不得正式采集。
