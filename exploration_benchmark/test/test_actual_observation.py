import csv
import json
import tempfile
import unittest
from pathlib import Path

from exploration_benchmark.actual_observation import (build_actual_observation,
                                                       write_actual_observation)
from exploration_benchmark.execution_intervals import INTERVAL_FIELDS


def _interval(identifier, start, end, distance=1.0):
    row = {field: "" for field in INTERVAL_FIELDS}
    row.update({
        "interval_id": identifier,
        "trajectory_id": identifier,
        "global_sequence": 1,
        "start_sim": start,
        "end_sim": end,
        "duration_sim": end-start,
        "start_wall": start,
        "end_wall": end,
        "duration_wall": end-start,
        "start_reason": "test",
        "end_reason": "SUPERSEDED_BY_TRAJECTORY",
        "odom_count": 10,
        "executed_distance": distance,
        "valid": True,
        "errors": "[]",
    })
    return row


def _write_fixture(root, messages, intervals=None):
    intervals = intervals or [_interval(1, 1.0, 2.0), _interval(2, 2.0, 3.0, 2.0)]
    with (root / "execution_intervals.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=INTERVAL_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(intervals)
    with (root / "observation_deltas.jsonl").open("w", encoding="utf-8") as stream:
        for message in messages:
            stream.write(json.dumps(message) + "\n")


def _message(sequence, sim_time, logged_interval, addresses, observed_total):
    return {
        "sensor_sequence": sequence,
        "sim_time": sim_time,
        "execution_interval_id": logged_interval,
        "addresses": addresses,
        "delta_count": len(addresses),
        "observed_total": observed_total,
    }


class ActualObservationTest(unittest.TestCase):
    def test_timestamp_reassociation_union_and_rates(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _write_fixture(root, [
                _message(1, 0.5, 0, [1], 1),
                _message(2, 1.5, 1, [2, 3], 3),
                _message(3, 2.0, 1, [4], 4),
                _message(4, 2.5, 2, [5], 5),
                _message(5, 3.5, 0, [6], 6),
            ])
            result = build_actual_observation(root)
            self.assertEqual(result["status"], "VALID")
            self.assertEqual(result["logged_vs_timestamp_association_mismatch_count"], 1)
            self.assertEqual(result["unassociated_address_count"], 2)
            self.assertEqual(result["intervals"][0]["addresses"], [2, 3])
            self.assertEqual(result["intervals"][1]["addresses"], [4, 5])
            self.assertEqual(result["intervals"][0]["actual_new_voxels_per_meter"], 2.0)
            self.assertEqual(result["intervals"][1]["actual_new_voxels_per_meter"], 1.0)

    def test_sensor_sequence_gap_invalidates_result(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _write_fixture(root, [
                _message(1, 1.1, 1, [1], 1),
                _message(3, 1.2, 1, [2], 2),
            ])
            result = build_actual_observation(root)
            self.assertEqual(result["status"], "INVALID")
            self.assertTrue(any("sequence gap" in error for error in result["errors"]))

    def test_repeated_first_observation_address_invalidates_result(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _write_fixture(root, [
                _message(1, 1.1, 1, [7], 1),
                _message(2, 1.2, 1, [7], 2),
            ])
            result = build_actual_observation(root)
            self.assertEqual(result["status"], "INVALID")
            self.assertTrue(any("repeats" in error for error in result["errors"]))
            self.assertTrue(any("global union" in error for error in result["errors"]))

    def test_writer_preserves_sets_and_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _write_fixture(root, [_message(1, 1.5, 1, [8, 9], 2)])
            summary = write_actual_observation(root)
            self.assertEqual(summary["intervals_with_observation"], 1)
            self.assertTrue((root / "actual_observation_summary.json").is_file())
            rows = [json.loads(line) for line in
                    (root / "actual_observation_sets.jsonl").read_text().splitlines()]
            self.assertEqual(rows[0]["addresses"], [8, 9])
            self.assertEqual(rows[1]["addresses"], [])


if __name__ == "__main__":
    unittest.main()
