"""Deterministic ground-truth masks from primitive SDF collision geometry."""
from collections import deque
from dataclasses import dataclass
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import xml.etree.ElementTree as ET
import zipfile
import zlib

import numpy as np


@dataclass(frozen=True)
class OrientedBox:
    model: str
    link: str
    collision: str
    center: np.ndarray
    rotation: np.ndarray
    size: np.ndarray

    def aabb(self):
        extent = np.abs(self.rotation).dot(self.size / 2.0)
        return self.center - extent, self.center + extent


@dataclass(frozen=True)
class GridSpec:
    map_origin: np.ndarray
    resolution: float
    global_index_min: np.ndarray
    shape: tuple

    def centers(self, axis):
        indices = self.global_index_min[axis] + np.arange(self.shape[axis])
        return self.map_origin[axis] + (indices + 0.5) * self.resolution

    def position_to_local_index(self, position):
        global_index = np.floor(
            (np.asarray(position, dtype=float) - self.map_origin) / self.resolution
        ).astype(int)
        return global_index - self.global_index_min


def _pose_values(element):
    pose = element.find("pose")
    if pose is None or not (pose.text or "").strip():
        return np.zeros(6)
    if pose.get("relative_to"):
        raise ValueError("relative_to SDF poses are not supported by this generator")
    values = np.fromstring(pose.text, sep=" ")
    if values.size != 6:
        raise ValueError("expected six SDF pose values")
    return values


def _pose_matrix(values):
    x, y, z, roll, pitch, yaw = values
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    rx = np.array(((1, 0, 0), (0, cr, -sr), (0, sr, cr)))
    ry = np.array(((cp, 0, sp), (0, 1, 0), (-sp, 0, cp)))
    rz = np.array(((cy, -sy, 0), (sy, cy, 0), (0, 0, 1)))
    transform = np.eye(4)
    transform[:3, :3] = rz.dot(ry).dot(rx)
    transform[:3, 3] = (x, y, z)
    return transform


def parse_static_boxes(world_path, model_names):
    """Parse direct world/model/link/collision box primitives.

    The current CERLAB floorplan worlds do not use SDF frames or nested models.
    Unsupported collision geometry is rejected instead of being silently omitted.
    """
    root = ET.parse(str(world_path)).getroot()
    world = root.find("world")
    if world is None:
        raise ValueError("SDF world element is missing")
    wanted = set(model_names)
    found = set()
    boxes = []
    for model in world.findall("model"):
        model_name = model.get("name", "")
        if model_name not in wanted:
            continue
        found.add(model_name)
        if (model.findtext("static") or "0").strip().lower() not in ("1", "true"):
            raise ValueError("model %s is not static" % model_name)
        model_transform = _pose_matrix(_pose_values(model))
        for link in model.findall("link"):
            link_transform = model_transform.dot(_pose_matrix(_pose_values(link)))
            for collision in link.findall("collision"):
                geometry = collision.find("geometry")
                box = geometry.find("box") if geometry is not None else None
                if box is None:
                    raise ValueError(
                        "unsupported collision geometry: %s/%s/%s" %
                        (model_name, link.get("name", ""), collision.get("name", ""))
                    )
                size = np.fromstring(box.findtext("size", ""), sep=" ")
                if size.size != 3 or np.any(size <= 0):
                    raise ValueError("invalid box size")
                transform = link_transform.dot(_pose_matrix(_pose_values(collision)))
                boxes.append(OrientedBox(
                    model=model_name,
                    link=link.get("name", ""),
                    collision=collision.get("name", ""),
                    center=transform[:3, 3].copy(),
                    rotation=transform[:3, :3].copy(),
                    size=size,
                ))
    missing = wanted - found
    if missing:
        raise ValueError("static model(s) missing: %s" % sorted(missing))
    if not boxes:
        raise ValueError("no box collisions found")
    return boxes


def union_aabb(boxes):
    bounds = [box.aabb() for box in boxes]
    return (np.min(np.vstack([item[0] for item in bounds]), axis=0),
            np.max(np.vstack([item[1] for item in bounds]), axis=0))


