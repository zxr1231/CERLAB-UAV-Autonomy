# I2-01 — Generic route controls, protocol v1

Status: protocol frozen; route algorithms and online integration NOT implemented.
Date: 2026-10-08. This is a bounded implementation specification, not a performance result.
Machine-readable settings: `I2_01_PROTOCOL.json`. No I1 run, evaluator, default or
Benchmark condition is changed. I1-06 remains frozen and Unique-online remains no-go
as the operational default. Later protocol revisions require a new version and a
reason recorded before collecting the affected experiments.

## Purpose and controls

Determine whether multiple geometric routes supply useful alternatives, and establish
fair controls for future observation-guided generation. Ordinary K-shortest is a
control, not a paper contribution. I2 is not intended to rescue the I1 result.

| Control | Generation | Online scoring | Purpose |
|---|---|---|---|
| historical_legacy | original A* and shortcut, unchanged | original node sum / estimated time | operational and historical reference |
| distance_single | one deterministic distance route per original Goal | legacy formula on common snapshot | isolate new solver/snapshot infrastructure |
| generic_k_shortest | shortest loopless alternatives | same formula | ordinary multi-route control |
| geometric_diverse | geometric selection from exactly the same K-route pool | same formula | diversity control, no observation-guided generation |

Unique evaluation is shadow-only in the first I2 pilot. A later ranking factorial
must separately register Legacy vs Unique on the identical generated candidate set;
never attribute a scoring change to route generation. Future guided generation must
use the same Goal set, limits, ranking and simplification as its generic comparator.
Single-route controls naturally have fewer actual candidates. Report this honestly;
match caps and compute allowance among multi-route methods, then do a matched-count
shadow comparison on snapshots. Never pad a missing route with duplicates.

## Source evidence and compatibility blockers

Source is anchored at parent b721bf5 and global_planner 65c2510:

- `dep.cpp:900 findCandidatePath`: directed synthetic start connections, geometric
  A* for each prefiltered Goal, then shortcut. All-goals-disconnected recovery exists;
  preserve it and log recovery events separately from nominal comparisons.
- `PRMAstar.h`: Euclidean g and h, shared Node g/f/parent. Queue entries reference
  nodes whose f is mutated after insertion. Heap-order correctness is a risk, NOT a
  proven failure on historical runs. Do not claim strict shortest-path optimality or
  silently replace the frozen A*. The distance_single control isolates replacement.
- `dep.cpp:978 findBestPath`: recomputes each intermediate node/yaw gain, adds Goal
  best-yaw gain, divides by distance/vel + yawPenalty*yawDistance/angularVel. This
  is not endpoint-only scoring, and it has no cross-node voxel-set deduplication.
- `dep.cpp:1300 shortcutPath`: collision-free geometric simplification. Distinct raw
  routes can collapse to the same simplified route; count and deduplicate afterward.
- Existing Unique mode captures a snapshot separately from live-map Legacy scoring.
  Current source therefore does NOT already provide common-snapshot scoring for
  the proposed new controls. Snapshot-consistent collision/yaw/scoring adapters
  must be implemented and verified before a fair shadow or online comparison.

No baseline search/evaluator fix is justified by this review alone.

## Immutable graph and search contract (I2-02)

Copy positions, directed adjacency and goal identities to an immutable graph.
Preserve existing directions; never manufacture reciprocal edges. Stable local IDs
are lexicographically ordered positions; duplicate positions require an explicitly
logged secondary identity. Sort neighbor IDs and order equal-cost queue entries by
stable IDs. Searches own distance/parent arrays and immutable heap entries with stale
entry rejection; they do not write PRM Node g/f/parent or mutate live adjacency.

