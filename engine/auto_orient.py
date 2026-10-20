# ------------------------------------------------------------------
# Copyright (c) 2026 Sleia Engine Development Team.
# This file is distributed under the MIT License. See LICENSE.
#
# Sleia Easy v 1.0.1 - Thermoplastic Python Slicer
#
# File: auto_orient.py
# Description: flips the part to a stable face and drops it on the bed.
# ------------------------------------------------------------------

from __future__ import annotations

import logging
from typing import List, Tuple

import numpy as np

from .mesh_processor import Mesh, MeshProcessor
from .slicer_core import Point3D

logger = logging.getLogger(__name__)

_FACE_ROTATIONS: List[Tuple[float, float, float]] = [
    (0.0, 0.0, 0.0),
    (180.0, 0.0, 0.0),
    (90.0, 0.0, 0.0),
    (-90.0, 0.0, 0.0),
    (0.0, 90.0, 0.0),
    (0.0, -90.0, 0.0),
]


def auto_orient_and_place(
    mesh: Mesh,
    bed_size: Tuple[float, float] = (220.0, 220.0),
    print_center: Tuple[float, float] = (110.0, 110.0),
) -> Mesh:
    best_mesh = mesh
    best_score = None

    for rotation in _FACE_ROTATIONS:
        candidate = MeshProcessor.transform_mesh(mesh, rotation=rotation)
        score = _orientation_score(candidate)
        if best_score is None or score > best_score:
            best_score = score
            best_mesh = candidate

    logger.info("Auto-orient selected contact score %.1f", best_score or 0.0)
    return place_on_baseplate(best_mesh, bed_size, print_center)


def place_on_baseplate(
    mesh: Mesh,
    bed_size: Tuple[float, float] = (220.0, 220.0),
    print_center: Tuple[float, float] = None,
) -> Mesh:
    if print_center is None:
        print_center = (bed_size[0] / 2.0, bed_size[1] / 2.0)
    mesh.calculate_bounds()
    min_b, max_b = mesh.bounds
    cx = (min_b.x + max_b.x) / 2.0
    cy = (min_b.y + max_b.y) / 2.0
    translation = Point3D(
        print_center[0] - cx,
        print_center[1] - cy,
        -min_b.z,
    )
    placed = MeshProcessor.transform_mesh(mesh, translation=translation)
    logger.info(
        "Placed on baseplate %sx%s mm at (%.1f, %.1f), z=0",
        bed_size[0],
        bed_size[1],
        print_center[0],
        print_center[1],
    )
    return placed


def _orientation_score(mesh: Mesh) -> float:
    vertices = np.asarray(mesh.vertices, dtype=float)
    faces = np.asarray(mesh.faces, dtype=int)
    if len(vertices) == 0 or len(faces) == 0:
        return 0.0

    min_z = float(np.min(vertices[:, 2]))
    max_z = float(np.max(vertices[:, 2]))
    height = max(max_z - min_z, 1e-6)
    contact_tol = 0.4
    contact_area = 0.0

    for face in faces:
        pts = vertices[face]
        if float(np.max(pts[:, 2])) > min_z + contact_tol:
            continue
        v0, v1, v2 = pts
        normal = np.cross(v1 - v0, v2 - v0)
        area = 0.5 * float(np.linalg.norm(normal))
        if area > 0:
            contact_area += area

    return contact_area * 10.0 - height
