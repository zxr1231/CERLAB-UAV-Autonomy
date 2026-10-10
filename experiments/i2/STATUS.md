# I2 status

| Task | Status | Evidence |
|---|---|---|
| I2-00 Bounded I1 mismatch diagnosis | Complete | six-run read-only log linkage, seed-2 feedback window, R2 sensor-model control; no evaluator bug demonstrated |
| I2-01 Generic multi-route protocol and controls | Complete (protocol only) | I2_01_GENERIC_ROUTE_PROTOCOL.md + I2_01_PROTOCOL.json; no algorithm changes |
| I2-02 Deterministic single-distance / Yen solver | Complete (isolated solver) | routeSearch.h + six correctness tests; see I2_02_ROUTE_SEARCH_REPORT.md and validation JSON |
| I2-03 Geometric diversity control | Complete (isolated controls) | routeCandidates.h + nine contract tests; online counts remain I2-04 |
| I2-04 Integration and safety smoke | Complete | snapshot adapter/scoring/logs; 20 C++ + 7 Python tests; V2 four bounded smoke runs; V1 defect/data retained |
| I2-05 Candidate-supply gate then paired pilot |12/12 collected and verified; pilot checkpoint complete | first attempts/failures/censoring retained; paired summary/report; I2-06 pending |
| I2-06 Decision and held-out gate | Not started | freeze held-out ordering protocol before collection/I3 |
| I3 observation-guided route generation gate | Pending | requires held-out-scene predicted/actual ordering check after I2 controls |

Legacy remains the operational default. The I1-06 data and conclusion are frozen.
