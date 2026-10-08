# Three-part paper contribution draft

Updated: 2026-10-08. This is a research framing, not a claim of established novelty
or performance. The publication target is an ordinary SCI/EI journal.

1. **Path-history-aware observation evaluation.** On a consistent map snapshot,
   evaluate yaw-aware, occlusion-aware visible Unknown voxel sets along sampled PRM
   paths; report raw, unique and marginal gain and check predicted sets against actual
   first observations. This is the common evaluator. Voxel union and path gain have
   prior art, so the contribution claim must be about the coherent path/trajectory
   validation mechanism and its demonstrated role in this planner, not being first.

2. **Observation-opportunity-guided route generation.** Condition on the baseline
   geometric route, find reachable observation opportunities that it misses, and
   construct a small number of bounded detours to the same goal. Rank complete routes
   by net unique observation and motion cost. This is the proposed primary method.
   It must outperform single-route, generic K-shortest/geometric diversity and naive
   residual-viewpoint insertion under the same goal set, candidate count and compute
   budget. A via point plus two A* searches alone is insufficient.

3. **Observation-value-preserving simplification.** When shortcutting an informative
   route, compare full-route observation sets before and after simplification and keep
   loss within a global budget while preserving safety and B-spline feasibility.
   Validate that the intended value survives actual execution. A local threshold alone
   is a weak stand-alone claim; this is a companion to the guided-route method.

Current evidence: the evaluator in point 1 is implemented and tested, but the
three-seed Unique-only pilot is unfinished. Points 2 and 3 remain hypotheses and have
not been implemented. Edge caching is a conditional engineering optimization after
profiling; it is not one of these three paper claims by default.

See `r2/R2_FINAL_DECISION.md`, `i1/STATUS.md`, and the final novelty audit in
`/home/zxr2/下载/CERLAB_Research_Documents/current/` for claim boundaries and
prior-work comparisons.
