# I1-04-01 checkpoint: live-shadow launch preparation

Date: 2026-09-22

Status: preparation complete; no live Unique shadow run was started in this checkpoint.

The exploration launch, return-home smoke include and benchmark runner now accept an
explicit `path_gain_mode` with values `legacy`, `unique_shadow` or `unique_online`.
The default remains Legacy. The runner records the selected mode in `run.json` and
passes it after the exploration YAML is loaded, avoiding temporary config edits.

`unique_shadow` enables counterfactual evaluation while DEP continues to emit
`selection_gain_mode=legacy`. `unique_online` remains fail-closed at DEP construction.

Next command for a bounded development smoke:

```bash
source /opt/ros/noetic/setup.bash
source /home/zxr2/cerlab_benchmark_ws/devel/setup.bash
python3 exploration_benchmark/scripts/run_experiment.py \
  --workspace /home/zxr2/cerlab_benchmark_ws \
  --experiment-id EXP-I1-04-SHADOW-SMOKE-V1 \
  --environment-seed 1 --planner-seed 1 \
  --mode smoke --timeout 180 --disable-coverage \
  --path-gain-mode unique_shadow
```

Before interpreting performance, verify populated Unique fields, Legacy active
selection, successful return/no collision, evaluation status distribution and
evaluation/global-planning timing. Do not automatically retry a slow or failed run.

