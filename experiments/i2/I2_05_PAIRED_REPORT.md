# I2-05 paired pilot checkpoint — collected12/12

User requested stop after seed3. All first attempts are retained, checksum-backed and
source/config audited. Collection commit0677947; same sensor/world/dynamics/Coverage,
K6/budgets, Legacy selection plus Unique shadow, headless, no rosbag. No algorithm
or parameter was changed during collection. Per-trial archive proofs are under
下载/CERLAB_I2_Backups/I2_05_PAIRED_RUNS_2026-10-10/.

| Mode | Seed1 T95(s) | Seed2 T95(s) | Seed3 T95(s) | Home event | Runner outcomes |
|---|---:|---:|---:|---:|---|
| historical Legacy |385.174|408.791|416.489|3/3|SUCCESS x3|
| distance single |censored|500.931|457.146|2/3|USER_ABORT, SUCCESS, SUCCESS|
| generic K |511.322|423.078|censored|2/3|SUCCESS, SUCCESS, TIMEOUT|
| geometric diverse |416.649|496.147|395.983|3/3|SUCCESS, TIMEOUT, SUCCESS|

Seed1 single-route was user-aborted after92.29% plateau/repeated B-spline infeasibility;
its originalUSER_ABORT is preserved, not a900s timeout. Seed3 generic reached94.25%
and suffered the same repeated execution infeasibility until900s. No favorable rerun.
Seed2 geometry reachedHOME_REACHED near the deadline but not the runner's extra
monitoring dwell; its originalTIMEOUT and actual home event are reported separately.
All twelve collision records report zero episodes; source/ROI/logging checks pass.

Legacy observed T95 mean403.485s, sample std16.318s (3/3 uncensored). Geometric
mean436.260s, std52.884s (3/3); geometry-vs-Legacy per-seed differences are mixed
(+31.475,+87.357,-20.506s), with mean+32.775s. Single/generic each miss oneT95;
uncensored-only means are conditional and cannot silently rank all3 trials.

Complete exploration distance means: Legacy187.288m; geometry338.870m, greater
on all3 seeds. Single and generic completed-only distance means exclude their failed
attempts and are explicitly labelled conditional in JSON. No significance/general
superiority claim with N3. Generic or geometric multi-route generation alone does
not establish stable exploration efficiency improvement in this pilot.

This tests internal CONTROLS, not the intended observation-opportunity-guided
construction. It neither validates nor disproves that primary proposed contribution.
The B-spline failures show that map-safe PRM routes need execution feasibility
consideration; they are retained limitations, not hidden data exceptions.

Summary retains frozen whole-run T thresholds and supplemental pre-exploration-end
reach flags, failures/censoring, CPU/RSS/RTF, trajectory, and sensor-only accessible
first-observation rates until completion/stop. Failed runs include stalled time;
per-metre rates alone can reward short stalled trajectories and must be read with
success/time. These rates are not executed counterfactuals for unselected candidates.

Reproduction: source workspace Python path then run
experiments/analysis/summarize_i2_paired.py --batch-root <registered result root>.
Derived JSON must match I2_05_PAIRED_SUMMARY.json. Raw data are never overwritten.

Next on explicit continuation: I2-06 decision and preregistered held-out observation
ordering gate, plus bounded assessment of execution feasibility. No core method
implementation starts automatically. User preference: after guided method is added,
NEW registered cohorts should use uniformly calibrated isolated parallel simulations;
keep current serial pilot distinct. No I1 data/conclusion or external baseline claim
was changed. Current task ends with GitHub/local checkpoint backup.
