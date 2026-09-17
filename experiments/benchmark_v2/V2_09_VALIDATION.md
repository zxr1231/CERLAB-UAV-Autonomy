# V2-09 aggregation validation

Date: 2026-09-15

## Scope

The schema-1 aggregator consumes a V2-08 `batch_state.json` and emits:

- `runs.csv`: one row per recorded attempt, including retries and failures;
- `aggregate.json`: outcome counts, algorithm-completion, return-success,
  collision-free and Coverage-valid rates with Wilson 95% intervals;
- distributions with count, mean, sample standard deviation, median, quartiles,
  p95, minimum, and maximum;
- separate T80/T90/T95 attainment rates, censored counts, and conditional time
  distributions among runs that actually attained each threshold.

Coverage, trajectory, and resource values enter their continuous distributions only
when the corresponding measurement status is valid. A missing result directory still
creates a failure row instead of silently disappearing.

## Verification

- Release build passed.
- Workspace test summary: 35 tests, 0 failures.
- Synthetic tests cover Wilson intervals, distributions, threshold censoring,
  invalid-Coverage filtering, and attempts with missing result directories.
- The completed V2-08 smoke batch produced exactly three rows for three attempts.
- Environment/planner seed pairs 1/1, 2/2, and 3/3 were preserved.
- All outcomes were `HOME_REACHED`; algorithm completion and return success were 3/3.
- All collision measurements were valid and collision-free in this smoke matrix.
- T80/T90/T95 remained censored with blank per-run times in all three rows.
- Aggregate threshold attainment was 0/3 with conditional-time count 0.
- The valid exploration CPU measurement entered the resource distribution.

The smoke free-Coverage range was 0.1246–0.1844, mean 0.1540. This is expected for
the small ROI and confirms why full-map T80 cannot be claimed from a smoke run. The
three runs do not constitute a formal comparison because the small ROI is only an
instrumentation scenario and seed 1 used a parent commit preceding the offline-only
V2-09 addition.

The final local validation output is under:
`/home/zxr2/cerlab_benchmark_ws/results/EXP-BENCH-V2-DEP-SMOKE-MATRIX-V1/aggregate_v1`.
It is not a paper result.
