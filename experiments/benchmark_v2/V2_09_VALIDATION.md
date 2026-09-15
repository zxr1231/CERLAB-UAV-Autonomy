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
- The real V2-08 batch state produced one row for its one completed attempt.
- Environment seed and planner seed were both preserved as 1.
- Outcome was `HOME_REACHED`; algorithm completion was 1/1.
- T80/T90/T95 remained censored with blank per-run times.
- Aggregate threshold attainment was 0/1 with conditional-time count 0.
- The valid exploration CPU measurement entered the resource distribution.

Validation output was generated under `/tmp/cerlab-v2-09-clean-check` and is not a
paper result. The input batch contains only one small-ROI smoke run.
