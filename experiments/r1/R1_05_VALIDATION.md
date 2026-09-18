# R1-05 checkpoint: early / middle / late snapshot study

Date: 2026-09-18

Status: complete as a single-run pilot. It supports continuing the diagnostic phase,
not a final paper claim.

## Protocol

- world: `floorplan2_dynamic_5.world`;
- Gazebo seed / DEP seed: 1 / 1;
- original online DEP/HIRE decisions and completion threshold 500;
- no GUI and no rosbag;
- collection from first successful global plan through completion;
- return triggered near simulation time 534.75 s; home reached near 569.62 s;
- 64 raw successful-planning snapshots;
- 25 retained by the gain-blind state-change rule: displacement >=1 m or map-version
  increase >=500,000, plus first/final;
- stages: 9 early, 8 middle, 8 late snapshots by retained planning-sequence tertiles;
- 0.5 m path sampling; 152 candidate routes; no diagnostic failures.

An initial stride-5 pilot produced only one snapshot by sequence 5 and was stopped
after about 116 simulation seconds because it could not support stage analysis. Its
directory is retained and excluded from all reported aggregates.

## Main descriptive results

| Metric | Overall | Early | Middle | Late |
|---|---:|---:|---:|---:|
| Snapshot count | 25 | 9 | 8 | 8 |
| Candidate count | 152 | 52 | 38 | 62 |
| Mean snapshot candidate duplicate ratio | 35.87% | 43.30% | 41.03% | 22.36% |
| Selected-route duplicate ratio | 48.61% | 47.28% | 52.12% | 46.58% |
| Raw→unique full-order change rate | 32.0% | 33.3% | 25.0% | 37.5% |
| Raw→unique Top-1 change rate | 8.0% | 11.1% | 12.5% | 0% |
| Raw/unique rank Spearman mean | 0.975 | 0.975 | 0.971 | 0.978 |
| Zero marginal sample fraction | 65.79% | 42.36% | 64.75% | 93.19% |

Pure path-history deduplication changed Top-1 in two snapshots:

- sequence 4, early: unique winner exceeded the raw winner by 5.30%;
- sequence 52, middle: unique winner exceeded the raw winner by 3.39%.

Across all snapshots, choosing the raw winner instead of the unique winner produced a
mean unique-utility regret of 0.35%, with a maximum of 5.30%. Legacy→unique Top-1
changed in 4/25 snapshots, but two additional changes include sampling-model effects
and cannot be credited to deduplication.

## Interpretation

H1 receives limited positive support:

- duplicated predicted observation is large and persistent, especially on the route
  selected by the baseline;
- deduplication changes some ordering and occasionally Top-1;
- the observed pure-dedup Top-1 effect is infrequent and modest in this run;
- late-stage marginal gains are often zero, but late-stage Top-1 did not change.

This result argues for keeping unique gain as the common evaluator and continuing to
R1-06. It does not justify presenting voxel union as the primary contribution. The
main paper value still needs observation-opportunity route generation to outperform
generic alternatives.

The 25 snapshots come from one trajectory and are temporally correlated. Stage labels
are equal-count state snapshots, not equal coverage intervals. No confidence interval
or significance claim is valid from this pilot alone. Formal H1 evidence still needs
multiple seeds and layouts, and H2 still needs predicted-versus-actual observation.

R1-06 subsequently found that 0.25 m is the defensible formal diagnostic spacing.
Under 0.25 m, raw→unique Top-1 changed in 4/25 snapshots (16%) and mean duplicate ratio
was 52.19%. These supersede the 0.5 m descriptive rates above for later R1 decisions;
the difference itself demonstrates that gain magnitude and ranking are sampling-step
sensitive. See `R1_06_VALIDATION.md`.