def grid_for_bbox(map_origin, map_size, resolution, bbox_min, bbox_max):
    map_origin = np.asarray(map_origin, dtype=float)
    map_size = np.asarray(map_size, dtype=float)
    bbox_min = np.asarray(bbox_min, dtype=float)
    bbox_max = np.asarray(bbox_max, dtype=float)
    if resolution <= 0 or np.any(map_size <= 0) or np.any(bbox_min >= bbox_max):
        raise ValueError("invalid grid or bounding box")
    map_shape = np.ceil(map_size / resolution).astype(int)
    eps = 1e-9
    index_min = np.ceil((bbox_min - map_origin) / resolution - 0.5 - eps).astype(int)
    index_max = (np.floor((bbox_max - map_origin) / resolution - 0.5 + eps)
                 .astype(int) + 1)
    index_min = np.maximum(index_min, 0)
    index_max = np.minimum(index_max, map_shape)
    if np.any(index_min >= index_max):
        raise ValueError("bounding box does not contain voxel centers")
    return GridSpec(map_origin, float(resolution), index_min,
                    tuple((index_max - index_min).tolist()))


def voxelize_boxes(boxes, grid, epsilon=1e-9):
    occupied = np.zeros(grid.shape, dtype=bool)
    axes = [grid.centers(axis) for axis in range(3)]
    for box in boxes:
        lower, upper = box.aabb()
        starts = [np.searchsorted(axes[i], lower[i] - epsilon, side="left")
                  for i in range(3)]
        stops = [np.searchsorted(axes[i], upper[i] + epsilon, side="right")
                 for i in range(3)]
        if any(starts[i] >= stops[i] for i in range(3)):
            continue
        coordinates = np.meshgrid(
            *(axes[i][starts[i]:stops[i]] for i in range(3)), indexing="ij")
        points = np.stack(coordinates, axis=-1)
        local = (points - box.center).dot(box.rotation)
        inside = np.all(np.abs(local) <= box.size / 2.0 + epsilon, axis=-1)
        region = tuple(slice(starts[i], stops[i]) for i in range(3))
        occupied[region] |= inside
    return occupied


def flood_fill(allowed, seed):
    seed = tuple(int(value) for value in seed)
    if len(seed) != allowed.ndim or any(seed[i] < 0 or seed[i] >= allowed.shape[i]
                                       for i in range(allowed.ndim)):
        raise ValueError("flood-fill seed is outside the grid")
    reached = np.zeros_like(allowed, dtype=bool)
    if not allowed[seed]:
        raise ValueError("flood-fill seed is not in allowed space")
    reached[seed] = True
    queue = deque([seed])
    while queue:
        current = queue.popleft()
        for axis in range(allowed.ndim):
            for step in (-1, 1):
                neighbor = list(current)
                neighbor[axis] += step
                neighbor = tuple(neighbor)
                if (0 <= neighbor[axis] < allowed.shape[axis] and
                        allowed[neighbor] and not reached[neighbor]):
                    reached[neighbor] = True
                    queue.append(neighbor)
    return reached


def dilate_box(mask, radii):
    result = mask.astype(bool, copy=True)
    for axis, radius in enumerate(radii):
        source = result
        expanded = np.zeros_like(source)
        for offset in range(-int(radius), int(radius) + 1):
            source_slice = [slice(None)] * source.ndim
            target_slice = [slice(None)] * source.ndim
            if offset < 0:
                source_slice[axis] = slice(-offset, None)
                target_slice[axis] = slice(None, offset)
            elif offset > 0:
                source_slice[axis] = slice(None, -offset)
                target_slice[axis] = slice(offset, None)
            expanded[tuple(target_slice)] |= source[tuple(source_slice)]
        result = expanded
    return result


