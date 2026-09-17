# R1-04 checkpoint: raw / unique / marginal path gain

Date: 2026-09-17

Status: complete for offline diagnostics. Online route ranking and the legacy
completion threshold remain unchanged.

## Implemented and verified

- exact per-candidate legacy gain, path length, yaw distance, estimated time and score
  are captured inside the existing `findBestPath()` loop;
- candidate polylines are sampled without duplicated shared endpoints;
- raw, unique, marginal, duplicate count/ratio and deterministic set hashes are logged;
- raw and unique utilities share each candidate's exact legacy time denominator;
- rankings and top-1 changes are reported separately for legacy, raw and unique;
- every candidate starts with a fresh history set;
- invariant failures raise instead of producing a report.

Seven new focused tests cover sampling/yaw semantics, repeated and disjoint
observations, zero gain, independent candidate histories, invalid spacing and a
constructed raw-to-unique ranking reversal. The focused R1 suite has 18 passing tests;
the complete benchmark regression has 48 passing tests. C++ packages, including the
dependent `autonomous_flight`, compile successfully. `return_home_checks` also passes,
including the configured threshold-500 near-completion case.

## Live smoke result

One seed-1 `floorplan2_dynamic_5` planning snapshot was evaluated with 0.5 m spacing:

| Candidate | Samples | Legacy gain | Legacy score | Raw | Unique | Duplicate ratio | Unique utility |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 3 | 2412 | 644.903 | 3846 | 1724 | 0.5517 | 460.950 |
| 1 | 3 | 2137 | 495.085 | 3139 | 1815 | 0.4218 | 420.487 |
| 2 | 3 | 1667 | 428.274 | 2353 | 1564 | 0.3353 | 401.812 |
| 3 | 4 | 1856 | 377.619 | 2619 | 1655 | 0.3681 | 336.724 |

All three utility rankings were `[0,1,2,3]`; neither legacy-to-unique nor
raw-to-unique top-1 changed. The diagnostic took 3.31 seconds internally and the
external command took 3.58 seconds. A second run was identical after removing timing
fields, including all candidate union hashes.

Interpretation: this snapshot shows substantial repeated predicted observation, but it
does not show a decision change. H1 therefore remains unresolved. R1-05 must sample
early/middle/late planning states and report ranking margins, rather than selecting only
snapshots where ranking changes.

The raw/unique values must not be numerically compared to legacy gain as if only
deduplication changed: the new evaluator uses stable voxel centers and 0.5 m along-edge
samples, while legacy evaluates shortcut nodes on its floating grid. Raw-to-unique is
the controlled deduplication comparison.
