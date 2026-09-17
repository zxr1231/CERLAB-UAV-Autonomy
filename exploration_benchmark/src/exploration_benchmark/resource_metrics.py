"""Low-overhead Linux process-group resource accounting."""
import csv
import os
from pathlib import Path

from exploration_benchmark.core import atomic_write_json, value_summary


RESOURCE_FIELDS = [
    "wall_elapsed", "sim_time", "component", "root_pid", "process_count",
    "cpu_seconds", "cpu_percent_one_core", "rss_bytes", "rss_mib",
]


def parse_proc_stat(text):
    """Return (parent PID, process group, CPU ticks, RSS pages) from /proc/PID/stat."""
    end = text.rfind(")")
    if end < 0:
        raise ValueError("invalid /proc stat: missing command terminator")
    fields = text[end + 2:].split()
    if len(fields) < 22:
        raise ValueError("invalid /proc stat: too few fields")
    return (int(fields[1]), int(fields[2]), int(fields[11]) + int(fields[12]),
            max(0, int(fields[21])))


def read_process_trees(root_pids, proc_root="/proc"):
    roots = set(int(value) for value in root_pids)
    processes = {}
    for entry in Path(proc_root).iterdir():
        if not entry.name.isdigit():
            continue
        try:
            ppid, _pgid, cpu_ticks, rss_pages = parse_proc_stat(
                (entry / "stat").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        processes[int(entry.name)] = {"ppid": ppid, "cpu_ticks": cpu_ticks,
                                      "rss_pages": rss_pages}
    totals = {root: {"process_count": 0, "cpu_ticks": 0, "rss_pages": 0}
              for root in roots}
    for pid, values in processes.items():
        ancestor = pid
        visited = set()
        while ancestor not in roots and ancestor in processes and ancestor not in visited:
            visited.add(ancestor)
            ancestor = processes[ancestor]["ppid"]
        if ancestor in roots:
            totals[ancestor]["process_count"] += 1
            totals[ancestor]["cpu_ticks"] += values["cpu_ticks"]
            totals[ancestor]["rss_pages"] += values["rss_pages"]
    return totals


class ResourceMonitor:
    """Sample named process trees and write a long-form CSV plus summary JSON."""
    def __init__(self, output_dir, clock_ticks=None, page_size=None, proc_root="/proc"):
        self.output_dir = Path(output_dir)
        self.clock_ticks = float(clock_ticks or os.sysconf("SC_CLK_TCK"))
        self.page_size = int(page_size or os.sysconf("SC_PAGE_SIZE"))
        self.proc_root = proc_root
        self.previous_wall = None
        self.previous_ticks = {}
        self.records = []
        self.stream = (self.output_dir / "resources.csv").open(
            "x", newline="", encoding="utf-8")
        self.writer = csv.DictWriter(self.stream, fieldnames=RESOURCE_FIELDS,
                                     lineterminator="\n")
        self.writer.writeheader()
        self.stream.flush()

    def sample(self, wall_elapsed, sim_time, roots):
        roots = {str(name): int(pid) for name, pid in roots.items()}
        raw = read_process_trees(roots.values(), self.proc_root)
        delta_wall = (None if self.previous_wall is None else
                      float(wall_elapsed) - self.previous_wall)
        rows = []
        for name, root_pid in sorted(roots.items()):
            values = raw[root_pid]
            cpu_seconds = values["cpu_ticks"] / self.clock_ticks
            previous = self.previous_ticks.get(name)
            cpu_percent = (None if previous is None or not delta_wall or delta_wall <= 0
                           else 100.0 * (values["cpu_ticks"] - previous) /
                           self.clock_ticks / delta_wall)
            rss_bytes = values["rss_pages"] * self.page_size
            row = {
                "wall_elapsed": float(wall_elapsed),
                "sim_time": sim_time,
                "component": name,
                "root_pid": root_pid,
                "process_count": values["process_count"],
                "cpu_seconds": cpu_seconds,
                "cpu_percent_one_core": cpu_percent,
                "rss_bytes": rss_bytes,
                "rss_mib": rss_bytes / (1024.0 * 1024.0),
            }
            self.writer.writerow({key: "" if value is None else value
                                  for key, value in row.items()})
            self.records.append(row)
            rows.append(row)
            self.previous_ticks[name] = values["cpu_ticks"]
        self.previous_wall = float(wall_elapsed)
        self.stream.flush()
        return rows

    def close(self):
        if self.stream.closed:
            raise RuntimeError("resource monitor already closed")
        self.stream.flush()
        self.stream.close()
        components = {}
        for name in sorted(set(row["component"] for row in self.records)):
            rows = [row for row in self.records if row["component"] == name]
            components[name] = {
                "sample_count": len(rows),
                "cpu_percent_one_core": value_summary([
                    row["cpu_percent_one_core"] for row in rows
                    if row["cpu_percent_one_core"] is not None]),
                "rss_mib": value_summary([row["rss_mib"] for row in rows]),
                "peak_process_count": max((row["process_count"] for row in rows),
                                          default=0),
            }
        summary = {
            "schema_version": 1,
            "status": "VALID" if self.records else "NO_SAMPLES",
            "cpu_percent_definition": "summed process CPU; 100 percent equals one logical core",
            "rss_definition": "sum of per-process resident pages; shared pages may be counted repeatedly",
            "sampling_scope": "runner-created process trees after PLANNING_ACTIVE",
            "components": components,
        }
        atomic_write_json(self.output_dir / "resource_summary.json", summary)
        return summary
