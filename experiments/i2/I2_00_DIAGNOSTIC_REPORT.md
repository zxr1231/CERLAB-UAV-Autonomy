# I2-00 bounded diagnosis: I1 predicted versus actual observation

Date: 2026-10-08

**Status: complete.** The frozen protocol in `I2_00_DIAGNOSTIC_PROTOCOL.md` was
applied to exactly six I1-06 primary runs, the retained R2 aligned sensor-model
comparison, and I1-03 frozen C++/Python agreement. No seed was rerun, no I1-06 raw
file or decision was changed, and no evaluator or online algorithm code was modified.
`I2_00_DIAGNOSIS.json` and `experiments/analysis/diagnose_i1_execution.py` make the
log linkage reproducible.

## Evidence by diagnostic question

| Question | Evidence | Classification |
|---|---|---|
| Did a changed Unique winner fly? | In the three Unique runs, 25 + 6 + 20 = 51 global plans differed from the Legacy winner available in that same planner state. Fifty linked to at least one activated local interval, but only 11 + 4 + 17 = 32 accumulated at least 0.5 m of interval odometry. | Partial execution; 19 changed plans did not receive a 0.5 m execution prefix. |
| Does full PRM gain describe execution? | Each global plan can activate several local B-splines and may be superseded. The median raw-to-shortcut geometric length retention was about 0.93–0.95 across runs. Odometry-to-B-spline median distance varied between changed and unchanged groups without a consistent direction. | Shortcut, local trajectory and replanning effects must be kept separate. Full-route predicted gain cannot be compared directly with a short executed prefix. |
| Why 257 global plans in seed 2 Unique? | A 44.744 s window (simulation 131.978–176.722) contains 222 consecutive plans less than 1 s apart. All select the same goal `[2.308, 7.702, 0.901]`; Legacy and Unique rank the same candidate in all 222. For 220 associated planning-log lines, the immediately preceding message says the local goal is unsafe. Odom net displacement was 0.012 m, accumulated motion 0.008 m, and Coverage stayed near 53.976%. The source's `replanCheckCB()` requests a new global path when the local trajectory endpoint fails `isPosValid()`. | Repeated local-safety/global-replan feedback while nearly stationary. The logs identify the immediate trigger, not why the first unsafe endpoint arose or whether an earlier Unique choice led to this state. |
| Is the observation model matched to the sensor? | On the existing 19 aligned R2 execution intervals, the planner 2 m proxy had mean Jaccard 0.087 and count Spearman 0.077 against actual new observations; the 5 m mapper-matched shadow had 0.531 and 0.812. Its late-stage precision was only 0.186 because frozen Unknown space cannot reveal future wall occlusion. | Systematic sensor-model mismatch plus irreducible unknown-occlusion error. These are offline prefix diagnostics, not exact counterfactual candidate outcomes. |
| Is there a reproducible evaluator implementation error? | I1-03 C++ and Python matched raw/unique/marginal gains and final addresses on all 24 frozen snapshots and 217 candidates; the I1 online runs logged valid Unique evaluation without fallback. This diagnosis found no violated set invariant or frozen-fixture counterexample. | No demonstrated evaluator implementation defect. This does not prove the 2 m utility predicts physical observations well. |

The per-global-plan actual observations in the JSON are **full-map first-observation
counts associated by execution interval ID**. Comparisons between changed and
unchanged plans are descriptive and confounded by Coverage stage, route length and
partial execution. The actual outcome of an unselected route was not observed.
I1-06 did not save a map snapshot for every candidate decision, so exact 2 m/5 m
candidate-set overlap cannot be reconstructed from those six runs. This missing
counterfactual is recorded, not estimated from the executed route.

## Decision and exit

All five protocol questions have an evidence table and a classification. The
systematic difference visible here is between the planner proxy and physical sensor;
the 257-plan seed-2 outlier is an execution feedback window. Neither supplies a
reproducible frozen-snapshot evaluator bug. **No evaluator modification is justified
by I2-00.** The I1-06 no-go for Unique-only as the default remains unchanged.

The bounded diagnosis ends here. Proceed to I2 generic multi-route controls using
the frozen Legacy default and equal Goal, candidate, motion and computation budgets.
Before implementing I3 observation-guided routes, perform a held-out-scene
predicted-versus-actual ordering check on aligned executed prefixes. If that check
reveals a reproducible model failure, decide explicitly whether to revise the
evaluation definition; do not keep calibrating against I1-06 until results turn
positive. Unknown occlusion and execution truncation should be reported as
limitations when they remain unobservable.

## Integrity

- All six global planning sequence lists have unique IDs and their raw/shortcut PRM
  path logs are present.
- Execution interval IDs match timestamp-canonical actual observation interval IDs;
  all such interval records are valid.
- The diagnosis script reproduced an identical SHA-256 on two runs:
  `7c542e406ef9c90de08082c55a738886799dd4f6d6dc087a85a2a90e7721e749`.
- The current I1 final decision and summary match commit `7920940` byte-for-byte;
  the current I1-06 batch state matches the pre-diagnosis final data backup archive.
- Source, map, Benchmark definitions and frozen I1 branches were not changed.
