# CERLAB experiment records

For a new Codex conversation, start with [`CODEX_HANDOFF.md`](CODEX_HANDOFF.md). It is
the maintained single-file project state and continuation prompt.

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

Phase R1 observation-gain diagnostics are specified under [`r1`](r1/README.md).
Generated map snapshots stay in `experiments/r1/snapshots/` and are intentionally
ignored; only manifests, selected fixtures, aggregate tables, and reports should be
committed.

Phase R2 predicted-versus-actual observation validation is complete under
[`r2`](r2/R2_FINAL_DECISION.md). Its final decision conditionally authorizes the
feature-flagged Innovation-1 unique-gain phase while retaining the legacy completion
gate and frozen Benchmark-v2 controls.

Innovation 1 progress and validation records are under [`i1`](i1/STATUS.md).
