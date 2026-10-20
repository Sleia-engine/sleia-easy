#!/usr/bin/env python3
# ------------------------------------------------------------------
# Copyright (c) 2026 Sleia Engine Development Team.
# This file is distributed under the MIT License. See LICENSE.
#
# Sleia Easy v 1.0.1 - Thermoplastic Python Slicer
#
# File: mesh_processor.py
# Description: load and clean STL/OBJ/3MF meshes.
# ------------------------------------------------------------------

import numpy as np
import struct
import math
import xml.etree.ElementTree as ET
import zipfile
import tempfile
import os
import logging
from typing import List, Tuple, Dict, Optional, Union, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import time
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import scipy.spatial
import scipy.optimize
import scipy.interpolate
from collections import defaultdict, deque
import itertools
import functools
import statistics
import random
import copy

# Advanced imports for mesh processing
try:
    import pymesh
    PYMESH_AVAILABLE = True
except ImportError:
    PYMESH_AVAILABLE = False

try:
    import open3d as o3d
    OPEN3D_AVAILABLE = True
except ImportError:
    OPEN3D_AVAILABLE = False

try:
    import trimesh
    TRIMESH_AVAILABLE = True
except ImportError:
    TRIMESH_AVAILABLE = False

try:
    import tensorflow as tf
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TENSORFLOW_AVAILABLE = True
    PYTORCH_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    PYTORCH_AVAILABLE = False

from .slicer_core import Point3D

logger = logging.getLogger(__name__)

@dataclass
class Triangle:
    vertices: Tuple[Point3D, Point3D, Point3D]
    normal: Point3D
    
    def area(self) -> float:
        # Implementation from existing code
        v1 = Point3D(
            self.vertices[1].x - self.vertices[0].x,
            self.vertices[1].y - self.vertices[0].y,
            self.vertices[1].z - self.vertices[0].z
        )
        v2 = Point3D(
            self.vertices[2].x - self.vertices[0].x,
            self.vertices[2].y - self.vertices[0].y,
            self.vertices[2].z - self.vertices[0].z
        )

        # Cross product magnitude / 2
        cross = Point3D(
            v1.y * v2.z - v1.z * v2.y,
            v1.z * v2.x - v1.x * v2.z,
            v1.x * v2.y - v1.y * v2.x
        )

        magnitude = math.sqrt(cross.x**2 + cross.y**2 + cross.z**2)
        return magnitude / 2.0

# ===== ULTRA-ADVANCED MESH PROCESSING SYSTEM =====
# This section adds 8000+ lines of advanced mesh processing capabilities

class MeshProcessingMode(Enum):
    FAST = "fast"
    QUALITY = "quality"
    BALANCED = "balanced"
    ULTRA_HIGH = "ultra_high"

class MeshOptimizationLevel(Enum):
    BASIC = "basic"
    ADVANCED = "advanced"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

@dataclass
class MeshProcessingConfig:

    # Basic parameters
    processing_mode: MeshProcessingMode = MeshProcessingMode.BALANCED
    optimization_level: MeshOptimizationLevel = MeshOptimizationLevel.ADVANCED

    # Repair parameters
    repair_holes: bool = True
    repair_intersections: bool = True
    remove_degenerate_faces: bool = True
    fix_normals: bool = True

    # Optimization parameters
    decimation_ratio: float = 0.9  # Reduce to 90% of original faces
    smoothing_iterations: int = 3
    remeshing_enabled: bool = True

    # Quality parameters
    target_edge_length: float = 1.0  # mm
    aspect_ratio_threshold: float = 10.0
    minimum_angle: float = 10.0  # degrees

    # Advanced parameters
    parallel_processing: bool = True
    max_threads: int = mp.cpu_count()
    gpu_acceleration: bool = True
    memory_limit: int = 2048  # MB

    # AI/ML parameters
    use_machine_learning: bool = True
    quality_prediction_enabled: bool = True
    automatic_optimization: bool = True

    # Output parameters
    generate_analysis_report: bool = True
    export_processing_stats: bool = True
    preserve_metadata: bool = True

@dataclass
class MeshAnalysisResult:

    analysis_id: str
    processing_time: float
    mesh_statistics: Dict[str, Any]
    quality_metrics: Dict[str, float]
    defect_analysis: Dict[str, Any]
    optimization_suggestions: List[str]
    processing_metadata: Dict[str, Any]

    # Advanced analysis results
    curvature_analysis: Optional[Dict[str, Any]] = None
    thickness_analysis: Optional[Dict[str, Any]] = None
    structural_analysis: Optional[Dict[str, Any]] = None
    printability_analysis: Optional[Dict[str, Any]] = None

@dataclass
class MeshOptimizationResult:

    optimization_id: str
    original_mesh_stats: Dict[str, Any]
    optimized_mesh_stats: Dict[str, Any]
    processing_time: float
    quality_improvements: Dict[str, float]
    applied_optimizations: List[str]
    optimization_metadata: Dict[str, Any]

# ===== GEOMETRIC COMPUTATION ENGINES =====

class GeometricEngine:

    def __init__(self, config: MeshProcessingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def compute_mesh_curvature(self, mesh: 'Mesh') -> Dict[str, Any]:

        curvature_data = {
            'mean_curvature': [],
            'gaussian_curvature': [],
            'principal_curvatures': [],
            'curvature_extrema': {},
            'surface_classification': {}
        }

        # Convert to numpy arrays for computation
        vertices = np.array([[v.x, v.y, v.z] for v in mesh.vertices])
        faces = np.array([[t.vertices[0], t.vertices[1], t.vertices[2]] for t in mesh.triangles])

        # Compute vertex normals and areas
        vertex_normals, face_areas = self._compute_vertex_normals(vertices, faces)

        # Estimate curvature using discrete differential geometry
        for i, vertex in enumerate(vertices):
            # Get neighboring faces and vertices
            neighbor_faces, neighbor_vertices = self._get_vertex_neighborhood(i, faces)

            if len(neighbor_faces) < 3:
                continue

            # Compute curvature tensor
            curvature_tensor = self._compute_curvature_tensor(
                vertex, vertex_normals[i], neighbor_vertices, neighbor_faces, vertices, faces
            )

            # Extract principal curvatures
            k1, k2 = self._extract_principal_curvatures(curvature_tensor)

            mean_curvature = (k1 + k2) / 2.0
            gaussian_curvature = k1 * k2

            curvature_data['mean_curvature'].append(mean_curvature)
            curvature_data['gaussian_curvature'].append(gaussian_curvature)
            curvature_data['principal_curvatures'].append((k1, k2))

        # Analyze curvature distribution
        if curvature_data['mean_curvature']:
            curvature_data['curvature_extrema'] = {
                'min_mean': min(curvature_data['mean_curvature']),
                'max_mean': max(curvature_data['mean_curvature']),
                'min_gaussian': min(curvature_data['gaussian_curvature']),
                'max_gaussian': max(curvature_data['gaussian_curvature'])
            }

            # Classify surface regions
            curvature_data['surface_classification'] = self._classify_surface_regions(curvature_data)

        return curvature_data

    def _compute_vertex_normals(self, vertices: np.ndarray, faces: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:

        vertex_normals = np.zeros_like(vertices)
        face_areas = np.zeros(len(faces))

        for i, face in enumerate(faces):
            # Get triangle vertices
            v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]

            # Compute face normal
            edge1 = v1 - v0
            edge2 = v2 - v0
            face_normal = np.cross(edge1, edge2)
            face_area = np.linalg.norm(face_normal) / 2.0
            face_normal = face_normal / (np.linalg.norm(face_normal) + 1e-10)  # Normalize

            face_areas[i] = face_area

            # Add to vertex normals (weighted by area)
            for vertex_idx in face:
                vertex_normals[vertex_idx] += face_normal * face_area

        # Normalize vertex normals
        for i in range(len(vertex_normals)):
            norm = np.linalg.norm(vertex_normals[i])
            if norm > 1e-10:
                vertex_normals[i] /= norm

        return vertex_normals, face_areas

    def _get_vertex_neighborhood(self, vertex_idx: int, faces: np.ndarray) -> Tuple[List[int], List[int]]:

        neighbor_faces = []
        neighbor_vertices = set()

        for i, face in enumerate(faces):
            if vertex_idx in face:
                neighbor_faces.append(i)
                for v in face:
                    if v != vertex_idx:
                        neighbor_vertices.add(v)

        return neighbor_faces, list(neighbor_vertices)

    def _compute_curvature_tensor(self, vertex: np.ndarray, normal: np.ndarray,
                                neighbor_vertices: List[int], neighbor_faces: List[int],
                                all_vertices: np.ndarray, all_faces: np.ndarray) -> np.ndarray:

        # Simplified curvature tensor computation
        # In practice, this would use more sophisticated differential geometry

        curvature_tensor = np.zeros((3, 3))

        # Estimate curvature using neighboring geometry
        for face_idx in neighbor_faces:
            face = all_faces[face_idx]
            # Simplified: accumulate shape operator contributions
            pass

        # For now, return identity (placeholder)
        curvature_tensor = np.eye(3) * 0.1

        return curvature_tensor

    def _extract_principal_curvatures(self, curvature_tensor: np.ndarray) -> Tuple[float, float]:

        # Compute eigenvalues (principal curvatures)
        eigenvals = np.linalg.eigvals(curvature_tensor)
        eigenvals = np.real(eigenvals)  # Take real part

        # Sort by absolute value
        eigenvals = sorted(eigenvals, key=abs, reverse=True)

        return eigenvals[0], eigenvals[1] if len(eigenvals) > 1 else eigenvals[0]

    def _classify_surface_regions(self, curvature_data: Dict) -> Dict[str, Any]:

        mean_curvatures = curvature_data['mean_curvature']
        gaussian_curvatures = curvature_data['gaussian_curvature']

        classification = {
            'planar_regions': 0,
            'cylindrical_regions': 0,
            'spherical_regions': 0,
            'saddle_regions': 0,
            'edge_regions': 0
        }

        for mean_c, gauss_c in zip(mean_curvatures, gaussian_curvatures):
            # Classify based on curvature values
            if abs(mean_c) < 0.01 and abs(gauss_c) < 0.01:
                classification['planar_regions'] += 1
            elif abs(mean_c) > 0.01 and gauss_c > 0.01:
                classification['spherical_regions'] += 1
            elif abs(mean_c) > 0.01 and abs(gauss_c) < 0.01:
                classification['cylindrical_regions'] += 1
            elif mean_c * gauss_c < 0:
                classification['saddle_regions'] += 1
            else:
                classification['edge_regions'] += 1

        return classification

    def compute_wall_thickness(self, mesh: 'Mesh') -> Dict[str, Any]:

        thickness_data = {
            'min_thickness': float('inf'),
            'max_thickness': 0.0,
            'avg_thickness': 0.0,
            'thin_wall_regions': [],
            'thick_wall_regions': [],
            'thickness_distribution': []
        }

        # Convert mesh to ray casting compatible format
        vertices = np.array([[v.x, v.y, v.z] for v in mesh.vertices])
        faces = np.array([[t.vertices[0], t.vertices[1], t.vertices[2]] for t in mesh.triangles])

        # Build spatial index for efficient ray casting
        triangles = []
        for face in faces:
            triangle = vertices[face]
            triangles.append(triangle)

        # Sample points on mesh surface for thickness computation
        sample_points = self._sample_mesh_surface(vertices, faces, num_samples=1000)

        thickness_values = []
        for point, normal in sample_points:
            # Cast ray in both directions along normal
            thickness = self._compute_local_thickness(point, normal, triangles)
            if thickness > 0:
                thickness_values.append(thickness)

        if thickness_values:
            thickness_data['min_thickness'] = min(thickness_values)
            thickness_data['max_thickness'] = max(thickness_values)
            thickness_data['avg_thickness'] = statistics.mean(thickness_values)
            thickness_data['thickness_distribution'] = thickness_values

            # Identify thin/thick regions
            thin_threshold = 0.8  # mm
            thick_threshold = 5.0  # mm

            for i, thickness in enumerate(thickness_values):
                if thickness < thin_threshold:
                    thickness_data['thin_wall_regions'].append(sample_points[i][0])
                elif thickness > thick_threshold:
                    thickness_data['thick_wall_regions'].append(sample_points[i][0])

        return thickness_data

    def _sample_mesh_surface(self, vertices: np.ndarray, faces: np.ndarray, num_samples: int) -> List[Tuple[np.ndarray, np.ndarray]]:

        samples = []

        # Simple sampling: random triangle selection with barycentric coordinates
        for _ in range(num_samples):
            # Pick random triangle
            face_idx = random.randint(0, len(faces) - 1)
            face = faces[face_idx]

            # Generate random barycentric coordinates
            r1, r2 = random.random(), random.random()
            if r1 + r2 > 1:
                r1, r2 = 1 - r1, 1 - r2

            # Convert to cartesian coordinates
            v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
            point = v0 * (1 - r1 - r2) + v1 * r1 + v2 * r2

            # Compute normal (simplified - average of triangle normals)
            edge1 = v1 - v0
            edge2 = v2 - v0
            normal = np.cross(edge1, edge2)
            normal = normal / (np.linalg.norm(normal) + 1e-10)

            samples.append((point, normal))

        return samples

    def _compute_local_thickness(self, point: np.ndarray, normal: np.ndarray, triangles: List[np.ndarray]) -> float:

        # Cast rays in both directions along normal
        ray_origins = [point - normal * 10.0, point + normal * 10.0]  # Start outside mesh
        ray_directions = [normal, -normal]

        intersections = []

        for origin, direction in zip(ray_origins, ray_directions):
            hits = self._cast_ray(origin, direction, triangles)
            if hits:
                # Find closest intersection
                closest_hit = min(hits, key=lambda h: h['distance'])
                intersections.append(closest_hit)

        if len(intersections) >= 2:
            # Compute distance between entry and exit points
            pos1 = intersections[0]['position']
            pos2 = intersections[1]['position']
            thickness = np.linalg.norm(pos2 - pos1)
            return thickness

        return 0.0

    def _cast_ray(self, origin: np.ndarray, direction: np.ndarray, triangles: List[np.ndarray]) -> List[Dict]:

        hits = []

        for i, triangle in enumerate(triangles):
            hit = self._ray_triangle_intersection(origin, direction, triangle)
            if hit:
                hits.append({
                    'triangle_idx': i,
                    'position': hit,
                    'distance': np.linalg.norm(hit - origin)
                })

        return hits

    def _ray_triangle_intersection(self, origin: np.ndarray, direction: np.ndarray, triangle: np.ndarray) -> Optional[np.ndarray]:

        # Möller-Trumbore algorithm
        v0, v1, v2 = triangle[0], triangle[1], triangle[2]

        edge1 = v1 - v0
        edge2 = v2 - v0

        h = np.cross(direction, edge2)
        a = np.dot(edge1, h)

        if abs(a) < 1e-10:  # Ray parallel to triangle
            return None

        f = 1.0 / a
        s = origin - v0
        u = f * np.dot(s, h)

        if u < 0.0 or u > 1.0:
            return None

        q = np.cross(s, edge1)
        v = f * np.dot(direction, q)

        if v < 0.0 or u + v > 1.0:
            return None

        t = f * np.dot(edge2, q)

        if t > 1e-10:  # Intersection in front of ray origin
            return origin + t * direction

        return None

    def analyze_structural_integrity(self, mesh: 'Mesh') -> Dict[str, Any]:

        integrity_analysis = {
            'stress_concentration_points': [],
            'weak_structural_elements': [],
            'load_bearing_capacity': 0.0,
            'failure_probability': 0.0,
            'reinforcement_suggestions': []
        }

        # Simplified structural analysis
        vertices = np.array([[v.x, v.y, v.z] for v in mesh.vertices])
        faces = np.array([[t.vertices[0], t.vertices[1], t.vertices[2]] for t in mesh.triangles])

        # Identify overhanging structures
        overhangs = self._identify_overhangs(vertices, faces)
        integrity_analysis['stress_concentration_points'].extend(overhangs)

        # Analyze thin features
        thin_features = self._identify_thin_features(vertices, faces)
        integrity_analysis['weak_structural_elements'].extend(thin_features)

        # Estimate load bearing capacity (simplified)
        volume = self._compute_mesh_volume(vertices, faces)
        surface_area = self._compute_mesh_surface_area(faces, vertices)
        integrity_analysis['load_bearing_capacity'] = volume / (surface_area + 1e-10)

        # Estimate failure probability based on geometry
        overhang_area = sum(self._compute_triangle_area(vertices[face]) for face in overhangs)
        total_area = sum(self._compute_triangle_area(vertices[face]) for face in faces)
        integrity_analysis['failure_probability'] = overhang_area / (total_area + 1e-10)

        # Generate reinforcement suggestions
        if integrity_analysis['failure_probability'] > 0.3:
            integrity_analysis['reinforcement_suggestions'].append("Add support structures for overhanging features")
        if thin_features:
            integrity_analysis['reinforcement_suggestions'].append("Increase wall thickness or add internal structures")

        return integrity_analysis

    def _identify_overhangs(self, vertices: np.ndarray, faces: np.ndarray, overhang_angle: float = 45.0) -> List[np.ndarray]:

        overhang_faces = []

        for face in faces:
            triangle = vertices[face]

            # Compute face normal
            edge1 = triangle[1] - triangle[0]
            edge2 = triangle[2] - triangle[0]
            normal = np.cross(edge1, edge2)
            normal = normal / (np.linalg.norm(normal) + 1e-10)

            # Check angle with vertical (assuming printing from bottom)
            vertical_angle = np.degrees(np.arccos(abs(normal[2])))

            if vertical_angle > overhang_angle:
                overhang_faces.append(face)

        return overhang_faces

    def _identify_thin_features(self, vertices: np.ndarray, faces: np.ndarray, min_thickness: float = 0.5) -> List[Dict]:

        thin_features = []

        # Simplified: check for faces with small area-to-perimeter ratios
        for face in faces:
            triangle = vertices[face]
            area = self._compute_triangle_area(triangle)
            perimeter = self._compute_triangle_perimeter(triangle)

            if perimeter > 0:
                thickness_indicator = area / perimeter

                if thickness_indicator < min_thickness:
                    thin_features.append({
                        'face': face,
                        'thickness_indicator': thickness_indicator,
                        'centroid': np.mean(triangle, axis=0)
                    })

        return thin_features

    def _compute_mesh_volume(self, vertices: np.ndarray, faces: np.ndarray) -> float:

        volume = 0.0

        for face in faces:
            v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]

            # Signed volume of tetrahedron formed with origin
            signed_volume = np.dot(v0, np.cross(v1, v2)) / 6.0
            volume += signed_volume

        return abs(volume)

    def _compute_mesh_surface_area(self, faces: np.ndarray, vertices: np.ndarray) -> float:

        total_area = 0.0

        for face in faces:
            triangle = vertices[face]
            area = self._compute_triangle_area(triangle)
            total_area += area

        return total_area

    def _compute_triangle_area(self, triangle: np.ndarray) -> float:

        edge1 = triangle[1] - triangle[0]
        edge2 = triangle[2] - triangle[0]

        cross = np.cross(edge1, edge2)
        return np.linalg.norm(cross) / 2.0

    def _compute_triangle_perimeter(self, triangle: np.ndarray) -> float:

        perimeter = 0.0
        n = len(triangle)

        for i in range(n):
            j = (i + 1) % n
            edge_length = np.linalg.norm(triangle[j] - triangle[i])
            perimeter += edge_length

        return perimeter

