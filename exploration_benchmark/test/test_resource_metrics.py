#!/usr/bin/env python3
import csv
import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from exploration_benchmark.resource_metrics import (ResourceMonitor, parse_proc_stat,
                                                    read_process_trees)


def stat_line(pid, command, ppid, pgrp, utime, stime, rss):
    fields = ["S", str(ppid), str(pgrp), "1", "0", "0", "0", "0", "0", "0", "0",
              str(utime), str(stime), "0", "0", "0", "0", "1", "0", "0", "0",
              str(rss)]
    return "%d (%s) %s\n" % (pid, command, " ".join(fields))


class ResourceMetricsTest(unittest.TestCase):
    def test_parse_handles_spaces_and_parentheses_in_command(self):
        self.assertEqual(parse_proc_stat(
            stat_line(4, "a tricky) name", 2, 9, 20, 3, 7)), (2, 9, 23, 7))

    def test_group_aggregation_and_cpu_delta(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            proc = root / "proc"
            output = root / "output"
            proc.mkdir(); output.mkdir()
            for pid, parent, ticks, pages in ((10, 1, 20, 3), (11, 10, 30, 5)):
                directory = proc / str(pid); directory.mkdir()
                (directory / "stat").write_text(stat_line(pid, "worker", parent, pid,
                                                           ticks, 0, pages))
            totals = read_process_trees([10], proc)
            self.assertEqual(totals[10], {"process_count": 2, "cpu_ticks": 50,
                                           "rss_pages": 8})
            monitor = ResourceMonitor(output, clock_ticks=10, page_size=4096,
                                      proc_root=proc)
            monitor.sample(1, 2, {"exploration": 10})
            (proc / "10/stat").write_text(stat_line(10, "worker", 1, 10, 25, 0, 3))
            (proc / "11/stat").write_text(stat_line(11, "worker", 10, 11, 35, 0, 5))
            rows = monitor.sample(3, 4, {"exploration": 10})
            self.assertAlmostEqual(rows[0]["cpu_percent_one_core"], 50.0)
            summary = monitor.close()
            self.assertEqual(summary["status"], "VALID")
            self.assertEqual(summary["components"]["exploration"]["sample_count"], 2)
            with (output / "resources.csv").open() as stream:
                self.assertEqual(len(list(csv.DictReader(stream))), 2)
            with (output / "resource_summary.json").open() as stream:
                self.assertEqual(json.load(stream)["status"], "VALID")


if __name__ == "__main__":
    unittest.main()
