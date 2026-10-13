# I3-02E V2 文档验证

2026-10-13，PASS。只进行文档/输入完整性检查，没有编译、算法测试或新实验。

- V2 JSON可解析；引用的method、audit和inputs文件存在。
- 六状态顺序、13负控制、五有效状态及原早中晚分层一致。
- 六份map/planner/manifest SHA及I3-01B request/result SHA与旧登记一致。
- 每状态camera/context canonical fingerprint重新计算一致，并与原request的camera一致。
- 首次指纹校验发现中间JSON序列化将1.0写为1，使基于原序列化的hash不一致；已在采集前
  修正为保留原输入JSON数值表示。源文件和数值未改，复验全部通过。
- 4份E V1文档与a5bed84中的字节完全一致；独立审核拷贝与下载目录源SHA一致。
- 12000组合、5走廊、1reference、最多6精评分、1extra输出分别计数。
- 475+25=500预算一致；256MiB visibility scratch上限一致；不准入guided generation/E2。
- git diff --check通过；算法及submodule源码没有改动。

下一步是用户另行启动的V2 E1基础验证；这些文档检查不表示接口实现、算法测试或性能通过。
