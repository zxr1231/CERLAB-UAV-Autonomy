"""Build actual sensor-observed voxel sets for R2 execution intervals."""

import bisect
import csv
import hashlib
import json
import math
import os
import struct
from pathlib import Path

from exploration_benchmark.core import atomic_write_json


ACTUAL_FIELDS = [
    "interval_id", "trajectory_id", "global_sequence", "start_sim", "end_sim",
    "duration_sim", "executed_distance", "odom_count", "start_reason", "end_reason",
    "delta_message_count", "actual_new_voxels", "actual_new_voxels_per_meter",
    "actual_new_voxels_per_second", "logged_association_mismatch_count",
    "actual_set_sha256", "valid", "errors",
]


def _parse_optional_int(value):
    return None if value in (None, "") else int(value)


def _parse_bool(value):
    return str(value).lower() in ("1", "true", "yes")


def _set_hash(addresses):
    digest = hashlib.sha256()
    for address in sorted(addresses):
        digest.update(struct.pack("<I", address))
    return digest.hexdigest()


def _read_intervals(path):
    with Path(path).open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    intervals = []
    errors = []
    seen_ids = set()
    for row in rows:
        interval_id = int(row["interval_id"])
        if interval_id in seen_ids:
            errors.append("duplicate interval_id %d" % interval_id)
        seen_ids.add(interval_id)
        item = {
            "interval_id": interval_id,
            "trajectory_id": int(row["trajectory_id"]),
            "global_sequence": int(row["global_sequence"]),
            "start_sim": float(row["start_sim"]),
            "end_sim": float(row["end_sim"]),
            "duration_sim": float(row["duration_sim"]),
            "executed_distance": float(row["executed_distance"]),
            "odom_count": int(row["odom_count"]),
            "start_reason": row["start_reason"],
            "end_reason": row["end_reason"],
            "source_valid": _parse_bool(row["valid"]),
            "source_errors": json.loads(row["errors"] or "[]"),
            "addresses": set(),
            "delta_message_count": 0,
            "logged_association_mismatch_count": 0,
        }
        if item["end_sim"] < item["start_sim"]:
            errors.append("interval %d has reversed time" % interval_id)
        intervals.append(item)
    intervals.sort(key=lambda item: (item["start_sim"], item["end_sim"], item["interval_id"]))
    for previous, current in zip(intervals, intervals[1:]):
        if current["start_sim"] < previous["end_sim"] - 1e-9:
            errors.append("intervals %d and %d overlap" %
                          (previous["interval_id"], current["interval_id"]))
    return intervals, errors


def _canonical_interval(intervals, starts, sim_time):
    index = bisect.bisect_right(starts, sim_time) - 1
    if index < 0:
        return None
    interval = intervals[index]
    is_final = index == len(intervals)-1
    if sim_time < interval["end_sim"] or (is_final and sim_time <= interval["end_sim"]):
        return interval
    return None


