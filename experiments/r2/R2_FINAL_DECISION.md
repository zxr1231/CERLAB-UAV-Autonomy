# Phase R2 final decision

Date: 2026-09-22

## Decision

**Conditional GO to Innovation 1: path-history-aware unique observation gain.**

The authorization is for a bounded, feature-flagged implementation and validation
phase. It is not evidence that unique gain already improves exploration, and it does
not authorize observation-guided route generation before the Innovation-1 gate is
evaluated.

## Why the gate passes

R1 and R2 jointly establish the minimum evidence needed to implement the mechanism:

1. The baseline accumulates intermediate-node gains but does not deduplicate voxel
   identities across a path. This is a source-code fact, not an endpoint-only reading.
2. At 0.25 m sampling, the R1 pilot found 52.19% mean candidate duplication, 67.15%
   selected-route duplication, 36% full-order change and 16% Top-1 change. Duplicate
   counting can therefore affect decisions, although the evidence is one trajectory.
3. Planning, shortcut, B-spline and executed odometry are now separated by stable IDs
   and immutable execution-start snapshots. Artificial clearing is excluded from the
   actual observation stream.
4. The mapper-matched shadow evaluator improved the R2-05 smoke Jaccard from 0.040 to
   0.714 and count Spearman from 0.662 to 0.965 on identical odometry samples. This
   confirms that predicted/actual validation is technically meaningful when the
   sensor model is controlled.
5. In the formal seed-1 run, shadow Jaccard was 0.531 versus 0.087 for the legacy
   proxy, and count Spearman was 0.812 versus 0.077 across 19 eligible intervals.
   Early/middle agreement was strong enough to continue.

## Why the decision remains conditional

- R1 ranking evidence and R2 actual-observation evidence each use one scene and one
  seed/run; neither is an independent multi-scene paper result.
- The shadow evaluator overpredicts late-stage opportunity: late Precision was 0.186
  despite Recall 0.991. A frozen map cannot know where still-Unknown physical surfaces
  will terminate future depth rays.
- R2 validates executed baseline prefixes. It does not observe the counterfactual
  outcome of an unselected unique-ranked route.
- Unique voxel union is an evaluation mechanism with close prior art. It remains a
  supporting contribution, not the paper's primary novelty.

These limits do not justify stopping implementation. They require isolation of the
online change and a real paired experiment before any benefit claim.

## Frozen Innovation-1 definition

For one immutable planning snapshot and path samples `s_i` at 0.25 m spacing:

```
raw_gain(tau) = sum_i |V_planner(s_i)|
unique_gain(tau) = |union_i V_planner(s_i)|
marginal_gain_i = |V_planner(s_i) minus union_{j<i} V_planner(s_j)|
duplicate_ratio = 1 - unique_gain/raw_gain
unique_utility = unique_gain / expected_execution_time
```

`V_planner` deliberately preserves the baseline planner model: 2 m range, baseline
horizontal yaw rule, baseline vertical z-envelope, Unknown transparency, inflated-map
occlusion and the same planning ROI. Intermediate yaw follows the path direction and
the endpoint preserves the baseline endpoint-yaw rule. The denominator preserves the
current translation/yaw time formula.

The mapper-matched 5 m pinhole shadow model remains an offline validation model. It
must be logged alongside planner predictions where practical, but it must not select
the online route in Innovation 1. No late-stage correction factor may be tuned on the
R2-06 seed-1 run and then reported as independent validation.

## Isolation rules

Innovation 1 changes only candidate path ranking behind a feature flag.

- Goal generation and node-gain prefiltering remain unchanged.
- Each goal retains its existing single A* route.
- A* edge cost remains nonnegative geometric distance.
- Existing shortcut behavior remains unchanged.
- FoV, speed, acceleration, safety distance, start, world and seeds remain unchanged.
- The legacy `completion_gain_threshold=500` gate continues to consume the legacy
  gain, even when unique ranking is enabled.
- The legacy route is retained as a fallback when unique evaluation fails or exceeds
  an explicit computation budget.
- Candidate histories are independent; an unselected candidate never updates another
  candidate's set or the real observation history.
- No occupancy confidence, semantics, energy, loop closure or cache is added.

## Innovation-1 task sequence

### I1-01 — Freeze interfaces and flags

Define `legacy`, `unique_shadow` and `unique_online` modes; add schema-versioned event
fields without changing the default baseline. Freeze the exact sampling/yaw/visibility
contract above.

