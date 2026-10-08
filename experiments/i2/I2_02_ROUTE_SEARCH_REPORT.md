# I2-02 — Isolated deterministic route search

Date: 2026-10-08. Implementation stage, not an exploration-performance experiment.
Parent/submodule branches: `feat/i2-route-controls`.

## Implemented

`global_planner/include/global_planner/routeSearch.h` is a header-only C++14,
ROS-independent graph/search component. Graph copies caller-supplied positions and
directed adjacency; sorts/deduplicates neighbors and exposes const access only.
Caller must supply stable snapshot IDs; mapping live PRM/map to these IDs is deferred
until integration. Finite Euclidean edge costs include zero-length edges for distinct
coincident nodes. Self loops are removed because routes must be loopless.

Dijkstra uses immutable queue entries, private distance/path/closed arrays, stable
cost/node-sequence ordering, and stale-entry rejection. Yen uses root-node and
prefix-edge exclusions, a persistent deviation pool and node-sequence deduplication.
No PRM Node g/f/parent or live adjacency is accessed or modified.

Returned diagnostics distinguish pool exhaustion from requested K and budget cutoff.
The reference route is mandatory and its pops are counted separately. Alternatives
consume the caller-owned cumulative heap-pop budget (spur heaps plus candidate heap)
and optional steady-clock deadline. A caller can reuse that budget across Goals for
a global cap. Only complete accepted routes are returned on expiry. The deadline is
cooperative, not a hard real-time guarantee. K=0 returns no routes; start=Goal returns
the singleton reference. Invalid/nonfinite graph or terminal data are rejected.

For equal-cost paths output is deterministic, but no claim is made that all global
cost ties follow a single lexicographic order. Exhaustive checks compare costs and
path membership/completeness; repeat runs and input-edge permutations check stability.

## Correctness evidence

`global_planner/test/route_search_test.cpp` contains six tests:

1. Directed/asymmetric graph, shared prefixes, equal costs, cycles, disconnected
   Goal, singleton route and K deficit.
2. Zero-length edges between coincident vertices and edge-order permutation.
3. Complete directed six-vertex graphs, with geometric and all-zero positions:
   all 65 loopless start-to-Goal routes per graph match exhaustive enumeration.
4. Zero/pop-limited and expired-deadline alternatives preserve the reference.
5. Exclusions, invalid input and immutable graph checks.
6. 300 random directed graphs of 2–7 vertices using fixed fixture RNG 20261008:
   exhaustive DFS oracle checks all paths and small K prefixes, route costs,
   membership, looplessness, uniqueness, completeness and repeatability.

These are solver fixtures, NOT Gazebo seeds or experiments. No Coverage/T95 or
improvement claim follows from these tests.

Catkin target: `route_search_test`, built without rebuilding the deployed planner.
Standalone compiler and sanitizer results are recorded in `I2_02_VALIDATION.json`.
LeakSanitizer cannot run under this sandbox's ptrace environment; ASan runs disable
leak detection explicitly. A leak-check pass is not claimed.

## Errors located and resolved

- One fixed fixture initially asserted six routes; exhaustive enumeration and
  direct inspection showed five. Its expected deficit was corrected; solver stayed
  unchanged. The additional complete-graph fixture checks genuine full enumeration.
- Catkin linked gtest without gtest_main, causing missing main. Existing package
  tests use explicit main; this test now follows that pattern.
- One build invocation used the project directory as workspace root; it was corrected
  with explicit `catkin_make -C /home/zxr2/cerlab_benchmark_ws`. No dependency installed.
- Initial ASan/UBSan tests passed but LeakSanitizer exited with ptrace limitation;
  final sanitizer validation explicitly disables leak detection.

## Boundaries and next task

No online call site includes this header. Historical `PRMAstar.h`, `dep.cpp`, YAML
settings, default Legacy behavior, I1 data/conclusions and frozen protocol are unchanged.
This proves isolated graph-search correctness on the tested cases; it does not prove
snapshot collision consistency, equal online candidates, execution safety or benefit.
Live graph stable-ID adapter, common-snapshot visibility/collision/scoring and
historical A* comparison on exported graphs remain I2-04 integration work.

Next I2-03: select geometric-diverse controls from exactly the same Yen pool, implement
motion-limit and post-shortcut deduplication contracts, and test the decisions without
using observation values. No full seed matrix before I2-04 smoke and registration.