def adjacent_to(mask):
    adjacent = np.zeros_like(mask, dtype=bool)
    for axis in range(mask.ndim):
        for step in (-1, 1):
            source = [slice(None)] * mask.ndim
            target = [slice(None)] * mask.ndim
            if step < 0:
                source[axis] = slice(1, None)
                target[axis] = slice(None, -1)
            else:
                source[axis] = slice(None, -1)
                target[axis] = slice(1, None)
            adjacent[tuple(target)] |= mask[tuple(source)]
    return adjacent


def _shift_2d(mask, dx, dy):
    """Return values at target+(dx,dy), filling outside the array with false."""
    result = np.zeros_like(mask, dtype=bool)
    nx, ny = mask.shape
    if ((dx >= 0 and dx >= nx) or (dx < 0 and -dx >= nx) or
            (dy >= 0 and dy >= ny) or (dy < 0 and -dy >= ny)):
        return result
    target_x = slice(0, nx-dx) if dx >= 0 else slice(-dx, nx)
    source_x = slice(dx, nx) if dx >= 0 else slice(0, nx+dx)
    target_y = slice(0, ny-dy) if dy >= 0 else slice(-dy, ny)
    source_y = slice(dy, ny) if dy >= 0 else slice(0, ny+dy)
    result[target_x, target_y] = mask[source_x, source_y]
    return result


def _bresenham_offsets(end_x, end_y):
    """Integer cells after the origin on a 2-D Bresenham ray."""
    x = y = 0
    dx, dy = abs(int(end_x)), abs(int(end_y))
    sx = 1 if end_x > 0 else -1 if end_x < 0 else 0
    sy = 1 if end_y > 0 else -1 if end_y < 0 else 0
    error = dx - dy
    result = []
    while x != end_x or y != end_y:
        twice = 2 * error
        if twice > -dy:
            error -= dy
            x += sx
        if twice < dx:
            error += dx
            y += sy
        result.append((x, y))
    return result


def _validate_visibility_config(config):
    required = ("body_to_camera", "depth_intrinsics", "image_cols", "image_rows",
                "depth_filter_margin", "depth_skip_pixel", "raycast_max_length",
                "azimuth_samples", "convergence_samples")
    visibility = config.get("visibility_oracle", {})
    missing = [name for name in required if name not in visibility]
    if missing:
        raise ValueError("visibility oracle field(s) missing: %s" % missing)
    transform = np.asarray(visibility["body_to_camera"], dtype=float).reshape((4, 4))
    expected_rotation = np.array(((0.0, 0.0, 1.0),
                                  (-1.0, 0.0, 0.0),
                                  (0.0, -1.0, 0.0)))
    if not np.allclose(transform[:3, :3], expected_rotation, atol=1e-9):
        raise ValueError("visibility oracle currently requires the level CERLAB camera rotation")
    if abs(transform[1, 3]) > 1e-9:
        raise ValueError("visibility oracle currently requires zero lateral camera offset")
    samples = int(visibility["azimuth_samples"])
    convergence = [int(value) for value in visibility["convergence_samples"]]
    if samples <= 0 or not convergence or convergence[-1] != samples:
        raise ValueError("invalid visibility convergence samples")
    if any(value <= 0 or samples % value or
           (i and value <= convergence[i-1]) for i, value in enumerate(convergence)):
        raise ValueError("visibility convergence samples must be increasing divisors")
    intrinsics = np.asarray(visibility["depth_intrinsics"], dtype=float)
    if intrinsics.size != 4 or np.any(intrinsics[:2] <= 0):
        raise ValueError("invalid visibility camera intrinsics")
    if int(visibility["image_cols"]) <= 2 * int(visibility["depth_filter_margin"]):
        raise ValueError("invalid visibility image columns")
    if int(visibility["depth_skip_pixel"]) <= 0:
        raise ValueError("invalid visibility pixel stride")
    return visibility, transform, intrinsics, convergence


