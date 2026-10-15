# I4-01 已完成并停止

最新决定：[I4_01_REPORT.md](I4_01_REPORT.md)。正确性通过，成本门槛失败，不自动进入I4-02。

- [冻结协议](I4_01_PROTOCOL.md)、[输入清单](I4_01_INPUTS.json)
- [汇总数据](I4_01_RESULTS.json)、[验证](I4_01_VALIDATION.json)
- `prepare_i4_01.py`准备来源路径；`run_i4_01.py`执行36个固定任务；
  `summarize_i4_01.py`和`validate_i4_01.py`复核已保存结果。
- `test_i4_01_analysis.py`验证统计拒绝缺失记录、相同计数但错误地址等情况。
- `run_ros_regression.py`仅用于已有回归的独立临时ROS Master，finally关闭，不运行仿真。

本轮构建（原依赖与CMake工具链已存在，不需要重新安装）：

```bash
source /opt/ros/noetic/setup.bash
source /home/zxr2/cerlab_benchmark_ws/devel/setup.bash
cmake --build /home/zxr2/cerlab_benchmark_ws/build \
  --target incremental_gain_test incremental_gain_runner camera_gain_evaluator_test -j2
```

分析已有原始结果：

```bash
python3 experiments/i4/summarize_i4_01.py /home/zxr2/cerlab_benchmark_ws/results/EXP-I4-01-INCREMENTAL-REPLAY-V1
```

不要将“可复现命令”当成重跑授权。所有原失败日志及原始数据保留；程序在研究分支，
新算法库没有接入在线DEP。对照是固定完整相机收益的计算方法，不是Legacy探索效率排名。
