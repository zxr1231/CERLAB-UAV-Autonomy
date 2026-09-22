# Innovation 1: path-history-aware unique observation gain

Innovation 1 implements the shared path evaluator before observation-guided route
generation. Its online effect is isolated behind a feature flag; the legacy completion
gate remains unchanged.

Authoritative scope and gates are in `../r2/R2_FINAL_DECISION.md`.

Current state: I1-01 complete. Continue from I1-02, the C++ visible-set and path
evaluator, without changing route selection.

