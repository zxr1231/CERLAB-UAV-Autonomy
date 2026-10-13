# I3 status

| Task | Status |
|---|---|
| I3-00 definition, C++ implementation and frozen parity | Complete first batch,15 C++ tests;12 snapshots/239poses exact |
| I3-00 online cost admission | FAIL V1/V2:1178.820→872.728ms >500ms; max2 optimizations completed, same-snapshot audit now completed below |
| I3-00 same-snapshot actual-route budget audit | Complete:51references/6states,only startup passes500ms; no admission |
| I3-01A scope review / method protocol | Complete: explicit distance_single/Legacy StageA + same-goal2-route StageB contract, offline probe only |
| I3-01B minimal offline supply/budget probe | Complete, NOT admitted: reference5/5pass; 4supply deficits,1alternative timeout; negative13passed |
| I3-01C fixed-pool observation/simplification diagnostic | Complete: predicted loss10/10, direct raw-retention leads0; NOT admitted |
| I3-02 observation opportunities / anchors | I3-02E design complete; Edge/corridor E1 implementation and experiment pending, phase incomplete |
| I3-03 guided candidate construction | Pending |
| I3-04 observation-preserving simplification | Pending |
| I3-05 online integration | Pending |
| I3-06 bounded simulation checks | Pending |
| I3-07 paired pilot | Pending |
| I3-08 ablation / mechanism analysis | Pending |
| I3-09 decision and backup | Pending |

Historical checkpoint2026-10-12: see I3_00_REPORT.md. Camera evaluation is isolated,
Legacy default unchanged. No online/performance win or guided method claimed.

V2 complete: see I3_00_PERFORMANCE_REPORT.md/results.15 tests,12/239 exact; prefixp95=60.432ms. No third kernel optimization in current protocol or guided-route implementation.

Same-snapshot audit complete2026-10-12:4sampler+2guard tests,all incomplete Goal sets fallback,500ms worst overshoot0.218ms. No kernel/default changes. Full all-Goal cost still fails; I3_BUDGET_POLICY_DRAFT.md is a proposal, not deployed.

I3-01A protocol checks complete: no runtime/kernel/sensor changes or new experimental result. StageB500ms includes nested generation50ms and final-check reserve25ms. CommonA is not historical A* equivalent. I3-01B must prove actual two-route supply/budget before guided construction; equal caps alone do not establish H3.

Historical I3-01A stop was resumed by user; I3-01B is now complete as recorded below. Reference-only target1 versus multi-route target2 is explicit in contract.

I3-01B complete:6 C++ tests,one registered6-state batch. 28raw→15motion feasible→6distinct incl5references. INCONCLUSIVE_SUPPLY; state27 also has actual alternative scoring budget failure. No online/guided code. Next only fixed-pool observation-loss diagnosis after new protocol.

2026-10-13: resumed only pending I3-01B backup after prior approval-quota interruption; raw artifact hashes verified unchanged. No new experiment/I3-01C started. Backup receipt records actual GitHub sync.

2026-10-13 current: I3-01C complete. 15paths/60outputs, material predicted loss for
all10extras, median17.10%; all10raw-as-final time/yaw violations and lower primary
utility than final reference. Direct retention leads0, no admission. Four accounting
tests and fixture/reference/hash checks pass. Read I3_01C_REPORT.md. User requested
backup then stop. Next is a method-scope decision/new bounded protocol if justified;
I3-02/03 and online integration remain pending, not automatically authorized by results.

I3-01D method-scope review COMPLETE2026-10-13: see I3_01D_METHOD_DECISION.md.

I3-02A COMPLETE2026-10-13, decision PROXY_NOT_SUPPORTED. Fixed five valid states plus
negative13;3498/3498 combinations,14 fixed-pool routes. States26/38 contain useful
oracle routes, but Residual-cost selects a useful route only at38 (required>=2) and
equals Geometry in every nonempty state. No I3-02B admission, online integration,
simulation, kernel change or performance claim. Read I3_02A_REPORT.md/RESULTS.json/
VALIDATION.json. Next is a research-scope decision; do not enlarge pool, rerun seeds,
use oracle candidate636, or automatically enter I3-03. Local backup only; I3-02 is
not complete and no GitHub push is claimed for this checkpoint.

I3-02R COMPLETE2026-10-13: read-only attribution over the same14 saved candidates,
zero camera calls/new candidates/simulation. Segment changed-window score chooses the
same reference/candidate as full oracle in5/5states; route-level Spearman/sign agreement
both1.0. It finds candidate636 at26 and preserves197 at38. Spatially,95.25%/97.31%
of added voxels lie within5m of inserted corridors versus41.84%/56.05% of anchors.
Decision SEGMENT_SIGNAL_ONLY_REQUIRES_NEW_OPPORTUNITY_GENERATOR. This does not change
I3-02A failure: the score consumes saved full-route marginals and changed windows cover
median76.1% of poses. No timing/online admission. Its requested I3-02E design step is
now complete below; no implementation result is implied. Local backup only; no GitHub
push claimed.

I3-02E DESIGN COMPLETE2026-10-13: source audit, directed PRM Edge+two safe connector
corridor representation, exact unchanged-reference/corridor set composition, common
Geometry/Naive/Proposed pool, fixed12000 pair/5 corridor caps and E1/E2 kill gates are
recorded in I3_02E_SOURCE_AUDIT.md, METHOD_PROTOCOL.md, PROTOCOL.json and
DESIGN_REVIEW.md. No code/experiment/online mode was added. Next implement isolated
I3-02E1 fixture and run the one fixed6-state batch. Any supply/value/distinction gate
failure stops this representation; a pass admits only E2 budget probe. Local backup
only; no GitHub push claimed.
