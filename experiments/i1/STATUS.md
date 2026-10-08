# Innovation 1 status

| Task | Status | Evidence |
|---|---|---|
| I1-01 Interfaces, flags and logging schema | Complete | schema-1 contract, fail-closed modes, schema-4 events, smoke and regression tests |
| I1-02 C++ visible-set and path evaluator | Complete | immutable snapshot, stable-address visible sets, raw/unique/marginal metrics; Legacy selection retained |
| I1-03 Correctness and offline-reference agreement | Complete | 24 snapshots, 217 candidates and 13,131 samples exactly match Python stable-address reference |
| I1-04 Live shadow-mode validation | Complete | small/full seed-1 diagnostics; 31/31 valid full-run evaluations, 51.6% Top-1 change, measured cost retained |
| I1-05 Feature-flagged online selection | Complete | deterministic selection/fallback tests and successful seed-1 online smoke |
| I1-06 Three-seed paired pilot and decision | Complete | all three pairs verified; Unique-only online default downgraded under I1-KC5; see `I1_FINAL_DECISION.md` |

Default mode remains Legacy. `unique_shadow` is validated for diagnostics and
`unique_online` remains available behind the explicit feature flag for controlled
ablation. Its three-seed pilot did not support an independent performance claim.
Completion remains Legacy gain in every mode. I1 is closed; proceed to I2 controls
and reassess actual observation ordering before I3 route generation.
