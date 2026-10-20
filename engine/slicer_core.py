#!/usr/bin/env python3
# ------------------------------------------------------------------
# Copyright (c) 2026 Sleia Engine Development Team.
# This file is distributed under the MIT License. See LICENSE.
#
# Sleia Easy v 1.0.1 - Thermoplastic Python Slicer
#
# File: slicer_core.py
# Description: core types and layer slicing.
# ------------------------------------------------------------------

import numpy as np
import logging
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import math
import time
from pathlib import Path
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InfillPattern(Enum):
    RECTILINEAR = "rectilinear"
    GRID = "grid"
    TRIANGULAR = "triangular"
    STARS = "stars"
    CUBIC = "cubic"
    LINE = "line"
    CONCENTRIC = "concentric"
    HONEYCOMB = "honeycomb"
    GYROID = "gyroid"
    HILBERT_CURVE = "hilbert_curve"
    ALIGNED_RECTILINEAR = "aligned_rectilinear"
    MONOTONIC = "monotonic"
    CROSS_HATCH = "cross_hatch"
    CROSS = "cross"
    TRI_HEXAGON = "tri_hexagon"
    HONEYCOMB_3D = "honeycomb_3d"
    ADAPTIVE_CUBIC = "adaptive_cubic"
    SUPPORT_CUBIC = "support_cubic"
    TETRAHEDRAL = "tetrahedral"
    OCTET = "octet"
    SPIRAL = "spiral"
    ARCHIMEDEAN_CHORDS = "archimedean_chords"
    OCTAGRAM_SPIRAL = "octagram_spiral"
    LIGHTNING = "lightning"
    WAVES = "waves"
    ZIGZAG = "zigzag"
    VORONOI = "voronoi"

class SupportType(Enum):
    NONE = "none"
    EVERYWHERE = "everywhere"
    BUILD_PLATE_ONLY = "build_plate_only"
    TREE = "tree"

@dataclass
class PrintSettings:
    # Layer settings
    layer_height: float = 0.2
    first_layer_height: float = 0.3

    # Perimeters
    perimeters: int = 2
    external_perimeter_speed: float = 50.0
    perimeter_speed: float = 60.0
    order_of_walls: str = "inner-outer"
    detect_thin_walls: bool = False
    seam_position: str = "aligned"
    staggered_inner_seams: bool = False
    seam_gap: float = 0.0
    wipe_on_loops: bool = False
    wipe_speed: float = 80.0

    # Infill
    fill_density: float = 0.15  # 15%
    fill_pattern: InfillPattern = InfillPattern.RECTILINEAR
    infill_speed: float = 80.0
    top_surface_pattern: str = "concentric"
    top_shell_layers: int = 3
    top_shell_thickness: float = 0.60
    bottom_surface_pattern: str = "rectilinear"
    bottom_shell_layers: int = 3
    bottom_shell_thickness: float = 0.60
    enable_ironing: bool = False
    ironing_surface: str = "top"
    ironing_speed: float = 20.0
    ironing_flow: float = 10.0

    # Support
    support_material: bool = False
    support_type: SupportType = SupportType.BUILD_PLATE_ONLY
    support_angle: float = 60.0
    support_interface_layers: int = 3
    support_density: float = 0.15
    support_infill_pattern: str = "rectilinear"
    on_build_plate_only: bool = False
    remove_small_overhangs: bool = False

    # Speed settings
    travel_speed: float = 120.0
    first_layer_speed: float = 30.0
    print_speed: float = 50.0
    min_layer_time: float = 10.0
    slow_down_layers: bool = True
    fan_speed: float = 100.0

    # Temperature settings
    nozzle_temperature: float = 210.0
    bed_temperature: float = 60.0
    first_layer_nozzle_temp: float = 215.0
    first_layer_bed_temp: float = 65.0

    # Extrusion settings (legacy single-extruder, kept for compatibility)
    extrusion_width: float = 0.45
    default_line_width: float = 0.42
    first_layer_line_width: float = 0.50
    outer_wall_line_width: float = 0.42
    inner_wall_line_width: float = 0.45
    sparse_infill_line_width: float = 0.45
    support_line_width: float = 0.40
    nozzle_diameter: float = 0.4
    filament_diameter: float = 1.75
    extrusion_multiplier: float = 1.0

    # Retraction (legacy single-extruder, kept for compatibility)
    retract_length: float = 2.0
    retract_speed: float = 40.0
    retract_restart_extra: float = 0.0
    retract_before_travel: float = 2.0
    wipe_distance: float = 0.0

    # Print bed
    bed_size: Tuple[float, float] = (220.0, 220.0)
    print_center: Tuple[float, float] = (110.0, 110.0)

    # Adaptive layer height (Basic Layers tab)
    adaptive_layer_height_enabled: bool = False
    adaptive_min_layer_height: float = 0.05
    adaptive_max_layer_height: float = 0.3
    adaptive_base_layer_height: float = 0.2
    adaptive_quality_level: str = "standard"
    adaptive_curvature_threshold: float = 0.1
    adaptive_detail_threshold: float = 0.5
    adaptive_smoothing_iterations: int = 3

    adhesion_type: str = "skirt"
    skirt_enabled: bool = True
    skirt_distance: float = 2.0
    skirt_lines: int = 2
    skirt_height: int = 1
    skirt_speed: float = 50.0
    skirt_extrusion_width: float = 0.4
    brim_enabled: bool = False
    brim_type: str = "outer-only"
    brim_width: float = 5.0
    brim_object_gap: float = 0.15
    brim_lines: int = 3
    brim_speed: float = 60.0
    brim_extrusion_width: float = 0.4
    raft_enabled: bool = False
    raft_layers: int = 3
    raft_layer_height: float = 0.3
    raft_air_gap: float = 0.25
    raft_extra_margin: float = 3.0
    raft_speed: float = 60.0
    timelapse_type: str = "off"
    timelapse_interval_s: float = 10.0
    filament_density: float = 1.24
    start_gcode: str = ""
    end_gcode: str = ""
    before_layer_change_gcode: str = ""
    layer_change_gcode: str = ""
    tool_change_gcode: str = ""
    gcode_flavor: str = "marlin-legacy"
    use_relative_e_distances: bool = False
    use_firmware_retraction: bool = False
    printable_height: float = 250.0

    # Cooling (Basic Motion tab)
    fan_enabled: bool = True
    fan_max_speed: float = 100.0
    fan_default_speed: float = 50.0

