# R1-01 checkpoint: baseline and definitions frozen

Date: 2026-09-17

Status: complete.

The exact baseline revisions, gain definitions, fixed Benchmark v2 controls, and
separation from the legacy completion gate are recorded in `README.md`. Source review
confirmed that the mission still evaluates completion using legacy
`getBestPathGain()` and `reachableGainExhausted()` with threshold 500. No R1 metric is
connected to either call.

This checkpoint authorizes only offline diagnosis. It does not claim that duplicate
gain is significant or that route ranking will change.