def oracle_visibility_masks(task_shape, flight_reachable, static_occupied,
                            grid, config):
    """Conservative visibility union from every flight voxel and nested yaw samples."""
    visibility, transform, intrinsics, convergence = _validate_visibility_config(config)
    final_samples = convergence[-1]
    resolution = float(grid.resolution)
    forward_offset = float(transform[0, 3])
    camera_height = float(transform[2, 3])
    _fx, fy, _cx, cy = intrinsics
    image_rows = int(visibility["image_rows"])
    margin = int(visibility["depth_filter_margin"])
    pixel_stride = int(visibility["depth_skip_pixel"])
    max_range = float(visibility["raycast_max_length"])
    if image_rows <= 2 * margin or max_range <= 0 or forward_offset < 0:
        raise ValueError("invalid visibility image bounds or range")
    if task_shape[2] > 31:
        raise ValueError("visibility bit mask supports at most 31 z cells")

    occupied_xy = np.any(static_occupied, axis=2)
    if not np.array_equal(static_occupied,
                          np.broadcast_to(occupied_xy[:, :, None], static_occupied.shape)):
        raise ValueError("visibility oracle currently requires vertically extruded occupancy")
    target_z = grid.centers(2)
    body_z = grid.centers(2)
    radius_cells = int(math.ceil((max_range + forward_offset) / resolution))
    endpoint_by_direction = []
    seen_endpoints = set()
    for index in range(final_samples):
        angle = 2.0 * math.pi * index / final_samples
        endpoint = (int(round(radius_cells * math.cos(angle))),
                    int(round(radius_cells * math.sin(angle))))
        if endpoint == (0, 0) or endpoint in seen_endpoints:
            continue
        seen_endpoints.add(endpoint)
        endpoint_by_direction.append((index, endpoint))

    visible_bits = np.zeros(task_shape[:2], dtype=np.uint32)
    snapshots = {}
    processed = set()
    for sample_count in convergence:
        step = final_samples // sample_count
        direction_indices = {index for index in range(0, final_samples, step)} - processed
        processed.update(direction_indices)
        for index, endpoint in endpoint_by_direction:
            if index not in direction_indices:
                continue
            blocked = np.zeros(task_shape[:2], dtype=bool)
            for dx, dy in _bresenham_offsets(*endpoint):
                body_distance = math.hypot(dx, dy) * resolution
                optical_depth = body_distance - forward_offset
                if optical_depth > 0:
                    for body_z_index in range(flight_reachable.shape[2]):
                        source = (_shift_2d(flight_reachable[:, :, body_z_index], dx, dy) &
                                  ~blocked)
                        if not np.any(source):
                            continue
                        delta_z = target_z - (body_z[body_z_index] + camera_height)
                        pixel_v = cy - fy * delta_z / optical_depth
                        last_pixel_v = margin + ((image_rows-margin-1-margin) //
                                                  pixel_stride) * pixel_stride
                        nearest_pixel_v = np.clip(
                            margin + np.rint((pixel_v-margin) / pixel_stride) * pixel_stride,
                            margin, last_pixel_v)
                        ray_delta_z = (cy-nearest_pixel_v) * optical_depth / fy
                        valid_z = ((np.abs(ray_delta_z-delta_z) <= resolution/2.0 + 1e-9) &
                                   (np.hypot(optical_depth, delta_z) <= max_range + 1e-9))
                        if np.any(valid_z):
                            bit_value = np.uint32(sum(1 << int(z) for z in np.flatnonzero(valid_z)))
                            visible_bits[source] |= bit_value
                blocked |= _shift_2d(occupied_xy, dx, dy)
        mask = np.zeros(task_shape, dtype=bool)
        for z_index in range(task_shape[2]):
            mask[:, :, z_index] = (visible_bits & np.uint32(1 << z_index)) != 0
        snapshots[sample_count] = mask
    return snapshots


def canonical_mask_sha256(arrays):
    digest = hashlib.sha256()
    for name in sorted(arrays):
        array = np.ascontiguousarray(arrays[name])
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(array.dtype.str.encode("ascii") + b"\0")
        digest.update(json.dumps(array.shape).encode("ascii") + b"\0")
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def write_deterministic_npz(path, arrays):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with zipfile.ZipFile(str(temporary), "w") as archive:
        for name in sorted(arrays):
            stream = io.BytesIO()
            np.lib.format.write_array(stream, np.ascontiguousarray(arrays[name]),
                                      allow_pickle=False)
            info = zipfile.ZipInfo(name + ".npy", (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, stream.getvalue())
    temporary.replace(path)


def _png_chunk(kind, data):
    return (struct.pack(">I", len(data)) + kind + data +
            struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff))