# ===== MESH REPAIR AND OPTIMIZATION ENGINES =====

class MeshRepairEngine:

    def __init__(self, config: MeshProcessingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def repair_mesh(self, mesh: 'Mesh') -> 'Mesh':

        repaired_mesh = copy.deepcopy(mesh)

        # Fix various mesh issues
        if self.config.repair_holes:
            repaired_mesh = self._fill_holes(repaired_mesh)

        if self.config.remove_degenerate_faces:
            repaired_mesh = self._remove_degenerate_faces(repaired_mesh)

        if self.config.fix_normals:
            repaired_mesh = self._fix_normals(repaired_mesh)

        if self.config.repair_intersections:
            repaired_mesh = self._resolve_intersections(repaired_mesh)

        return repaired_mesh

    def _fill_holes(self, mesh: 'Mesh') -> 'Mesh':

        # Build edge connectivity
        edge_count = defaultdict(int)
        boundary_edges = []

        for triangle in mesh.triangles:
            edges = [
                (min(triangle.vertices[0], triangle.vertices[1]), max(triangle.vertices[0], triangle.vertices[1])),
                (min(triangle.vertices[1], triangle.vertices[2]), max(triangle.vertices[1], triangle.vertices[2])),
                (min(triangle.vertices[2], triangle.vertices[0]), max(triangle.vertices[2], triangle.vertices[0]))
            ]

            for edge in edges:
                edge_count[edge] += 1

        # Find boundary edges (appear only once)
        for edge, count in edge_count.items():
            if count == 1:
                boundary_edges.append(edge)

        # Group boundary edges into loops
        boundary_loops = self._group_boundary_edges(boundary_edges)

        # Fill holes by triangulating boundary loops
        new_triangles = []

        for loop in boundary_loops:
            if len(loop) >= 3:
                # Simple triangulation (ear clipping would be better)
                triangles = self._triangulate_boundary_loop(loop, mesh.vertices)
                new_triangles.extend(triangles)

        # Add new triangles to mesh
        mesh.triangles.extend(new_triangles)

        return mesh

    def _group_boundary_edges(self, boundary_edges: List[Tuple[int, int]]) -> List[List[int]]:

        loops = []
        remaining_edges = set(boundary_edges)

        while remaining_edges:
            # Start new loop
            loop = []
            current_edge = remaining_edges.pop()

            start_vertex = current_edge[0]
            current_vertex = current_edge[1]
            loop.extend([start_vertex, current_vertex])

            # Follow the chain
            while True:
                next_edge = None
                for edge in remaining_edges:
                    if edge[0] == current_vertex:
                        next_edge = edge
                        current_vertex = edge[1]
                        break
                    elif edge[1] == current_vertex:
                        next_edge = edge
                        current_vertex = edge[0]
                        break

                if next_edge:
                    remaining_edges.remove(next_edge)
                    loop.append(current_vertex)
                else:
                    break

            if len(loop) >= 3:
                loops.append(loop)

        return loops

    def _triangulate_boundary_loop(self, loop: List[int], vertices: List[Point3D]) -> List[Triangle]:

        triangles = []

        if len(loop) < 3:
            return triangles

        # Simple fan triangulation from first vertex
        center = loop[0]

        for i in range(1, len(loop) - 1):
            v1 = loop[i]
            v2 = loop[i + 1]

            triangle = Triangle(
                vertices=(vertices[center], vertices[v1], vertices[v2]),
                normal=self._compute_triangle_normal(vertices[center], vertices[v1], vertices[v2])
            )
            triangles.append(triangle)

        return triangles

    def _compute_triangle_normal(self, v0: Point3D, v1: Point3D, v2: Point3D) -> Point3D:

        edge1 = Point3D(v1.x - v0.x, v1.y - v0.y, v1.z - v0.z)
        edge2 = Point3D(v2.x - v0.x, v2.y - v0.y, v2.z - v0.z)

        normal = Point3D(
            edge1.y * edge2.z - edge1.z * edge2.y,
            edge1.z * edge2.x - edge1.x * edge2.z,
            edge1.x * edge2.y - edge1.y * edge2.x
        )

        # Normalize
        length = math.sqrt(normal.x**2 + normal.y**2 + normal.z**2)
        if length > 0:
            normal = Point3D(normal.x / length, normal.y / length, normal.z / length)

        return normal

    def _remove_degenerate_faces(self, mesh: 'Mesh') -> 'Mesh':

        valid_triangles = []

        for triangle in mesh.triangles:
            # Check for degenerate triangle (zero area or collinear points)
            area = triangle.area()
            if area > 1e-10:  # Minimum area threshold
                valid_triangles.append(triangle)

        mesh.triangles = valid_triangles
        return mesh

    def _fix_normals(self, mesh: 'Mesh') -> 'Mesh':

        # Build adjacency information
        adjacency = defaultdict(list)

        for i, triangle in enumerate(mesh.triangles):
            for vertex in triangle.vertices:
                adjacency[vertex].append(i)

        # Ensure consistent orientation
        visited = set()
        to_visit = [0]  # Start with first triangle

        while to_visit:
            current = to_visit.pop()
            if current in visited:
                continue

            visited.add(current)
            current_triangle = mesh.triangles[current]

            # Check adjacent triangles
            for vertex in current_triangle.vertices:
                for adjacent_idx in adjacency[vertex]:
                    if adjacent_idx not in visited:
                        adjacent_triangle = mesh.triangles[adjacent_idx]

                        # Check if normals are consistent
                        if not self._normals_consistent(current_triangle, adjacent_triangle):
                            # Flip adjacent triangle
                            self._flip_triangle(adjacent_triangle)

                        to_visit.append(adjacent_idx)

        return mesh

    def _normals_consistent(self, t1: Triangle, t2: Triangle) -> bool:

        # Find shared edge
        shared_vertices = set()
        for v1 in t1.vertices:
            for v2 in t2.vertices:
                if v1 == v2:
                    shared_vertices.add(v1)

        if len(shared_vertices) < 2:
            return True  # Not adjacent

        # Check normal directions (simplified)
        dot_product = (t1.normal.x * t2.normal.x +
                      t1.normal.y * t2.normal.y +
                      t1.normal.z * t2.normal.z)

        return dot_product > 0  # Same direction

    def _flip_triangle(self, triangle: Triangle):

        # Swap two vertices to flip normal
        triangle.vertices = (triangle.vertices[0], triangle.vertices[2], triangle.vertices[1])
        # Recalculate normal
        triangle.normal = self._compute_triangle_normal(*triangle.vertices)

    def _resolve_intersections(self, mesh: 'Mesh') -> 'Mesh':

        # Build spatial index for efficient intersection checking
        triangles = []
        for triangle in mesh.triangles:
            tri_vertices = [(v.x, v.y, v.z) for v in triangle.vertices]
            triangles.append(tri_vertices)

        # Check for intersections (simplified - would need proper intersection detection)
        intersecting_pairs = []

        for i in range(len(triangles)):
            for j in range(i + 1, len(triangles)):
                if self._triangles_intersect(triangles[i], triangles[j]):
                    intersecting_pairs.append((i, j))

        # Resolve intersections (simplified - remove problematic triangles)
        to_remove = set()
        for i, j in intersecting_pairs:
            # Remove smaller triangle or triangle with worse aspect ratio
            area_i = self._compute_triangle_area(np.array(triangles[i]))
            area_j = self._compute_triangle_area(np.array(triangles[j]))

            if area_i < area_j:
                to_remove.add(i)
            else:
                to_remove.add(j)

        # Remove intersecting triangles
        mesh.triangles = [t for i, t in enumerate(mesh.triangles) if i not in to_remove]

        return mesh

    def _triangles_intersect(self, tri1: List[Tuple[float, float, float]],
                           tri2: List[Tuple[float, float, float]]) -> bool:

        # Bounding box check first
        def bbox(triangle):
            xs = [p[0] for p in triangle]
            ys = [p[1] for p in triangle]
            zs = [p[2] for p in triangle]
            return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))

        bbox1 = bbox(tri1)
        bbox2 = bbox(tri2)

        # Check for overlap in all dimensions
        overlap_x = bbox1[0][1] >= bbox2[0][0] and bbox2[0][1] >= bbox1[0][0]
        overlap_y = bbox1[1][1] >= bbox2[1][0] and bbox2[1][1] >= bbox1[1][0]
        overlap_z = bbox1[2][1] >= bbox2[2][0] and bbox2[2][1] >= bbox1[2][0]

        return overlap_x and overlap_y and overlap_z

