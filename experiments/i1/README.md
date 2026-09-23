# Innovation 1: path-history-aware unique observation gain

Innovation 1 implements the shared path evaluator before observation-guided route
generation. Its online effect is isolated behind a feature flag; the legacy completion
gate remains unchanged.

Authoritative scope and gates are in `../r2/R2_FINAL_DECISION.md`.

Current state: I1-01 through I1-04 complete. Continue from I1-05 feature-flagged
online selection and fallback tests. `unique_online` remains unavailable at this
checkpoint.
