# I2-00 bounded diagnosis of the I1 observation gap

Frozen before analysis: 2026-10-08.

## Purpose and corpus

Explain why the I1 Unique-only online selector failed to improve actual observation
efficiency consistently. This is a diagnosis of a closed experiment, not a search for
a favorable seed or a reason to revise the I1-06 result.

The complete corpus is the six preselected primary runs in
`/home/zxr2/cerlab_benchmark_ws/results/EXP-I1-06-PAIRED-PILOT-V1/batch_state.json`,
the retained 24 R2 frozen execution snapshots and the existing R2-05/R2-06 aligned
sensor-model comparison. Later valid repeats and failed attempts are retained as
separate audit material. No new simulation or seed is authorized by this protocol.

Input files are read-only. Derived JSON/CSV and reports belong under `experiments/i2/`
or a new analysis output directory; the I1-06 matrix, raw logs, final decision and
frozen experiment branch `10e9c35` must not be edited.

## Questions and observable evidence

1. **Did Unique actually change a flown decision?** Join each successful global plan
   to activated execution intervals by `global_sequence`; count changed Top-1 plans,
   plans with no local execution, associated distance/duration and actual sensor-first
   observations. Unselected route outcomes are unobserved counterfactuals.
2. **Where does a planned route cease to describe execution?** For linked plans,
   summarize raw PRM, shortcut path, input path, B-spline and odometry association.
   A short prefix or a replanned trajectory is not proof that a full PRM route had
   inaccurate gain.
3. **Why did seed 2 produce 257 Unique plans versus 38 primary Legacy plans?**
   Partition plans by fixed task Coverage bands (<80%, 80–95%, >=95%), inter-plan
   time, path length, gain, local execution count and replan reasons. Report the
   distribution; do not infer a causal mechanism from count alone.
4. **What does the sensor-model control show?** Reuse the existing aligned R2
   execution-prefix comparison of the planner 2 m proxy and mapper-matched 5 m
   shadow. This can establish model mismatch on executed poses. I1-06 did not save
   a map snapshot for every changed plan, so exact candidate-set overlap for those
   decisions cannot be reconstructed; label it unavailable.
5. **Is there a demonstrable evaluator defect?** Check the frozen C++/Python set
   equality and invariants from I1-03, current schema/provenance and any newly
   discovered reproducible counterexample. Distinguish an implementation defect
   from Unknown-geometry occlusion, map evolution, partial execution and B-spline
   effects.

## Fixed exit conditions

The diagnosis ends once all five questions have an evidence table and every gap is
classified as: reproducible evaluator error, sensor/model limitation, execution
limitation, or unobservable counterfactual. The report must state which findings are
descriptive rather than causal. No repeated tuning loop or additional seed run is
part of I2-00.

Only a reproducible systematic evaluator error, demonstrated on a frozen fixture or
through a violated invariant, permits modifying the evaluator. Such a fix requires a
separate test and fresh validation; it never rewrites the I1-06 data or conclusion.
If remaining discrepancies are Unknown occlusion or execution limitations, record
them and continue to I2 generic multi-route controls. Do not add occupancy
confidence, cache, semantics or unrelated modules to force a positive result.
