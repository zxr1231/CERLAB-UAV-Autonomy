import json
import tempfile
import unittest
from pathlib import Path

from exploration_benchmark.r1_snapshot_study import (aggregate_rows,
                                                      assign_stages,
                                                      select_decorrelated_snapshots,
                                                      summarize_report)


def _candidate(candidate_id, duplicate_ratio, unique_utility, marginals):
    raw = 100
    unique = round(raw * (1.0 - duplicate_ratio))
    return {
        "candidate_id": candidate_id,
        "sample_count": len(marginals),
        "raw_gain": raw,
        "unique_gain": unique,
        "marginal_gains": marginals,
        "duplicate_ratio": duplicate_ratio,
        "unique_utility": unique_utility,
        "raw_utility": unique_utility + duplicate_ratio * 100,
        "legacy_metrics": {"valid": True, "score": unique_utility + 10},
    }


class R1SnapshotStudyTest(unittest.TestCase):
    def test_summary_reports_ranking_change_and_regret(self):
        report = {
            "planning_sequence": 12,
            "map_version": 8,
            "selected_candidate": 0,
            "total_wall_seconds": 2.5,
            "rankings": {
                "legacy_score": [0, 1],
                "raw_utility": [0, 1],
                "unique_utility": [1, 0],
            },
            "candidates": [
                _candidate(0, 0.5, 30.0, [40, 0]),
                _candidate(1, 0.1, 40.0, [20, 20]),
            ],
        }
        row = summarize_report(report)
        self.assertTrue(row["raw_unique_top1_changed"])
        self.assertTrue(row["legacy_unique_top1_changed"])
        self.assertEqual(row["unique_best_candidate"], 1)
        self.assertEqual(row["selected_unique_regret"], 10.0)
        self.assertEqual(row["selected_unique_relative_regret"], 0.25)
        self.assertEqual(row["raw_best_candidate"], 0)
        self.assertEqual(row["raw_choice_unique_relative_regret"], 0.25)
        self.assertEqual(row["zero_marginal_fraction"], 0.25)
        self.assertEqual(row["raw_unique_rank_spearman"], -1.0)

    def test_equal_count_stage_assignment_is_ordered_and_complete(self):
        rows = [{"planning_sequence": value} for value in (70, 10, 60, 20, 50, 30, 40)]
        assigned = assign_stages(rows)
        self.assertEqual([row["planning_sequence"] for row in assigned],
                         [10, 20, 30, 40, 50, 60, 70])
        self.assertEqual([row["stage"] for row in assigned],
                         ["early", "early", "early", "middle", "middle", "late", "late"])

    def test_aggregate_uses_snapshot_level_rates(self):
        rows = []
        for index, changed in enumerate((False, True, True)):
            rows.append({
                "stage": ("early", "middle", "late")[index],
                "candidate_count": 2,
                "legacy_unique_top1_changed": changed,
                "raw_unique_top1_changed": changed,
                "legacy_unique_order_changed": changed,
                "raw_unique_order_changed": changed,
                "duplicate_ratio_mean": 0.2 + index * 0.1,
                "selected_duplicate_ratio": 0.3,
                "raw_unique_rank_spearman": 1.0 if not changed else -1.0,
                "selected_unique_relative_regret": 0.0 if not changed else 0.1,
                "raw_choice_unique_relative_regret": 0.0 if not changed else 0.05,
                "zero_marginal_fraction": 0.25,
                "diagnostic_wall_seconds": 2.0,
            })
        aggregate = aggregate_rows(rows)
        self.assertEqual(aggregate["overall"]["snapshot_count"], 3)
        self.assertEqual(aggregate["overall"]["candidate_count"], 6)
        self.assertAlmostEqual(aggregate["overall"]["raw_unique_top1_change_rate"], 2 / 3)
        self.assertEqual(aggregate["by_stage"]["early"]["snapshot_count"], 1)
        self.assertEqual(aggregate["overall"]["diagnostic_wall_seconds_sum"], 6.0)

    def test_decorrelation_uses_pose_and_map_version_not_gain(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = []
            fixtures = [
                ((0.0, 0.0, 0.0), 100, 1),
                ((0.1, 0.0, 0.0), 110, 9999),
                ((1.2, 0.0, 0.0), 120, 2),
                ((1.3, 0.0, 0.0), 700000, 8888),
                ((1.4, 0.0, 0.0), 700010, 7777),
            ]
            for index, (position, version, gain) in enumerate(fixtures):
                path = Path(temp) / f"snapshot_{index:06d}"
                path.mkdir()
                (path / "planner.json").write_text(json.dumps({
                    "vehicle": {"position": position},
                    "map_version": version,
                    "legacy_best_path_gain": gain,
                }), encoding="utf-8")
                paths.append(path)
            selected = select_decorrelated_snapshots(paths, 1.0, 500000, True)
            self.assertEqual([path.name for path in selected],
                             ["snapshot_000000", "snapshot_000002",
                              "snapshot_000003", "snapshot_000004"])

    def test_summary_rejects_missing_candidates(self):
        with self.assertRaisesRegex(ValueError, "no candidates"):
            summarize_report({"candidates": []})


if __name__ == "__main__":
    unittest.main()
