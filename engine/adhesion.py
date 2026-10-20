# ------------------------------------------------------------------
# Copyright (c) 2026 Sleia Engine Development Team.
# This file is distributed under the MIT License. See LICENSE.
#
# Sleia Easy v 1.0.1 - Thermoplastic Python Slicer
#
# File: adhesion.py
# Description: skirt, brim, and raft loops around the first layer.
# ------------------------------------------------------------------

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .slicer_core import Layer, LayerPolygon, Point2D, PrintSettings, SlicedModel

XY = Tuple[float, float]


def _poly_points(polygon: LayerPolygon) -> List[XY]:
    return [(float(p.x), float(p.y)) for p in (polygon.points or [])]


def _bbox(points: Sequence[XY]) -> Tuple[float, float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _rect_loop(bounds: Tuple[float, float, float, float], expand: float) -> List[XY]:
    min_x, min_y, max_x, max_y = bounds
    return [
        (min_x - expand, min_y - expand),
        (max_x + expand, min_y - expand),
        (max_x + expand, max_y + expand),
        (min_x - expand, max_y + expand),
    ]


def _offset_polygon(points: Sequence[XY], distance: float) -> List[XY]:
    if abs(distance) < 1e-9:
        return [(p[0], p[1]) for p in points]
    n = len(points)
    if n < 3:
        return _rect_loop(_bbox(points), abs(distance))
    signed_area = sum(
        points[i][0] * points[(i + 1) % n][1]
        - points[(i + 1) % n][0] * points[i][1]
        for i in range(n)
    ) / 2.0
    outward_sign = -1.0 if signed_area > 0 else 1.0
    effective_distance = distance * outward_sign
    out: List[XY] = []
    for i in range(n):
        prev_p = points[(i - 1) % n]
        cur = points[i]
        nxt = points[(i + 1) % n]
        e1x, e1y = cur[0] - prev_p[0], cur[1] - prev_p[1]
        e2x, e2y = nxt[0] - cur[0], nxt[1] - cur[1]
        l1 = math.hypot(e1x, e1y) or 1.0
        l2 = math.hypot(e2x, e2y) or 1.0
        n1x, n1y = -e1y / l1, e1x / l1
        n2x, n2y = -e2y / l2, e2x / l2
        nx, ny = n1x + n2x, n1y + n2y
        ln = math.hypot(nx, ny)
        if ln < 1e-9:
            nx, ny = n1x, n1y
            ln = math.hypot(nx, ny) or 1.0
        nx, ny = nx / ln, ny / ln
        miter = max(0.25, nx * n1x + ny * n1y)
        out.append(
            (
                cur[0] + nx * effective_distance / miter,
                cur[1] + ny * effective_distance / miter,
            )
        )
    return out


def _closed_loop(points: Sequence[XY]) -> List[XY]:
    if len(points) < 2:
        return list(points)
    a, b = points[0], points[-1]
    if math.hypot(a[0] - b[0], a[1] - b[1]) < 1e-6:
        return list(points)
    return list(points) + [a]


def _outlines(layer: Layer) -> Tuple[List[List[XY]], List[List[XY]]]:
    islands: List[List[XY]] = []
    holes: List[List[XY]] = []
    for poly in layer.polygons or []:
        pts = _poly_points(poly)
        if len(pts) < 3:
            continue
        if poly.is_hole:
            holes.append(pts)
        else:
            islands.append(pts)
    return islands, holes


def _push_loop(paths: List[Dict[str, Any]], kind: str, layer: int, z: float, points: Sequence[XY], extra: Optional[Dict[str, Any]] = None) -> None:
    if len(points) < 3:
        return
    item: Dict[str, Any] = {
        "type": kind,
        "layer": layer,
        "z": z,
        "points": _closed_loop(points),
    }
    if extra:
        item.update(extra)
    paths.append(item)


def _add_hatch(paths: List[Dict[str, Any]], kind: str, layer: int, z: float, bounds: Tuple[float, float, float, float], step: float) -> None:
    if step <= 0:
        return
    min_x, min_y, max_x, max_y = bounds
    flip = False
    y = min_y
    while y <= max_y + 1e-6:
        start = (max_x, y) if flip else (min_x, y)
        end = (min_x, y) if flip else (max_x, y)
        paths.append({"type": kind, "layer": layer, "z": z, "start": start, "end": end})
        flip = not flip
        y += step


def build_adhesion_paths(sliced: SlicedModel, settings: Optional[PrintSettings] = None) -> Tuple[List[Dict[str, Any]], float]:
    settings = settings or sliced.settings
    raw_type = str(getattr(settings, "adhesion_type", "skirt") or "skirt").lower()
    if raw_type == "none" or not sliced.layers:
        return [], 0.0

    first = sliced.layers[0]
    islands, holes = _outlines(first)
    if not islands:
        return [], 0.0

    width = float(getattr(settings, "extrusion_width", 0.45) or 0.45)
    first_z = float(first.z_height)
    layer_h = float(settings.layer_height)
    first_h = float(settings.first_layer_height or first_z or layer_h)
    skirt_speed = float(getattr(settings, "skirt_speed", 50.0) or 50.0)
    paths: List[Dict[str, Any]] = []
    lift_z = 0.0

    def add_skirt() -> None:
        loops = max(0, int(getattr(settings, "skirt_lines", getattr(settings, "skirt_loops", 2)) or 0))
        if loops < 1:
            return
        distance = max(0.0, float(getattr(settings, "skirt_distance", 2.0) or 0.0))
        height = max(1, int(getattr(settings, "skirt_height", 1) or 1))
        for layer_i in range(height):
            src = sliced.layers[min(layer_i, len(sliced.layers) - 1)]
            z = float(src.z_height)
            for outline in islands:
                for i in range(loops):
                    _push_loop(paths, "skirt", layer_i, z, _offset_polygon(outline, distance + i * width), {"speed": skirt_speed})

    def add_brim(extra_gap: float = 0.0) -> None:
        brim_type = str(getattr(settings, "brim_type", "outer-only") or "outer-only").lower().replace("_", "-")
        if brim_type in {"no-brim", "none"}:
            return
        brim_width = max(0.1, float(getattr(settings, "brim_width", 5.0) or 5.0))
        gap = max(0.0, float(getattr(settings, "brim_object_gap", 0.15) or 0.0) + extra_gap)
        loops = max(1, int(round(brim_width / width) or 1))
        do_outer = brim_type not in {"inner", "inner-only"}
        do_inner = brim_type in {"inner-outer", "everywhere", "inner", "inner-only"}
        if do_outer:
            for outline in islands:
                for i in range(loops):
                    _push_loop(paths, "brim", 0, first_z, _offset_polygon(outline, gap + i * width))
        if do_inner:
            for hole in holes:
                for i in range(loops):
                    inner = _offset_polygon(hole, -(gap + i * width))
                    if inner:
                        _push_loop(paths, "brim", 0, first_z, inner)

    def add_draft_shield() -> None:
        distance = max(float(getattr(settings, "skirt_distance", 5.0) or 5.0), 3.0)
        for layer_i, layer in enumerate(sliced.layers):
            z = float(layer.z_height)
            for outline in islands:
                _push_loop(paths, "skirt", layer_i, z, _offset_polygon(outline, distance), {"speed": skirt_speed})

    def add_raft() -> None:
        nonlocal lift_z
        raft_layers = max(1, int(getattr(settings, "raft_layers", 3) or 3))
        expand = max(0.0, float(getattr(settings, "raft_extra_margin", 3.0) or 0.0))
        air_gap = max(0.0, float(getattr(settings, "raft_air_gap", 0.2) or 0.0))
        expanded = [_offset_polygon(o, expand) for o in islands]
        flat = [p for loop in expanded for p in loop]
        raft_box = _bbox(flat)
        z = 0.0
        for layer_i in range(raft_layers):
            z += first_h if layer_i == 0 else layer_h
            if layer_i == 0:
                step = width * 1.2
            elif layer_i == raft_layers - 1:
                step = width * 1.0
            else:
                step = width * 2.0
            for loop in expanded:
                _push_loop(paths, "raft", layer_i, z, loop)
            _add_hatch(paths, "raft", layer_i, z, raft_box, step)
        lift_z = z + air_gap

    if raw_type == "skirt":
        add_skirt()
    elif raw_type == "brim":
        add_brim(0.0)
    elif raw_type == "brim_elephant_foot_compensation":
        add_brim(0.0)
    elif raw_type == "raft":
        add_raft()
    elif raw_type == "brim_draft_shield":
        add_brim(0.0)
        add_draft_shield()
    elif raw_type == "brim_raft":
        add_raft()
        add_brim(0.0)
        if lift_z > 0:
            for item in paths:
                if item.get("type") == "brim":
                    item["z"] = float(item.get("z") or first_z) + lift_z
    else:
        add_skirt()

    return paths, lift_z


def apply_adhesion(sliced: SlicedModel) -> SlicedModel:
    paths, lift_z = build_adhesion_paths(sliced)
    sliced.adhesion_paths = paths
    adhesion = str(getattr(sliced.settings, "adhesion_type", "") or "").lower()
    if adhesion == "brim_elephant_foot_compensation" and sliced.layers:
        shrink = 0.075
        for poly in sliced.layers[0].polygons:
            if poly.is_hole or len(poly.points) < 3:
                continue
            pts = _offset_polygon(_poly_points(poly), -shrink)
            poly.points = [Point2D(x, y) for x, y in pts]
    if lift_z > 0:
        for layer in sliced.layers:
            layer.z_height += lift_z
    return sliced
