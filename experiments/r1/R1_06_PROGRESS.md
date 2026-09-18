# R1-06 progress checkpoint

Date: 2026-09-18

Status: completed after resuming from the recoverable checkpoint. Final evidence and
decision are in `R1_06_VALIDATION.md` and `R1_06_SENSITIVITY_SUMMARY.json`.

Completed:

- detailed timing fields added to each path report;
- study summaries now record process maximum RSS;
- sampling comparison tool implemented for gain error, Top-1/full-rank agreement,
  Spearman rank correlation, sample counts, wall time and RSS;
- exact pose/yaw sample reuse and directed sampled-edge reuse profiling implemented;
- cache recommendation uses the predeclared 20% edge-reuse gate and explicitly limits
  its scope to the offline Python diagnostic;
- two sensitivity tests pass, including mismatched-study rejection;
- the complete 0.25 m reference group finished: 25 snapshots, zero failures, aggregate
  diagnostic time 235.214 s, process maximum RSS 37,780 KiB.

Reference artifacts:

- generated directory: `experiments/r1/studies/sensitivity_025_20260918/`;
- summary SHA-256: `33909c83cea3c83697fbcfa13139eea0818eb6183ae898e61491a3dc411004a7`;
- CSV SHA-256: `f76aac49113dca1d3eb1624ea6d14f248168e8b86ce738153c94c92425d3d22e`.

The following resume list was completed:

1. run the same 25 snapshots at 0.5 m into `sensitivity_050_20260918` with fresh
   reports, not the older R1-05 cached timing;
2. run 1.0 m into `sensitivity_100_20260918`;
3. call `compare_r1_sampling.py` with 0.25/0.5/1.0 studies;
4. inspect gain/ranking stability, timing, RSS, exact sample reuse and directed-edge
   reuse; decide whether 0.5 m is retained and whether Edge Cache passes its gate;
5. run full tests/build, write `R1_06_VALIDATION.md`, then commit and back up.

No new simulation was started. The 25 state-decorrelated snapshots backed up in R1-05
were reused. No online algorithm or completion condition changed.
