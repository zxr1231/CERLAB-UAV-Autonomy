# R1-02 checkpoint: fixed snapshot and candidate export

Date: 2026-09-17

Status: complete for the export foundation; no simulation snapshot was collected in
this batch.

Implemented:

- immutable occupancy/inflation value copy protected against concurrent map writers;
- monotonically increasing map version;
- disabled-by-default planner export after legacy path scoring;
- deterministic PRM ordering, goals, shortcut candidate paths, selected candidate,
  vehicle state, sensor/motion configuration and legacy gains;
- binary map and JSON planner payloads with a manifest committed by directory rename;
- FNV-1a integrity validation and a standalone inspection command;
- overwrite refusal and bounded stride/count controls.

Validation performed:

```text
catkin_make --pkg map_manager global_planner exploration_benchmark -DCMAKE_BUILD_TYPE=Release
Result: PASS

PYTHONPATH=exploration_benchmark/src nosetests3 -v exploration_benchmark/test/test_r1_snapshot.py
Result: 3/3 PASS
```

The tests verify deterministic repeated loading, corruption rejection, and rejection
of a directory without the manifest completion marker. Compilation verifies the C++
map capture/export integration. A short live export smoke test belongs at the start of
R1-03 data collection; until then, no claim is made that a real snapshot dataset has
been collected.

Known scope boundary: the snapshot captures one atomic mapper value state after legacy
path scoring. Candidate routes and legacy gain fields record what the live baseline
produced during that planning cycle; because the baseline itself reads a changing live
map, those historical legacy fields are not asserted to be recomputable from the final
snapshot. New raw/unique/marginal values will all be recomputed from the one fixed
snapshot in R1-03/04.
