# I2 status

| Task | Status | Evidence |
|---|---|---|
| I2-00 Bounded I1 mismatch diagnosis | Complete | six-run read-only log linkage, seed-2 feedback window, R2 sensor-model control; no evaluator bug demonstrated |
| I2-01 Generic multi-route protocol and controls | Complete (protocol only) | I2_01_GENERIC_ROUTE_PROTOCOL.md + I2_01_PROTOCOL.json; no algorithm changes |
| I2-02 Deterministic single-distance / Yen solver | Complete (isolated solver) | routeSearch.h + six correctness tests; see I2_02_ROUTE_SEARCH_REPORT.md and validation JSON |
| I2-03 Geometric diversity control | Complete (isolated controls) | routeCandidates.h + nine contract tests; online counts remain I2-04 |
| I2-04 Integration and safety smoke | Complete | snapshot adapter/scoring/logs; 20 C++ + 7 Python tests; V2 four bounded smoke runs; V1 defect/data retained |
| I2-05 Candidate-supply gate then paired pilot |12/12 collected and verified; pilot checkpoint complete | first attempts/failures/censoring retained; paired summary/report; pre-fix feedback confound labelled, I2-06 complete |
| I2-06 Decision and held-out gate | Complete, Conditional Go | contract fix + one preregistered held-out scene: mapper-shadow passes,2m proxy fails overlap; I2_FINAL_DECISION.md |
| I3-00 sensor-matched C++ parity / cost gate | Pending, next task | held-out mapper-shadow support requires matching C++ contract before guided routes |
| I3 observation-guided route generation | Pending | starts only after I3-00 parity/cost admission; corrected controls need new cohort |

Legacy remains the operational default. The I1-06 data and conclusion are frozen.

2026-10-10: I2-05 new controls are pre-fix (missing scored-gain feedback). Frozen trial values and conclusions stay; causal interpretation must acknowledge this confound. Repair3267e3d has no post-fix online performance evidence. That checkpoint was continued2026-10-12 as recorded below.

2026-10-12: I2-06 complete. One bounded floorplan1_static seed4 run retainedTIMEOUT, no Coverage claims.12 samples: mapper-shadow per-metre rho0.859649 / medianJaccard0.841764 passes;2m proxy rho0.435831 / medianJaccard0.111103 fails full gate. ConditionalGo to sensor-matched C++ parity/cost ONLY; not paper performance proof. All raw failures/history preserved.
