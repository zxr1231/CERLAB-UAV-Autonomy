#!/usr/bin/env python3
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from exploration_benchmark.batch import (canonical_hash, eligible_tasks,
                                         parse_matrix_config, recover_running_tasks)


class BatchTest(unittest.TestCase):
    def test_expands_seed_pairs_and_repeats_in_order(self):
        matrix = parse_matrix_config({
            "schema_version": 1, "experiment_id": "EXP-MATRIX", "mode": "smoke",
            "timeout": 30, "seed_pairs": [[1, 2], [3, 4]], "repeats": 2,
        })
        self.assertEqual([task["task_id"] for task in matrix["tasks"]], [
            "env001_planner002_repeat01", "env001_planner002_repeat02",
            "env003_planner004_repeat01", "env003_planner004_repeat02"])

    def test_duplicate_and_invalid_configs_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            parse_matrix_config({"schema_version": 1, "experiment_id": "EXP",
                                 "seed_pairs": [[1, 1], [1, 1]]})
        with self.assertRaises(ValueError):
            parse_matrix_config({"schema_version": 2, "experiment_id": "EXP",
                                 "seed_pairs": [[1, 1]]})

    def test_resume_policy_and_hash(self):
        tasks = [{"task_id": "a", "status": "SUCCESS", "attempts": []},
                 {"task_id": "b", "status": "FAILED", "attempts": []},
                 {"task_id": "c", "status": "RUNNING",
                  "attempts": [{"status": "RUNNING"}]}]
        self.assertEqual(recover_running_tasks(tasks), 1)
        self.assertEqual([task["task_id"] for task in eligible_tasks(tasks)], ["c"])
        self.assertEqual([task["task_id"] for task in eligible_tasks(tasks, True)],
                         ["b", "c"])
        self.assertEqual(canonical_hash({"b": 2, "a": 1}),
                         canonical_hash({"a": 1, "b": 2}))


if __name__ == "__main__":
    unittest.main()