Dijkstra with nonnegative Euclidean edge lengths supplies the reference route and
Yen's loopless K-route enumeration supplies alternatives. Root exclusions, directed
edge exclusions, persistent spur-candidate heap and full node-sequence deduplication
are required. Ties are deterministic. A capped enumeration is a truncated K-route
pool, not a claim that all mathematically shortest alternatives were returned.
Reference: [Yen, Management Science 17(11), 1971](https://pubsonline.informs.org/doi/10.1287/mnsc.17.11.712),
[original paper scan](https://people.csail.mit.edu/minilek/yen_kth_shortest.pdf).

Map snapshot/version, graph identity, original Goal IDs, start/yaw and all settings
must be exported. Collision checks, shortcut and new-control scoring use that same
map state. Before execution, the selected route must still pass current-map safety
and trajectory feasibility checks; stale snapshot rejection is logged. Snapshot
creation/graph validation costs are included in total planning time. They are not
hidden by the alternative-only deadline.

## Candidate and motion limits

Engineering starting limits, not empirically optimal values:

- At most six loopless raw pool routes per Goal; at most three scored routes per
  Goal and 30 globally (original Goal maximum is ten). Keep a feasible reference
  route for each Goal first; distribute remaining slots in stable round-robin order.
- Generic selects remaining feasible routes by distance. Geometric selects from the
  exact same exported pool by maximizing minimum post-shortcut directed-edge-set
  Jaccard distance to already selected routes; distance then stable route ID breaks
  ties. A simplified direct segment is a pair of stable endpoint IDs. If the pool
  has no distinct alternatives, return a deficit, not synthetic diversity.
- On both raw and shortcut routes require length <= 1.25 * corresponding reference
  length, estimated time <= 1.25 * reference time, and total yaw <= reference yaw
  + pi/2. Estimated time uses the existing distance/yaw formula; no new weights.
  A zero-length reference produces no alternative (logged). These constraints do
  not guarantee equal actual flight distance; measure actual odometry and B-spline.
- Deduplicate raw node sequences, then simplified ordered endpoint sequences with
  tolerance 1e-6 m. Report raw-generated, motion-feasible, post-shortcut-unique and
  scored counts, and all rejection reasons. Post-shortcut collapse is an outcome.

## Compute budget and repeatability

Pool enumeration has 10,000 heap pops per Goal and 100,000 globally, including failed
spur searches. This operation cap and six-route pool apply to both generic and
geometric controls. Offline tests use operation caps only for deterministic results.
Online alternatives also have a 50 ms steady-clock deadline after mandatory reference
routes; it includes alternative search, selection, validation and shortcut. Check
inside spur searches/expensive loops and retain only fully validated routes on expiry.
This is a cooperative deadline, NOT a hard real-time guarantee. Record overshoot.
Mandatory references and all scoring/snapshot overhead are outside this incremental
allowance but inside total planning runtime; compare those totals and RTF too.

Deadline cutoffs can differ under CPU load even at the same seed. Log cutoff reason,
heap pops and actual counts; do not promise identical online trajectories. Profiling
may show the initial caps are unsuitable. If so, revise the protocol before pilot
collection; do not tune against favorable T95 or discard deadline failures.

## Logging and evidence

Extend existing lightweight logs with protocol hash, mode, map/graph versions, Goal
IDs, full raw/simplified route IDs and geometry, per-stage route counts, fallback,
recovery, deadline status, search pops, generation/shortcut/scoring/total milliseconds,
length/time/yaw and raw/unique shadow metrics. Keep execution association with
B-spline, odometry and first sensor-observation deltas. Never equate an unexecuted
alternative's predicted set with actual counterfactual observations.

The three seed pairs (1,1), (2,2), (3,3) are only a pilot. Freeze mode matrix and stop
conditions before collection; retain failures and report first-valid attempt policy
without rerunning for favorable performance. Existing world, sensor provenance,
resolution, speed/acceleration, safety distances, starting conditions, completion500,
Coverage denominator and observation definitions remain unchanged.

## Acceptance and stop gates

I2-02: exhaustive enumeration on small directed fixtures must match ordered K paths
and costs, including ties, disconnected Goal, cycle, shared prefix, asymmetric edge,
K deficit and budget truncation. Inputs remain unchanged. Reference distance must
match brute-force optimum; historical A* differences are reported, not erased.

I2-03: generic/diverse share byte-identical pool, caps and Goal IDs; geometric selection
reads no observation gain. Shortcut collapse, yaw/time/length rejections and stable
selection must have explicit checks. If normal shortcut removes nearly all diversity,
report control limitations; do not introduce preservation secretly during I2.

I2-04: disabled feature reproduces original behavior, snapshot adapter matches legacy
formula on frozen inputs, no stale/inconsistent route is executed, no crash/collision
in smoke, logging links all route layers, no rosbag. Build and test only changed code.

I2-05: preregister small paired matrix before running. Compare Coverage/T80/T90/T95,
actual first-observation/m and /s, distance, collisions, success, planning distributions,
CPU/RSS and RTF, plus candidate deficits and simplified diversity. A pilot cannot
establish population significance or multi-scene generality.

I2-06: decide if route alternatives survive simplification and offer usable decision
freedom within budgets. Freeze a held-out world and matched executed-prefix
predicted/actual ordering test BEFORE collecting it and BEFORE I3. Its sample size,
eligibility, effect estimate and uncertainty criterion must be a separate preregistered
protocol, not invented after seeing outcomes. Neither aggregate correlation alone
nor I1 raw-gain reduction establishes route-selection utility. If no usable observation
ordering remains, stop the guided claim or record a bounded representation change;
do not reopen I1 endlessly or add unrelated modules to hide failure.

## Next checkpoint

I2-01 ends with this protocol, JSON validation, unchanged-code/data check and verified
Git/local backup. Next: I2-02 isolated deterministic graph solver + Yen unit fixtures;
no full seed batch until integration and safety/logging gates are passed.
