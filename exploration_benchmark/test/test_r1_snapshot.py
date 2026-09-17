import json
import struct
import tempfile
import unittest
from pathlib import Path

from exploration_benchmark.r1_snapshot import MAP_HEADER, SnapshotError, fnv1a64, load_snapshot


def _write_snapshot(root):
    root.mkdir()
    states = [(-1, 0), (0, 0), (1, 1), (0, 1)]
    header = MAP_HEADER.pack(
        b"CR1MAP1\0", 1, 7, 0.1,
        0.0, 0.0, 0.0, 0.2, 0.2, 0.1,
        2, 2, 1, -1.0, 0.5, len(states),
    )
    payload = b"".join(struct.pack("<bB", *state) for state in states)
    (root / "map.bin").write_bytes(header + payload)
    planner = {
        "schema": "cerlab-r1-planner-v1",
        "planning_sequence": 3,
        "map_version": 7,
        "roadmap_nodes": [],
        "roadmap_edges": [],
        "goal_candidates": [],
        "candidate_paths": [],
        "selected_candidate": -1,
    }
    (root / "planner.json").write_text(json.dumps(planner), encoding="utf-8")
    manifest = {
        "schema": "cerlab-r1-snapshot-v1",
        "complete": True,
        "planning_sequence": 3,
        "map_version": 7,
        "map_file": "map.bin",
        "map_fnv1a64": fnv1a64(root / "map.bin"),
        "planner_file": "planner.json",
        "planner_fnv1a64": fnv1a64(root / "planner.json"),
    }
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


class R1SnapshotTest(unittest.TestCase):
    def test_snapshot_round_trip_and_repeatability(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / "snapshot_000003"
            _write_snapshot(directory)
            first = load_snapshot(directory)
            second = load_snapshot(directory)
            self.assertEqual(first, second)
            self.assertEqual(first["map"]["occupancy_counts"],
                             {"unknown": 1, "free": 2, "occupied": 1})
            self.assertEqual(first["map"]["inflated_count"], 2)

    def test_snapshot_rejects_changed_payload(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / "snapshot_000003"
            _write_snapshot(directory)
            with (directory / "map.bin").open("ab") as stream:
                stream.write(b"x")
            with self.assertRaisesRegex(SnapshotError, "hash mismatch"):
                load_snapshot(directory)

    def test_snapshot_requires_manifest_commit_marker(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(SnapshotError, "commit marker"):
                load_snapshot(temp)
