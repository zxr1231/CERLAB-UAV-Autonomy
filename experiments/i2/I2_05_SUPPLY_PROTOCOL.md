# I2-05 first batch: bounded candidate-supply diagnostic

Preregistered before new results on 2026-10-08. Read I2_05_SUPPLY_PROTOCOL.json for
fixed inputs, caps, counterfactual diagnostics and end/gate criteria.

Use ALL 24 existing R2 execution-start snapshots, chronologically divided 8/8/8.
Phase labels are chronology within one run, not measured Coverage stages and not
independent seeds/scenes. Existing exports contain reciprocal PRM edge pairs, not
directed adjacency. Source at 60ff159 confirms symmetric insertion and removal of
invalid nodes; restore reciprocal graph edges, then validate each direction against
the captured map. Synthetic start connectors remain directed. Connector distance
1.5 m is anchored in historical deployment config. Record this reconstruction and
reject ambiguous duplicate/missing IDs; do not fabricate discarded directions.

Preserve frozen Goal set and all sensors/dynamics. Recompute terminal best yaw on
the same captured map. Offline operation caps apply; the online 50 ms wall deadline
is intentionally disabled to separate deterministic route supply from CPU cutoff.
No claim of online deadline feasibility follows.

Primary uses exact I2 V1 limits and K=6. Diagnostics on the same snapshot: pool
caps 12 and 24 under identical operation caps; raw+shortcut constraints, post-
shortcut-only constraints and no motion limits with original geometric shortcut.
These latter cases are explanations, not changes to the live algorithm or a new
method. No best-case parameter is selected for deployment in this task.

Gate: at least six of 24 snapshots retain an actually selected extra route under
PRIMARY settings, including at least two middle and two late snapshots. This is
a pragmatic admission threshold, not a statistically significant improvement.
Failure means stop before the full three-seed matrix. Success only permits its
registration, not a claim that multiple routes improve actual observation.

End after 72 snapshot/pool combinations and exact non-timing repeat of preselected
execution_000079. Preserve failures; do not add maps, tune limits, repeat seeds or
implement preservation shortcut to chase a pass. Report stage counts, overlapping
rejection reasons, per-Goal deficits/pops, geometric alternatives and generic/diverse
selection changes. Existing execution snapshots cannot support route-counterfactual
actual information or T95 claims. Update handoff and verified backups at this gate.
