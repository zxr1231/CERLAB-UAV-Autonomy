# Innovation 1: path-history-aware unique observation gain

Innovation 1 implements the shared path evaluator before observation-guided route
generation. Its online effect is isolated behind a feature flag; the legacy completion
gate remains unchanged.

Authoritative scope and gates are in `../r2/R2_FINAL_DECISION.md`.

Current state: I1-01 through I1-06 complete. See `I1_FINAL_DECISION.md`. The
three-seed pilot does not support enabling Unique-only ranking by default; the
evaluator remains available for diagnostics and ablation. Next is I2 generic
multi-route controls, with observation-model reassessment before I3.
