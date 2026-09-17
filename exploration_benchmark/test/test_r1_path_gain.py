import math
import unittest
from unittest import mock

from exploration_benchmark.r1_path_gain import (diagnose_snapshot_paths,
                                                 evaluate_candidate_path,
                                                 sample_candidate_path)
from exploration_benchmark.r1_visibility import LegacyVisibilityConfig


CONFIG = LegacyVisibilityConfig(math.pi / 2, math.pi / 2, 0.0, 3.0,
                                (-10.0, -10.0, -10.0), (10.0, 10.0, 10.0))


def _candidate(candidate_id, points, legacy_score=1.0):
    return {
        "id": candidate_id,
        "legacy_metrics": {
            "valid": True,
            "gain": 10,
            "path_length": 1.0,
            "yaw_distance": 0.0,
            "estimated_time": 1.0,
            "score": legacy_score,
        },
        "waypoints": [
            {"position": list(position), "yaw": yaw} for position, yaw in points
        ],
    }


class R1PathGainTest(unittest.TestCase):
    def test_polyline_sampling_uses_outgoing_and_terminal_yaw(self):
        path = _candidate(0, [
            ((0.0, 0.0, 0.0), 0.0),
            ((1.0, 0.0, 0.0), math.pi / 2),
            ((1.0, 1.0, 0.0), math.pi),
        ])
        samples = sample_candidate_path(path["waypoints"], 0.5)
        self.assertEqual([round(sample.distance_along_path, 6) for sample in samples],
                         [0.0, 0.5, 1.0, 1.5, 2.0])
        self.assertEqual([sample.yaw for sample in samples],
                         [0.0, 0.0, math.pi / 2, math.pi / 2, math.pi])

    def test_repeated_observation_has_zero_second_marginal(self):
        path = _candidate(0, [
            ((0.0, 0.0, 0.0), 0.0),
            ((1.0, 0.0, 0.0), 0.0),
            ((2.0, 0.0, 0.0), 0.0),
        ])

        def visibility(_grid, position, _yaw, _config):
            return {1, 2} if position[0] < 1.5 else {3}

        result = evaluate_candidate_path(object(), path, CONFIG, 1.0, visibility)
        self.assertEqual(result["sample_gains"], [2, 2, 1])
        self.assertEqual(result["marginal_gains"], [2, 0, 1])
        self.assertEqual(result["raw_gain"], 5)
        self.assertEqual(result["unique_gain"], 3)
        self.assertAlmostEqual(result["duplicate_ratio"], 0.4)

    def test_disjoint_observations_have_no_duplicates(self):
        path = _candidate(0, [
            ((0.0, 0.0, 0.0), 0.0),
            ((1.0, 0.0, 0.0), 0.0),
        ])

        def visibility(_grid, position, _yaw, _config):
            return {1, 2} if position[0] < 0.5 else {3, 4}

        result = evaluate_candidate_path(object(), path, CONFIG, 1.0, visibility)
        self.assertEqual(result["raw_gain"], 4)
        self.assertEqual(result["unique_gain"], 4)
        self.assertEqual(result["marginal_gains"], [2, 2])
        self.assertEqual(result["duplicate_ratio"], 0.0)

    def test_zero_gain_ratio_is_defined(self):
        path = _candidate(0, [((0.0, 0.0, 0.0), 0.0)])
        result = evaluate_candidate_path(object(), path, CONFIG, 0.5,
                                         lambda *_args: set())
        self.assertEqual(result["raw_gain"], 0)
        self.assertEqual(result["unique_gain"], 0)
        self.assertEqual(result["duplicate_ratio"], 0.0)

    def test_candidate_histories_are_independent(self):
        path = _candidate(0, [
            ((0.0, 0.0, 0.0), 0.0),
            ((1.0, 0.0, 0.0), 0.0),
        ])
        visibility = lambda *_args: {11, 12}
        first = evaluate_candidate_path(object(), path, CONFIG, 1.0, visibility)
        second = evaluate_candidate_path(object(), path, CONFIG, 1.0, visibility)
        self.assertEqual(first["marginal_gains"], [2, 0])
        self.assertEqual(second["marginal_gains"], [2, 0])
        self.assertEqual(first["unique_set_sha256"], second["unique_set_sha256"])

    def test_diagnostic_detects_raw_to_unique_ranking_reversal(self):
        candidates = [
            _candidate(0, [((0.0, 0.0, 0.0), 0.0),
                           ((1.0, 0.0, 0.0), 0.0)], legacy_score=10.0),
            _candidate(1, [((0.0, 1.0, 0.0), 0.0),
                           ((1.0, 1.0, 0.0), 0.0)], legacy_score=9.0),
        ]
        planner = {
            "planning_sequence": 4,
            "selected_candidate": 0,
            "sensor_model": {
                "horizontal_fov": math.pi / 2,
                "vertical_fov": math.pi / 2,
                "dmin": 0.0,
                "dmax": 3.0,
                "visibility_model": "legacy_inflated_occupied_line",
            },
            "planning_region": {"min": [-10, -10, -10], "max": [10, 10, 10]},
            "candidate_paths": candidates,
        }
        snapshot = {"planner": planner, "manifest": {"map_file": "map.bin"}}
        grid = mock.Mock(version=8)

        def visibility(_grid, position, _yaw, _config):
            if position[1] == 0.0:
                return {1, 2, 3}
            return {4, 5} if position[0] == 0.0 else {6, 7}

        with mock.patch("exploration_benchmark.r1_path_gain.load_snapshot",
                        return_value=snapshot), mock.patch(
                            "exploration_benchmark.r1_path_gain.load_frozen_map",
                            return_value=grid):
            report = diagnose_snapshot_paths("fixture", 1.0, visibility)
        self.assertEqual(report["rankings"]["legacy_score"], [0, 1])
        self.assertEqual(report["rankings"]["raw_utility"], [0, 1])
        self.assertEqual(report["rankings"]["unique_utility"], [1, 0])
        self.assertTrue(report["ranking_changes"]["raw_to_unique_top1"])
        self.assertTrue(report["ranking_changes"]["legacy_to_unique_top1"])
        self.assertTrue(all(report["invariants"].values()))

    def test_invalid_spacing_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "spacing"):
            sample_candidate_path([], 0.0)


if __name__ == "__main__":
    unittest.main()
