# R2-03 validation: actual newly observed voxel sets

Date: 2026-09-21

Status: complete for offline actual-set construction. No predicted set or correlation
metric has been computed.

## Method

The analyzer reads `execution_intervals.csv` and `observation_deltas.jsonl` and:

1. validates unique, ordered, non-overlapping execution intervals;
2. validates sensor sequence continuity, `delta_count`, cumulative `observed_total`,
   and global first-observation uniqueness;
3. assigns each delta to a canonical half-open execution interval using the sensor
   message timestamp, not callback arrival state;
4. records callback-ID versus timestamp-ID mismatches without hiding them;
5. unions stable voxel addresses independently for every interval;
6. retains before-first, between-interval and after-final observations separately;
7. reports actual-new count, per-meter/per-second rates, set SHA-256 and full sorted
   address sets.

The result is invalidated by sequence gaps, observed-total inconsistency, repeated
first-observation addresses, malformed messages, duplicate intervals or interval
overlap. Correctable callback-boundary mismatch is audited rather than treated as
sensor data loss.

Artificial takeoff/detector clearing is excluded by provenance: `setFree` and
`freeRegion` do not call `SensorObservationTracker::mark()`. The existing C++ test
`ArtificialMapClearingDoesNotCreateSensorProvenance` directly verifies this property.
The first rostest invocation used a stale September test executable and terminated
before producing results. After rebuilding the specific test target against the current
map_manager ABI, all three sensor-observation tracker tests passed, including the
artificial-clearing case. The stale-binary failure is not counted as an algorithm pass.

## Tests

Four new tests cover timestamp boundary reassignment, interval unions/rates, sensor
sequence gaps, repeated first-observation addresses and deterministic file output.
Together with previous tests, the exploration benchmark suite has 63 passing tests.

## Passing smoke result

The passing R2-01/02 fixture produced:

- 43 valid execution intervals; all 43 received actual observations;
- 1,416 delta messages and 490,729 globally unique first-observation addresses;
- no sensor sequence gap, duplicate address, count mismatch or total mismatch;
- 443,024 addresses assigned to execution intervals by message timestamp;
- 47,705 addresses before the first interval, covering startup/takeoff/no-active-plan;
- zero between-interval and after-final addresses;
- 39 callback-ID/timestamp-ID mismatches, of which 38 were reassigned into canonical
  intervals and one fell outside the canonical interval timeline.

The mismatches are expected near rapid B-spline replacement because ROS callbacks are
not an atomic transaction. R2 uses timestamp-canonical sets and keeps mismatch counts
for R2-05 alignment acceptance.

| Generated file | SHA-256 |
|---|---|
| `actual_observation_summary.json` | `193221a1a8d68ed93a0d047d195674cb319dc6e53183afc22b57c02f8f2a80de` |
| `actual_observation_intervals.csv` | `3a79ce07f865f2a2e70e7331f8768d4b20efe6ceeb42e84455142aad8407463c` |
| `actual_observation_sets.jsonl` | `c4fad36d5e55b2196cae28a65266631cc7cabf6fa299d55f989f090b1cd0a34d` |

## Limitations

- this is a manually stopped integration fixture, not a full exploration experiment;
- per-meter rates can be extremely large for short intervals and are not yet an
  effectiveness metric;
- observations during startup are excluded from interval comparison but retained in
  the summary;
- R2-04 must construct predicted sets for PRM, shortcut, B-spline and actual odometry
  prefixes before overlap, precision, recall or calibration can be assessed.
