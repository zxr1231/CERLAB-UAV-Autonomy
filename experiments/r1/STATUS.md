# Phase R1 status

| Task | Status | Evidence |
|---|---|---|
| R1-01 Freeze definitions and baseline | Complete | `README.md`, branch and revision records |
| R1-02 Fixed snapshot and candidate export | Complete | disabled-by-default C++ exporter, immutable map copy, Python validator/tests |
| R1-03 Visible unknown voxel set | Complete | evaluator/CLI, eight geometry tests, 41-test regression, one live snapshot smoke |
| R1-04 Path gain diagnostics | Complete | exact per-candidate legacy export, raw/unique/marginal evaluator, seven focused tests, one live smoke |
| R1-05 Snapshot study | Not started | depends on R1-04 |
| R1-06 Runtime and sensitivity | Not started | depends on R1-04 |
| R1-07 Phase decision | Not started | depends on R1-05/06 |

Resume from R1-05. Do not repeat R1-01/02/03/04 unless validation fails or the schema
changes. R1-03 and R1-04 each retain one seed-1 integration fixture; neither is a
formal experiment result.
