# Innovation 1: path-history-aware unique observation gain

Innovation 1 implements the shared path evaluator before observation-guided route
generation. Its online effect is isolated behind a feature flag; the legacy completion
gate remains unchanged.

Authoritative scope and gates are in `../r2/R2_FINAL_DECISION.md`.

Current state: I1-01 and I1-02 complete. Continue from I1-03 frozen-fixture
C++/Python agreement and boundary correctness tests. Online selection remains Legacy.
