# Innovation 1 status

| Task | Status | Evidence |
|---|---|---|
| I1-01 Interfaces, flags and logging schema | Complete | schema-1 contract, fail-closed modes, schema-4 events, smoke and regression tests |
| I1-02 C++ visible-set and path evaluator | Complete | immutable snapshot, stable-address visible sets, raw/unique/marginal metrics; Legacy selection retained |
| I1-03 Correctness and offline-reference agreement | Complete | 24 snapshots, 217 candidates and 13,131 samples exactly match Python stable-address reference |
| I1-04 Live shadow-mode validation | Complete | small/full seed-1 diagnostics; 31/31 valid full-run evaluations, 51.6% Top-1 change, measured cost retained |
| I1-05 Feature-flagged online selection | Not started | next task: selection switch, fallback tests, then smoke |
| I1-06 Three-seed paired pilot and decision | Not started | depends on I1-05 |

Default online behavior is still Legacy. `unique_shadow` is validated for diagnostics;
`unique_online` remains fail-closed until I1-05 implements selection and fallback.