def build_actual_observation(run_directory):
    run_directory = Path(run_directory)
    intervals, errors = _read_intervals(run_directory / "execution_intervals.csv")
    starts = [item["start_sim"] for item in intervals]
    global_addresses = set()
    previous_sequence = None
    previous_total = None
    message_count = 0
    address_count = 0
    mismatches = 0
    unassociated = {"before_first": 0, "between_intervals": 0, "after_final": 0}

    with (run_directory / "observation_deltas.jsonl").open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            message_count += 1
            try:
                row = json.loads(line)
                sequence = int(row["sensor_sequence"])
                observed_total = int(row["observed_total"])
                addresses = [int(value) for value in row["addresses"]]
                sim_time = float(row["sim_time"])
                logged_interval_id = int(row.get("execution_interval_id") or 0)
            except (KeyError, TypeError, ValueError) as error:
                errors.append("line %d invalid: %s" % (line_number, error))
                continue
            if int(row.get("delta_count", -1)) != len(addresses):
                errors.append("sequence %d delta_count mismatch" % sequence)
            if previous_sequence is not None and sequence != previous_sequence + 1:
                errors.append("sensor sequence gap %d->%d" % (previous_sequence, sequence))
            if previous_total is None:
                if observed_total != len(addresses):
                    errors.append("first observed_total does not equal first delta")
            elif observed_total != previous_total + len(addresses):
                errors.append("sequence %d observed_total mismatch" % sequence)
            previous_sequence = sequence
            previous_total = observed_total

            duplicate_count = sum(address in global_addresses for address in addresses)
            if duplicate_count:
                errors.append("sequence %d repeats %d first-observation addresses" %
                              (sequence, duplicate_count))
            global_addresses.update(addresses)
            address_count += len(addresses)

            interval = _canonical_interval(intervals, starts, sim_time)
            canonical_id = 0 if interval is None else interval["interval_id"]
            if logged_interval_id != canonical_id:
                mismatches += 1
                if interval is not None:
                    interval["logged_association_mismatch_count"] += 1
            if interval is None:
                if not intervals or sim_time < intervals[0]["start_sim"]:
                    unassociated["before_first"] += len(addresses)
                elif sim_time > intervals[-1]["end_sim"]:
                    unassociated["after_final"] += len(addresses)
                else:
                    unassociated["between_intervals"] += len(addresses)
                continue
            interval["addresses"].update(addresses)
            interval["delta_message_count"] += 1

    if previous_total is not None and previous_total != len(global_addresses):
        errors.append("final observed_total does not equal reconstructed global union")

    records = []
    for interval in intervals:
        interval_errors = list(interval["source_errors"])
        if not interval["source_valid"]:
            interval_errors.append("source interval invalid")
        count = len(interval["addresses"])
        distance = interval["executed_distance"]
        duration = interval["duration_sim"]
        records.append({
            "interval_id": interval["interval_id"],
            "trajectory_id": interval["trajectory_id"],
            "global_sequence": interval["global_sequence"],
            "start_sim": interval["start_sim"],
            "end_sim": interval["end_sim"],
            "duration_sim": duration,
            "executed_distance": distance,
            "odom_count": interval["odom_count"],
            "start_reason": interval["start_reason"],
            "end_reason": interval["end_reason"],
            "delta_message_count": interval["delta_message_count"],
            "actual_new_voxels": count,
            "actual_new_voxels_per_meter": count/distance if distance > 0 else None,
            "actual_new_voxels_per_second": count/duration if duration > 0 else None,
            "logged_association_mismatch_count": interval["logged_association_mismatch_count"],
            "actual_set_sha256": _set_hash(interval["addresses"]),
            "addresses": sorted(interval["addresses"]),
            "valid": not interval_errors,
            "errors": interval_errors,
        })
    return {
        "schema": "cerlab-r2-actual-observation-v1",
        "run_directory": str(run_directory),
        "provenance": "map_manager_sensor_observation_delta_first_observation_union",
        "artificial_clear_included": False,
        "interval_count": len(records),
        "valid_interval_count": sum(record["valid"] for record in records),
        "message_count": message_count,
        "delta_address_count": address_count,
        "global_unique_address_count": len(global_addresses),
        "logged_vs_timestamp_association_mismatch_count": mismatches,
        "unassociated_address_count": sum(unassociated.values()),
        "unassociated_addresses_by_phase": unassociated,
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
        "intervals": records,
    }


def write_actual_observation(run_directory, output_directory=None):
    run_directory = Path(run_directory)
    output_directory = Path(output_directory) if output_directory else run_directory
    output_directory.mkdir(parents=True, exist_ok=True)
    result = build_actual_observation(run_directory)
    summary = {key: value for key, value in result.items() if key != "intervals"}
    summary["intervals_with_observation"] = sum(
        item["actual_new_voxels"] > 0 for item in result["intervals"])
    atomic_write_json(output_directory / "actual_observation_summary.json", summary)
    with (output_directory / "actual_observation_intervals.csv").open(
            "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=ACTUAL_FIELDS, lineterminator="\n")
        writer.writeheader()
        for item in result["intervals"]:
            row = {field: item[field] for field in ACTUAL_FIELDS}
            row["errors"] = json.dumps(row["errors"], sort_keys=True)
            writer.writerow(row)
    sets_path = output_directory / "actual_observation_sets.jsonl"
    temporary = sets_path.with_name(sets_path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        for item in result["intervals"]:
            stream.write(json.dumps({
                "interval_id": item["interval_id"],
                "trajectory_id": item["trajectory_id"],
                "global_sequence": item["global_sequence"],
                "actual_new_voxels": item["actual_new_voxels"],
                "actual_set_sha256": item["actual_set_sha256"],
                "addresses": item["addresses"],
            }, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(str(temporary), str(sets_path))
    return summary
