# I2-04 integration/safety checkpoint

Scope: integrate I2 controls with a common map snapshot and historical scoring;
verify disabled-default compatibility, provenance and a bounded simulation smoke.
No full pilot, no I1 data edits and no performance selection from repeated seeds.

Acceptance before I2-05:

- Build planner, exploration node and route tests. Preserve default historical_legacy
  plus default legacy scoring. Unique-online combinations with new controls reject.
- Real occMap vs snapshot collision/Unknown and Legacy gain/scoring tests pass.
- Original A* comparison must use the same frozen map as Dijkstra; map updates in
  the planning worker cannot turn live reads into a frozen-state comparison.
- Generation, shortcut, legacy scoring and Unique shadow share one map version.
  The selected route is revalidated on a new complete snapshot before release.
  This checks one map state, not a guarantee against later map/obstacle changes;
  the existing local/B-spline safety checks remain required.
- Log complete graph/Goal/route provenance, raw/feasible/distinct/selected/scored
  counts, rejects/cutoffs, scores, map/validation versions and sequence association.
- Sequential headless checks on original world and seed pair 1/1, 35 wall seconds
  after planning starts; default plus three new controls. Automatic official Enter
  confirmations only; no artificial Goal, rosbag, ROI or dynamics changes.
- Smoke passes only with execution movement, valid collision/resource/trajectory
  records, no collision/crash, PRM/raw/input/B-spline layers and execution linkage.
  New modes must produce ready non-fallback route records with consistent scoring
  versions and snapshot A* comparisons. Preserve TIMEOUT outcome as expected
  bounded stop, never relabel it as full mission success or a valid T95 trial.

Pre-fix four-run corpus EXP-I2-04-SMOKE-V1 is retained. It exposed concurrent mapping:
planning runs in exploreReplanWorker_, while callbacks continue to update the map.
The first adapter's live A* comparison and live final safety reads therefore do not
satisfy the frozen-state contract, although all four smoke runs moved without recorded
collisions. Correct this system integration defect and collect a separately named
V2 smoke corpus. Do not replace V1 results or use either corpus as I1-06 evidence.

After acceptance update STATUS/CODEX_HANDOFF, commit/push all changed repositories,
verify a local bundle/code/docs/evidence backup, and proceed to preregistered I2-05.
