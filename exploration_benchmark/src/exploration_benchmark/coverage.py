"""Ground-truth coverage accounting from sensor-observation address deltas."""
import json
from pathlib import Path

import numpy as np


class CoverageAccumulator:
    THRESHOLDS = (0.80, 0.90, 0.95)

    def __init__(self, mask_path, metadata_path):
        self.mask_path = Path(mask_path).resolve()
        self.metadata_path = Path(metadata_path).resolve()
        self.metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        with np.load(self.mask_path) as archive:
            self.accessible_free = archive["accessible_free"].astype(bool, copy=True)
            self.static_surface = archive["static_surface"].astype(bool, copy=True)
            has_observable_free = "observable_free" in archive.files
            has_observable_surface = "observable_static_surface" in archive.files
            if has_observable_free != has_observable_surface:
                raise ValueError("observable free and surface masks must be provided together")
            self.observable_free = (archive["observable_free"].astype(bool, copy=True)
                                    if has_observable_free else None)
            self.observable_surface = (
                archive["observable_static_surface"].astype(bool, copy=True)
                if has_observable_surface else None)

        self.task_shape = tuple(int(value) for value in self.metadata["shape"])
        self.map_shape = tuple(int(value) for value in self.metadata["map_shape"])
        self.index_min = np.asarray(self.metadata["global_index_min"], dtype=np.int64)
        if self.accessible_free.shape != self.task_shape:
            raise ValueError("accessible_free shape does not match metadata")
        if self.static_surface.shape != self.task_shape:
            raise ValueError("static_surface shape does not match metadata")
        if len(self.map_shape) != 3 or any(value <= 0 for value in self.map_shape):
            raise ValueError("invalid full map shape")
        if any(self.index_min[i] < 0 or
               self.index_min[i] + self.task_shape[i] > self.map_shape[i]
               for i in range(3)):
            raise ValueError("task grid is outside the full map")
        if not np.any(self.accessible_free):
            raise ValueError("accessible-free denominator is zero")
        if not np.any(self.static_surface):
            raise ValueError("static-surface denominator is zero")
        self.observability_audited = False
        self.observable_free_fraction = None
        self.observable_surface_fraction = None
        if self.observable_free is not None:
            if (self.observable_free.shape != self.task_shape or
                    self.observable_surface.shape != self.task_shape):
                raise ValueError("observable mask shape does not match metadata")
            if np.any(self.observable_free & ~self.accessible_free):
                raise ValueError("observable-free mask is not a subset of accessible free")
            if np.any(self.observable_surface & ~self.static_surface):
                raise ValueError("observable-surface mask is not a subset of static surface")
            self.observable_free_fraction = (int(self.observable_free.sum()) /
                                             int(self.accessible_free.sum()))
            self.observable_surface_fraction = (int(self.observable_surface.sum()) /
                                                int(self.static_surface.sum()))
            self.observability_audited = (
                np.array_equal(self.observable_free, self.accessible_free) and
                np.array_equal(self.observable_surface, self.static_surface))

        self.accessible_flat = self.accessible_free.ravel(order="C")
        self.surface_flat = self.static_surface.ravel(order="C")
        self.full_seen = np.zeros(int(np.prod(self.map_shape)), dtype=bool)
        self.sequence = 0
        self.full_seen_count = 0
        self.task_seen_count = 0
        self.accessible_seen_count = 0
        self.surface_seen_count = 0
        self.valid = True
        self.errors = []
        self.planning_start_sim = None
        self.threshold_times = {threshold: None for threshold in self.THRESHOLDS}
        self.last_planning_sample = None

    def _invalidate(self, message):
        self.valid = False
        if message not in self.errors:
            self.errors.append(message)

    def invalidate(self, message):
        self._invalidate(str(message))

    def set_planning_start(self, sim_time):
        sim_time = float(sim_time)
        if self.planning_start_sim is not None:
            if abs(self.planning_start_sim - sim_time) > 1e-6:
                self._invalidate("planning start time changed")
            return
        self.planning_start_sim = sim_time
        coverage = self.free_coverage
        self.last_planning_sample = (0.0, coverage)
        for threshold in self.THRESHOLDS:
            if coverage >= threshold:
                self.threshold_times[threshold] = 0.0

    @property
    def free_denominator(self):
        return int(self.accessible_flat.sum())

    @property
    def surface_denominator(self):
        return int(self.surface_flat.sum())

    @property
    def free_coverage(self):
        return self.accessible_seen_count / self.free_denominator

    @property
    def surface_coverage(self):
        return self.surface_seen_count / self.surface_denominator

    def _update_thresholds(self, sim_time, coverage):
        if self.planning_start_sim is None:
            return None
        elapsed = max(0.0, float(sim_time) - self.planning_start_sim)
        previous = self.last_planning_sample
        if previous is not None:
            previous_time, previous_coverage = previous
            if elapsed < previous_time:
                self._invalidate("coverage simulation time moved backwards")
            for threshold in self.THRESHOLDS:
                if self.threshold_times[threshold] is not None or coverage < threshold:
                    continue
                if coverage <= previous_coverage:
                    crossing = elapsed
                else:
                    fraction = (threshold - previous_coverage) / (coverage - previous_coverage)
                    crossing = previous_time + fraction * (elapsed - previous_time)
                self.threshold_times[threshold] = max(0.0, crossing)
        self.last_planning_sample = (elapsed, coverage)
        return elapsed

    def ingest(self, sequence, observed_total, addresses, sim_time, raycast_id=0):
        sequence = int(sequence)
        observed_total = int(observed_total)
        expected = self.sequence + 1
        if sequence != expected:
            self._invalidate("observation sequence gap: expected %d, got %d" %
                             (expected, sequence))
        self.sequence = max(self.sequence, sequence)

        raw = np.asarray(addresses, dtype=np.int64)
        if raw.ndim != 1:
            self._invalidate("observation addresses are not one-dimensional")
            raw = raw.ravel()
        in_range = (raw >= 0) & (raw < self.full_seen.size)
        if not np.all(in_range):
            self._invalidate("observation address outside full map")
            raw = raw[in_range]
        unique = np.unique(raw)
        if unique.size != raw.size:
            self._invalidate("duplicate address inside observation delta")
        new_addresses = unique[~self.full_seen[unique]]
        if new_addresses.size != unique.size:
            self._invalidate("repeated address across observation deltas")
        self.full_seen[new_addresses] = True
        self.full_seen_count += int(new_addresses.size)

        yz = self.map_shape[1] * self.map_shape[2]
        x_index = new_addresses // yz
        remainder = new_addresses % yz
        y_index = remainder // self.map_shape[2]
        z_index = remainder % self.map_shape[2]
        local_x = x_index - self.index_min[0]
        local_y = y_index - self.index_min[1]
        local_z = z_index - self.index_min[2]
        inside = ((local_x >= 0) & (local_x < self.task_shape[0]) &
                  (local_y >= 0) & (local_y < self.task_shape[1]) &
                  (local_z >= 0) & (local_z < self.task_shape[2]))
        task_flat = ((local_x[inside] * self.task_shape[1] + local_y[inside]) *
                     self.task_shape[2] + local_z[inside]).astype(np.int64)
        self.task_seen_count += int(task_flat.size)
        self.accessible_seen_count += int(np.count_nonzero(self.accessible_flat[task_flat]))
        self.surface_seen_count += int(np.count_nonzero(self.surface_flat[task_flat]))

        if self.full_seen_count != observed_total:
            self._invalidate("cumulative observation count mismatch: received %d, reconstructed %d" %
                             (observed_total, self.full_seen_count))
        planning_elapsed = self._update_thresholds(sim_time, self.free_coverage)
        return {
            "sim_time": float(sim_time),
            "planning_elapsed": planning_elapsed,
            "sequence": sequence,
            "raycast_id": int(raycast_id),
            "delta_count": int(raw.size),
            "new_unique_count": int(new_addresses.size),
            "observed_total_full_map": observed_total,
            "reconstructed_total_full_map": self.full_seen_count,
            "observed_task": self.task_seen_count,
            "accessible_observed": self.accessible_seen_count,
            "accessible_denominator": self.free_denominator,
            "free_coverage": self.free_coverage,
            "surface_observed": self.surface_seen_count,
            "surface_denominator": self.surface_denominator,
            "surface_coverage": self.surface_coverage,
            "known_volume_m3": self.task_seen_count * float(self.metadata["voxel_volume_m3"]),
            "valid": self.valid,
            "errors": list(self.errors),
        }

    def summary(self):
        if not self.valid:
            status = "INVALID_PROVENANCE_STREAM"
        elif self.sequence == 0:
            status = "PROVISIONAL_NO_PROVENANCE_MESSAGES"
        elif self.planning_start_sim is None:
            status = "PROVISIONAL_NO_PLANNING_TIME_ORIGIN"
        elif self.observable_free is not None and not self.observability_audited:
            status = "PROVISIONAL_OBSERVABILITY_GAP"
        elif self.observability_audited:
            status = "VALID_ACCESSIBLE_FREE_V2"
        else:
            status = "PROVISIONAL_ACCESSIBLE_FREE_V1"
        thresholds = {}
        for threshold in self.THRESHOLDS:
            value = self.threshold_times[threshold]
            thresholds["T%d" % int(threshold * 100)] = {
                "seconds": value,
                "censored": value is None,
            }
        return {
            "schema_version": ("cerlab-coverage-v2-1"
                               if self.observable_free is not None else
                               "cerlab-coverage-v2-provisional-1"),
            "status": status,
            "valid": self.valid,
            "errors": list(self.errors),
            "sequence": self.sequence,
            "planning_start_sim": self.planning_start_sim,
            "observed_total_full_map": self.full_seen_count,
            "observed_task": self.task_seen_count,
            "accessible_observed": self.accessible_seen_count,
            "accessible_denominator": self.free_denominator,
            "free_coverage": self.free_coverage,
            "surface_observed": self.surface_seen_count,
            "surface_denominator": self.surface_denominator,
            "surface_coverage": self.surface_coverage,
            "known_volume_m3": self.task_seen_count * float(self.metadata["voxel_volume_m3"]),
            "thresholds": thresholds,
            "mask_content_sha256": self.metadata["mask_content_sha256"],
            "observability_audited": self.observability_audited,
            "observable_free_fraction": self.observable_free_fraction,
            "observable_surface_fraction": self.observable_surface_fraction,
            "note": ("Static observability and clean full-run invariants passed; formal performance still requires a same-commit multi-seed experiment."
                     if self.observability_audited else
                     "Provisional until oracle visibility and runtime validation pass."),
        }
