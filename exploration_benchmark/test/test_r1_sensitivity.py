import json
import tempfile
import unittest
from pathlib import Path

from exploration_benchmark.r1_sensitivity import compare_sampling_studies


def _candidate(candidate_id, unique_gain, utility, positions):
    return {
        "candidate_id": candidate_id,
        "unique_gain": unique_gain,
        "unique_utility": utility,
        "sample_count": len(positions),
        "evaluation_wall_seconds": 1.0,
        "samples": [
            {"position": list(position), "yaw": 0.0} for position in positions
        ],
    }


def _write_study(root, spacing, candidates, rank):
    root.mkdir()
    (root / "reports").mkdir()
    summary = {
        "rows": [{"snapshot": "snapshot_000001"}],
        "process_max_rss_kib": 1234,
    }
    report = {
        "candidates": candidates,
        "rankings": {"unique_utility": rank},
        "total_wall_seconds": 3.0,
    }
    (root / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (root / "reports" / "snapshot_000001.json").write_text(
        json.dumps(report), encoding="utf-8")


class R1SensitivityTest(unittest.TestCase):
    def test_compare_reports_gain_error_ranking_and_reuse(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shared = [((0, 0, 0), (1, 0, 0)), ((0, 0, 0), (1, 0, 0))]
            fine_candidates = [
                _candidate(0, 100, 10, shared[0]),
                _candidate(1, 80, 8, shared[1]),
            ]
            coarse_candidates = [
                _candidate(0, 75, 7.5, shared[0]),
                _candidate(1, 80, 8, shared[1]),
            ]
            _write_study(root / "fine", 0.25, fine_candidates, [0, 1])
            _write_study(root / "coarse", 0.5, coarse_candidates, [1, 0])
            result = compare_sampling_studies({0.25: root / "fine", 0.5: root / "coarse"})
            comparison = result["comparisons"]["0.5"]
            self.assertEqual(comparison["unique_top1_agreement_vs_finest"], 0.0)
            self.assertAlmostEqual(comparison["unique_gain_relative_error_mean_vs_finest"], 0.125)
            self.assertEqual(result["operational_reuse"]["exact_sample_reuse_fraction"], 0.5)
            self.assertEqual(result["operational_reuse"]["exact_directed_edge_reuse_fraction"], 0.5)
            self.assertEqual(result["cache_gate"]["recommendation"],
                             "edge_cache_profiling_gate_passed")

    def test_mismatched_snapshots_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            candidates = [_candidate(0, 10, 1, [(0, 0, 0)])]
            _write_study(root / "first", 0.25, candidates, [0])
            _write_study(root / "second", 0.5, candidates, [0])
            summary_path = root / "second" / "summary.json"
            summary = json.loads(summary_path.read_text())
            summary["rows"][0]["snapshot"] = "snapshot_000002"
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            report_path = root / "second" / "reports" / "snapshot_000001.json"
            report_path.rename(root / "second" / "reports" / "snapshot_000002.json")
            with self.assertRaisesRegex(ValueError, "same snapshots"):
                compare_sampling_studies({0.25: root / "first", 0.5: root / "second"})


if __name__ == "__main__":
    unittest.main()