### I1-02 — C++ visible-set and path evaluator

Implement stable global voxel-address sets on one immutable map snapshot. Produce raw,
unique, marginal and duplicate metrics for every candidate. Do not implement Edge
cache in this task.

### I1-03 — Correctness and reference agreement

Test repeated poses, overlapping edges, independent candidates, yaw wrap, Unknown
boundaries, inflated occlusion, zero-length segments and snapshot repeatability.
Cross-check selected C++ results against the existing offline 0.25 m reference.

### I1-04 — Live shadow-mode validation

Run baseline selection while logging unique rankings, score margins, evaluation time,
selected-route disagreement and planner/shadow predicted sets. Confirm no online
trajectory, completion or return behavior changes.

### I1-05 — Feature-flagged online selection

Enable unique utility only for candidate ranking. Preserve the legacy completion gate
and fallback. Run smoke, fault/fallback and return-home tests before formal trials.

### I1-06 — Paired pilot and decision

Use at least seeds 1–3 under the frozen Benchmark-v2 protocol. Compare baseline and
Unique-only with the same environment/planner seed pairs. Retain failures. Report
Coverage/T80/T90/T95, distance, success, collisions, planning time/resources,
selection-change rate, duplicate ratio and actual new observation per metre/second.

The final paper-scale ten-seed and multi-scene Unique-only ablation is deferred to the
full-method experiment matrix, but I1 cannot be declared beneficial from one smoke.

## Acceptance gates

Engineering acceptance requires all of the following:

1. `raw_gain >= unique_gain`, every marginal is nonnegative, and marginal sum equals
   unique gain on every tested candidate.
2. Fixed-snapshot repetition is bitwise stable; candidates do not share mutable
   history; map-version mismatch fails closed.
3. C++ and offline reference sets/counts agree for frozen fixtures under the same
   planner model.
4. Default `legacy` mode reproduces the current selected candidate and completion
   behavior.
5. Unique mode completes smoke exploration and return without crash or collision;
   fallback is observable rather than silent.
6. New scoring time, p95 global planning time, CPU/RSS and real-time factor are
   reported. Any computation budget is fixed before paired performance testing.

Scientific continuation requires:

- live ranking changes with non-negligible score margins rather than duplicate counts
  alone;
- changed selections that can be traced through shortcut, B-spline and odometry;
- no evidence that apparent improvement comes from a changed completion event;
- a paired three-seed pilot that does not show a consistent material degradation in
  actual observation efficiency or task metrics.

Unique-only is allowed to be neutral in global T95 because its paper role is a common
evaluator. If it is neutral, it may continue only as infrastructure for the primary
route-generation hypothesis and must not be claimed as an independent performance
contribution.

## Kill and downgrade criteria

- **I1-KC1:** any set invariant, candidate isolation or fixed-snapshot repeatability
  failure that cannot be corrected without changing the definition: stop online use.
- **I1-KC2:** planner-model C++ results cannot match the frozen offline reference:
  stop and repair the evaluator before simulation comparisons.
- **I1-KC3:** unique scoring repeatedly violates the fixed planning budget or disrupts
  real-time execution without a simple exact implementation path: keep it offline;
  do not introduce a complex cache to hide the failure.
- **I1-KC4:** live ranking almost never changes, or changes have negligible margins
  across the paired pilot: downgrade unique gain to a diagnostic implementation.
- **I1-KC5:** changed selections consistently reduce actual observation efficiency or
  materially worsen T80/T90/T95/distance: disable online unique ranking and reassess
  the model before guided-route work.
- **I1-KC6:** mapper-matched predicted/actual ordering fails again on a held-out scene:
  pause the main observation-guided route claim; do not add unrelated modules.

## Paper claim boundary

After R2, the defensible statement is that path-internal observation duplication is
measurable and sometimes decision-relevant in this implementation, and that a
sensor-matched offline evaluator can validate actual observation with known late-stage
limits. It is not yet defensible to claim exploration improvement, generality, novelty
of voxel union, or superiority over PIPE/TARE/FALCON.

The intended primary paper contribution remains observation-opportunity-guided,
budgeted alternative-route generation. Unique gain is its common evaluator and a
possible supporting method component if the Innovation-1 experiments pass.

## Final R2 status

R2 is complete. Proceed to I1-01. Online baseline behavior remains unchanged at this
checkpoint.

