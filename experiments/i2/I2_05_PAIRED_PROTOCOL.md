# I2-05 paired pilot V1 — preregistration

Registered 2026-10-09 before any full-pilot outcome. Matrix: I2_05_PAIRED_MATRIX.json.
Twelve serial runs: four route modes x seed pairs1/1,2/2,3/3. Route order rotates by
seed index to reduce fixed order effects. One attempt per task; no favorable-result
retries. Timeout900 wall seconds after planning starts, inherited from I1-06 full
pilot. Stop at natural completion/home or timeout. Failure and censored T thresholds
remain in the dataset; return failure is reported separately from exploration metrics.

## Frozen treatment and costs

All four use unique_shadow: Legacy node-sum/time chooses routes, Unique only logs.
All V1 sensor/world/dynamics/coverage/completion500, Goal prefilter and seed settings
stay fixed. K6 pool, <=3 selected per Goal, <=30 globally, raw AND simplified motion
caps1.25x time/length and +pi/2 yaw,10k/100k pops and50ms incremental deadline stay.
All runs headless, no rosbag, same machine, no parallel simulation or build workload.

Keep the already tested frozen-A* audit copy, full graph/candidate JSON and Unique
shadow enabled. Charge all copying, comparison, generation, scoring and serialization
in total planning/runtime/resources. No instrumentation subtraction or hidden cache.
Historical Legacy has its original infrastructure; distance_single controls snapshot,
pose and solver changes. Primary contrasts are generic-vs-distance_single and
geometric-vs-distance_single; generic-vs-geometric tests that control choice.
Historical-vs-distance_single is secondary infrastructure effect, not route diversity.
Same caps do not imply same actual candidate counts; report deficits and fallback.
Goal sets can diverge in closed-loop runs; fixed-state control evidence remains
separate. This pilot does not establish H3's exact matched-state/count claim by itself.

## Evidence, failures and analysis

Record Coverage curves, censored T80/T90/T95, exploration/end/return outcomes,
trajectory distance, actual first sensor observations per metre and second, collisions,
planning mean/p95/max, CPU/RSS, RTF, actual pool/selected/scored counts, shortcuts,
cutoffs, fallback and pose/map consistency. Preserve raw observations/execution joins.
Primary attempt is the FIRST registered attempt, including experimental failure.
Technical invalidity remains reported and halts collection for diagnosis, rather than
silently replacing the attempt. A corrected implementation requires a new documented
epoch/protocol; no cross-commit pooling or reuse of I1 data as current controls.

Report each paired seed and aggregate means/medians/ranges, with N=3 explicitly
exploratory. Do not treat snapshots/plans as independent seed samples. Report all
failures and censored thresholds; never compute optimistic means by dropping them.
No general superiority/significance/novelty claim follows from a positive pilot alone.

## Execution and resumability

Commit this protocol and runner before collection; batch_state pins source HEAD.
Keep the same source HEAD throughout matrix collection. A kernel lock blocks duplicate
runners; an existing ROS master blocks a new run. Save every attempt/status/result_dir
atomically. No automatic retry of failed or interrupted tasks. A stale RUNNING task
must first be reconciled against actual child processes and raw run manifests.
A STOP_AFTER_CURRENT marker in the batch root allows a checkpoint after a run; an
explicit later continuation may remove the marker after checking state.
Do not commit source/handoff changes during an active matrix: save external progress
notes/state for mid-matrix backup, so the source HEAD remains fixed. Final docs can
be committed after the matrix. Preserving a source checkout may be required when
resuming after a documentation-only checkpoint on another branch.

## Completion

After12 terminal trials, validate logs/provenance, summarize paired results, update
STATUS/CODEX_HANDOFF and push/verify local backup. A technical error pauses the
matrix for diagnosis. I2-06 and the held-out prediction/actual gate remain separate;
this pilot cannot promote Unique-online or start I3 automatically.