def write_rgb_png(path, image, scale=1):
    image = np.asarray(image, dtype=np.uint8)
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("RGB image must have shape (height, width, 3)")
    if scale > 1:
        image = np.repeat(np.repeat(image, scale, axis=0), scale, axis=1)
    height, width, _ = image.shape
    raw = b"".join(b"\x00" + image[row].tobytes() for row in range(height))
    payload = (b"\x89PNG\r\n\x1a\n" +
               _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) +
               _png_chunk(b"IDAT", zlib.compress(raw, 9)) +
               _png_chunk(b"IEND", b""))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_masks(world_path, config):
    boxes = parse_static_boxes(world_path, config["static_models"])
    boundary_links = set(config["boundary_links"])
    boundary_boxes = [box for box in boxes if box.link in boundary_links]
    if len(boundary_boxes) != len(boundary_links):
        found = {box.link for box in boundary_boxes}
        raise ValueError("boundary link(s) missing: %s" % sorted(boundary_links - found))
    boundary_min, boundary_max = union_aabb(boundary_boxes)
    if "task_z" in config:
        boundary_min[2], boundary_max[2] = config["task_z"]
    grid = grid_for_bbox(config["map_origin"], config["map_size"],
                         config["resolution"], boundary_min, boundary_max)
    occupied = voxelize_boxes(boxes, grid)
    home_index = grid.position_to_local_index(config["home_position"])
    accessible_free = flood_fill(~occupied, home_index)
    static_surface = occupied & adjacent_to(accessible_free)

    robot_size = np.asarray(config["robot_size"], dtype=float)
    inflation_cells = np.ceil(robot_size / (2.0 * grid.resolution)).astype(int)
    inflated_occupied = dilate_box(occupied, inflation_cells)
    z_centers = grid.centers(2)
    flight_min, flight_max = config["flight_z"]
    flight_altitude = ((z_centers >= flight_min - 1e-9) &
                       (z_centers <= flight_max + 1e-9))
    flight_allowed = (~inflated_occupied & accessible_free &
                      flight_altitude.reshape((1, 1, -1)))
    flight_reachable = flood_fill(flight_allowed, home_index)
    unreachable_free = (~occupied) & (~accessible_free)

    arrays = {
        "accessible_free": accessible_free,
        "flight_reachable": flight_reachable,
        "inflated_occupied": inflated_occupied,
        "static_occupied": occupied,
        "static_surface": static_surface,
        "unreachable_free": unreachable_free,
    }
    visibility_metadata = None
    if "visibility_oracle" in config:
        convergence_masks = oracle_visibility_masks(
            accessible_free.shape, flight_reachable, occupied, grid, config)
        sample_counts = sorted(convergence_masks)
        observable_free = convergence_masks[sample_counts[-1]] & accessible_free
        unobservable_accessible = accessible_free & ~observable_free
        observable_static_surface = convergence_masks[sample_counts[-1]] & static_surface
        unobservable_static_surface = static_surface & ~observable_static_surface
        arrays["observable_free"] = observable_free
        arrays["observable_static_surface"] = observable_static_surface
        arrays["unobservable_accessible"] = unobservable_accessible
        arrays["unobservable_static_surface"] = unobservable_static_surface
        visibility_metadata = {
            "algorithm": "nested_discrete_yaw_voxel_occlusion_v1",
            "conservative_lower_bound": True,
            "level_body_pose": True,
            "dynamic_obstacles_excluded": True,
            "azimuth_samples": sample_counts[-1],
            "convergence_counts": {
                str(samples): int((convergence_masks[samples] & accessible_free).sum())
                for samples in sample_counts
            },
            "convergence_additions": {
                str(sample_counts[i]): int(
                    (convergence_masks[sample_counts[i]] & accessible_free).sum() -
                    ((convergence_masks[sample_counts[i-1]] & accessible_free).sum()
                                            if i else 0))
                for i in range(len(sample_counts))
            },
            "config": config["visibility_oracle"],
        }
    voxel_volume = grid.resolution ** 3
    task_voxel_count = int(np.prod(grid.shape))
    accessible_voxel_count = int(accessible_free.sum())
    map_shape = np.ceil(np.asarray(config["map_size"], dtype=float) /
                        grid.resolution).astype(int)
    metadata = {
        "schema_version": ("cerlab-ground-truth-mask-v2" if visibility_metadata
                           else "cerlab-ground-truth-mask-v1"),
        "map_frame": config.get("map_frame", "map"),
        "map_origin": grid.map_origin.tolist(),
        "map_size": list(config["map_size"]),
        "map_shape": map_shape.tolist(),
        "resolution": grid.resolution,
        "global_index_min": grid.global_index_min.tolist(),
        "global_index_max_exclusive": (grid.global_index_min +
                                       np.asarray(grid.shape)).tolist(),
        "shape": list(grid.shape),
        "task_bbox_collision_aabb_min": boundary_min.tolist(),
        "task_bbox_collision_aabb_max": boundary_max.tolist(),
        "home_position": list(config["home_position"]),
        "home_local_index": home_index.tolist(),
        "robot_size": robot_size.tolist(),
        "inflation_cells": inflation_cells.tolist(),
        "flight_z": list(config["flight_z"]),
        "static_models": list(config["static_models"]),
        "boundary_links": list(config["boundary_links"]),
        "box_count": len(boxes),
        "voxel_volume_m3": voxel_volume,
        "task_voxel_count": task_voxel_count,
        "task_volume_m3": task_voxel_count * voxel_volume,
        "accessible_fraction_of_task": accessible_voxel_count / task_voxel_count,
        "counts": {name: int(mask.sum()) for name, mask in arrays.items()},
        "volumes_m3": {name: float(mask.sum() * voxel_volume)
                       for name, mask in arrays.items()},
        "accessible_free_touches_xy_boundary": int(
            accessible_free[0, :, :].sum() + accessible_free[-1, :, :].sum() +
            accessible_free[:, 0, :].sum() + accessible_free[:, -1, :].sum()),
        "mask_content_sha256": canonical_mask_sha256(arrays),
        "boxes": [{
            "model": box.model,
            "link": box.link,
            "collision": box.collision,
            "center": box.center.tolist(),
            "size": box.size.tolist(),
            "rotation": box.rotation.tolist(),
        } for box in boxes],
    }
    if visibility_metadata is not None:
        metadata["visibility_oracle"] = visibility_metadata
        metadata["observable_fraction_of_accessible"] = (
            int(arrays["observable_free"].sum()) / accessible_voxel_count)
        metadata["observable_fraction_of_static_surface"] = (
            int(arrays["observable_static_surface"].sum()) / int(static_surface.sum()))
    return arrays, metadata, grid


def topdown_image(arrays, grid, home_position):
    occupied = arrays["static_occupied"].any(axis=2)
    accessible = arrays["accessible_free"].any(axis=2)
    unreachable = arrays["unreachable_free"].any(axis=2)
    flight = arrays["flight_reachable"].any(axis=2)
    image = np.full(occupied.shape + (3,), 220, dtype=np.uint8)
    image[unreachable] = (150, 150, 150)
    image[accessible] = (245, 245, 245)
    if "unobservable_accessible" in arrays:
        image[arrays["unobservable_accessible"].any(axis=2)] = (235, 165, 65)
    image[occupied] = (20, 20, 20)
    image[flight] = (80, 190, 110)
    home = grid.position_to_local_index(home_position)
    if 0 <= home[0] < image.shape[0] and 0 <= home[1] < image.shape[1]:
        image[max(0, home[0]-1):home[0]+2, max(0, home[1]-1):home[1]+2] = (30, 80, 230)
    return np.flipud(np.transpose(image, (1, 0, 2)))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)
