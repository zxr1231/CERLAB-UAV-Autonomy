# I1-03 validation: exact C++/Python frozen-fixture agreement

Date: 2026-09-22

Status: complete. The I1 C++ evaluator passes exact reference agreement and boundary
correctness gates. Online route selection remains Legacy.

## Cross-language method

A deterministic C++ fixture runner independently reads and validates each R1/R2
snapshot manifest, FNV hashes, planner JSON and binary map payload. It evaluates all
shortcut candidate paths at 0.25 m and exports raw, unique, marginal and sorted unique
voxel-address results.

The Python comparison tool loads the same files through the established R1 reference,
recomputes each set, and requires:

- identical sample count;
- identical raw and unique integer gains;
- identical per-sample marginal sequence;
- identical sorted stable voxel-address set;
- duplicate ratio and unique utility equal within 1e-12 floating tolerance.

No expected gain values were copied into tests.

## Result

All retained R2 reference fixtures were evaluated:

```text
snapshots: 24 / 24 matched
candidates: 217 / 217 matched
path samples: 13,131
cumulative raw gain: 909,412
cumulative unique gain: 316,001
weighted duplicate ratio: 65.252%
mean per-candidate duplicate ratio: 51.546%
candidates with nonzero duplication: 178 / 217
```

The first six-snapshot run reported 45/52 matches because empty C++ address arrays
were serialized as JSON `null` instead of `[]`. Raw, unique, marginal and sample counts
already matched in those seven cases. The runner now initializes empty arrays
explicitly; the unchanged six snapshots then matched 52/52 before the 24-snapshot run.
This was a fixture serialization defect, not an evaluator change.

The committed agreement artifact is `I1_03_CPP_PYTHON_AGREEMENT.json`, SHA-256
`87e6944b0a36fbd913ecf030e6dd040c3bfa8ef39f52920c71b2c59f2c2bd12c`.

## Boundary verification

Nine C++ tests now cover:

- mode/schema/spacing capability validation;
- stable addresses and Unknown transparency;
- inflated-wall occlusion;
- raw/unique/marginal invariants and repeatability;
- expected snapshot-version mismatch;
- planning ROI clipping and yaw wrap;
- zero-length segment with distinct terminal yaw;
- malformed frozen map rejection.

The complete 85-test Python suite also passes. I1-03 performs no live flight and makes
no claim that Unique ranking improves exploration.

## Revision and next gate

- `global_planner`: `acfe5e8`;
- next task: I1-04 live `unique_shadow` validation;
- I1-04 must keep `selection_gain_mode=legacy`, measure evaluation cost and ranking
  changes, and trace any changed counterfactual route through the existing logs;
- `unique_online` remains fail-closed.

