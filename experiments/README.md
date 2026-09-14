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

Map-point counts are map-size proxies. They are not coverage and must not be used to
derive T80/T90/T95 until a verified evaluation volume and explorable-space
denominator are available.
