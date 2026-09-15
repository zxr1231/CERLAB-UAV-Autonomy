# V2-08 resumable matrix validation

Date: 2026-09-15

## Scope

The matrix runner accepts explicit environment/planner seed pairs and expands stable
task IDs in configuration order. It executes one isolated `run_experiment.py` child
at a time and atomically checkpoints every attempt in `batch_state.json`.

- `--dry-run` performs no filesystem or ROS mutation.
- `--max-tasks N` bounds work in one invocation.
- Successful and failed tasks are skipped on resume.
- Interrupted tasks are eligible for recovery.
- Failed tasks rerun only with `--retry-failed`.
- Every attempt records its exact command, result directory, return code, and outcome.
- Raw failed and interrupted runs are never deleted.

## Verification

- Parent implementation commit: `60cb836dccebdb8e38a04c2ba480ffe5e998631c`
- Matrix config: `floorplan2_dep_smoke_matrix_v1.json`
- Initial dry-run listed seed pairs 1/1, 2/2, and 3/3 without creating state.
- A real invocation with `--max-tasks 1` executed only 1/1.
- The task checkpoint transitioned from `RUNNING` to `SUCCESS`.
- The child run reached `HOME_REACHED` from a clean Git state; collision, resource,
  trajectory, and Coverage statuses were valid.
- Seed pairs 2/2 and 3/3 remained `PENDING`.
- A resumed `--max-tasks 1 --dry-run` skipped 1/1 and selected 2/2.
- No ROS/Gazebo process remained.
- Release build passed; workspace test summary: 32 tests, 0 failures.

Batch state:
`/home/zxr2/cerlab_benchmark_ws/results/EXP-BENCH-V2-DEP-SMOKE-MATRIX-V1/batch_state.json`

Seed-1 raw run:
`/home/zxr2/cerlab_benchmark_ws/results/EXP-BENCH-V2-DEP-SMOKE-MATRIX-V1/environment_seed_001/planner_seed_001/20260915T211634`

The same batch was then resumed without a task limit. Seed pairs 2/2 and 3/3 ran
serially after 1/1 was skipped; all three tasks ended `SUCCESS` with outcome
`HOME_REACHED`. No duplicate attempt or residual ROS/Gazebo process was created.

Seed 1 ran at parent `60cb836`, while seeds 2 and 3 ran at `224cbf0`. The intervening
changes add only the offline aggregator and documentation, but the exact parent commit
is still not identical. This matrix validates orchestration and recovery only and is
not a formal performance experiment.