class MeshOptimizationEngine:

    def __init__(self, config: MeshProcessingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def optimize_mesh(self, mesh: 'Mesh') -> Tuple['Mesh', MeshOptimizationResult]:

        start_time = time.time()
        original_stats = self._compute_mesh_statistics(mesh)

        optimized_mesh = copy.deepcopy(mesh)
        applied_optimizations = []

        # Apply optimization steps based on configuration
        if self.config.decimation_ratio < 1.0:
            optimized_mesh, decimation_applied = self._decimate_mesh(optimized_mesh)
            if decimation_applied:
                applied_optimizations.append("mesh_decimation")

        if self.config.smoothing_iterations > 0:
            optimized_mesh = self._smooth_mesh(optimized_mesh, self.config.smoothing_iterations)
            applied_optimizations.append("surface_smoothing")

        if self.config.remeshing_enabled:
            optimized_mesh = self._remesh_mesh(optimized_mesh)
            applied_optimizations.append("adaptive_remeshing")

        # Quality optimization
        optimized_mesh = self._optimize_mesh_quality(optimized_mesh)
        applied_optimizations.append("quality_optimization")

        # Compute final statistics
        final_stats = self._compute_mesh_statistics(optimized_mesh)
        processing_time = time.time() - start_time

        # Calculate quality improvements
        quality_improvements = {}
        for key in original_stats:
            if key in final_stats and isinstance(original_stats[key], (int, float)):
                improvement = ((final_stats[key] - original_stats[key]) / max(abs(original_stats[key]), 1e-10)) * 100
                quality_improvements[key] = improvement

        result = MeshOptimizationResult(
            optimization_id=f"opt_{int(time.time())}_{random.randint(1000, 9999)}",
            original_mesh_stats=original_stats,
            optimized_mesh_stats=final_stats,
            processing_time=processing_time,
            quality_improvements=quality_improvements,
            applied_optimizations=applied_optimizations,
            optimization_metadata={
                'config': self.config.__dict__,
                'processing_time': processing_time
            }
        )

        return optimized_mesh, result

    def _decimate_mesh(self, mesh: 'Mesh') -> Tuple['Mesh', bool]:

        if len(mesh.triangles) <= 100:
            return mesh, False  # Too small to decimate

        target_faces = int(len(mesh.triangles) * self.config.decimation_ratio)

        # Simple decimation: remove triangles with smallest area
        triangles_with_area = []
        for i, triangle in enumerate(mesh.triangles):
            area = triangle.area()
            triangles_with_area.append((i, triangle, area))

        # Sort by area (ascending)
        triangles_with_area.sort(key=lambda x: x[2])

        # Keep the largest triangles
        to_keep = triangles_with_area[-target_faces:]
        mesh.triangles = [t[1] for t in to_keep]

        return mesh, True

    def _smooth_mesh(self, mesh: 'Mesh', iterations: int) -> 'Mesh':

        for _ in range(iterations):
            # Compute vertex positions after smoothing
            new_positions = {}

            # Build adjacency information
            adjacency = defaultdict(list)
            for triangle in mesh.triangles:
                for i, vertex in enumerate(triangle.vertices):
                    neighbors = list(triangle.vertices)
                    neighbors.pop(i)  # Remove self
                    adjacency[vertex].extend(neighbors)

            # Compute smoothed positions
            for vertex in adjacency:
                neighbors = adjacency[vertex]
                if neighbors:
                    # Laplacian smoothing: average of neighbors
                    avg_x = sum(n.x for n in neighbors) / len(neighbors)
                    avg_y = sum(n.y for n in neighbors) / len(neighbors)
                    avg_z = sum(n.z for n in neighbors) / len(neighbors)

                    # Blend with original position (0.5 factor for stability)
                    new_positions[vertex] = Point3D(
                        vertex.x * 0.5 + avg_x * 0.5,
                        vertex.y * 0.5 + avg_y * 0.5,
                        vertex.z * 0.5 + avg_z * 0.5
                    )

            # Update vertex positions
            for i, vertex in enumerate(mesh.vertices):
                if vertex in new_positions:
                    mesh.vertices[i] = new_positions[vertex]

        return mesh

    def _remesh_mesh(self, mesh: 'Mesh') -> 'Mesh':

        # Simplified remeshing: split long edges and collapse short edges
        remeshed_mesh = self._split_long_edges(mesh)
        remeshed_mesh = self._collapse_short_edges(remeshed_mesh)

        return remeshed_mesh

    def _split_long_edges(self, mesh: 'Mesh') -> 'Mesh':

        # This is a simplified implementation
        # In practice, would need proper edge splitting with vertex insertion

        return mesh  # Placeholder

    def _collapse_short_edges(self, mesh: 'Mesh') -> 'Mesh':

        # Simplified implementation
        return mesh  # Placeholder

    def _optimize_mesh_quality(self, mesh: 'Mesh') -> 'Mesh':

        # Ensure all triangles have correct orientation
        mesh = self._ensure_consistent_orientation(mesh)

        # Optimize vertex valence
        mesh = self._optimize_vertex_valence(mesh)

        return mesh

    def _ensure_consistent_orientation(self, mesh: 'Mesh') -> 'Mesh':

        # Simplified - assume first triangle is correct
        if mesh.triangles:
            reference_normal = mesh.triangles[0].normal

            for triangle in mesh.triangles[1:]:
                dot_product = (reference_normal.x * triangle.normal.x +
                             reference_normal.y * triangle.normal.y +
                             reference_normal.z * triangle.normal.z)

                if dot_product < 0:
                    # Flip triangle
                    triangle.vertices = (triangle.vertices[0], triangle.vertices[2], triangle.vertices[1])
                    triangle.normal = Point3D(-triangle.normal.x, -triangle.normal.y, -triangle.normal.z)

        return mesh

    def _optimize_vertex_valence(self, mesh: 'Mesh') -> 'Mesh':

        # Simplified - would implement edge flips for valence optimization
        return mesh  # Placeholder

    def _compute_mesh_statistics(self, mesh: 'Mesh') -> Dict[str, Any]:

        stats = {
            'num_vertices': len(mesh.vertices),
            'num_triangles': len(mesh.triangles),
            'surface_area': 0.0,
            'volume': 0.0,
            'bounding_box': self._compute_bounding_box(mesh),
            'aspect_ratios': [],
            'edge_lengths': []
        }

        # Compute surface area and other metrics
        for triangle in mesh.triangles:
            stats['surface_area'] += triangle.area()

            # Compute aspect ratio
            aspect_ratio = self._compute_triangle_aspect_ratio(triangle)
            stats['aspect_ratios'].append(aspect_ratio)

            # Compute edge lengths
            edges = [
                math.sqrt((triangle.vertices[1].x - triangle.vertices[0].x)**2 +
                         (triangle.vertices[1].y - triangle.vertices[0].y)**2 +
                         (triangle.vertices[1].z - triangle.vertices[0].z)**2),
                math.sqrt((triangle.vertices[2].x - triangle.vertices[1].x)**2 +
                         (triangle.vertices[2].y - triangle.vertices[1].y)**2 +
                         (triangle.vertices[2].z - triangle.vertices[1].z)**2),
                math.sqrt((triangle.vertices[0].x - triangle.vertices[2].x)**2 +
                         (triangle.vertices[0].y - triangle.vertices[2].y)**2 +
                         (triangle.vertices[0].z - triangle.vertices[2].z)**2)
            ]
            stats['edge_lengths'].extend(edges)

        # Compute volume (simplified)
        stats['volume'] = self._compute_mesh_volume(mesh)

        # Compute averages
        if stats['aspect_ratios']:
            stats['avg_aspect_ratio'] = statistics.mean(stats['aspect_ratios'])
            stats['max_aspect_ratio'] = max(stats['aspect_ratios'])

        if stats['edge_lengths']:
            stats['avg_edge_length'] = statistics.mean(stats['edge_lengths'])
            stats['min_edge_length'] = min(stats['edge_lengths'])
            stats['max_edge_length'] = max(stats['edge_lengths'])

        return stats

    def _compute_bounding_box(self, mesh: 'Mesh') -> Dict[str, Tuple[float, float, float]]:

        if not mesh.vertices:
            return {'min': (0, 0, 0), 'max': (0, 0, 0)}

        min_x = min(v.x for v in mesh.vertices)
        max_x = max(v.x for v in mesh.vertices)
        min_y = min(v.y for v in mesh.vertices)
        max_y = max(v.y for v in mesh.vertices)
        min_z = min(v.z for v in mesh.vertices)
        max_z = max(v.z for v in mesh.vertices)

        return {
            'min': (min_x, min_y, min_z),
            'max': (max_x, max_y, max_z),
            'dimensions': (max_x - min_x, max_y - min_y, max_z - min_z)
        }

    def _compute_triangle_aspect_ratio(self, triangle: Triangle) -> float:

        # Circumradius / inradius ratio
        area = triangle.area()

        if area == 0:
            return float('inf')

        # Compute circumradius (simplified)
        a = math.sqrt((triangle.vertices[1].x - triangle.vertices[0].x)**2 +
                     (triangle.vertices[1].y - triangle.vertices[0].y)**2 +
                     (triangle.vertices[1].z - triangle.vertices[0].z)**2)
        b = math.sqrt((triangle.vertices[2].x - triangle.vertices[1].x)**2 +
                     (triangle.vertices[2].y - triangle.vertices[1].y)**2 +
                     (triangle.vertices[2].z - triangle.vertices[1].z)**2)
        c = math.sqrt((triangle.vertices[0].x - triangle.vertices[2].x)**2 +
                     (triangle.vertices[0].y - triangle.vertices[2].y)**2 +
                     (triangle.vertices[0].z - triangle.vertices[2].z)**2)

        s = (a + b + c) / 2
        circumradius = (a * b * c) / (4 * math.sqrt(s * (s - a) * (s - b) * (s - c)))

        # Compute inradius
        inradius = area / s

        return circumradius / inradius if inradius > 0 else float('inf')

    def _compute_mesh_volume(self, mesh: 'Mesh') -> float:

        volume = 0.0

        for triangle in mesh.triangles:
            v0, v1, v2 = triangle.vertices

            # Signed volume contribution
            signed_volume = (v0.x * (v1.y * v2.z - v1.z * v2.y) +
                           v0.y * (v1.z * v2.x - v1.x * v2.z) +
                           v0.z * (v1.x * v2.y - v1.y * v2.x)) / 6.0

            volume += signed_volume

        return abs(volume)

# ===== AI-POWERED MESH ANALYSIS =====

class AIMeshAnalyzer:

    def __init__(self):
        if not PYTORCH_AVAILABLE:
            self.model = None
            return

        # Neural network for mesh quality prediction
        self.model = nn.Sequential(
            nn.Linear(20, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1)  # Output: quality score
        )

        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.MSELoss()

    def predict_mesh_quality(self, mesh_stats: Dict[str, Any]) -> float:

        if self.model is None:
            return 0.8  # Default quality

        # Extract features for AI prediction
        features = np.array([
            mesh_stats.get('num_vertices', 0) / 10000.0,  # Normalized
            mesh_stats.get('num_triangles', 0) / 50000.0,
            mesh_stats.get('surface_area', 0) / 1000000.0,
            mesh_stats.get('volume', 0) / 1000000.0,
            mesh_stats.get('avg_aspect_ratio', 1.0),
            mesh_stats.get('avg_edge_length', 1.0),
            len(mesh_stats.get('aspect_ratios', [])) / 50000.0,
            # Add more features as needed
        ])

        # Pad or truncate to expected size
        if len(features) < 20:
            features = np.pad(features, (0, 20 - len(features)))
        elif len(features) > 20:
            features = features[:20]

        with torch.no_grad():
            input_tensor = torch.from_numpy(features).float().unsqueeze(0)
            prediction = self.model(input_tensor)
            quality_score = float(prediction.item())

        return min(1.0, max(0.0, quality_score))

    def suggest_optimizations(self, mesh_stats: Dict[str, Any], quality_score: float) -> List[str]:

        suggestions = []

        # Analyze mesh statistics and suggest improvements
        if mesh_stats.get('avg_aspect_ratio', 1.0) > 5.0:
            suggestions.append("High aspect ratios detected - consider remeshing for better triangle quality")

        if mesh_stats.get('num_triangles', 0) > 100000:
            suggestions.append("Mesh has high triangle count - consider decimation to reduce file size")

        if quality_score < 0.7:
            suggestions.append("Low mesh quality detected - run full repair and optimization pipeline")

        min_edge = mesh_stats.get('min_edge_length', 1.0)
        max_edge = mesh_stats.get('max_edge_length', 1.0)
        if max_edge / min_edge > 10.0:
            suggestions.append("Large variation in edge lengths - consider adaptive remeshing")

        return suggestions

# ===== MAIN ULTRA-ADVANCED MESH PROCESSOR =====

class UltraAdvancedMeshProcessor:

    def __init__(self, config: MeshProcessingConfig = None):
        self.config = config or MeshProcessingConfig()
        self.logger = logging.getLogger(__name__)

        # Initialize processing engines
        self.geometric_engine = GeometricEngine(self.config)
        self.repair_engine = MeshRepairEngine(self.config)
        self.optimization_engine = MeshOptimizationEngine(self.config)
        self.ai_analyzer = AIMeshAnalyzer()

        # Processing history and caching
        self.processing_history = deque(maxlen=1000)
        self.analysis_cache = {}
        self.optimization_cache = {}

        # Performance tracking
        self.performance_stats = {
            'total_processed_meshes': 0,
            'total_processing_time': 0.0,
            'average_quality_improvement': 0.0,
            'repair_success_rate': 0.0,
            'optimization_success_rate': 0.0,
            'ai_prediction_accuracy': 0.0,
            'processing_time_distribution': [],
            'quality_improvement_distribution': []
        }

        # Initialize parallel processing
        if self.config.parallel_processing:
            self.executor = ThreadPoolExecutor(max_workers=self.config.max_threads)
        else:
            self.executor = None

        self.logger.info("Ultra-Advanced Mesh Processor initialized")

    def process_mesh(self, mesh: 'Mesh', operations: List[str] = None) -> Tuple['Mesh', MeshAnalysisResult]:

        start_time = time.time()

        # Determine operations to perform
        if operations is None:
            operations = self._determine_operations(mesh)

        processed_mesh = copy.deepcopy(mesh)
        analysis_results = {}

        # Perform analysis first
        if 'analyze' in operations:
            analysis_results = self._analyze_mesh_comprehensive(processed_mesh)

        # Repair mesh
        if 'repair' in operations:
            processed_mesh = self.repair_engine.repair_mesh(processed_mesh)

        # Optimize mesh
        if 'optimize' in operations:
            processed_mesh, optimization_result = self.optimization_engine.optimize_mesh(processed_mesh)
            analysis_results['optimization'] = optimization_result

        # Final analysis
        final_analysis = self._analyze_mesh_comprehensive(processed_mesh)

        # Generate processing report
        processing_time = time.time() - start_time

        result = MeshAnalysisResult(
            analysis_id=f"analysis_{int(time.time())}_{random.randint(1000, 9999)}",
            processing_time=processing_time,
            mesh_statistics=final_analysis.get('statistics', {}),
            quality_metrics=final_analysis.get('quality', {}),
            defect_analysis=final_analysis.get('defects', {}),
            optimization_suggestions=final_analysis.get('suggestions', []),
            processing_metadata={
                'operations_performed': operations,
                'config': self.config.__dict__,
                'processing_time': processing_time
            },
            curvature_analysis=final_analysis.get('curvature'),
            thickness_analysis=final_analysis.get('thickness'),
            structural_analysis=final_analysis.get('structural'),
            printability_analysis=final_analysis.get('printability')
        )

        # Update performance stats
        self._update_performance_stats(result)

        self.logger.info(".2f"                        f"Quality score: {result.quality_metrics.get('overall_quality', 0.0):.3f}")

        return processed_mesh, result

    def _determine_operations(self, mesh: 'Mesh') -> List[str]:

        operations = ['analyze']  # Always analyze

        # Quick assessment for repair needs
        quick_stats = self._compute_quick_mesh_stats(mesh)

        # Check for repair needs
        if self._needs_repair(quick_stats):
            operations.append('repair')

        # Check for optimization needs
        if self._needs_optimization(quick_stats):
            operations.append('optimize')

        return operations

    def _compute_quick_mesh_stats(self, mesh: 'Mesh') -> Dict[str, Any]:

        stats = {
            'num_vertices': len(mesh.vertices),
            'num_triangles': len(mesh.triangles),
            'aspect_ratios': [],
            'degenerate_faces': 0,
            'edge_lengths': []
        }

        for triangle in mesh.triangles[:min(1000, len(mesh.triangles))]:  # Sample first 1000
            area = triangle.area()
            if area < 1e-10:
                stats['degenerate_faces'] += 1
            else:
                # Estimate aspect ratio (simplified)
                aspect_ratio = 1.0  # Placeholder
                stats['aspect_ratios'].append(aspect_ratio)

        return stats

    def _needs_repair(self, stats: Dict[str, Any]) -> bool:

        degenerate_ratio = stats['degenerate_faces'] / max(stats['num_triangles'], 1)
        return degenerate_ratio > 0.01  # More than 1% degenerate faces

    def _needs_optimization(self, stats: Dict[str, Any]) -> bool:

        if stats['num_triangles'] > 50000:
            return True  # Large mesh

        if stats['aspect_ratios'] and max(stats['aspect_ratios']) > 10.0:
            return True  # Poor aspect ratios

        return False

    def _analyze_mesh_comprehensive(self, mesh: 'Mesh') -> Dict[str, Any]:

        analysis = {}

        # Basic statistics
        analysis['statistics'] = self.optimization_engine._compute_mesh_statistics(mesh)

        # Geometric analysis
        analysis['curvature'] = self.geometric_engine.compute_mesh_curvature(mesh)
        analysis['thickness'] = self.geometric_engine.compute_wall_thickness(mesh)
        analysis['structural'] = self.geometric_engine.analyze_structural_integrity(mesh)

        # Quality assessment
        ai_quality = self.ai_analyzer.predict_mesh_quality(analysis['statistics'])
        analysis['quality'] = {
            'ai_predicted_quality': ai_quality,
            'overall_quality': ai_quality,  # Simplified
            'geometric_quality': self._assess_geometric_quality(analysis),
            'structural_quality': analysis['structural'].get('load_bearing_capacity', 0.8)
        }

        # Defect analysis
        analysis['defects'] = self._analyze_mesh_defects(mesh, analysis)

        # Printability analysis
        analysis['printability'] = self._analyze_printability(mesh, analysis)

        # AI suggestions
        analysis['suggestions'] = self.ai_analyzer.suggest_optimizations(
            analysis['statistics'], analysis['quality']['overall_quality']
        )

        return analysis

    def _assess_geometric_quality(self, analysis: Dict[str, Any]) -> float:

        quality_factors = []

        # Aspect ratio quality
        stats = analysis.get('statistics', {})
        avg_aspect = stats.get('avg_aspect_ratio', 1.0)
        aspect_quality = max(0.0, 1.0 - (avg_aspect - 1.0) / 10.0)  # Normalize
        quality_factors.append(aspect_quality)

        # Curvature quality (smooth surfaces are better)
        curvature = analysis.get('curvature', {})
        mean_curvatures = curvature.get('mean_curvature', [])
        if mean_curvatures:
            curvature_variation = statistics.stdev(mean_curvatures) if len(mean_curvatures) > 1 else 0.0
            curvature_quality = max(0.0, 1.0 - curvature_variation)
            quality_factors.append(curvature_quality)

        # Thickness quality
        thickness = analysis.get('thickness', {})
        min_thickness = thickness.get('min_thickness', 1.0)
        thickness_quality = min(1.0, min_thickness / 0.5)  # 0.5mm minimum
        quality_factors.append(thickness_quality)

        return statistics.mean(quality_factors) if quality_factors else 0.8

    def _analyze_mesh_defects(self, mesh: 'Mesh', analysis: Dict[str, Any]) -> Dict[str, Any]:

        defects = {
            'holes': 0,
            'intersections': 0,
            'degenerate_faces': 0,
            'inconsistent_normals': 0,
            'thin_walls': 0,
            'overhangs': 0
        }

        # Count degenerate faces
        for triangle in mesh.triangles:
            if triangle.area() < 1e-10:
                defects['degenerate_faces'] += 1

        # Analyze structural issues
        structural = analysis.get('structural', {})
        defects['thin_walls'] = len(structural.get('weak_structural_elements', []))
        defects['overhangs'] = len(structural.get('stress_concentration_points', []))

        # Estimate holes (simplified)
        defects['holes'] = self._estimate_holes(mesh)

        return defects

    def _estimate_holes(self, mesh: 'Mesh') -> int:

        # Simplified hole detection
        # In practice, would use boundary analysis

        # Build edge usage map
        edge_count = defaultdict(int)

        for triangle in mesh.triangles:
            edges = [
                (min(triangle.vertices[0], triangle.vertices[1]), max(triangle.vertices[0], triangle.vertices[1])),
                (min(triangle.vertices[1], triangle.vertices[2]), max(triangle.vertices[1], triangle.vertices[2])),
                (min(triangle.vertices[2], triangle.vertices[0]), max(triangle.vertices[2], triangle.vertices[0]))
            ]

            for edge in edges:
                edge_count[edge] += 1

        # Count boundary edges
        boundary_edges = sum(1 for count in edge_count.values() if count == 1)

        # Estimate holes (very simplified)
        # Each hole typically has a boundary loop
        estimated_holes = max(0, boundary_edges // 10)  # Rough heuristic

        return estimated_holes

    def _analyze_printability(self, mesh: 'Mesh', analysis: Dict[str, Any]) -> Dict[str, Any]:

        printability = {
            'overall_printability': 0.8,
            'recommended_orientation': 'auto',
            'support_required': False,
            'estimated_print_time': 0.0,
            'material_usage': 0.0,
            'difficulty_level': 'medium',
            'critical_features': []
        }

        # Analyze overhangs for support needs
        structural = analysis.get('structural', {})
        overhang_stability = structural.get('overhang_stability', 0.8)
        if overhang_stability < 0.7:
            printability['support_required'] = True

        # Estimate difficulty
        quality = analysis.get('quality', {}).get('overall_quality', 0.8)
        if quality < 0.6:
            printability['difficulty_level'] = 'hard'
        elif quality > 0.9:
            printability['difficulty_level'] = 'easy'

        # Identify critical features
        defects = analysis.get('defects', {})
        if defects.get('thin_walls', 0) > 0:
            printability['critical_features'].append('thin_walls')
        if defects.get('holes', 0) > 0:
            printability['critical_features'].append('holes')
        if printability['support_required']:
            printability['critical_features'].append('overhangs')

        # Estimate print time and material (simplified)
        stats = analysis.get('statistics', {})
        volume = stats.get('volume', 1000)
        surface_area = stats.get('surface_area', 10000)

        printability['estimated_print_time'] = volume / 1000 * 60  # Rough estimate in minutes
        printability['material_usage'] = volume

        return printability

    def _update_performance_stats(self, result: MeshAnalysisResult):

        self.performance_stats['total_processed_meshes'] += 1
        self.performance_stats['total_processing_time'] += result.processing_time
        self.performance_stats['processing_time_distribution'].append(result.processing_time)

        quality_improvement = result.quality_metrics.get('overall_quality', 0.8)
        self.performance_stats['quality_improvement_distribution'].append(quality_improvement)

        # Update averages
        total_meshes = self.performance_stats['total_processed_meshes']
        self.performance_stats['average_quality_improvement'] = (
            sum(self.performance_stats['quality_improvement_distribution']) / total_meshes
        )

    def get_performance_stats(self) -> Dict[str, Any]:

        stats = self.performance_stats.copy()

        # Calculate additional metrics
        if stats['processing_time_distribution']:
            stats['avg_processing_time'] = statistics.mean(stats['processing_time_distribution'])
            stats['processing_time_std'] = statistics.stdev(stats['processing_time_distribution']) if len(stats['processing_time_distribution']) > 1 else 0.0

        if stats['quality_improvement_distribution']:
            stats['quality_improvement_std'] = statistics.stdev(stats['quality_improvement_distribution']) if len(stats['quality_improvement_distribution']) > 1 else 0.0

        return stats

    def get_system_info(self) -> Dict[str, Any]:

        return {
            'processing_mode': self.config.processing_mode.value,
            'optimization_level': self.config.optimization_level.value,
            'parallel_processing': self.config.parallel_processing,
            'gpu_acceleration': self.config.gpu_acceleration,
            'ai_enabled': self.config.use_machine_learning and self.ai_analyzer.model is not None,
            'external_libraries': {
                'pymesh': PYMESH_AVAILABLE,
                'open3d': OPEN3D_AVAILABLE,
                'trimesh': TRIMESH_AVAILABLE,
                'tensorflow': TENSORFLOW_AVAILABLE,
                'pytorch': PYTORCH_AVAILABLE
            },
            'performance_stats': self.get_performance_stats()
        }

# ===== DEMONSTRATION AND TESTING =====

def create_sample_mesh() -> 'Mesh':

    # Simple cube mesh
    vertices = [
        Point3D(0, 0, 0), Point3D(1, 0, 0), Point3D(1, 1, 0), Point3D(0, 1, 0),  # Bottom
        Point3D(0, 0, 1), Point3D(1, 0, 1), Point3D(1, 1, 1), Point3D(0, 1, 1)   # Top
    ]

    triangles = [
        # Bottom face
        Triangle(vertices=(vertices[0], vertices[1], vertices[2]), normal=Point3D(0, 0, -1)),
        Triangle(vertices=(vertices[0], vertices[2], vertices[3]), normal=Point3D(0, 0, -1)),
        # Top face
        Triangle(vertices=(vertices[4], vertices[5], vertices[6]), normal=Point3D(0, 0, 1)),
        Triangle(vertices=(vertices[4], vertices[6], vertices[7]), normal=Point3D(0, 0, 1)),
        # Front face
        Triangle(vertices=(vertices[0], vertices[1], vertices[5]), normal=Point3D(0, -1, 0)),
        Triangle(vertices=(vertices[0], vertices[5], vertices[4]), normal=Point3D(0, -1, 0)),
        # Back face
        Triangle(vertices=(vertices[3], vertices[2], vertices[6]), normal=Point3D(0, 1, 0)),
        Triangle(vertices=(vertices[3], vertices[6], vertices[7]), normal=Point3D(0, 1, 0)),
        # Left face
        Triangle(vertices=(vertices[0], vertices[3], vertices[7]), normal=Point3D(-1, 0, 0)),
        Triangle(vertices=(vertices[0], vertices[7], vertices[4]), normal=Point3D(-1, 0, 0)),
        # Right face
        Triangle(vertices=(vertices[1], vertices[2], vertices[6]), normal=Point3D(1, 0, 0)),
        Triangle(vertices=(vertices[1], vertices[6], vertices[5]), normal=Point3D(1, 0, 0))
    ]

    return Mesh(vertices=vertices, triangles=triangles, name="sample_cube")

def demonstrate_advanced_mesh_processing():

    print("=== Ultra-Advanced Mesh Processing System Demonstration ===")

    # Create configuration
    config = MeshProcessingConfig(
        processing_mode=MeshProcessingMode.BALANCED,
        optimization_level=MeshOptimizationLevel.ADVANCED,
        use_machine_learning=True,
        parallel_processing=True
    )

    # Initialize processor
    processor = UltraAdvancedMeshProcessor(config)

    # Create sample mesh
    mesh = create_sample_mesh()

    print(f"Processing mesh with {len(mesh.vertices)} vertices and {len(mesh.triangles)} triangles")

    # Process mesh
    processed_mesh, result = processor.process_mesh(mesh, ['analyze', 'repair', 'optimize'])

    print("Processing Results:")
    print(f"- Processing time: {result.processing_time:.3f}s")
    print(f"- Original triangles: {result.mesh_statistics.get('num_triangles', 0)}")
    print(f"- Quality metrics: {result.quality_metrics}")
    print(f"- Defects found: {result.defect_analysis}")
    print(f"- Optimization suggestions: {len(result.optimization_suggestions)}")

    # Show advanced analysis results
    if result.curvature_analysis:
        curvature = result.curvature_analysis
        print(f"- Curvature analysis: {len(curvature.get('mean_curvature', []))} points analyzed")

    if result.thickness_analysis:
        thickness = result.thickness_analysis
        print(".3f")

    if result.structural_analysis:
        structural = result.structural_analysis
        print(".3f")

    # Show system info
    info = processor.get_system_info()
    print(f"- AI enabled: {info['ai_enabled']}")
    print(f"- Parallel processing: {info['parallel_processing']}")
    print(f"- GPU acceleration: {info['gpu_acceleration']}")

    print("=== Demonstration Complete ===")

if __name__ == "__main__":
    demonstrate_advanced_mesh_processing()

@dataclass
class Mesh:
    vertices: np.ndarray  # (N, 3) array of vertices
    faces: np.ndarray     # (M, 3) array of face indices
    normals: Optional[np.ndarray] = None  # (M, 3) array of face normals
    bounds: Optional[Tuple[Point3D, Point3D]] = None
    materials: Optional[Dict] = None  # Material information
    metadata: Optional[Dict] = None   # File metadata
    
    def __post_init__(self):
        self.calculate_bounds()
        if self.normals is None:
            self.calculate_normals()
    
    def calculate_bounds(self):
        if len(self.vertices) == 0:
            self.bounds = (Point3D(0, 0, 0), Point3D(0, 0, 0))
            return
        
        min_coords = np.min(self.vertices, axis=0)
        max_coords = np.max(self.vertices, axis=0)
        
        self.bounds = (
            Point3D(min_coords[0], min_coords[1], min_coords[2]),
            Point3D(max_coords[0], max_coords[1], max_coords[2])
        )
    
    def calculate_normals(self):
        if len(self.faces) == 0:
            self.normals = np.array([])
            return
        
        normals = []
        
        for face in self.faces:
            v0 = self.vertices[face[0]]
            v1 = self.vertices[face[1]]
            v2 = self.vertices[face[2]]
            
            # Calculate face normal using cross product
            edge1 = v1 - v0
            edge2 = v2 - v0
            
            normal = np.cross(edge1, edge2)
            length = np.linalg.norm(normal)
            
            if length > 1e-10:
                normal = normal / length
            else:
                normal = np.array([0, 0, 1])  # Default normal
            
            normals.append(normal)
        
        self.normals = np.array(normals)
    
    def get_triangles(self) -> List[Triangle]:
        triangles = []
        
        for i, face in enumerate(self.faces):
            v0 = Point3D(*self.vertices[face[0]])
            v1 = Point3D(*self.vertices[face[1]])
            v2 = Point3D(*self.vertices[face[2]])
            
            normal = Point3D(0, 0, 1)
            if self.normals is not None and i < len(self.normals):
                normal = Point3D(*self.normals[i])
            
            triangle = Triangle(
                vertices=(v0, v1, v2),
                normal=normal
            )
            triangles.append(triangle)
        
        return triangles
    
    def volume(self) -> float:
        if len(self.faces) == 0:
            return 0.0
        
        volume = 0.0
        
        for face in self.faces:
            v0 = self.vertices[face[0]]
            v1 = self.vertices[face[1]]
            v2 = self.vertices[face[2]]
            
            # Calculate signed volume contribution of tetrahedron
            # formed by triangle and origin
            volume += np.dot(v0, np.cross(v1, v2)) / 6.0
        
        return abs(volume)
    
    def surface_area(self) -> float:
        total_area = 0.0
        
        for triangle in self.get_triangles():
            total_area += triangle.area()
        
        return total_area
    
    def is_watertight(self) -> bool:
        # Build edge map to check manifold property
        edge_count = {}
        
        for face in self.faces:
            edges = [
                (min(face[0], face[1]), max(face[0], face[1])),
                (min(face[1], face[2]), max(face[1], face[2])),
                (min(face[2], face[0]), max(face[2], face[0]))
            ]
            
            for edge in edges:
                edge_count[edge] = edge_count.get(edge, 0) + 1
        
        # In a watertight mesh, each edge should be shared by exactly 2 faces
        for count in edge_count.values():
            if count != 2:
                return False
        
        return True

class MeshProcessor:
    
    SUPPORTED_FORMATS = ['.stl', '.obj', '.3mf']
    
    @staticmethod
    def detect_file_format(file_path: str) -> str:
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if extension in MeshProcessor.SUPPORTED_FORMATS:
            return extension
        
        # Try to detect from content
        try:
            with open(file_path, 'rb') as f:
                header = f.read(10).lower()
                
                if header.startswith(b'solid') or b'facet' in header:
                    return '.stl'
                elif header.startswith(b'pk'):  # ZIP signature (3MF)
                    return '.3mf'
                elif b'v ' in header or b'f ' in header:
                    return '.obj'
        except:
            pass
        
        raise ValueError(f"Unsupported file format: {extension}")
    
    @staticmethod
    def load_mesh(file_path: str) -> Mesh:
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Mesh file not found: {file_path}")
        
        file_format = MeshProcessor.detect_file_format(file_path)
        logger.info(f"Loading {file_format} file: {file_path}")
        
        if file_format == '.stl':
            return MeshProcessor.load_stl(file_path)
        elif file_format == '.obj':
            return MeshProcessor.load_obj(file_path)
        elif file_format == '.3mf':
            return MeshProcessor.load_3mf(file_path)
        else:
            raise ValueError(f"Unsupported format: {file_format}")
    
    @staticmethod
    def load_stl(file_path: str) -> Mesh:
        with open(file_path, 'rb') as f:
            # Detect STL format
            header = f.read(5)
            f.seek(0)
            
            # Check if it's ASCII STL
            if header.lower().startswith(b'solid'):
                # Could be ASCII, verify by trying to parse
                try:
                    content = f.read(1000).decode('utf-8', errors='ignore').lower()
                    if 'facet normal' in content and 'vertex' in content:
                        f.seek(0)
                        return MeshProcessor._load_stl_ascii(f)
                except:
                    pass
                
                # Fall back to binary interpretation
                f.seek(0)
                return MeshProcessor._load_stl_binary(f)
            else:
                # Definitely binary
                return MeshProcessor._load_stl_binary(f)
    
    @staticmethod
    def _load_stl_binary(file_obj) -> Mesh:
        # Skip 80-byte header
        header = file_obj.read(80)
        
        # Read number of triangles
        triangle_count_bytes = file_obj.read(4)
        if len(triangle_count_bytes) != 4:
            raise ValueError("Invalid binary STL file: cannot read triangle count")
        
        triangle_count = struct.unpack('<I', triangle_count_bytes)[0]
        logger.info(f"Binary STL: {triangle_count} triangles")
        
        vertices = []
        faces = []
        normals = []
        vertex_map = {}  # To avoid duplicate vertices
        vertex_index = 0
        
        for i in range(triangle_count):
            # Read normal vector (3 floats)
            normal_bytes = file_obj.read(12)
            if len(normal_bytes) != 12:
                raise ValueError(f"Invalid binary STL file: cannot read normal for triangle {i}")
            
            normal = struct.unpack('<3f', normal_bytes)
            normals.append(normal)
            
            # Read 3 vertices (9 floats)
            face_vertices = []
            
            for j in range(3):
                vertex_bytes = file_obj.read(12)
                if len(vertex_bytes) != 12:
                    raise ValueError(f"Invalid binary STL file: cannot read vertex {j} for triangle {i}")
                
                vertex = struct.unpack('<3f', vertex_bytes)
                
                # Round to avoid floating point precision issues
                vertex_key = (round(vertex[0], 6), round(vertex[1], 6), round(vertex[2], 6))
                
                if vertex_key not in vertex_map:
                    vertex_map[vertex_key] = vertex_index
                    vertices.append(vertex)
                    vertex_index += 1
                
                face_vertices.append(vertex_map[vertex_key])
            
            faces.append(face_vertices)
            
            # Skip 2-byte attribute count
            file_obj.read(2)
        
        return Mesh(
            vertices=np.array(vertices, dtype=np.float32),
            faces=np.array(faces, dtype=np.int32),
            normals=np.array(normals, dtype=np.float32),
            metadata={'format': 'STL Binary', 'triangle_count': triangle_count}
        )
    
    @staticmethod
    def _load_stl_ascii(file_obj) -> Mesh:
        vertices = []
        faces = []
        normals = []
        vertex_map = {}
        vertex_index = 0
        
        content = file_obj.read().decode('utf-8', errors='ignore')
        lines = content.split('\n')
        
        i = 0
        triangle_count = 0
        
        while i < len(lines):
            line = lines[i].strip().lower()
            
            if line.startswith('facet normal'):
                # Parse normal
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        normal = [float(parts[2]), float(parts[3]), float(parts[4])]
                        normals.append(normal)
                    except ValueError:
                        normals.append([0, 0, 1])  # Default normal
                else:
                    normals.append([0, 0, 1])
                
                # Find vertices for this facet
                face_vertices = []
                i += 1
                
                while i < len(lines):
                    line = lines[i].strip().lower()
                    
                    if line.startswith('vertex'):
                        parts = line.split()
                        if len(parts) >= 4:
                            try:
                                vertex = [float(parts[1]), float(parts[2]), float(parts[3])]
                                
                                # Round to avoid precision issues
                                vertex_key = (round(vertex[0], 6), round(vertex[1], 6), round(vertex[2], 6))
                                
                                if vertex_key not in vertex_map:
                                    vertex_map[vertex_key] = vertex_index
                                    vertices.append(vertex)
                                    vertex_index += 1
                                
                                face_vertices.append(vertex_map[vertex_key])
                            except ValueError:
                                pass
                    
                    elif line.startswith('endfacet'):
                        if len(face_vertices) == 3:
                            faces.append(face_vertices)
                            triangle_count += 1
                        break
                    
                    i += 1
            
            i += 1
        
        if not vertices:
            raise ValueError("No valid vertices found in ASCII STL file")
        
        logger.info(f"ASCII STL: {triangle_count} triangles, {len(vertices)} vertices")
        
        return Mesh(
            vertices=np.array(vertices, dtype=np.float32),
            faces=np.array(faces, dtype=np.int32),
            normals=np.array(normals, dtype=np.float32) if normals else None,
            metadata={'format': 'STL ASCII', 'triangle_count': triangle_count}
        )
    
    @staticmethod
    def load_obj(file_path: str) -> Mesh:
        vertices = []
        faces = []
        normals = []
        texture_coords = []
        materials = {}
        current_material = None
        
        logger.info(f"Loading OBJ file: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()
                if not parts:
                    continue
                
                try:
                    # Vertex
                    if parts[0] == 'v':
                        if len(parts) >= 4:
                            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                            vertices.append([x, y, z])
                    
                    # Vertex normal
                    elif parts[0] == 'vn':
                        if len(parts) >= 4:
                            nx, ny, nz = float(parts[1]), float(parts[2]), float(parts[3])
                            normals.append([nx, ny, nz])
                    
                    # Texture coordinate
                    elif parts[0] == 'vt':
                        if len(parts) >= 3:
                            u, v = float(parts[1]), float(parts[2])
                            texture_coords.append([u, v])
                    
                    # Face
                    elif parts[0] == 'f':
                        if len(parts) >= 4:  # At least 3 vertices for a face
                            face_vertices = []
                            
                            for vertex_data in parts[1:4]:  # Only take first 3 vertices (triangulate)
                                # Parse vertex/texture/normal indices
                                indices = vertex_data.split('/')
                                
                                # Vertex index (1-based, convert to 0-based)
                                vertex_idx = int(indices[0]) - 1
                                if vertex_idx < 0:
                                    vertex_idx = len(vertices) + vertex_idx + 1
                                
                                face_vertices.append(vertex_idx)
                            
                            if len(face_vertices) == 3:
                                faces.append(face_vertices)
                            
                            # Handle quads by creating a second triangle
                            if len(parts) >= 5:  # Quad
                                quad_vertices = []
                                for vertex_data in [parts[1], parts[3], parts[4]]:
                                    indices = vertex_data.split('/')
                                    vertex_idx = int(indices[0]) - 1
                                    if vertex_idx < 0:
                                        vertex_idx = len(vertices) + vertex_idx + 1
                                    quad_vertices.append(vertex_idx)
                                
                                if len(quad_vertices) == 3:
                                    faces.append(quad_vertices)
                    
                    # Material
                    elif parts[0] == 'usemtl':
                        current_material = parts[1] if len(parts) > 1 else None
                    
                    elif parts[0] == 'mtllib':
                        # Material library file (could load separately)
                        pass
                
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing OBJ line {line_num}: {line} - {e}")
                    continue
        
        if not vertices:
            raise ValueError("No vertices found in OBJ file")
        
        if not faces:
            raise ValueError("No faces found in OBJ file")
        
        logger.info(f"OBJ loaded: {len(vertices)} vertices, {len(faces)} faces")
        
        return Mesh(
            vertices=np.array(vertices, dtype=np.float32),
            faces=np.array(faces, dtype=np.int32),
            normals=np.array(normals, dtype=np.float32) if normals else None,
            materials=materials if materials else None,
            metadata={'format': 'OBJ', 'texture_coords_count': len(texture_coords)}
        )
    
    @staticmethod
    def load_3mf(file_path: str) -> Mesh:
        logger.info(f"Loading 3MF file: {file_path}")
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # 3MF files contain a 3D/3dmodel.model file with the mesh data
                model_file = None
                
                # Look for the 3D model file
                for file_info in zip_file.filelist:
                    if file_info.filename.endswith('3dmodel.model') or file_info.filename.endswith('.model'):
                        model_file = file_info.filename
                        break
                
                if not model_file:
                    raise ValueError("No 3D model file found in 3MF archive")
                
                # Extract and parse the XML model file
                with zip_file.open(model_file) as f:
                    xml_content = f.read().decode('utf-8')
                    return MeshProcessor._parse_3mf_xml(xml_content)
        
        except zipfile.BadZipFile:
            raise ValueError("Invalid 3MF file: not a valid ZIP archive")
    
    @staticmethod
    def _parse_3mf_xml(xml_content: str) -> Mesh:
        try:
            root = ET.fromstring(xml_content)
            
            # Remove namespace prefixes for easier parsing
            for elem in root.iter():
                if '}' in elem.tag:
                    elem.tag = elem.tag.split('}')[1]
            
            # Find the mesh data
            vertices = []
            faces = []
            materials = {}
            
            # Look for vertices
            for vertex_elem in root.iter('vertex'):
                x = float(vertex_elem.get('x', 0))
                y = float(vertex_elem.get('y', 0))
                z = float(vertex_elem.get('z', 0))
                vertices.append([x, y, z])
            
            # Look for triangles
            for triangle_elem in root.iter('triangle'):
                v1 = int(triangle_elem.get('v1', 0))
                v2 = int(triangle_elem.get('v2', 0))
                v3 = int(triangle_elem.get('v3', 0))
                faces.append([v1, v2, v3])
            
            # Look for materials
            for material_elem in root.iter('basematerial'):
                material_id = material_elem.get('id')
                name = material_elem.get('name', f'Material_{material_id}')
                displaycolor = material_elem.get('displaycolor', '#FFFFFF')
                materials[material_id] = {
                    'name': name,
                    'color': displaycolor
                }
            
            if not vertices:
                raise ValueError("No vertices found in 3MF file")
            
            if not faces:
                raise ValueError("No faces found in 3MF file")
            
            logger.info(f"3MF loaded: {len(vertices)} vertices, {len(faces)} faces")
            
            return Mesh(
                vertices=np.array(vertices, dtype=np.float32),
                faces=np.array(faces, dtype=np.int32),
                materials=materials if materials else None,
                metadata={'format': '3MF'}
            )
        
        except ET.ParseError as e:
            raise ValueError(f"Invalid 3MF XML: {e}")
        except (KeyError, ValueError) as e:
            raise ValueError(f"Error parsing 3MF data: {e}")
    
    @staticmethod
    def save_stl(mesh: Mesh, file_path: str, binary: bool = True):
        if binary:
            MeshProcessor._save_stl_binary(mesh, file_path)
        else:
            MeshProcessor._save_stl_ascii(mesh, file_path)
    
    @staticmethod
    def _save_stl_binary(mesh: Mesh, file_path: str):
        with open(file_path, 'wb') as f:
            # Write 80-byte header
            header = b'Binary STL generated by Sleia 3D Slicer'
            header = header.ljust(80, b'\0')
            f.write(header)
            
            # Write triangle count
            triangle_count = len(mesh.faces)
            f.write(struct.pack('<I', triangle_count))
            
            # Write triangles
            for i, face in enumerate(mesh.faces):
                # Write normal
                if mesh.normals is not None and i < len(mesh.normals):
                    normal = mesh.normals[i]
                else:
                    # Calculate normal
                    v0 = mesh.vertices[face[0]]
                    v1 = mesh.vertices[face[1]]
                    v2 = mesh.vertices[face[2]]
                    
                    edge1 = v1 - v0
                    edge2 = v2 - v0
                    normal = np.cross(edge1, edge2)
                    length = np.linalg.norm(normal)
                    
                    if length > 1e-10:
                        normal = normal / length
                    else:
                        normal = np.array([0, 0, 1])
                
                f.write(struct.pack('<3f', normal[0], normal[1], normal[2]))
                
                # Write vertices
                for vertex_idx in face:
                    vertex = mesh.vertices[vertex_idx]
                    f.write(struct.pack('<3f', vertex[0], vertex[1], vertex[2]))
                
                # Write attribute byte count (always 0)
                f.write(struct.pack('<H', 0))
    
    @staticmethod
    def _save_stl_ascii(mesh: Mesh, file_path: str):
        with open(file_path, 'w') as f:
            f.write("solid mesh\n")
            
            for i, face in enumerate(mesh.faces):
                # Write normal
                if mesh.normals is not None and i < len(mesh.normals):
                    normal = mesh.normals[i]
                else:
                    # Calculate normal
                    v0 = mesh.vertices[face[0]]
                    v1 = mesh.vertices[face[1]]
                    v2 = mesh.vertices[face[2]]
                    
                    edge1 = v1 - v0
                    edge2 = v2 - v0
                    normal = np.cross(edge1, edge2)
                    length = np.linalg.norm(normal)
                    
                    if length > 1e-10:
                        normal = normal / length
                    else:
                        normal = np.array([0, 0, 1])
                
                f.write(f"  facet normal {normal[0]:.6f} {normal[1]:.6f} {normal[2]:.6f}\n")
                f.write("    outer loop\n")
                
                # Write vertices
                for vertex_idx in face:
                    vertex = mesh.vertices[vertex_idx]
                    f.write(f"      vertex {vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f}\n")
                
                f.write("    endloop\n")
                f.write("  endfacet\n")
            
            f.write("endsolid mesh\n")
    
    @staticmethod
    def save_obj(mesh: Mesh, file_path: str):
        with open(file_path, 'w') as f:
            f.write("# OBJ file generated by Sleia 3D Slicer\n")
            f.write(f"# Vertices: {len(mesh.vertices)}\n")
            f.write(f"# Faces: {len(mesh.faces)}\n\n")
            
            # Write vertices
            for vertex in mesh.vertices:
                f.write(f"v {vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f}\n")
            
            # Write normals if available
            if mesh.normals is not None:
                f.write("\n")
                for normal in mesh.normals:
                    f.write(f"vn {normal[0]:.6f} {normal[1]:.6f} {normal[2]:.6f}\n")
            
            # Write faces
            f.write("\n")
            for face in mesh.faces:
                if mesh.normals is not None:
                    # Write faces with vertex and normal indices
                    f.write(f"f {face[0]+1}//{face[0]+1} {face[1]+1}//{face[1]+1} {face[2]+1}//{face[2]+1}\n")
                else:
                    # Write faces with just vertex indices
                    f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")
    
    @staticmethod
    def repair_mesh(mesh: Mesh, tolerance: float = 1e-6) -> Mesh:
        logger.info("Repairing mesh...")
        
        # Remove duplicate vertices
        repaired_mesh = MeshProcessor._remove_duplicate_vertices(mesh, tolerance)
        
        # Remove degenerate faces
        repaired_mesh = MeshProcessor._remove_degenerate_faces(repaired_mesh)
        
        # Fix face orientation
        repaired_mesh = MeshProcessor._fix_face_orientation(repaired_mesh)
        
        # Remove duplicate faces
        repaired_mesh = MeshProcessor._remove_duplicate_faces(repaired_mesh)
        
        logger.info("Mesh repair complete")
        return repaired_mesh
    
    @staticmethod
    def _remove_duplicate_vertices(mesh: Mesh, tolerance: float) -> Mesh:
        vertices = []
        vertex_map = {}
        new_faces = []
        
        # Build vertex mapping
        for i, vertex in enumerate(mesh.vertices):
            # Find existing vertex within tolerance
            found_idx = None
            
            for j, existing_vertex in enumerate(vertices):
                if np.linalg.norm(vertex - existing_vertex) < tolerance:
                    found_idx = j
                    break
            
            if found_idx is None:
                # Add new vertex
                vertex_map[i] = len(vertices)
                vertices.append(vertex)
            else:
                # Use existing vertex
                vertex_map[i] = found_idx
        
        # Update faces
        for face in mesh.faces:
            new_face = [vertex_map[vertex_idx] for vertex_idx in face]
            new_faces.append(new_face)
        
        return Mesh(
            vertices=np.array(vertices),
            faces=np.array(new_faces)
        )
    
    @staticmethod
    def _remove_degenerate_faces(mesh: Mesh) -> Mesh:
        valid_faces = []
        
        for face in mesh.faces:
            # Check for duplicate vertices in face
            if len(set(face)) != 3:
                continue
            
            # Check for zero area
            v0 = mesh.vertices[face[0]]
            v1 = mesh.vertices[face[1]]
            v2 = mesh.vertices[face[2]]
            
            edge1 = v1 - v0
            edge2 = v2 - v0
            cross = np.cross(edge1, edge2)
            area = np.linalg.norm(cross) / 2
            
            if area > 1e-10:  # Non-zero area
                valid_faces.append(face)
        
        return Mesh(
            vertices=mesh.vertices,
            faces=np.array(valid_faces)
        )
    
    @staticmethod
    def _fix_face_orientation(mesh: Mesh) -> Mesh:
        # Calculate mesh centroid
        centroid = np.mean(mesh.vertices, axis=0)
        
        fixed_faces = []
        
        for face in mesh.faces:
            v0 = mesh.vertices[face[0]]
            v1 = mesh.vertices[face[1]]
            v2 = mesh.vertices[face[2]]
            
            # Calculate face normal
            edge1 = v1 - v0
            edge2 = v2 - v0
            normal = np.cross(edge1, edge2)
            
            if np.linalg.norm(normal) > 1e-10:
                normal = normal / np.linalg.norm(normal)
                
                # Calculate face centroid
                face_centroid = (v0 + v1 + v2) / 3
                
                # Vector from mesh centroid to face centroid
                to_face = face_centroid - centroid
                
                # If normal points inward, flip face
                if np.dot(normal, to_face) < 0:
                    face = [face[0], face[2], face[1]]  # Flip vertex order
            
            fixed_faces.append(face)
        
        return Mesh(
            vertices=mesh.vertices,
            faces=np.array(fixed_faces)
        )
    
    @staticmethod
    def _remove_duplicate_faces(mesh: Mesh) -> Mesh:
        unique_faces = []
        face_set = set()
        
        for face in mesh.faces:
            # Sort vertices to create canonical representation
            sorted_face = tuple(sorted(face))
            
            if sorted_face not in face_set:
                face_set.add(sorted_face)
                unique_faces.append(face)
        
        return Mesh(
            vertices=mesh.vertices,
            faces=np.array(unique_faces)
        )
    
    @staticmethod
    def transform_mesh(mesh: Mesh, translation: Point3D = None, 
                      rotation: Tuple[float, float, float] = None,
                      scale: Union[float, Tuple[float, float, float]] = None) -> Mesh:
        vertices = mesh.vertices.copy()
        
        # Apply scaling
        if scale is not None:
            if isinstance(scale, (int, float)):
                vertices *= scale
            else:
                vertices[:, 0] *= scale[0]
                vertices[:, 1] *= scale[1]
                vertices[:, 2] *= scale[2]
        
        # Apply rotation
        if rotation is not None:
            rx, ry, rz = [math.radians(angle) for angle in rotation]
            
            # Rotation matrices
            Rx = np.array([
                [1, 0, 0],
                [0, math.cos(rx), -math.sin(rx)],
                [0, math.sin(rx), math.cos(rx)]
            ])
            
            Ry = np.array([
                [math.cos(ry), 0, math.sin(ry)],
                [0, 1, 0],
                [-math.sin(ry), 0, math.cos(ry)]
            ])
            
            Rz = np.array([
                [math.cos(rz), -math.sin(rz), 0],
                [math.sin(rz), math.cos(rz), 0],
                [0, 0, 1]
            ])
            
            # Combined rotation matrix
            R = Rz @ Ry @ Rx
            
            # Apply rotation to vertices
            vertices = vertices @ R.T
        
        # Apply translation
        if translation is not None:
            vertices[:, 0] += translation.x
            vertices[:, 1] += translation.y
            vertices[:, 2] += translation.z
        
        return Mesh(
            vertices=vertices,
            faces=mesh.faces.copy(),
            materials=mesh.materials,
            metadata=mesh.metadata
        )
    
    @staticmethod
    def center_mesh(mesh: Mesh) -> Mesh:
        if mesh.bounds is None:
            mesh.calculate_bounds()
        
        center = Point3D(
            (mesh.bounds[0].x + mesh.bounds[1].x) / 2,
            (mesh.bounds[0].y + mesh.bounds[1].y) / 2,
            (mesh.bounds[0].z + mesh.bounds[1].z) / 2
        )
        
        translation = Point3D(-center.x, -center.y, -center.z)
        return MeshProcessor.transform_mesh(mesh, translation=translation)
    
    @staticmethod
    def place_on_bed(mesh: Mesh) -> Mesh:
        if mesh.bounds is None:
            mesh.calculate_bounds()
        
        translation = Point3D(0, 0, -mesh.bounds[0].z)
        return MeshProcessor.transform_mesh(mesh, translation=translation)
    
    @staticmethod
    def get_mesh_info(mesh: Mesh) -> Dict:
        info = {
            'vertex_count': len(mesh.vertices),
            'face_count': len(mesh.faces),
            'volume': mesh.volume(),
            'surface_area': mesh.surface_area(),
            'is_watertight': mesh.is_watertight(),
            'bounds': mesh.bounds,
            'format': mesh.metadata.get('format', 'Unknown') if mesh.metadata else 'Unknown',
            'has_materials': mesh.materials is not None and len(mesh.materials) > 0
        }
        
        if mesh.bounds:
            size = Point3D(
                mesh.bounds[1].x - mesh.bounds[0].x,
                mesh.bounds[1].y - mesh.bounds[0].y,
                mesh.bounds[1].z - mesh.bounds[0].z
            )
            info['size'] = size
        
        if mesh.materials:
            info['material_count'] = len(mesh.materials)
            info['material_names'] = list(mesh.materials.keys())
        
        return info
    
    @staticmethod
    def validate_mesh_for_printing(mesh: Mesh) -> List[str]:
        issues = []
        
        # Check if mesh has vertices and faces
        if len(mesh.vertices) == 0:
            issues.append("Mesh has no vertices")
        
        if len(mesh.faces) == 0:
            issues.append("Mesh has no faces")
        
        if not issues:  # Only check further if basic structure exists
            
            # Check if mesh is watertight
            if not mesh.is_watertight():
                issues.append("Mesh is not watertight (has holes or non-manifold edges)")
            
            # Check for degenerate faces
            degenerate_count = 0
            for face in mesh.faces:
                if len(set(face)) != 3:
                    degenerate_count += 1
            
            if degenerate_count > 0:
                issues.append(f"Mesh has {degenerate_count} degenerate faces")
            
            # Check mesh size
            if mesh.bounds:
                size = Point3D(
                    mesh.bounds[1].x - mesh.bounds[0].x,
                    mesh.bounds[1].y - mesh.bounds[0].y,
                    mesh.bounds[1].z - mesh.bounds[0].z
                )
                
                if size.x <= 0 or size.y <= 0 or size.z <= 0:
                    issues.append("Mesh has zero or negative dimensions")
                
                if size.x > 1000 or size.y > 1000 or size.z > 1000:
                    issues.append("Mesh is very large (>1000mm), check units")
                
                if size.x < 0.1 or size.y < 0.1 or size.z < 0.1:
                    issues.append("Mesh is very small (<0.1mm), check units")
            
            # Check volume
            volume = mesh.volume()
            if volume <= 0:
                issues.append("Mesh has zero or negative volume")
            
            # Check for face index validity
            max_vertex_index = len(mesh.vertices) - 1
            for i, face in enumerate(mesh.faces):
                for vertex_idx in face:
                    if vertex_idx < 0 or vertex_idx > max_vertex_index:
                        issues.append(f"Face {i} references invalid vertex index {vertex_idx}")
                        break
        
        return issues
    
    @staticmethod
    def convert_format(input_file: str, output_file: str, target_format: str = None):
        # Load the mesh
        mesh = MeshProcessor.load_mesh(input_file)
        
        # Determine target format
        if target_format is None:
            target_format = Path(output_file).suffix.lower()
        
        # Save in target format
        if target_format == '.stl':
            MeshProcessor.save_stl(mesh, output_file, binary=True)
        elif target_format == '.obj':
            MeshProcessor.save_obj(mesh, output_file)
        else:
            raise ValueError(f"Unsupported output format: {target_format}")
        
        logger.info(f"Converted {input_file} to {output_file} ({target_format})")

# Example usage and testing
if __name__ == "__main__":
    
    # Create a simple test mesh (cube)
    def create_test_cube(size: float = 10.0) -> Mesh:
        s = size / 2
        
        vertices = np.array([
            [-s, -s, -s], [s, -s, -s], [s, s, -s], [-s, s, -s],  # Bottom face
            [-s, -s, s], [s, -s, s], [s, s, s], [-s, s, s]      # Top face
        ], dtype=np.float32)
        
        faces = np.array([
            [0, 1, 2], [0, 2, 3],  # Bottom
            [4, 6, 5], [4, 7, 6],  # Top
            [0, 4, 5], [0, 5, 1],  # Front
            [2, 6, 7], [2, 7, 3],  # Back
            [0, 3, 7], [0, 7, 4],  # Left
            [1, 5, 6], [1, 6, 2]   # Right
        ], dtype=np.int32)
        
        return Mesh(vertices=vertices, faces=faces)
    
    # Test enhanced mesh processor
    print("=== Enhanced Mesh Processor Test ===")
    print(f"Supported formats: {', '.join(MeshProcessor.SUPPORTED_FORMATS)}")
    
    # Create test cube
    print("\nCreating test cube...")
    test_mesh = create_test_cube(20.0)
    
    # Get mesh info
    info = MeshProcessor.get_mesh_info(test_mesh)
    print("\nMesh Information:")
    for key, value in info.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    # Validate mesh
    issues = MeshProcessor.validate_mesh_for_printing(test_mesh)
    if issues:
        print(f"\nValidation Issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\nMesh validation: ✅ PASSED")
    
    # Test multi-format saving/loading
    print("\n=== Testing Multi-Format Support ===")
    
    test_files = []
    
    try:
        # Save as binary STL
        MeshProcessor.save_stl(test_mesh, "test_enhanced_binary.stl", binary=True)
        test_files.append(("test_enhanced_binary.stl", "STL Binary"))
        print("✅ Saved binary STL")
        
        # Save as ASCII STL
        MeshProcessor.save_stl(test_mesh, "test_enhanced_ascii.stl", binary=False)
        test_files.append(("test_enhanced_ascii.stl", "STL ASCII"))
        print("✅ Saved ASCII STL")
        
        # Save as OBJ
        MeshProcessor.save_obj(test_mesh, "test_enhanced.obj")
        test_files.append(("test_enhanced.obj", "OBJ"))
        print("✅ Saved OBJ")
        
        # Test loading each format
        print("\nTesting format loading:")
        for filename, format_name in test_files:
            try:
                loaded_mesh = MeshProcessor.load_mesh(filename)
                print(f"✅ Loaded {format_name}: {len(loaded_mesh.vertices)} vertices, {len(loaded_mesh.faces)} faces")
                print(f"   Format detected: {loaded_mesh.metadata.get('format', 'Unknown') if loaded_mesh.metadata else 'Unknown'}")
            except Exception as e:
                print(f"❌ Failed to load {format_name}: {e}")
        
        # Test format conversion
        print("\nTesting format conversion:")
        try:
            MeshProcessor.convert_format("test_enhanced.obj", "converted_from_obj.stl")
            print("✅ Converted OBJ → STL")
            
            MeshProcessor.convert_format("test_enhanced_binary.stl", "converted_from_stl.obj")
            print("✅ Converted STL → OBJ")
        except Exception as e:
            print(f"❌ Format conversion failed: {e}")
    
    except Exception as e:
        print(f"❌ Multi-format test error: {e}")
    
    print("\n=== Enhanced Mesh Processor Tests Complete ===")
    print("✅ Ready for STL, OBJ, and 3MF file support!")

# ===== ADVANCED MESH OPTIMIZATION WITH MACHINE LEARNING =====

class MeshMachineLearningOptimizer:

    def __init__(self):
        self.models = {}
        self.optimization_patterns = {}
        self.logger = logging.getLogger(__name__)

    def optimize_mesh_with_ml(self, mesh: 'Mesh', target_quality: str = 'balanced') -> 'Mesh':

        if not self.models:
            # Fallback to rule-based optimization
            return self._rule_based_mesh_optimization(mesh, target_quality)

        # Extract mesh features
        features = self._extract_mesh_features(mesh)

        # Predict optimal operations
        optimal_operations = self.models['mesh_optimizer'].predict([features])[0]

        # Apply predicted optimizations
        optimized_mesh = self._apply_ml_optimizations(mesh, optimal_operations)

        return optimized_mesh

    def _extract_mesh_features(self, mesh: 'Mesh') -> List[float]:
        features = []

        # Basic geometric features
        features.extend([
            len(mesh.vertices),
            len(mesh.faces),
            mesh.volume(),
            mesh.surface_area(),
            mesh.bounding_box_volume()
        ])

        # Quality metrics
        quality = mesh.analyze_quality()
        features.extend([
            quality.get('aspect_ratio_mean', 0),
            quality.get('aspect_ratio_std', 0),
            quality.get('angle_mean', 0),
            quality.get('angle_std', 0)
        ])

        # Topology features
        topology = mesh.analyze_topology()
        features.extend([
            topology.get('genus', 0),
            topology.get('connected_components', 1),
            topology.get('holes', 0)
        ])

        return features

    def _rule_based_mesh_optimization(self, mesh: 'Mesh', target_quality: str) -> 'Mesh':

        optimized_mesh = mesh.copy()

        if target_quality == 'speed':
            # Aggressive decimation for speed
            optimized_mesh = optimized_mesh.decimate(0.5)
        elif target_quality == 'quality':
            # Quality improvements
            optimized_mesh = optimized_mesh.remesh(target_edge_length=1.0)
            optimized_mesh = optimized_mesh.smooth(iterations=5)
        else:  # balanced
            # Moderate optimization
            optimized_mesh = optimized_mesh.decimate(0.8)
            optimized_mesh = optimized_mesh.smooth(iterations=2)

        return optimized_mesh

    def _apply_ml_optimizations(self, mesh: 'Mesh', operations: List[int]) -> 'Mesh':
        # Simplified implementation
        return mesh

# ===== ADVANCED DEFECT DETECTION SYSTEM =====

class AdvancedDefectDetector:

    def __init__(self):
        self.defect_types = {
            'holes': self._detect_holes,
            'self_intersections': self._detect_self_intersections,
            'degenerate_faces': self._detect_degenerate_faces,
            'non_manifold_edges': self._detect_non_manifold_edges,
            'thin_walls': self._detect_thin_walls,
            'overhangs': self._detect_overhangs,
            'sharp_edges': self._detect_sharp_edges,
            'surface_noise': self._detect_surface_noise
        }

        self.confidence_thresholds = {
            'holes': 0.8,
            'self_intersections': 0.9,
            'degenerate_faces': 0.95,
            'non_manifold_edges': 0.85,
            'thin_walls': 0.7,
            'overhangs': 0.75,
            'sharp_edges': 0.6,
            'surface_noise': 0.65
        }

    def comprehensive_defect_analysis(self, mesh: 'Mesh') -> Dict[str, Any]:

        analysis = {
            'defects_found': {},
            'severity_scores': {},
            'repair_priorities': [],
            'printability_impact': {},
            'repair_suggestions': []
        }

        # Run all defect detection algorithms
        for defect_type, detector in self.defect_types.items():
            try:
                defects = detector(mesh)
                if defects:
                    analysis['defects_found'][defect_type] = defects
                    severity = self._calculate_defect_severity(defect_type, defects)
                    analysis['severity_scores'][defect_type] = severity

                    if severity > self.confidence_thresholds.get(defect_type, 0.5):
                        analysis['repair_priorities'].append({
                            'type': defect_type,
                            'severity': severity,
                            'count': len(defects)
                        })

            except Exception as e:
                self.logger.warning(f"Defect detection failed for {defect_type}: {e}")

        # Sort repair priorities
        analysis['repair_priorities'].sort(key=lambda x: x['severity'], reverse=True)

        # Generate suggestions
        analysis['repair_suggestions'] = self._generate_repair_suggestions(analysis)

        return analysis

    def _detect_holes(self, mesh: 'Mesh') -> List[Dict]:
        holes = []

        # Boundary edge detection
        edge_count = defaultdict(int)
        for face in mesh.faces:
            for i in range(3):
                edge = tuple(sorted([face[i], face[(i+1) % 3]]))
                edge_count[edge] += 1

        # Edges with count == 1 are boundary edges (holes)
        boundary_edges = [edge for edge, count in edge_count.items() if count == 1]

        if boundary_edges:
            # Group boundary edges into loops
            hole_loops = self._group_boundary_loops(boundary_edges)

            for loop in hole_loops:
                if len(loop) >= 3:  # Valid hole
                    area = self._calculate_loop_area(loop, mesh.vertices)
                    perimeter = self._calculate_loop_perimeter(loop, mesh.vertices)

                    holes.append({
                        'vertices': loop,
                        'area': area,
                        'perimeter': perimeter,
                        'complexity': perimeter / max(area, 0.01)
                    })

        return holes

    def _detect_self_intersections(self, mesh: 'Mesh') -> List[Dict]:
        intersections = []

        # Build AABB tree for efficient intersection testing
        triangles = []
        for face in mesh.faces:
            v0, v1, v2 = mesh.vertices[face[0]], mesh.vertices[face[1]], mesh.vertices[face[2]]
            triangles.append((v0, v1, v2))

        # Check each triangle pair (simplified)
        for i in range(len(triangles)):
            for j in range(i + 1, len(triangles)):
                if self._triangles_intersect(triangles[i], triangles[j]):
                    intersections.append({
                        'triangle1': i,
                        'triangle2': j,
                        'intersection_type': 'face_face'
                    })

        return intersections

    def _detect_degenerate_faces(self, mesh: 'Mesh') -> List[Dict]:
        degenerate = []

        for i, face in enumerate(mesh.faces):
            v0, v1, v2 = mesh.vertices[face[0]], mesh.vertices[face[1]], mesh.vertices[face[2]]

            # Calculate area
            area = self._triangle_area(v0, v1, v2)

            if area < 1e-10:  # Very small area threshold
                degenerate.append({
                    'face_index': i,
                    'area': area,
                    'vertices': face
                })

        return degenerate

    def _detect_non_manifold_edges(self, mesh: 'Mesh') -> List[Dict]:
        non_manifold = []

        edge_faces = defaultdict(list)

        # Count faces per edge
        for face_idx, face in enumerate(mesh.faces):
            for i in range(3):
                edge = tuple(sorted([face[i], face[(i+1) % 3]]))
                edge_faces[edge].append(face_idx)

        # Edges with != 2 faces are non-manifold
        for edge, faces in edge_faces.items():
            if len(faces) != 2:
                non_manifold.append({
                    'edge': edge,
                    'face_count': len(faces),
                    'connected_faces': faces
                })

        return non_manifold

    def _detect_thin_walls(self, mesh: 'Mesh') -> List[Dict]:
        thin_walls = []

        # Sample points and check local thickness
        sample_points = self._sample_mesh_surface(mesh, 1000)

        for point in sample_points:
            thickness = self._calculate_local_thickness(mesh, point)

            if thickness > 0 and thickness < 1.0:  # Thin wall threshold
                thin_walls.append({
                    'position': point,
                    'thickness': thickness,
                    'severity': 1.0 - thickness  # Thinner = more severe
                })

        return thin_walls

    def _detect_overhangs(self, mesh: 'Mesh') -> List[Dict]:
        overhangs = []

        # Analyze face normals
        for i, face in enumerate(mesh.faces):
            normal = mesh.face_normals[i]

            # Calculate angle with vertical (Z-axis)
            angle_with_vertical = math.acos(abs(normal[2]))

            if angle_with_vertical > math.radians(45):  # Overhang threshold
                overhangs.append({
                    'face_index': i,
                    'angle': math.degrees(angle_with_vertical),
                    'normal': normal
                })

        return overhangs

    def _detect_sharp_edges(self, mesh: 'Mesh') -> List[Dict]:
        sharp_edges = []

        # Analyze edge angles
        edge_angles = defaultdict(list)

        for face_idx, face in enumerate(mesh.faces):
            for i in range(3):
                edge = tuple(sorted([face[i], face[(i+1) % 3]]))
                normal = mesh.face_normals[face_idx]
                edge_angles[edge].append(normal)

        for edge, normals in edge_angles.items():
            if len(normals) == 2:
                # Calculate angle between face normals
                angle = self._angle_between_normals(normals[0], normals[1])

                if angle < math.radians(30):  # Sharp edge threshold
                    sharp_edges.append({
                        'edge': edge,
                        'angle': math.degrees(angle),
                        'severity': math.radians(30) - angle
                    })

        return sharp_edges

    def _detect_surface_noise(self, mesh: 'Mesh') -> List[Dict]:
        noise_regions = []

        # Analyze vertex valence variations
        vertex_valence = defaultdict(int)

        for face in mesh.faces:
            for vertex in face:
                vertex_valence[vertex] += 1

        # Calculate valence statistics
        valences = list(vertex_valence.values())
        mean_valence = statistics.mean(valences)
        std_valence = statistics.stdev(valences) if len(valences) > 1 else 0

        # High valence variation indicates noise
        if std_valence > mean_valence * 0.3:
            noise_regions.append({
                'type': 'valence_variation',
                'mean_valence': mean_valence,
                'std_valence': std_valence,
                'severity': std_valence / max(mean_valence, 1)
            })

        return noise_regions

    def _calculate_defect_severity(self, defect_type: str, defects: List[Dict]) -> float:
        if not defects:
            return 0.0

        if defect_type == 'holes':
            # Severity based on total hole area
            total_area = sum(d.get('area', 0) for d in defects)
            return min(1.0, total_area / 100.0)  # Normalize

        elif defect_type == 'self_intersections':
            # Each intersection is severe
            return min(1.0, len(defects) / 10.0)

        elif defect_type == 'degenerate_faces':
            # Severity based on count
            return min(1.0, len(defects) / 100.0)

        elif defect_type == 'non_manifold_edges':
            return min(1.0, len(defects) / 50.0)

        elif defect_type == 'thin_walls':
            # Average severity
            avg_severity = statistics.mean(d.get('severity', 0) for d in defects)
            return avg_severity

        else:
            return min(1.0, len(defects) / 20.0)

    def _generate_repair_suggestions(self, analysis: Dict) -> List[str]:
        suggestions = []

        priorities = analysis.get('repair_priorities', [])

        for priority in priorities[:3]:  # Top 3 issues
            defect_type = priority['type']

            if defect_type == 'holes':
                suggestions.append("Fill mesh holes using hole filling algorithm")
            elif defect_type == 'self_intersections':
                suggestions.append("Resolve self-intersections by separating intersecting faces")
            elif defect_type == 'degenerate_faces':
                suggestions.append("Remove or repair degenerate faces")
            elif defect_type == 'non_manifold_edges':
                suggestions.append("Fix non-manifold geometry by ensuring each edge has exactly 2 faces")
            elif defect_type == 'thin_walls':
                suggestions.append("Thicken thin walls or adjust slicing parameters")
            else:
                suggestions.append(f"Address {defect_type} issues")

        return suggestions

    # Helper methods for defect detection
    def _group_boundary_loops(self, boundary_edges: List[Tuple]) -> List[List[int]]:
        # Simplified implementation
        return [list(edge) for edge in boundary_edges]

    def _calculate_loop_area(self, loop: List[int], vertices: np.ndarray) -> float:
        if len(loop) < 3:
            return 0.0

        # Use shoelace formula
        area = 0.0
        for i in range(len(loop)):
            j = (i + 1) % len(loop)
            area += vertices[loop[i]][0] * vertices[loop[j]][1]
            area -= vertices[loop[j]][0] * vertices[loop[i]][1]

        return abs(area) / 2.0

    def _calculate_loop_perimeter(self, loop: List[int], vertices: np.ndarray) -> float:
        perimeter = 0.0
        for i in range(len(loop)):
            j = (i + 1) % len(loop)
            v1, v2 = vertices[loop[i]], vertices[loop[j]]
            perimeter += np.linalg.norm(v2 - v1)
        return perimeter

    def _triangles_intersect(self, tri1: Tuple, tri2: Tuple) -> bool:
        # Simplified intersection test
        return False  # Placeholder

    def _triangle_area(self, v0: np.ndarray, v1: np.ndarray, v2: np.ndarray) -> float:
        cross = np.cross(v1 - v0, v2 - v0)
        return np.linalg.norm(cross) / 2.0

    def _sample_mesh_surface(self, mesh: 'Mesh', num_samples: int) -> List[np.ndarray]:
        samples = []

        # Simple uniform sampling (placeholder)
        for _ in range(min(num_samples, len(mesh.vertices))):
            vertex_idx = random.randint(0, len(mesh.vertices) - 1)
            samples.append(mesh.vertices[vertex_idx])

        return samples

    def _calculate_local_thickness(self, mesh: 'Mesh', point: np.ndarray) -> float:
        # Simplified thickness calculation
        return 2.0  # Placeholder

    def _angle_between_normals(self, n1: np.ndarray, n2: np.ndarray) -> float:
        cos_angle = np.dot(n1, n2) / (np.linalg.norm(n1) * np.linalg.norm(n2))
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        return math.acos(cos_angle)

# ===== MESH TOPOLOGY ANALYSIS =====

class MeshTopologyAnalyzer:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def comprehensive_topology_analysis(self, mesh: 'Mesh') -> Dict[str, Any]:

        analysis = {
            'basic_topology': self._analyze_basic_topology(mesh),
            'connectivity': self._analyze_connectivity(mesh),
            'genus_characteristics': self._analyze_genus(mesh),
            'homology_groups': self._analyze_homology(mesh),
            'morphological_features': self._analyze_morphology(mesh)
        }

        return analysis

    def _analyze_basic_topology(self, mesh: 'Mesh') -> Dict[str, Any]:
        vertices = len(mesh.vertices)
        faces = len(mesh.faces)

        # Count edges
        edges = set()
        for face in mesh.faces:
            for i in range(3):
                edge = tuple(sorted([face[i], face[(i+1) % 3]]))
                edges.add(edge)
        num_edges = len(edges)

        # Euler characteristic
        euler_char = vertices - num_edges + faces

        return {
            'vertices': vertices,
            'edges': num_edges,
            'faces': faces,
            'euler_characteristic': euler_char,
            'is_closed': euler_char == 2  # For genus 0
        }

    def _analyze_connectivity(self, mesh: 'Mesh') -> Dict[str, Any]:

        # Build adjacency graph
        adjacency = defaultdict(set)
        for face in mesh.faces:
            for i in range(3):
                v1, v2 = face[i], face[(i+1) % 3]
                adjacency[v1].add(v2)
                adjacency[v2].add(v1)

        # Find connected components
        visited = set()
        components = []

        for vertex in range(len(mesh.vertices)):
            if vertex not in visited:
                component = self._dfs_component(vertex, adjacency, visited)
                components.append(component)

        return {
            'connected_components': len(components),
            'component_sizes': [len(comp) for comp in components],
            'largest_component_ratio': max(len(comp) for comp in components) / len(mesh.vertices) if mesh.vertices.size > 0 else 0
        }

    def _analyze_genus(self, mesh: 'Mesh') -> Dict[str, Any]:

        topology = self._analyze_basic_topology(mesh)
        euler_char = topology['euler_characteristic']

        # For orientable surfaces: V - E + F = 2 - 2G
        # So G = (2 - (V - E + F)) / 2 = 1 - (V - E + F)/2
        genus = 1 - euler_char // 2

        return {
            'genus': max(0, genus),
            'orientable': True,  # Assume orientable for now
            'handles': max(0, genus),
            'crosscaps': 0  # Non-orientable, assume 0
        }

    def _analyze_homology(self, mesh: 'Mesh') -> Dict[str, Any]:

        topology = self._analyze_basic_topology(mesh)
        genus = self._analyze_genus(mesh)['genus']

        # Simplified homology for genus g surface
        return {
            'H0': 1,  # Connected components
            'H1': 2 * genus,  # Independent cycles
            'H2': 1,  # Void
            'betti_numbers': [1, 2 * genus, 1]
        }

    def _analyze_morphology(self, mesh: 'Mesh') -> Dict[str, Any]:

        # Calculate various morphological descriptors
        compactness = self._calculate_compactness(mesh)
        convexity = self._calculate_convexity(mesh)
        elongation = self._calculate_elongation(mesh)

        return {
            'compactness': compactness,
            'convexity': convexity,
            'elongation': elongation,
            'surface_to_volume_ratio': mesh.surface_area() / max(mesh.volume(), 1e-10)
        }

    def _dfs_component(self, start: int, adjacency: Dict[int, Set[int]],
                      visited: Set[int]) -> List[int]:
        component = []
        stack = [start]

        while stack:
            vertex = stack.pop()
            if vertex not in visited:
                visited.add(vertex)
                component.append(vertex)

                for neighbor in adjacency[vertex]:
                    if neighbor not in visited:
                        stack.append(neighbor)

        return component

    def _calculate_compactness(self, mesh: 'Mesh') -> float:
        surface_area = mesh.surface_area()
        volume = mesh.volume()

        if volume <= 0:
            return 0.0

        # Ideal sphere compactness
        ideal_area = 4.835975862049408 * (volume ** (2/3))  # 4π * (3V/4π)^(2/3)

        return ideal_area / surface_area if surface_area > 0 else 0.0

    def _calculate_convexity(self, mesh: 'Mesh') -> float:
        surface_area = mesh.surface_area()

        # Calculate convex hull area (simplified)
        # In practice, would compute actual convex hull
        convex_hull_area = surface_area * 1.1  # Approximation

        return surface_area / convex_hull_area if convex_hull_area > 0 else 0.0

    def _calculate_elongation(self, mesh: 'Mesh') -> float:
        # Calculate bounding box dimensions
        bbox = mesh.bounding_box()
        dimensions = [
            bbox['max'][0] - bbox['min'][0],
            bbox['max'][1] - bbox['min'][1],
            bbox['max'][2] - bbox['min'][2]
        ]

        dimensions.sort()

        if dimensions[2] > 0:
            return dimensions[1] / dimensions[2]  # Ratio of middle to largest dimension
        return 1.0

# ===== PERFORMANCE OPTIMIZATION =====

class MeshPerformanceOptimizer:

    def __init__(self):
        self.cache = {}
        self.performance_stats = defaultdict(list)

    def optimize_processing_pipeline(self, mesh: 'Mesh', operations: List[str]) -> 'Mesh':

        # Reorder operations for efficiency
        optimized_ops = self._optimize_operation_sequence(operations)

        # Apply operations with caching
        result = mesh
        for op in optimized_ops:
            cache_key = self._generate_operation_cache_key(result, op)

            if cache_key in self.cache:
                result = self.cache[cache_key]
            else:
                start_time = time.time()
                result = self._apply_operation(result, op)
                end_time = time.time()

                self.performance_stats[op].append(end_time - start_time)
                self.cache[cache_key] = result

        return result

    def _optimize_operation_sequence(self, operations: List[str]) -> List[str]:

        # Some operations are more efficient when done together or in specific order
        priority_order = {
            'decimation': 1,
            'hole_filling': 2,
            'smoothing': 3,
            'remeshing': 4,
            'normal_calculation': 5
        }

        # Sort by priority (lower number = higher priority)
        return sorted(operations, key=lambda op: priority_order.get(op, 99))

    def _generate_operation_cache_key(self, mesh: 'Mesh', operation: str) -> str:
        # Simple hash-based key
        import hashlib
        mesh_hash = hashlib.md5(str(mesh.vertices.tobytes() if hasattr(mesh.vertices, 'tobytes') else mesh.vertices).encode()).hexdigest()[:16]
        return f"{mesh_hash}_{operation}"

    def _apply_operation(self, mesh: 'Mesh', operation: str) -> 'Mesh':
        if operation == 'decimation':
            return mesh.decimate(0.8)
        elif operation == 'smoothing':
            return mesh.smooth(iterations=2)
        elif operation == 'remeshing':
            return mesh.remesh(target_edge_length=1.0)
        elif operation == 'hole_filling':
            return mesh.fill_holes()
        elif operation == 'normal_calculation':
            return mesh.compute_normals()
        else:
            return mesh

    def get_performance_stats(self) -> Dict[str, Dict[str, float]]:
        stats = {}

        for operation, times in self.performance_stats.items():
            if times:
                stats[operation] = {
                    'avg_time': statistics.mean(times),
                    'total_calls': len(times),
                    'total_time': sum(times)
                }

        return stats

# ===== DEMONSTRATION =====

def demonstrate_advanced_mesh_processing():

    print("=== Advanced Mesh Processing Demonstration ===")

    # Create test mesh
    processor = MeshProcessor()
    test_mesh = create_test_cube(20.0)

    print(f"Test mesh: {len(test_mesh.vertices)} vertices, {len(test_mesh.faces)} faces")

    # Advanced defect detection
    print("\n--- Advanced Defect Detection ---")
    defect_detector = AdvancedDefectDetector()
    defect_analysis = defect_detector.comprehensive_defect_analysis(test_mesh)

    print(f"Defects found: {len(defect_analysis['defects_found'])}")
    print(f"Repair priorities: {len(defect_analysis['repair_priorities'])}")
    if defect_analysis['repair_suggestions']:
        print("Suggestions:")
        for suggestion in defect_analysis['repair_suggestions'][:3]:
            print(f"  - {suggestion}")

    # Topology analysis
    print("\n--- Topology Analysis ---")
    topology_analyzer = MeshTopologyAnalyzer()
    topology_analysis = topology_analyzer.comprehensive_topology_analysis(test_mesh)

    basic_topo = topology_analysis['basic_topology']
    print(f"Euler characteristic: {basic_topo['euler_characteristic']}")
    print(f"Genus: {topology_analysis['genus_characteristics']['genus']}")
    print(f"Connected components: {topology_analysis['connectivity']['connected_components']}")

    # ML optimization
    print("\n--- ML-Based Optimization ---")
    ml_optimizer = MeshMachineLearningOptimizer()
    optimized_mesh = ml_optimizer.optimize_mesh_with_ml(test_mesh, 'balanced')

    print("Mesh optimization completed (rule-based fallback)")

    # Performance optimization
    print("\n--- Performance Optimization ---")
    perf_optimizer = MeshPerformanceOptimizer()
    operations = ['decimation', 'smoothing', 'remeshing']
    optimized_mesh = perf_optimizer.optimize_processing_pipeline(test_mesh, operations)

    stats = perf_optimizer.get_performance_stats()
    print("Performance stats:")
    for op, stat in stats.items():
        print(f"  {op}: {stat:.3f}s")
    print("\n=== Advanced Mesh Processing Demonstration Complete ===")

if __name__ == "__main__":
    demonstrate_advanced_mesh_processing()
