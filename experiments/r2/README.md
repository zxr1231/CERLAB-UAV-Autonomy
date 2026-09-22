# Phase R2: final retained record

R2 is complete. It established timestamp-linked execution intervals, actual sensor
first-observation sets, four predicted path/execution layers and a mapper-matched
frozen-map shadow evaluator. Artificial takeoff clearing remains excluded and no
rosbag is required.

Only the files needed by later development are retained here:

- `R2_FINAL_DECISION.md`: authoritative Go/No-Go decision, frozen Innovation-1
  definitions, acceptance gates and kill criteria;
- `R2_FINAL_SUMMARY.json`: machine-readable R1/R2 evidence and next-task contract;
- `R2_06_VALIDATION.md` and `R2_06_FORMAL.json`: final predicted-versus-actual evidence
  and the documented late-stage overprediction limitation;
- `STATUS.md`: compact completion index.

Stage reports and smoke summaries were removed after consolidation. They remain
recoverable from Git history and the final R2 bundle. The lightweight 24-snapshot
reference fixture for Innovation 1 is stored at
`/home/zxr2/cerlab_benchmark_ws/results/R2_FINAL_REFERENCE_20260922`; its compressed
copy and all relevant Git bundles are in
`/home/zxr2/下载/CERLAB_R2_Final_2026-09-22`.

The next task is I1-01. Online baseline behavior is unchanged at this checkpoint.
