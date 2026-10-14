# I3-03-01（历史名称 G1-D0）隔离实现

2026-10-14。遵守 `I3_G1_D0_PROTOCOL.md/json` 和 `I3_G1_D0_INPUTS.json`。

- `global_planner/test/boundDiagnostic.h`：规划区域内 Unknown 的三维 int64 前缀表；N 与 Q=N\R 独立构建；最多三盒精确包含排除并集。
- `bound_diagnostic_runner.cpp`：只读取冻结地图、参考集合和已保存的两段几何；无相机评价器调用，也不链接 global_planner 算法库。单独计时构建、查询、排序、释放及整个准备阶段。
- `run_i3_03_01_bound_diagnostic.py`：校验全部冻结文件、相机/运动配置和不变前后缀采样合同；保存全部排名及 SHA 后读取历史 alternative full labels。独立扫描二进制体素，验证计数/新地址包含/上界；固定 K1 和预登记门槛。

隔离 C++ 分配跟踪覆盖计数表容量、Q 临时 reference 标记索引、得分数组和排序期间的堆分配，256MiB 硬上限。地图、输入 JSON、预加载参考与路线几何不放入计数工作区；地图 payload 与参考/路线容器容量另列，整个进程 RSS 用 `/usr/bin/time` 实测。栈、库及输入 JSON 内存由进程 RSS 覆盖，不能称 allocator 数字为全进程用量。相机模型不构造，其历史实际容量仍未测量。

正确性测试：6 项 C++ 测试覆盖小网格暴力查询、2/3 盒重叠/裁剪/空集、闭合中心边界、非法输入、Unknown 标记、内存追踪及限额拒绝；5 项 Python 测试覆盖 reference fallback、零分母、K2 不挽救 K1、正例顺序与独立成本门槛。

编译过程中，两个 `EXPECT_THROW` 写在同一行导致 gtest 使用重复的行号标签；已拆行后编译成功。这是测试源码错误，正式诊断尚未运行时修复，没有改协议。CMake 报已有 VTK 导入目标缺失警告，本次目标不使用这些目标，构建完成，未安装/替换依赖。

构建及测试命令（研究工作空间，先 source ROS/research devel）：

```bash
catkin_make --make-args bound_diagnostic_runner bound_diagnostic_test -j2
devel/lib/global_planner/bound_diagnostic_test
python3 -m unittest -v test_i3_03_01_bound_diagnostic.py
```

正式批次使用注册六状态，串行测量防止共享资源污染计时；不 warmup、不重测求速度、不改变盒大小/预算/K/候选。用户新偏好为以后多个测试并行，后续任务应使用隔离环境并明确资源影响，本次预登记测量方式保持。
