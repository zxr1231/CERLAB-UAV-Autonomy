# Innovation 1 status

| Task | Status | Evidence |
|---|---|---|
| I1-01 Interfaces, flags and logging schema | Complete | schema-1 contract, fail-closed modes, schema-4 events, smoke and regression tests |
| I1-02 C++ visible-set and path evaluator | Complete | immutable snapshot, stable-address visible sets, raw/unique/marginal metrics; Legacy selection retained |
| I1-03 Correctness and offline-reference agreement | Complete | 24 snapshots, 217 candidates and 13,131 samples exactly match Python stable-address reference |
| I1-04 Live shadow-mode validation | Complete | small/full seed-1 diagnostics; 31/31 valid full-run evaluations, 51.6% Top-1 change, measured cost retained |
| I1-05 Feature-flagged online selection | Complete | deterministic selection/fallback tests and successful seed-1 online smoke |
| I1-06 Three-seed paired pilot and decision | Not started | next task: same-commit Legacy vs Unique-online seeds 1–3 |

Default mode remains Legacy. `unique_shadow` is validated for diagnostics and
`unique_online` is now available behind the explicit feature flag. Completion remains
Legacy gain in every mode.
