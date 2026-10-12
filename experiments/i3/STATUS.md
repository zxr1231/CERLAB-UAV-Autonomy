# I3 status

| Task | Status |
|---|---|
| I3-00 definition, C++ implementation and frozen parity | Complete first batch,15 C++ tests;12 snapshots/239poses exact |
| I3-00 online cost admission | FAIL V1/V2:1178.820→872.728ms >500ms; max2 optimizations completed, same-snapshot audit now completed below |
| I3-00 same-snapshot actual-route budget audit | Complete:51references/6states,only startup passes500ms; no admission |
| I3-01A scope review / method protocol | Complete: explicit distance_single/Legacy StageA + same-goal2-route StageB contract, offline probe only |
| I3-01B minimal offline supply/budget probe | Registered, NOT executed; next task,6 fixed cases incl state13negative control |
| I3-02 observation opportunities / anchors | Pending |
| I3-03 guided candidate construction | Pending |
| I3-04 observation-preserving simplification | Pending |
| I3-05 online integration | Pending |
| I3-06 bounded simulation checks | Pending |
| I3-07 paired pilot | Pending |
| I3-08 ablation / mechanism analysis | Pending |
| I3-09 decision and backup | Pending |

Current checkpoint2026-10-12: see I3_00_REPORT.md. Camera evaluation is isolated,
Legacy default unchanged. No online/performance win or guided method claimed.

V2 complete: see I3_00_PERFORMANCE_REPORT.md/results.15 tests,12/239 exact; prefixp95=60.432ms. No third kernel optimization in current protocol or guided-route implementation.

Same-snapshot audit complete2026-10-12:4sampler+2guard tests,all incomplete Goal sets fallback,500ms worst overshoot0.218ms. No kernel/default changes. Full all-Goal cost still fails; I3_BUDGET_POLICY_DRAFT.md is a proposal, not deployed.

I3-01A protocol checks complete: no runtime/kernel/sensor changes or new experimental result. StageB500ms includes nested generation50ms and final-check reserve25ms. CommonA is not historical A* equivalent. I3-01B must prove actual two-route supply/budget before guided construction; equal caps alone do not establish H3.

User requested backup and STOP at I3-01A checkpoint. I3-01B registered but never executed; next continuation starts there. Reference-only target1 versus multi-route target2 is explicit in contract.
