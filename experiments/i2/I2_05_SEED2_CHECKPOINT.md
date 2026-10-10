# Seed2 checkpoint — 2026-10-10

User requested finish seed2, back up, stop before seed3. All eight completed trials
are checksum-verified; original failed/censored states are retained. See JSON summary
for per-trial metrics. No full3-seed inference is made. Source stays frozen0677947.

Seed1 Legacy T95385.174s, generic511.322s, geometric416.649s; single-route stalled
at92.29% with repeated B-spline infeasibility and was user-aborted, not rerun.
Seed2 T95: Legacy408.791s, single500.931s, generic423.078s, geometric496.147s.
Seed2 geometric reached home near deadline; raw runnerTIMEOUT remains.

On these two seeds, Legacy has the lowest observedT95, while generic route controls
do not consistently reduce travel/time. These are controls, not observation-guided
methods; no main-contribution failure/success is inferred. Await seed3 and actual
observation/provenance audit before completing I2-05.

Next pending order: seed3 generic, geometric, historical, single. Inspect external
controller/state and remove user stop marker only on explicit continuation.
Future guided-method cohort uses uniformly registered parallel setup per user.
