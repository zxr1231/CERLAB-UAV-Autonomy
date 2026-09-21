# Phase R1 status

| Task | Status | Evidence |
|---|---|---|
| R1-01 Freeze definitions and baseline | Complete | `README.md`, branch and revision records |
| R1-02 Fixed snapshot and candidate export | Complete | disabled-by-default C++ exporter, immutable map copy, Python validator/tests |
| R1-03 Visible unknown voxel set | Complete | evaluator/CLI, eight geometry tests, 41-test regression, one live snapshot smoke |
| R1-04 Path gain diagnostics | Complete | exact per-candidate legacy export, raw/unique/marginal evaluator, seven focused tests, one live smoke |
| R1-05 Snapshot study | Complete as single-run pilot | 64 raw / 25 state-decorrelated snapshots, 152 candidates, `R1_05_VALIDATION.md` |
| R1-06 Runtime and sensitivity | Complete | 0.125 subset convergence; 0.25/0.5/1.0 full comparison; runtime/RSS/reuse/cache gate |
| R1-07 Phase decision | Complete | conditional GO to R2 shadow-mode predicted/actual validation; `R1_FINAL_DECISION.md` |

Phase R1 is complete. Resume from R2-01 only after explicit user instruction. Do not
rerun R1 unless validation fails or the snapshot/evaluator schema changes. Use 0.25 m
for formal diagnostics; 0.5 m is permitted only for labelled development checks.
