# I3 status

| Task | Status |
|---|---|
| I3-00 definition, C++ implementation and frozen parity | Complete first batch,15 C++ tests;12 snapshots/239poses exact |
| I3-00 online cost admission | FAIL V1/V2:1178.820→872.728ms >500ms; max2 optimizations completed, same-snapshot audit now completed below |
| I3-00 same-snapshot actual-route budget audit | Complete:51references/6states,only startup passes500ms; no admission |
| I3-01A scope review / method protocol | Complete: explicit distance_single/Legacy StageA + same-goal2-route StageB contract, offline probe only |
| I3-01B minimal offline supply/budget probe | Complete, NOT admitted: reference5/5pass; 4supply deficits,1alternative timeout; negative13passed |
| I3-01C fixed-pool observation/simplification diagnostic | Complete: predicted loss10/10, direct raw-retention leads0; NOT admitted |
| I3-02 observation opportunities / anchors | V2 E1 functional exactness verified; LIMITED_POOL_VALUE_FAIL; no E2/true guided generator admission |
| I3 scope decision | Grilling Q1--Q8 confirmed; historical true-Edge/state27 prerequisites revised; old negatives retained |
| I3-03-01 / G1-D0 lightweight bound diagnosis | Complete: exactness/cost PASS; NO_USEFUL_CONDITIONING_SIGNAL |
| I3-03-02 / G1-P1 prototype | Not admitted after D0 failure; scope decision first |
| I3-03-03 independent verification | Conditional/pending; no prototype admission |
| I3-03 guided candidate construction | Paused pending scope decision; not automatically authorized |
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

Historical I3-02E V1 DESIGN2026-10-13 (future execution superseded by V2): directed PRM Edge+two safe connector
corridor representation, exact unchanged-reference/corridor set composition, common
Geometry/Naive/Proposed pool, fixed12000 pair/5 corridor caps and E1/E2 kill gates are
recorded in I3_02E_SOURCE_AUDIT.md, METHOD_PROTOCOL.md, PROTOCOL.json and
DESIGN_REVIEW.md. No code/experiment/online mode was added. Next implement isolated
I3-02E1 fixture and run the one fixed6-state batch. Any supply/value/distinction gate
failure stops this representation; a pass admits only E2 budget probe. Local backup
only; no GitHub push claimed.

Historical: I3-02E V2 revision COMPLETE2026-10-13; implementation completed below. Read REVISION_V2,
METHOD_PROTOCOL_V2, PROTOCOL_V2 and INPUTS_V2. E1 is exact local evaluation/limited pool
value, not guided generation. V1 and earlier failures unchanged. Oracle agreement and
same-pool dominance are correctness properties; >=3 nonempty/nontruncated and >=2
positive-U states are bounded value diagnostics. Pass=FOUNDATION_PASS_COST_STUDY_PENDING,
not E2/innovation admission. Budget counts reference+up to5corridors, absolute deadline
and256MiB visibility scratch; context hashes/old stage labels locked. Next user-triggered
task is V2 isolated E1 implementation/tests/one batch/local backup then stop. No GitHub push.

Current2026-10-14: V2 E1 batch COMPLETE, LIMITED_POOL_VALUE_FAIL.18874pairs,
13corridors,4nonempty states but positive-U only26 (required2).13/13 route addresses/
raw/unique/marginal match full oracle; all5references match I3-01C.12new C++ plus
21regression and23Python tests pass. Optional API/fixture allocation guard implemented,
online planner and optical arithmetic unchanged. Resource-metadata gap: full process
peakRSS/model allocated capacity not collected; scratch22.34--32.64MiB recorded.
See I3_02E1_REPORT_V2.md/RESULTS/VALIDATION. Stop fixed pool; next scope decision only,
no rerun/E2/seed/cache. Local backup only; no GitHub push.

Scope decision COMPLETE2026-10-14: read I3_SCOPE_DECISION_2026-10-14.md/TRACE.json.
per-Edge insertion pruning excludes0; old positive26/38 exact paths excluded by mandatory
real-Edge representation. Unscored qualified routes47/121 at26/27 remain unknown.
No new routes/visibility/seed/simulation. One next hypothesis: same finite mother sets,
reference-conditioned optimistic visibility bounds to choose<=5 expensive queries BEFORE
pool lock; compare geometry and identical nonconditioned bounds. Not a novel B&B claim.
Next user-started step: freeze G1 contract/numeric+resource rules, isolated prototype and
one finite gate. Draft only, no automatic execution or E2. This turn ends after local backup.

Current2026-10-14: user accepted grilling Q1--Q8 and final shared understanding.
I3_GRILLING_CONSENSUS + I3_G1_D0_PROTOCOL.md/json + INPUTS.json supersede historical
scope future directions. D0only: all14old02A scored corridors, original6contexts, no new
gain/routes/seeds/sim. Exact box union fixed; K1primary quality and50ms counted-index
overhead target plus256MiB. Changed order alone not PASS. True Edge no longer necessary;
old5-state corpus no sole whole-line death verdict. One diagnosis, after pass one
separately registered prototype; do not autoexecute. Local backup only, no GitHub push.

Latest2026-10-14: I3-03-01 (old G1-D0) COMPLETE.6C++/5Python tests,74frozen file hashes,
14exact voxel counts/containment/upper bounds pass. N/Q max12.946/13.308ms and8.12MiB
workspace; process RSS max57.93MiB. K1 Q wins0against both controls, means equal,
state26positive delayed4→5; NO_USEFUL_CONDITIONING_SIGNAL. No new routes/camera calls/
seed/simulation, no whole500ms admission. Read I3_03_01_REPORT.md/results/validation.
Stop this bound ranking mechanism. Next scope decision only; no I3-03-02/P1/E2 or
automatic core implementation. Backup local only; no GitHub push for this checkpoint.

User execution boundary2026-10-14: stop serial diagnostic-only phases. Next user-started
batch allows at most one bounded method finalization then actual core route-generation
implementation, with correctness/profiling inside that batch. One complete prototype/
fixed comparison batch; at most one evidence-backed method revision, otherwise explicit
stop/downgrade decision. See the research execution boundary at the top of CODEX_HANDOFF.md.
D0 remains failed; this is not admission for the same AABB ranker/P1 under a new name.
