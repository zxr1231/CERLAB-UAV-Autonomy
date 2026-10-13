# I3-02E 源码与固定数据审查

2026-10-13，只读审查；没有算法、相机内核或运行配置修改。

## 可复用接口与约束

- `routeControls.cpp::findRouteControlCandidates()`在一次规划中固定pose和map snapshot，
  将live PRM按位置稳定排序后生成临时有向Graph。起点是临时ID0；PRM邻接按有向边保存，
  即使当前数据通常含双向弧也不能假设无向。
- Graph数值ID只在该snapshot/构图上下文有效。跨地图缓存不能仅以ID作为Edge身份；至少
  需要map version、端点几何、方向、相机配置和采样合同，新增/删除Edge也必须失效。
- `RouteSnapshot::free/freeLine()`只允许已知、未膨胀自由空间；Unknown和越界均不自由。
  候选连接段必须继续使用这个语义，不能把Unknown当捷径。
- 当前参考路线经过`routeCandidates::shortcut()`后可能含不属于原Graph的安全直连段。
  因此机会Edge不能直接替换“同一Graph Edge”，必须插入到最终参考段并显式验证连接。
- 状态26的有效I3-02A路线`[0,282,285,301]`中，`282->285`、`285->301`都不是Graph弧；
  节点285的实际邻边连接280/289/290/295/296。这证明需要“真实PRM有向Edge+
  两条安全连接段”的短走廊表示，不能把先前anchor路线误称为现有Edge路线。
- `CameraGainEvaluator::evaluateSamples()`能在统一budget下全有或全无地输出union/marginal，
  但不返回逐姿态集合；`visibleUnknown()`返回单姿态集合却没有外部budget参数。精确地重用
  参考未变化部分，需要新增隔离的budget-aware pose-set batch接口，或付出重复全路径评价。
  下一实现不得用无预算`visibleUnknown()`绕过475/500ms截止。
- 相机shadow中snapshot Occupied终止ray，observable Unknown被计数后ray继续；真实未知障碍
  遮挡仍是R2已知限制。Edge/走廊集合仍是预测观测，不是实际传感器新增观测。
- `routeSnapshot_`当前在规划结束清除，没有跨规划可见集缓存。一次请求内共享参考pose集合
  是显式计费的scratch reuse；跨请求Edge cache是以后单独审核的工程机制。

## 固定fixture规模

I3固定状态中的非起点有向PRM Edge长度约0.80--1.50m：

| 状态 | 最终参考段数 | 非起点有向Edge | 段×Edge组合 |
|---|---:|---:|---:|
| 1 | 1 | 10 | 10 |
| 14 | 1 | 934 | 934 |
| 26 | 2 | 1880 | 3760 |
| 27 | 6 | 1920 | 11520 |
| 38 | 1 | 2650 | 2650 |

每状态12000组合上限覆盖当前五个有效fixture且不应截断；未来更大图若截断必须记录，
不能后验提高上限。全图为每条Edge做camera评价显然不符合500ms目标，因此先做几何/
运动筛选、每Edge保留一个插入位置，再固定压缩到最多5条短走廊。

## 集成含义

候选最终表示为：

```text
reference prefix -> p_e -> u -> v -> p_(e+1) -> reference suffix
                         ^真实有向PRM Edge^
```

`p_e->u`和`v->p_(e+1)`为冻结地图安全连接；`u->v`必须是当前Graph弧。该三段短走廊
作为最终候选的一部分保留，不再被普通shortcut删除。Geometry和Naive对照使用完全相同
表示，因此“多保留一个Edge”本身不是拟议方法的优势来源。

参考路线每个插入位置可拆成未变化姿态集合`B_e`和被替换window。候选只需评价三段走廊
及下游出口yaw旋转`C`，完整预测集合为`B_e union C`。必须用完整地址集合验证它与整条
候选重算精确一致；计数相等不够。该合成是评价机制，不自动构成论文创新。