@dataclass
class Point2D:
    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y
    
    def __add__(self, other):
        return Point2D(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Point2D(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar):
        return Point2D(self.x * scalar, self.y * scalar)
    
    def distance(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def normalize(self):
        length = math.sqrt(self.x**2 + self.y**2)
        if length > 0:
            return Point2D(self.x / length, self.y / length)
        return Point2D(0, 0)

@dataclass
class Point3D:
    x: float
    y: float
    z: float
    
    def __add__(self, other):
        return Point3D(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return Point3D(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar):
        return Point3D(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def distance(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)

@dataclass
class Triangle:
    vertices: Tuple[Point3D, Point3D, Point3D]
    normal: Point3D

@dataclass
class LayerPolygon:
    points: List[Point2D] = field(default_factory=list)
    is_hole: bool = False
    
    def area(self) -> float:
        if len(self.points) < 3:
            return 0.0
        
        area = 0.0
        n = len(self.points)
        for i in range(n):
            j = (i + 1) % n
            area += self.points[i].x * self.points[j].y
            area -= self.points[j].x * self.points[i].y
        return abs(area) / 2.0
    
    def is_clockwise(self) -> bool:
        signed_area = 0.0
        n = len(self.points)
        for i in range(n):
            j = (i + 1) % n
            signed_area += (self.points[j].x - self.points[i].x) * (self.points[j].y + self.points[i].y)
        return signed_area > 0
    
    def reverse(self):
        self.points.reverse()

@dataclass
class Layer:
    z_height: float
    polygons: List[LayerPolygon] = field(default_factory=list)
    support_polygons: List[LayerPolygon] = field(default_factory=list)
    
    def add_polygon(self, polygon: LayerPolygon):
        self.polygons.append(polygon)
    
    def add_support_polygon(self, polygon: LayerPolygon):
        self.support_polygons.append(polygon)

@dataclass
class SlicedModel:
    layers: List[Layer] = field(default_factory=list)
    settings: PrintSettings = field(default_factory=PrintSettings)
    adhesion_paths: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_layer(self, layer: Layer):
        self.layers.append(layer)
    
    def get_layer_count(self) -> int:
        return len(self.layers)
    
    def get_print_time_estimate(self) -> float:
        total_time = 0.0
        for layer in self.layers:
            # Simplified calculation - would need path analysis for accuracy
            layer_time = len(layer.polygons) * 2.0  # Rough estimate
            total_time += layer_time
        return total_time
    
    def get_material_usage(self) -> float:
        total_volume = 0.0
        for layer in self.layers:
            layer_volume = 0.0
            for polygon in layer.polygons:
                layer_volume += polygon.area() * self.settings.layer_height
            total_volume += layer_volume
        return total_volume

# ===== ADVANCED SLICING ALGORITHMS =====

class AdaptiveSlicingEngine:

    def __init__(self, settings: PrintSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)

    def compute_adaptive_layers(self, mesh_vertices: np.ndarray,
                               mesh_faces: np.ndarray) -> List[float]:

        # Calculate model bounds
        min_z, max_z = np.min(mesh_vertices[:, 2]), np.max(mesh_vertices[:, 2])

        # Analyze surface curvature and detail
        curvature_map = self._analyze_surface_curvature(mesh_vertices, mesh_faces)
        detail_map = self._analyze_surface_detail(mesh_vertices, mesh_faces)

        # Generate adaptive layer heights
        layers = []
        current_z = min_z + self.settings.first_layer_height
        layers.append(current_z)

        while current_z < max_z:
            # Determine optimal layer height for current region
            optimal_height = self._compute_optimal_layer_height(
                current_z, curvature_map, detail_map, mesh_vertices, mesh_faces
            )

            # Apply constraints
            optimal_height = np.clip(
                optimal_height,
                self.settings.adaptive_min_layer_height,
                self.settings.adaptive_max_layer_height
            )

            current_z += optimal_height

            if current_z < max_z:
                layers.append(current_z)

        return layers

    def _analyze_surface_curvature(self, vertices: np.ndarray,
                                  faces: np.ndarray) -> Dict[float, float]:
        curvature_map = {}

        # Sample Z heights
        min_z, max_z = np.min(vertices[:, 2]), np.max(vertices[:, 2])
        z_samples = np.linspace(min_z, max_z, 100)

        for z in z_samples:
            # Get intersection points at this height
            intersections = self._get_plane_intersections(vertices, faces, z)

            if len(intersections) >= 3:
                # Calculate curvature metrics
                curvature = self._calculate_contour_curvature(intersections)
                curvature_map[z] = curvature

        return curvature_map

    def _analyze_surface_detail(self, vertices: np.ndarray,
                               faces: np.ndarray) -> Dict[float, float]:
        detail_map = {}

        # Use multiple sampling heights
        min_z, max_z = np.min(vertices[:, 2]), np.max(vertices[:, 2])
        z_samples = np.linspace(min_z, max_z, 50)

        for z in z_samples:
            intersections = self._get_plane_intersections(vertices, faces, z)

            if len(intersections) >= 6:
                # Calculate detail metrics
                detail_score = self._calculate_detail_complexity(intersections)
                detail_map[z] = detail_score

        return detail_map

    def _compute_optimal_layer_height(self, z: float, curvature_map: Dict,
                                    detail_map: Dict, vertices: np.ndarray,
                                    faces: np.ndarray) -> float:

        # Base layer height
        base_height = self.settings.adaptive_base_layer_height

        # Adjust for curvature
        curvature_factor = 1.0
        if curvature_map:
            nearest_curvatures = self._find_nearest_values(curvature_map, z, 5)
            avg_curvature = np.mean(nearest_curvatures)
            curvature_factor = 1.0 - (avg_curvature * 0.5)  # Reduce height for high curvature

        # Adjust for detail
        detail_factor = 1.0
        if detail_map:
            nearest_details = self._find_nearest_values(detail_map, z, 3)
            avg_detail = np.mean(nearest_details)
            detail_factor = 1.0 - (avg_detail * 0.3)  # Reduce height for high detail

        # Combine factors
        optimal_height = base_height * curvature_factor * detail_factor

        # Smooth transitions between layers
        optimal_height = self._smooth_layer_transitions(optimal_height, z)

        return optimal_height

    def _get_plane_intersections(self, vertices: np.ndarray,
                               faces: np.ndarray, z: float) -> List[Point2D]:
        intersections = []

        for face in faces:
            v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]

            # Check each edge
            edges = [(v0, v1), (v1, v2), (v2, v0)]
            for edge_start, edge_end in edges:
                if self._edge_intersects_plane(edge_start, edge_end, z):
                    intersection = self._find_plane_intersection(edge_start, edge_end, z)
                    if intersection:
                        intersections.append(Point2D(intersection[0], intersection[1]))

        return intersections

    def _calculate_contour_curvature(self, points: List[Point2D]) -> float:
        if len(points) < 3:
            return 0.0

        # Sort points by angle from centroid
        centroid = self._calculate_centroid(points)
        angles = []
        for point in points:
            angle = math.atan2(point.y - centroid.y, point.x - centroid.x)
            angles.append((angle, point))

        angles.sort(key=lambda x: x[0])

        # Calculate curvature using discrete derivatives
        curvatures = []
        n = len(angles)

        for i in range(n):
            p0 = angles[(i-1) % n][1]
            p1 = angles[i][1]
            p2 = angles[(i+1) % n][1]

            # Calculate local curvature
            curvature = self._calculate_local_curvature(p0, p1, p2)
            curvatures.append(abs(curvature))

        return np.mean(curvatures) if curvatures else 0.0

    def _calculate_local_curvature(self, p0: Point2D, p1: Point2D, p2: Point2D) -> float:
        # Use Menger curvature (circumcircle method)
        a = math.sqrt((p1.x - p0.x)**2 + (p1.y - p0.y)**2)
        b = math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)
        c = math.sqrt((p2.x - p0.x)**2 + (p2.y - p0.y)**2)

        # Check for collinear points
        if abs(a + b - c) < 1e-10 or abs(a + c - b) < 1e-10 or abs(b + c - a) < 1e-10:
            return 0.0

        # Calculate circumradius
        s = (a + b + c) / 2
        area = math.sqrt(s * (s - a) * (s - b) * (s - c))

        if area < 1e-10:
            return 0.0

        circumradius = (a * b * c) / (4 * area)

        # Curvature is 1/radius
        return 1.0 / circumradius if circumradius > 0 else 0.0

    def _calculate_detail_complexity(self, points: List[Point2D]) -> float:
        if len(points) < 6:
            return 0.0

        # Calculate variance in point distribution
        x_coords = [p.x for p in points]
        y_coords = [p.y for p in points]

        x_variance = np.var(x_coords)
        y_variance = np.var(y_coords)

        # Calculate point density variation
        centroid = self._calculate_centroid(points)
        distances = [math.sqrt((p.x - centroid.x)**2 + (p.y - centroid.y)**2) for p in points]
        distance_variance = np.var(distances)

        # Combine metrics
        complexity = (x_variance + y_variance + distance_variance) / 3.0

        # Normalize to 0-1 range
        return min(complexity / 1000.0, 1.0)

    def _calculate_centroid(self, points: List[Point2D]) -> Point2D:
        if not points:
            return Point2D(0, 0)

        x_sum = sum(p.x for p in points)
        y_sum = sum(p.y for p in points)

        return Point2D(x_sum / len(points), y_sum / len(points))

    def _find_nearest_values(self, value_map: Dict[float, float],
                           target_z: float, count: int) -> List[float]:
        distances = [(abs(z - target_z), value) for z, value in value_map.items()]
        distances.sort(key=lambda x: x[0])

        return [d[1] for d in distances[:count]] if distances else []

    def _smooth_layer_transitions(self, height: float, z: float) -> float:
        # Simple smoothing - could be enhanced with more sophisticated algorithms
        max_change = self.settings.adaptive_base_layer_height * 0.5

        # In practice, this would compare with previous layer height
        # For now, apply basic constraints
        return np.clip(height, 0.05, self.settings.adaptive_max_layer_height)

class MultiThreadedSlicer:

    def __init__(self, settings: PrintSettings, max_threads: int = None):
        self.settings = settings
        self.max_threads = max_threads or mp.cpu_count()
        self.logger = logging.getLogger(__name__)

    def slice_parallel(self, mesh_vertices: np.ndarray,
                      mesh_faces: np.ndarray, layer_heights: List[float]) -> SlicedModel:

        sliced_model = SlicedModel(settings=self.settings)

        # Divide layers among threads
        layer_chunks = self._divide_layers(layer_heights, self.max_threads)

        # Process chunks in parallel
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = []

            for chunk in layer_chunks:
                future = executor.submit(self._process_layer_chunk,
                                       mesh_vertices, mesh_faces, chunk)
                futures.append(future)

            # Collect results
            layer_results = []
            for future in futures:
                chunk_result = future.result()
                layer_results.extend(chunk_result)

        # Sort layers by height and add to model
        layer_results.sort(key=lambda l: l.z_height)
        for layer in layer_results:
            sliced_model.add_layer(layer)

        return sliced_model

    def _divide_layers(self, layer_heights: List[float], num_chunks: int) -> List[List[float]]:
        if len(layer_heights) <= num_chunks:
            return [[h] for h in layer_heights]

        chunk_size = len(layer_heights) // num_chunks
        chunks = []

        for i in range(num_chunks):
            start_idx = i * chunk_size
            if i == num_chunks - 1:
                end_idx = len(layer_heights)
            else:
                end_idx = (i + 1) * chunk_size

            chunks.append(layer_heights[start_idx:end_idx])

        return chunks

    def _process_layer_chunk(self, vertices: np.ndarray, faces: np.ndarray,
                           layer_chunk: List[float]) -> List[Layer]:
        layers = []

        for z_height in layer_chunk:
            layer = Layer(z_height=z_height)

            # Generate layer slice
            polygons = self._slice_at_height(vertices, faces, z_height)

            for polygon in polygons:
                layer.add_polygon(polygon)

            # Add support if enabled
            if self.settings.support_material:
                support_polygons = self._generate_support_for_layer(layer, None)
                for support_polygon in support_polygons:
                    layer.add_support_polygon(support_polygon)

            layers.append(layer)

        return layers

    def _slice_at_height(self, vertices: np.ndarray, faces: np.ndarray,
                        z: float) -> List[LayerPolygon]:
        polygons = []
        intersecting_points = []
        
        # Find all edges that intersect the slicing plane
        for face in faces:
            v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
            
            # Check each edge of the triangle
            edges = [(v0, v1), (v1, v2), (v2, v0)]
            
            for edge_start, edge_end in edges:
                if self._edge_intersects_plane(edge_start, edge_end, z):
                    intersection = self._find_plane_intersection(edge_start, edge_end, z)
                    if intersection is not None:
                        intersecting_points.append(intersection)
        
        # Group points into closed contours to form polygons
        if len(intersecting_points) >= 3:
            # Remove duplicate points (within tolerance)
            unique_points = self._remove_duplicate_points(intersecting_points, tolerance=1e-6)
            
            # Try to form closed polygons from the intersection points
            # This is a simplified approach - for production, use proper contour tracing
            if len(unique_points) >= 3:
                # Sort points to form a reasonable polygon (simple approach)
                # In production, this should use proper contour tracing algorithms
                sorted_points = self._sort_points_for_polygon(unique_points)
                
                if len(sorted_points) >= 3:
                    polygon_points = [Point2D(p[0], p[1]) for p in sorted_points]
                    polygon = LayerPolygon(points=polygon_points, is_hole=False)
                    polygons.append(polygon)
        
        return polygons
    
    def _remove_duplicate_points(self, points: List[Tuple[float, float]], tolerance: float) -> List[Tuple[float, float]]:
        unique = []
        for point in points:
            is_duplicate = False
            for existing in unique:
                dist = math.sqrt((point[0] - existing[0])**2 + (point[1] - existing[1])**2)
                if dist < tolerance:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique.append(point)
        return unique
    
    def _sort_points_for_polygon(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        if len(points) < 3:
            return points
        
        # Find centroid
        cx = sum(p[0] for p in points) / len(points)
        cy = sum(p[1] for p in points) / len(points)
        
        # Sort by angle from centroid
        def angle_from_center(point):
            dx = point[0] - cx
            dy = point[1] - cy
            return math.atan2(dy, dx)
        
        sorted_points = sorted(points, key=angle_from_center)
        return sorted_points

    def _edge_intersects_plane(self, v0: np.ndarray, v1: np.ndarray, z: float) -> bool:
        return (v0[2] <= z <= v1[2]) or (v1[2] <= z <= v0[2])

    def _find_plane_intersection(self, v0: np.ndarray, v1: np.ndarray, z: float):
        if abs(v1[2] - v0[2]) < 1e-10:
            return None

        t = (z - v0[2]) / (v1[2] - v0[2])
        if 0.0 <= t <= 1.0:
            x = v0[0] + t * (v1[0] - v0[0])
            y = v0[1] + t * (v1[1] - v0[1])
            return (x, y)
        return None

    def _generate_support_for_layer(self, layer: Layer, previous_layer: Layer):
        return []  # Placeholder

class QualityOptimizationEngine:

    def __init__(self, settings: PrintSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)

    def optimize_slicing_parameters(self, mesh_info: Dict) -> PrintSettings:

        optimized_settings = PrintSettings()
        # Copy current settings
        for field in PrintSettings.__dataclass_fields__:
            if hasattr(self.settings, field):
                setattr(optimized_settings, field, getattr(self.settings, field))

        # Analyze mesh characteristics
        volume = mesh_info.get('volume', 0)
        surface_area = mesh_info.get('surface_area', 0)
        complexity = mesh_info.get('complexity_score', 0.5)
        min_feature_size = mesh_info.get('min_feature_size', 1.0)

        # Optimize layer height based on model size and features
        if volume < 1000:  # Small model
            optimized_settings.layer_height = min(0.1, min_feature_size / 10)
        elif volume > 100000:  # Large model
            optimized_settings.layer_height = max(0.2, min_feature_size / 5)
        else:
            optimized_settings.layer_height = min_feature_size / 8

        # Optimize infill density based on strength requirements
        if complexity > 0.8:  # Complex model needs more support
            optimized_settings.fill_density = min(0.25, optimized_settings.fill_density + 0.05)
        elif complexity < 0.3:  # Simple model can use less
            optimized_settings.fill_density = max(0.1, optimized_settings.fill_density - 0.05)

        # Optimize perimeter count
        if min_feature_size < 1.0:  # Fine details
            optimized_settings.perimeters = min(4, optimized_settings.perimeters + 1)
        elif min_feature_size > 5.0:  # Large features
            optimized_settings.perimeters = max(2, optimized_settings.perimeters - 1)

        # Optimize speeds based on quality requirements
        quality_factor = self._calculate_quality_factor(mesh_info)

        optimized_settings.perimeter_speed *= quality_factor
        optimized_settings.infill_speed *= quality_factor
        optimized_settings.travel_speed *= (1 + quality_factor) / 2

        return optimized_settings

    def _calculate_quality_factor(self, mesh_info: Dict) -> float:
        complexity = mesh_info.get('complexity_score', 0.5)
        min_feature = mesh_info.get('min_feature_size', 1.0)

        # Higher complexity and smaller features require slower speeds
        complexity_factor = 1.0 - (complexity * 0.3)
        feature_factor = min(1.0, min_feature / 0.5)

        return (complexity_factor + feature_factor) / 2.0

class AdvancedMeshAnalyzer:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze_mesh_comprehensive(self, vertices: np.ndarray,
                                  faces: np.ndarray) -> Dict[str, Any]:

        analysis = {
            'basic_stats': self._calculate_basic_stats(vertices, faces),
            'geometric_properties': self._calculate_geometric_properties(vertices, faces),
            'quality_metrics': self._calculate_quality_metrics(vertices, faces),
            'printability_analysis': self._analyze_printability(vertices, faces),
            'optimization_suggestions': []
        }

        # Generate optimization suggestions
        analysis['optimization_suggestions'] = self._generate_optimization_suggestions(analysis)

        return analysis

    def _calculate_basic_stats(self, vertices: np.ndarray, faces: np.ndarray) -> Dict[str, Any]:
        return {
            'vertex_count': len(vertices),
            'face_count': len(faces),
            'edge_count': self._count_edges(faces),
            'volume': self._calculate_volume(vertices, faces),
            'surface_area': self._calculate_surface_area(vertices, faces),
            'bounding_box': self._calculate_bounding_box(vertices),
            'aspect_ratio': self._calculate_aspect_ratio(vertices)
        }

    def _calculate_geometric_properties(self, vertices: np.ndarray,
                                       faces: np.ndarray) -> Dict[str, Any]:
        return {
            'center_of_mass': self._calculate_center_of_mass(vertices, faces),
            'moment_of_inertia': self._calculate_moment_of_inertia(vertices, faces),
            'principal_axes': self._calculate_principal_axes(vertices),
            'convex_hull_volume': self._calculate_convex_hull_volume(vertices),
            'genus': self._calculate_genus(faces)
        }

    def _calculate_quality_metrics(self, vertices: np.ndarray,
                                  faces: np.ndarray) -> Dict[str, Any]:
        return {
            'aspect_ratios': self._calculate_face_aspect_ratios(vertices, faces),
            'angle_variations': self._calculate_angle_variations(vertices, faces),
            'edge_length_distribution': self._calculate_edge_length_distribution(vertices, faces),
            'warpage_measure': self._calculate_warpage_measure(vertices, faces),
            'complexity_score': self._calculate_complexity_score(vertices, faces)
        }

    def _analyze_printability(self, vertices: np.ndarray, faces: np.ndarray) -> Dict[str, Any]:
        return {
            'overhang_analysis': self._analyze_overhangs(vertices, faces),
            'thin_wall_detection': self._detect_thin_walls(vertices, faces),
            'bridge_detection': self._detect_bridges(vertices, faces),
            'support_requirements': self._estimate_support_requirements(vertices, faces),
            'print_orientation_suggestions': self._suggest_print_orientations(vertices, faces)
        }

    def _count_edges(self, faces: np.ndarray) -> int:
        edges = set()
        for face in faces:
            for i in range(3):
                edge = tuple(sorted([face[i], face[(i + 1) % 3]]))
                edges.add(edge)
        return len(edges)

    def _calculate_volume(self, vertices: np.ndarray, faces: np.ndarray) -> float:
        volume = 0.0
        for face in faces:
            v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
            volume += self._tetrahedron_volume(v0, v1, v2)
        return abs(volume)

    def _tetrahedron_volume(self, v0: np.ndarray, v1: np.ndarray, v2: np.ndarray) -> float:
        return np.dot(v0, np.cross(v1, v2)) / 6.0

    def _calculate_surface_area(self, vertices: np.ndarray, faces: np.ndarray) -> float:
        area = 0.0
        for face in faces:
            v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
            area += self._triangle_area(v0, v1, v2)
        return area

    def _triangle_area(self, v0: np.ndarray, v1: np.ndarray, v2: np.ndarray) -> float:
        cross = np.cross(v1 - v0, v2 - v0)
        return np.linalg.norm(cross) / 2.0

    def _calculate_bounding_box(self, vertices: np.ndarray) -> Dict[str, np.ndarray]:
        min_coords = np.min(vertices, axis=0)
        max_coords = np.max(vertices, axis=0)

        return {
            'min': min_coords,
            'max': max_coords,
            'size': max_coords - min_coords,
            'center': (min_coords + max_coords) / 2
        }

    def _calculate_aspect_ratio(self, vertices: np.ndarray) -> float:
        bbox = self._calculate_bounding_box(vertices)
        size = bbox['size']
        return max(size) / min(size) if min(size) > 0 else float('inf')

    def _calculate_center_of_mass(self, vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
        total_volume = 0.0
        weighted_sum = np.zeros(3)

        for face in faces:
            v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
            volume = self._tetrahedron_volume(v0, v1, v2)
            centroid = (v0 + v1 + v2) / 3.0

            total_volume += volume
            weighted_sum += volume * centroid

        return weighted_sum / total_volume if total_volume != 0 else np.zeros(3)

    def _calculate_moment_of_inertia(self, vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
        # Simplified calculation - full implementation would be more complex
        com = self._calculate_center_of_mass(vertices, faces)
        I = np.zeros((3, 3))

        for face in faces:
            v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]

            # Translate to center of mass
            v0_cm = v0 - com
            v1_cm = v1 - com
            v2_cm = v2 - com

            # Add contribution to moment of inertia
            # This is a simplified version
            for vi in [v0_cm, v1_cm, v2_cm]:
                I[0, 0] += vi[1]**2 + vi[2]**2
                I[1, 1] += vi[0]**2 + vi[2]**2
                I[2, 2] += vi[0]**2 + vi[1]**2
                I[0, 1] -= vi[0] * vi[1]
                I[0, 2] -= vi[0] * vi[2]
                I[1, 2] -= vi[1] * vi[2]

        # Symmetrize
        I[1, 0] = I[0, 1]
        I[2, 0] = I[0, 2]
        I[2, 1] = I[1, 2]

        return I

    def _calculate_principal_axes(self, vertices: np.ndarray) -> np.ndarray:
        # Center the points
        centered = vertices - np.mean(vertices, axis=0)

        # Calculate covariance matrix
        cov = np.cov(centered.T)

        # Find eigenvalues and eigenvectors
        eigenvalues, eigenvectors = np.linalg.eigh(cov)

        # Sort by eigenvalues (largest first)
        idx = np.argsort(eigenvalues)[::-1]
        return eigenvectors[:, idx]

    def _calculate_convex_hull_volume(self, vertices: np.ndarray) -> float:
        try:
            from scipy.spatial import ConvexHull
            hull = ConvexHull(vertices)
            return hull.volume
        except:
            # Fallback: approximate with bounding box
            bbox = self._calculate_bounding_box(vertices)
            return np.prod(bbox['size'])

    def _calculate_genus(self, faces: np.ndarray) -> int:
        v = len(set(faces.flatten()))  # Unique vertices
        e = self._count_edges(faces)
        f = len(faces)

        # Euler characteristic: V - E + F = 2 - 2G (for orientable surfaces)
        euler_char = v - e + f

        # Approximate genus (this is simplified)
        return max(0, (2 - euler_char) // 2)

    def _calculate_face_aspect_ratios(self, vertices: np.ndarray, faces: np.ndarray) -> List[float]:
        ratios = []

        for face in faces:
            v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]

            # Calculate edge lengths
            e0 = np.linalg.norm(v1 - v0)
            e1 = np.linalg.norm(v2 - v1)
            e2 = np.linalg.norm(v0 - v2)

            # Aspect ratio: longest edge / shortest edge
            if min(e0, e1, e2) > 0:
                ratio = max(e0, e1, e2) / min(e0, e1, e2)
                ratios.append(ratio)

        return ratios

    def _calculate_angle_variations(self, vertices: np.ndarray, faces: np.ndarray) -> List[float]:
        angles = []

        for face in faces:
            v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]

            # Calculate angles at each vertex
            for i in range(3):
                va = vertices[face[i]]
                vb = vertices[face[(i + 1) % 3]]
                vc = vertices[face[(i + 2) % 3]]

                # Vectors from vertex
                vab = vb - va
                vac = vc - va

                # Angle between vectors
                cos_angle = np.dot(vab, vac) / (np.linalg.norm(vab) * np.linalg.norm(vac))
                cos_angle = np.clip(cos_angle, -1, 1)
                angle = np.arccos(cos_angle)
                angles.append(angle)

        return angles

    def _calculate_edge_length_distribution(self, vertices: np.ndarray, faces: np.ndarray) -> Dict[str, float]:
        lengths = []

        edges = set()
        for face in faces:
            for i in range(3):
                edge = tuple(sorted([face[i], face[(i + 1) % 3]]))
                if edge not in edges:
                    edges.add(edge)
                    v0, v1 = vertices[edge[0]], vertices[edge[1]]
                    length = np.linalg.norm(v1 - v0)
                    lengths.append(length)

        if not lengths:
            return {'mean': 0, 'std': 0, 'min': 0, 'max': 0}

        return {
            'mean': np.mean(lengths),
            'std': np.std(lengths),
            'min': np.min(lengths),
            'max': np.max(lengths)
        }

    def _calculate_warpage_measure(self, vertices: np.ndarray, faces: np.ndarray) -> float:
        # Simplified warpage calculation
        total_warpage = 0.0
        count = 0

        for face in faces:
            v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]

            # Calculate normal
            normal = np.cross(v1 - v0, v2 - v0)
            normal_length = np.linalg.norm(normal)

            if normal_length > 0:
                normal = normal / normal_length

                # Check angle with adjacent faces
                # This is simplified - full implementation would check all adjacent faces
                total_warpage += abs(normal[2])  # Favor faces perpendicular to Z
                count += 1

        return total_warpage / count if count > 0 else 0.0

    def _calculate_complexity_score(self, vertices: np.ndarray, faces: np.ndarray) -> float:
        # Combine various metrics
        aspect_ratios = self._calculate_face_aspect_ratios(vertices, faces)
        edge_stats = self._calculate_edge_length_distribution(vertices, faces)

        complexity = 0.0

        # Aspect ratio complexity
        if aspect_ratios:
            avg_aspect = np.mean(aspect_ratios)
            complexity += min(avg_aspect / 5.0, 1.0) * 0.3

        # Edge length variation complexity
        if edge_stats['std'] > 0:
            cv = edge_stats['std'] / edge_stats['mean']  # Coefficient of variation
            complexity += min(cv, 1.0) * 0.3

        # Size complexity
        size_complexity = min(len(vertices) / 10000, 1.0)
        complexity += size_complexity * 0.4

        return complexity

    def _analyze_overhangs(self, vertices: np.ndarray, faces: np.ndarray) -> Dict[str, Any]:
        overhang_faces = []
        overhang_angles = []

        for face in faces:
            v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]

            # Calculate face normal
            normal = np.cross(v1 - v0, v2 - v0)
            normal_length = np.linalg.norm(normal)

            if normal_length > 0:
                normal = normal / normal_length

                # Calculate angle with vertical (Z-axis)
                angle_with_vertical = np.arccos(abs(normal[2]))
                angle_degrees = np.degrees(angle_with_vertical)

                if angle_degrees > 45:  # Overhang threshold
                    overhang_faces.append(face)
                    overhang_angles.append(angle_degrees)

        return {
            'overhang_face_count': len(overhang_faces),
            'overhang_percentage': len(overhang_faces) / len(faces) if faces.size > 0 else 0,
            'max_overhang_angle': max(overhang_angles) if overhang_angles else 0,
            'avg_overhang_angle': np.mean(overhang_angles) if overhang_angles else 0
        }

    def _detect_thin_walls(self, vertices: np.ndarray, faces: np.ndarray) -> List[Dict]:
        # Simplified thin wall detection
        thin_walls = []

        # Sample points and check local thickness
        # This is a placeholder - real implementation would be more sophisticated
        return thin_walls

    def _detect_bridges(self, vertices: np.ndarray, faces: np.ndarray) -> List[Dict]:
        # Simplified bridge detection
        bridges = []

        # Look for faces with no supporting geometry below
        # This is a placeholder - real implementation would be more sophisticated
        return bridges

    def _estimate_support_requirements(self, vertices: np.ndarray, faces: np.ndarray) -> Dict[str, Any]:
        overhang_analysis = self._analyze_overhangs(vertices, faces)

        return {
            'support_percentage': overhang_analysis['overhang_percentage'],
            'estimated_support_volume': overhang_analysis['overhang_face_count'] * 10,  # Rough estimate
            'support_complexity': 'high' if overhang_analysis['overhang_percentage'] > 0.3 else 'medium' if overhang_analysis['overhang_percentage'] > 0.1 else 'low'
        }

    def _suggest_print_orientations(self, vertices: np.ndarray, faces: np.ndarray) -> List[Dict]:
        suggestions = []

        # Analyze different orientations
        for axis in ['x', 'y', 'z']:
            for angle in [0, 90, 180, 270]:
                # Rotate and analyze
                rotated_vertices = self._rotate_mesh(vertices, axis, angle)
                overhang_analysis = self._analyze_overhangs(rotated_vertices, faces)
                support_req = self._estimate_support_requirements(rotated_vertices, faces)

                suggestions.append({
                    'axis': axis,
                    'angle': angle,
                    'overhang_percentage': overhang_analysis['overhang_percentage'],
                    'support_volume': support_req['estimated_support_volume'],
                    'score': 1.0 - overhang_analysis['overhang_percentage']  # Higher score = better
                })

        # Sort by score
        suggestions.sort(key=lambda x: x['score'], reverse=True)

        return suggestions[:5]  # Return top 5 suggestions

    def _rotate_mesh(self, vertices: np.ndarray, axis: str, angle: float) -> np.ndarray:
        angle_rad = np.radians(angle)
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)

        rotated = vertices.copy()

        if axis == 'x':
            rotated[:, 1], rotated[:, 2] = (rotated[:, 1] * cos_a - rotated[:, 2] * sin_a,
                                           rotated[:, 1] * sin_a + rotated[:, 2] * cos_a)
        elif axis == 'y':
            rotated[:, 0], rotated[:, 2] = (rotated[:, 0] * cos_a + rotated[:, 2] * sin_a,
                                           -rotated[:, 0] * sin_a + rotated[:, 2] * cos_a)
        elif axis == 'z':
            rotated[:, 0], rotated[:, 1] = (rotated[:, 0] * cos_a - rotated[:, 1] * sin_a,
                                           rotated[:, 0] * sin_a + rotated[:, 1] * cos_a)

        return rotated

    def _generate_optimization_suggestions(self, analysis: Dict[str, Any]) -> List[str]:
        suggestions = []

        quality_metrics = analysis.get('quality_metrics', {})
        printability = analysis.get('printability_analysis', {})

        # Aspect ratio suggestions
        aspect_ratios = quality_metrics.get('aspect_ratios', [])
        if aspect_ratios and np.mean(aspect_ratios) > 3.0:
            suggestions.append("Consider remeshing to improve face aspect ratios")

        # Overhang suggestions
        overhang_analysis = printability.get('overhang_analysis', {})
        if overhang_analysis.get('overhang_percentage', 0) > 0.2:
            suggestions.append("High overhang percentage detected - consider using supports or reorienting model")

        # Thin wall suggestions
        thin_walls = printability.get('thin_wall_detection', [])
        if thin_walls:
            suggestions.append("Thin walls detected - consider increasing wall thickness or using thin wall detection")

        # Complexity suggestions
        complexity = quality_metrics.get('complexity_score', 0)
        if complexity > 0.8:
            suggestions.append("High model complexity - consider simplifying geometry or using adaptive slicing")

        return suggestions

