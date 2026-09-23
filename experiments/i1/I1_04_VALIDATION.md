# I1-04 validation: live Unique shadow

Date: 2026-09-23

Status: complete with a conditional Go to I1-05. Shadow evaluation is correct and
stable enough to enable feature-flagged online selection, but its measured cost must
remain part of the method comparison.

## Runs

Two seed-1 diagnostics ran with `path_gain_mode=unique_shadow`. Both retained
`selection_gain_mode=legacy`, used no rosbag and reached HOME_REACHED without a
collision or process crash.

The small-ROI smoke produced 11/11 valid evaluations, a 7/11 counterfactual Top-1
change rate and 19.28 ms mean Unique evaluation time.

The full-floorplan run produced:

```text
final Coverage: 95.536%
T80/T90/T95: 226.808 / 329.542 / 423.896 s
mission time: 470.769 s
mission distance: 205.716 m
global plans: 31
valid Unique evaluations: 31/31
Top-1 changes: 16/31 (51.61%)
selected-path duplicate ratio: mean 66.06%, median 68.3%
```

Coverage-linked ranking changes were 9/16 before 80%, 4/9 from 80–95%, and 3/6 at or
above 95%. This shows the ranking effect persists across the run rather than appearing
only at startup.

## Computation

| Metric | Unique shadow seed 1 | Historical Legacy seed 1 |
|---|---:|---:|
| Unique evaluation mean / p95 / max | 47.57 / 101.90 / 112.22 ms | not applicable |
| Global planning mean / p95 / max | 96.41 / 177.85 / 203.56 ms | 35.96 / 116.16 / 133.05 ms |
| Mean RTF | 0.99918 | 0.99916 |
| Exploration CPU mean | 143.27% | 146.09% |
| Exploration RSS mean | 459.40 MiB | 444.51 MiB |

The historical run is descriptive context, not a paired causal comparison: added wall
time changes asynchronous mapping/planning timing even though the selected candidate
field remains Legacy. Mission T80/T90/T95 and distance must therefore not be used to
claim that shadow evaluation improves or degrades exploration.

Unique evaluation roughly doubles mean global-planning time in this run, while
absolute p95 remains below 0.2 s and RTF remains near one. I1-05 must carry this exact
cost; an Edge cache is not introduced before the conditional cache phase.

## Decision

I1-04 passes its engineering gate:

- all Unique fields are populated and all statuses are valid;
- every flown route and the completion gate remain Legacy;
- ranking changes are frequent and present in early/middle/late stages;
- the process remains real-time, collision-free and completes/returns;
- evaluation cost is material but currently bounded.

Proceed to I1-05 feature-flagged Unique online selection. Before running it, implement
the selection switch and explicit Legacy fallback tests. Do not compare I1-05 against
this shadow trajectory as if both had identical asynchronous state; use paired seed
runs under each declared mode.

