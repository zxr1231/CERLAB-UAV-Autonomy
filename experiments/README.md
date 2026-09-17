# CERLAB experiment records

This directory keeps reviewable experiment configuration, lightweight manifests,
aggregate tables, reports, and analysis code. Large raw logs and trajectories remain
under the benchmark workspace result root and are not committed to Git.

Layout:

- `configs/`: fixed experiment protocols and source run paths;
- `manifests/`: copies of each run's `run.json`, `runner_result.json`,
  `summary.json`, and mission-state events;
- `summaries/`: generated comparison tables;
- `reports/`: interpreted results and explicit limitations;
- `analysis/`: reusable aggregation scripts;
- `raw/`: optional local raw data; ignored by Git.

Historical map-point counts are map-size proxies and must not be mixed with Benchmark
v2 Coverage. The verified v2 task mask, sensor provenance, observability audit, and
T80/T90/T95 definitions are documented under `benchmark_v2`.

Benchmark v2 metric definitions, source audit, and deterministic floorplan2 masks are
under [`benchmark_v2`](benchmark_v2/METRICS_SPEC.md).

The completed ten-seed baseline, T95 repeat policy, per-seed table, and final aggregate
are documented in
[`FINAL_BASELINE_10SEED_2026-09-17.md`](benchmark_v2/FINAL_BASELINE_10SEED_2026-09-17.md).
