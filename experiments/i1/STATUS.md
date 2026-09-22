# Innovation 1 status

| Task | Status | Evidence |
|---|---|---|
| I1-01 Interfaces, flags and logging schema | Complete | schema-1 contract, fail-closed modes, schema-4 events, smoke and regression tests |
| I1-02 C++ visible-set and path evaluator | Complete | immutable snapshot, stable-address visible sets, raw/unique/marginal metrics; Legacy selection retained |
| I1-03 Correctness and offline-reference agreement | Not started | next task: retained frozen fixtures and boundary cases |
| I1-04 Live shadow-mode validation | Not started | depends on I1-03 |
| I1-05 Feature-flagged online selection | Not started | depends on I1-04 gate |
| I1-06 Three-seed paired pilot and decision | Not started | depends on I1-05 |

Default online behavior is still Legacy. `unique_shadow` and `unique_online` are
declared but fail closed until the evaluator is implemented and explicitly enabled.
