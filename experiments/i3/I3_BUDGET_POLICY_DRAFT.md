# Budget policy draft — reviewable, not deployed

Status2026-10-12: full original-Goal-set exact camera scoring NOT admitted.

- Physical sensor, speed/acceleration, map/coverage and Legacy stop threshold500 remain.
- Current test budget500ms counts map copy/model preparation/camera scoring. It does
  not mean whole global planner fits500ms; capture locks/search/safety/controls must
  be separately logged and included in later end-to-end policy.
- Require all common mandatory references before camera ranking; incomplete reference
  -> entire camera decisionfallback, no partial Goal set or partial-route gain.
- Optional candidates only after references; cooperative remaining-time limit, no
  padded duplicates or discarded failures. All experimental controls same rules.
- Candidate subset1/3/5/10 curves are cost diagnostics, never remove Goals for fairness.
- Existing50ms alternative generation cap remains prior I2 contract; anchor visibility
  or opportunity work must also be counted when future protocol allocates it.

Recommended scope to REVIEW BEFORE IMPLEMENTATION: common Legacy goal selection
first, then camera-scored routes to the SAME chosen Goal, all controls. It preserves
current sampling/default baseline and targets route opportunities, but changes the
camera comparison Goal set fromall prefilered Goals to one shared chosen Goal. This
must be explicit and newly registered, not called passing the failed all-Goal gate.
If chosen baseline fails final safety validation, no route refinement/flight is allowed
from that rejected proposal. Exact extra-candidate budgets still require new tests.

Alternative: retain all-Goal scope and register exact empty-observation/shared-pose
acceleration feasibility, preserving pose sets and candidate histories. No new kernel
optimization within completed2-intervention protocol, no threshold increase after data.
No core guided-route code yet. I3-01A chooses/freezes scope, sampler and full cost contract.