class SlicerCore:

    def __init__(self, settings: PrintSettings = None):
        self.settings = settings or PrintSettings()
        self.logger = logging.getLogger(__name__)

        # Initialize advanced components
        self.adaptive_engine = AdaptiveSlicingEngine(self.settings)
        self.parallel_slicer = MultiThreadedSlicer(self.settings)
        self.quality_optimizer = QualityOptimizationEngine(self.settings)
        self.mesh_analyzer = AdvancedMeshAnalyzer()

        # Performance tracking
        self.performance_stats = {
            'slicing_time': [],
            'layers_processed': [],
            'polygons_generated': [],
            'optimization_time': []
        }
        
    def slice_model(self, mesh_vertices: np.ndarray, mesh_faces: np.ndarray,
                   use_adaptive: bool = None, use_parallel: bool = None,
                   optimize_quality: bool = None) -> SlicedModel:
        start_time = time.time()
        self.logger.info("Starting model slicing...")

        if use_adaptive or (use_adaptive is None and self.settings.adaptive_layer_height_enabled):
            self.logger.info("Computing adaptive layer heights...")
            layer_heights = self.adaptive_engine.compute_adaptive_layers(mesh_vertices, mesh_faces)
        else:
            min_z = np.min(mesh_vertices[:, 2])
            max_z = np.max(mesh_vertices[:, 2])
            layer_heights = self._calculate_layer_heights(min_z, max_z)

        self.logger.info(f"Using {len(layer_heights)} layers with heights: {layer_heights[0]:.3f} to {layer_heights[-1]:.3f}")

        if use_parallel:
            sliced_model = self.parallel_slicer.slice_parallel(mesh_vertices, mesh_faces, layer_heights)
        else:
            sliced_model = self._slice_sequential(mesh_vertices, mesh_faces, layer_heights)

        self._validate_sliced_model(sliced_model)

        # Update performance stats
        slicing_time = time.time() - start_time
        self.performance_stats['slicing_time'].append(slicing_time)
        self.performance_stats['layers_processed'].append(len(layer_heights))
        self.performance_stats['polygons_generated'].append(sum(len(layer.polygons) for layer in sliced_model.layers))

        self.logger.info(f"Slicing complete in {slicing_time:.2f}s - "
                   f"layers: {len(layer_heights)}, "
                   f"total polygons: {sum(len(layer.polygons) for layer in sliced_model.layers)}")

        from .adhesion import apply_adhesion
        apply_adhesion(sliced_model)

        return sliced_model

    def _slice_sequential(self, mesh_vertices: np.ndarray, mesh_faces: np.ndarray,
                         layer_heights: List[float]) -> SlicedModel:
        sliced_model = SlicedModel(settings=self.settings)

        for i, z_height in enumerate(layer_heights):
            if i % 10 == 0:  # Progress logging
                self.logger.info(f"Processing layer {i+1}/{len(layer_heights)} at z={z_height:.3f}")

            layer = Layer(z_height=z_height)

            # Generate layer slice
            polygons = self._slice_at_height(mesh_vertices, mesh_faces, z_height)

            for polygon in polygons:
                layer.add_polygon(polygon)

            # Generate support if enabled
            if self.settings.support_material and i > 0:
                support_polygons = self._generate_support_for_layer(
                    layer, sliced_model.layers[i-1] if i > 0 else None
                )
                for support_polygon in support_polygons:
                    layer.add_support_polygon(support_polygon)

            sliced_model.add_layer(layer)

        return sliced_model

    def _apply_advanced_postprocessing(self, sliced_model: SlicedModel):
        self.logger.info("Applying advanced post-processing...")

        # Smooth layer transitions
        self._smooth_layer_transitions(sliced_model)

        # Optimize polygon ordering
        self._optimize_polygon_ordering(sliced_model)

        # Apply quality enhancements
        self._apply_quality_enhancements(sliced_model)

        # Validate sliced model
        self._validate_sliced_model(sliced_model)

    def _smooth_layer_transitions(self, sliced_model: SlicedModel):
        if len(sliced_model.layers) < 2:
            return

        for i in range(1, len(sliced_model.layers)):
            current_layer = sliced_model.layers[i]
            previous_layer = sliced_model.layers[i-1]

            # Smooth polygon transitions
            for polygon in current_layer.polygons:
                # Find corresponding polygon in previous layer
                corresponding = self._find_corresponding_polygon(polygon, previous_layer)

                if corresponding:
                    # Smooth the transition
                    polygon.points = self._smooth_polygon_transition(
                        corresponding.points, polygon.points
                    )

    def _find_corresponding_polygon(self, polygon: LayerPolygon, layer: Layer) -> Optional[LayerPolygon]:
        # Simplified correspondence finding based on centroid proximity
        poly_centroid = self._calculate_polygon_centroid(polygon)

        min_distance = float('inf')
        best_match = None

        for other_polygon in layer.polygons:
            other_centroid = self._calculate_polygon_centroid(other_polygon)
            distance = math.sqrt((poly_centroid.x - other_centroid.x)**2 +
                               (poly_centroid.y - other_centroid.y)**2)

            if distance < min_distance and distance < 1.0:  # 1mm threshold
                min_distance = distance
                best_match = other_polygon

        return best_match

    def _calculate_polygon_centroid(self, polygon: LayerPolygon) -> Point2D:
        if not polygon.points:
            return Point2D(0, 0)

        x_sum = sum(p.x for p in polygon.points)
        y_sum = sum(p.y for p in polygon.points)

        return Point2D(x_sum / len(polygon.points), y_sum / len(polygon.points))

    def _smooth_polygon_transition(self, points1: List[Point2D], points2: List[Point2D]) -> List[Point2D]:
        if len(points1) != len(points2):
            return points2  # Can't smooth if different number of points

        smoothed = []
        for p1, p2 in zip(points1, points2):
            # Simple linear interpolation for smoothing
            smoothed_x = (p1.x + p2.x) / 2
            smoothed_y = (p1.y + p2.y) / 2
            smoothed.append(Point2D(smoothed_x, smoothed_y))

        return smoothed

    def _optimize_polygon_ordering(self, sliced_model: SlicedModel):
        for layer in sliced_model.layers:
            if len(layer.polygons) < 2:
                continue

            # Sort polygons by area (largest first) for better printing
            layer.polygons.sort(key=lambda p: p.area(), reverse=True)

            # Optimize path direction for each polygon
            for polygon in layer.polygons:
                self._optimize_polygon_direction(polygon)

    def _optimize_polygon_direction(self, polygon: LayerPolygon):
        # Ensure counter-clockwise for external polygons
        if not polygon.is_hole and not self._is_counter_clockwise(polygon.points):
            polygon.reverse()

    def _is_counter_clockwise(self, points: List[Point2D]) -> bool:
        if len(points) < 3:
            return True

        # Calculate signed area
        signed_area = 0.0
        n = len(points)

        for i in range(n):
            j = (i + 1) % n
            signed_area += (points[j].x - points[i].x) * (points[j].y + points[i].y)

        return signed_area < 0

    def _apply_quality_enhancements(self, sliced_model: SlicedModel):
        for layer in sliced_model.layers:
            # Remove degenerate polygons
            layer.polygons = [p for p in layer.polygons if len(p.points) >= 3 and p.area() > 1e-6]

            # Simplify overly complex polygons
            for polygon in layer.polygons:
                if len(polygon.points) > 100:  # Too many points
                    polygon.points = self._simplify_polygon(polygon.points, tolerance=0.1)

    def _simplify_polygon(self, points: List[Point2D], tolerance: float) -> List[Point2D]:
        if len(points) <= 3:
            return points

        # Find point with maximum distance
        max_distance = 0
        max_index = 0

        for i in range(1, len(points) - 1):
            distance = self._point_to_line_distance(points[i], points[0], points[-1])
            if distance > max_distance:
                max_distance = distance
                max_index = i

        # If max distance is greater than tolerance, recursively simplify
        if max_distance > tolerance:
            left = self._simplify_polygon(points[:max_index + 1], tolerance)
            right = self._simplify_polygon(points[max_index:], tolerance)

            return left[:-1] + right
        else:
            return [points[0], points[-1]]

    def _point_to_line_distance(self, point: Point2D, line_start: Point2D, line_end: Point2D) -> float:
        # Vector from line_start to line_end
        line_vec = Point2D(line_end.x - line_start.x, line_end.y - line_start.y)
        line_length = math.sqrt(line_vec.x**2 + line_vec.y**2)

        if line_length < 1e-10:
            return math.sqrt((point.x - line_start.x)**2 + (point.y - line_start.y)**2)

        # Vector from line_start to point
        point_vec = Point2D(point.x - line_start.x, point.y - line_start.y)

        # Project point onto line
        projection = (point_vec.x * line_vec.x + point_vec.y * line_vec.y) / (line_length ** 2)

        # Clamp projection to line segment
        projection = max(0, min(1, projection))

        # Find closest point on line segment
        closest_x = line_start.x + projection * line_vec.x
        closest_y = line_start.y + projection * line_vec.y

        # Calculate distance
        return math.sqrt((point.x - closest_x)**2 + (point.y - closest_y)**2)

    def _validate_sliced_model(self, sliced_model: SlicedModel):
        issues = []

        for i, layer in enumerate(sliced_model.layers):
            # Check for empty layers
            if not layer.polygons and not layer.support_polygons:
                issues.append(f"Layer {i} is empty")

            # Check for invalid polygons
            for j, polygon in enumerate(layer.polygons):
                if len(polygon.points) < 3:
                    issues.append(f"Layer {i}, polygon {j} has fewer than 3 points")

                if polygon.area() < 0:
                    issues.append(f"Layer {i}, polygon {j} has negative area")

        if issues:
            self.logger.warning(f"Validation issues found: {issues}")
        else:
            self.logger.info("Sliced model validation passed")

    def get_performance_report(self) -> Dict[str, Any]:
        return {
            'slicing_performance': {
                'avg_slicing_time': np.mean(self.performance_stats['slicing_time']) if self.performance_stats['slicing_time'] else 0,
                'total_layers_processed': sum(self.performance_stats['layers_processed']),
                'total_polygons_generated': sum(self.performance_stats['polygons_generated']),
                'slicing_sessions': len(self.performance_stats['slicing_time'])
            },
            'optimization_stats': {
                'avg_optimization_time': np.mean(self.performance_stats['optimization_time']) if self.performance_stats['optimization_time'] else 0
            }
        }

    def reset_performance_stats(self):
        self.performance_stats = {
            'slicing_time': [],
            'layers_processed': [],
            'polygons_generated': [],
            'optimization_time': []
        }
    
    def _calculate_layer_heights(self, min_z: float, max_z: float) -> List[float]:
        layer_heights = []
        
        # First layer
        current_z = min_z + self.settings.first_layer_height
        layer_heights.append(current_z)
        
        # Remaining layers
        while current_z + self.settings.layer_height <= max_z:
            current_z += self.settings.layer_height
            layer_heights.append(current_z)
        
        return layer_heights
    
    def _slice_at_height(self, vertices: np.ndarray, faces: np.ndarray, z: float) -> List[LayerPolygon]:
        polygons = []
        intersecting_points = []
        
        # Find all edges that intersect the slicing plane
        for face in faces:
            v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
            
            # Check each edge of the triangle
            edges = [(v0, v1), (v1, v2), (v2, v0)]
            
            for edge_start, edge_end in edges:
                if self._edge_intersects_plane(edge_start, edge_end, z):
                    intersection = self._find_plane_intersection(edge_start, edge_end, z)
                    if intersection is not None:
                        intersecting_points.append(intersection)
        
        # Group points into closed contours to form polygons
        if len(intersecting_points) >= 3:
            # Remove duplicate points (within tolerance)
            unique_points = self._remove_duplicate_points(intersecting_points, tolerance=1e-6)
            
            # Try to form closed polygons from the intersection points
            if len(unique_points) >= 3:
                # Sort points to form a reasonable polygon
                sorted_points = self._sort_points_for_polygon(unique_points)
                
                if len(sorted_points) >= 3:
                    polygon_points = [Point2D(p[0], p[1]) for p in sorted_points]
                    polygon = LayerPolygon(points=polygon_points, is_hole=False)
                    polygons.append(polygon)
        
        return polygons
    
    def _remove_duplicate_points(self, points: List[Tuple[float, float]], tolerance: float) -> List[Tuple[float, float]]:
        unique = []
        for point in points:
            is_duplicate = False
            for existing in unique:
                dist = math.sqrt((point[0] - existing[0])**2 + (point[1] - existing[1])**2)
                if dist < tolerance:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique.append(point)
        return unique
    
    def _sort_points_for_polygon(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        if len(points) < 3:
            return points
        
        # Find centroid
        cx = sum(p[0] for p in points) / len(points)
        cy = sum(p[1] for p in points) / len(points)
        
        # Sort by angle from centroid
        def angle_from_center(point):
            dx = point[0] - cx
            dy = point[1] - cy
            return math.atan2(dy, dx)
        
        sorted_points = sorted(points, key=angle_from_center)
        return sorted_points
    
    def _edge_intersects_plane(self, v0: np.ndarray, v1: np.ndarray, z: float) -> bool:
        return (v0[2] <= z <= v1[2]) or (v1[2] <= z <= v0[2])
    
    def _find_plane_intersection(self, v0: np.ndarray, v1: np.ndarray, z: float) -> Optional[Tuple[float, float]]:
        if abs(v1[2] - v0[2]) < 1e-10:  # Edge is parallel to plane
            return None
        
        t = (z - v0[2]) / (v1[2] - v0[2])
        if 0.0 <= t <= 1.0:
            x = v0[0] + t * (v1[0] - v0[0])
            y = v0[1] + t * (v1[1] - v0[1])
            return (x, y)
        return None
    
    def _generate_support_for_layer(self, current_layer: Layer, previous_layer: Optional[Layer]) -> List[LayerPolygon]:
        support_polygons = []
        
        if not previous_layer:
            return support_polygons
        
        # Simplified support generation
        # Would need proper overhang detection and support structure generation
        if self.settings.support_type == SupportType.BUILD_PLATE_ONLY:
            # Generate support only where needed
            for polygon in current_layer.polygons:
                if self._needs_support(polygon, previous_layer):
                    support_polygon = self._create_support_polygon(polygon)
                    support_polygons.append(support_polygon)
        
        return support_polygons
    
    def _needs_support(self, polygon: LayerPolygon, previous_layer: Layer) -> bool:
        # Simplified support detection
        return len(previous_layer.polygons) == 0  # Support if nothing below
    
    def _create_support_polygon(self, polygon: LayerPolygon) -> LayerPolygon:
        # Simplified support polygon creation
        # Would need proper support pattern generation
        support_points = []
        
        # Create a simplified support pattern
        for point in polygon.points:
            support_points.append(Point2D(point.x, point.y))
        
        return LayerPolygon(points=support_points)

# Example usage and testing
if __name__ == "__main__":
    # Create a simple test case
    settings = PrintSettings(
        layer_height=0.2,
        fill_density=0.2,
        support_material=True,
        perimeters=3
    )
    
    slicer = SlicerCore(settings)
    
    # Create a simple cube mesh for testing
    vertices = np.array([
        [0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0],  # Bottom face
        [0, 0, 10], [10, 0, 10], [10, 10, 10], [0, 10, 10]  # Top face
    ])
    
    faces = np.array([
        [0, 1, 2], [0, 2, 3],  # Bottom
        [4, 6, 5], [4, 7, 6],  # Top
        [0, 4, 5], [0, 5, 1],  # Front
        [2, 6, 7], [2, 7, 3],  # Back
        [0, 3, 7], [0, 7, 4],  # Left
        [1, 5, 6], [1, 6, 2]   # Right
    ])
    
    # Slice the model
    sliced_model = slicer.slice_model(vertices, faces)
    
    print(f"Generated {sliced_model.get_layer_count()} layers")
    print(f"Estimated print time: {sliced_model.get_print_time_estimate():.1f} minutes")
    print(f"Estimated material usage: {sliced_model.get_material_usage():.2f} mm³")
