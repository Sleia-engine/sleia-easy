#!/usr/bin/env python3
# ------------------------------------------------------------------
# Copyright (c) 2026 Sleia Engine Development Team.
# This file is distributed under the MIT License. See LICENSE.
#
# Sleia Easy v 1.0.1 - Thermoplastic Python Slicer
#
# File: perimeter_generator.py
# Description: outer and inner walls.
# ------------------------------------------------------------------

import numpy as np
import math
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

try:
    # Try relative imports first (when used as package)
    from .slicer_core import Point2D, LayerPolygon, PrintSettings
except ImportError:
    # Fallback to absolute imports (when used standalone)
    from slicer_core import Point2D, LayerPolygon, PrintSettings

class PerimeterType(Enum):
    EXTERNAL = "external"
    INTERNAL = "internal"
    OVERHANG = "overhang"

@dataclass
class PerimeterPath:
    points: List[Point2D] = field(default_factory=list)
    perimeter_type: PerimeterType = PerimeterType.INTERNAL
    is_hole: bool = False
    speed: float = 60.0
    extrusion_width: float = 0.4
    
    def length(self) -> float:
        if len(self.points) < 2:
            return 0.0
        
        total_length = 0.0
        for i in range(len(self.points) - 1):
            total_length += self.points[i].distance(self.points[i + 1])
        
        # Add closing segment if it's a closed loop
        if len(self.points) > 2:
            total_length += self.points[-1].distance(self.points[0])
        
        return total_length
    
    def reverse(self):
        self.points.reverse()

@dataclass
class PerimeterLayer:
    paths: List[PerimeterPath] = field(default_factory=list)
    layer_height: float = 0.2
    
    def add_path(self, path: PerimeterPath):
        self.paths.append(path)
    
    def get_external_perimeters(self) -> List[PerimeterPath]:
        return [p for p in self.paths if p.perimeter_type == PerimeterType.EXTERNAL]
    
    def get_internal_perimeters(self) -> List[PerimeterPath]:
        return [p for p in self.paths if p.perimeter_type == PerimeterType.INTERNAL]

# ===== ADVANCED PERIMETER ALGORITHMS =====

class VariableWidthPerimeterGenerator:

    def __init__(self, base_width: float):
        self.base_width = base_width
        self.width_variation_factor = 0.3  # Maximum variation ±30%

    def compute_variable_widths(self, polygon: LayerPolygon,
                               curvature_threshold: float = 0.1) -> List[float]:
        widths = []

        for i, point in enumerate(polygon.points):
            # Calculate local curvature
            curvature = self._calculate_local_curvature(polygon.points, i)

            # Adjust width based on curvature
            if curvature > curvature_threshold:
                # Increase width for tight curves
                width_factor = 1.0 + min(curvature * 2.0, self.width_variation_factor)
            elif curvature < -curvature_threshold:
                # Decrease width for flat areas (optional)
                width_factor = 1.0 - min(abs(curvature) * 0.5, self.width_variation_factor * 0.5)
            else:
                width_factor = 1.0

            widths.append(self.base_width * width_factor)

        return widths

    def _calculate_local_curvature(self, points: List[Point2D], index: int) -> float:
        n = len(points)
        p0 = points[(index - 1) % n]
        p1 = points[index]
        p2 = points[(index + 1) % n]

        # Calculate angle at p1
        v1 = Point2D(p0.x - p1.x, p0.y - p1.y)
        v2 = Point2D(p2.x - p1.x, p2.y - p1.y)

        # Dot product
        dot = v1.x * v2.x + v1.y * v2.y
        len1 = math.sqrt(v1.x**2 + v1.y**2)
        len2 = math.sqrt(v2.x**2 + v2.y**2)

        if len1 < 1e-10 or len2 < 1e-10:
            return 0.0

        cos_angle = dot / (len1 * len2)
        cos_angle = max(-1.0, min(1.0, cos_angle))

        angle = math.acos(cos_angle)

        # Curvature (1/radius) - positive for convex, negative for concave
        if angle < math.pi:
            return 2.0 / max(angle, 0.01)  # Avoid division by zero
        else:
            return -2.0 / max(2*math.pi - angle, 0.01)

class OverhangCompensationGenerator:

    def __init__(self, overhang_threshold: float = 45.0):
        self.overhang_threshold = math.radians(overhang_threshold)

    def detect_overhang_regions(self, polygon: LayerPolygon,
                              previous_layer: Optional[LayerPolygon] = None) -> List[Tuple[int, float]]:
        overhang_regions = []

        if previous_layer is None:
            return overhang_regions

        for i, point in enumerate(polygon.points):
            # Calculate overhang angle at this point
            overhang_angle = self._calculate_overhang_angle(point, polygon, previous_layer)

            if overhang_angle > self.overhang_threshold:
                overhang_regions.append((i, overhang_angle))

        return overhang_regions

    def _calculate_overhang_angle(self, point: Point2D, current_polygon: LayerPolygon,
                                previous_polygon: LayerPolygon) -> float:
        # Find closest point in previous layer
        min_distance = float('inf')
        closest_point = None

        for prev_point in previous_polygon.points:
            distance = math.sqrt((point.x - prev_point.x)**2 + (point.y - prev_point.y)**2)
            if distance < min_distance:
                min_distance = distance
                closest_point = prev_point

        if closest_point is None or min_distance > 5.0:  # Too far, no support
            return math.pi / 2  # 90 degrees

        # Calculate angle between vertical and line connecting points
        dx = point.x - closest_point.x
        dy = point.y - closest_point.y
        dz = 0.2  # Layer height

        angle = math.atan2(math.sqrt(dx**2 + dy**2), dz)
        return angle

    def generate_overhang_perimeters(self, polygon: LayerPolygon,
                                   overhang_regions: List[Tuple[int, float]]) -> List[PerimeterPath]:
        overhang_paths = []

        if not overhang_regions:
            return overhang_paths

        # Group consecutive overhang regions
        overhang_groups = self._group_overhang_regions(overhang_regions, len(polygon.points))

        for group in overhang_groups:
            start_idx, end_idx = group
            avg_angle = sum(angle for _, angle in overhang_regions if start_idx <= _ <= end_idx) / (end_idx - start_idx + 1)

            # Create reinforced perimeter for overhang
            overhang_points = polygon.points[start_idx:end_idx + 1]

            overhang_path = PerimeterPath(
                points=overhang_points,
                perimeter_type=PerimeterType.OVERHANG,
                speed=self._calculate_overhang_speed(avg_angle),
                extrusion_width=self._calculate_overhang_width(avg_angle)
            )

            overhang_paths.append(overhang_path)

        return overhang_paths

    def _group_overhang_regions(self, overhang_regions: List[Tuple[int, float]],
                              total_points: int) -> List[Tuple[int, int]]:
        if not overhang_regions:
            return []

        groups = []
        current_group = [overhang_regions[0][0]]

        for i in range(1, len(overhang_regions)):
            current_idx = overhang_regions[i][0]
            prev_idx = overhang_regions[i-1][0]

            # Check if consecutive (considering wrap-around)
            if current_idx == (prev_idx + 1) % total_points:
                current_group.append(current_idx)
            else:
                groups.append((min(current_group), max(current_group)))
                current_group = [current_idx]

        if current_group:
            groups.append((min(current_group), max(current_group)))

        return groups

    def _calculate_overhang_speed(self, angle: float) -> float:
        angle_degrees = math.degrees(angle)

        if angle_degrees > 70:
            return 20.0  # Very slow for steep overhangs
        elif angle_degrees > 50:
            return 30.0  # Slow for moderate overhangs
        else:
            return 40.0  # Moderate speed

    def _calculate_overhang_width(self, angle: float) -> float:
        angle_degrees = math.degrees(angle)

        if angle_degrees > 60:
            return 0.35  # Thicker extrusion for support
        else:
            return 0.4   # Standard width

class MultiPassPerimeterGenerator:

    def __init__(self, base_width: float, num_passes: int = 3):
        self.base_width = base_width
        self.num_passes = num_passes

    def generate_multi_pass_perimeters(self, polygon: LayerPolygon) -> List[PerimeterPath]:
        multi_pass_paths = []

        for pass_num in range(self.num_passes):
            # Calculate offset for this pass
            offset_distance = pass_num * self.base_width * 0.5

            # Offset the polygon
            offset_polygon = self._offset_polygon(polygon, offset_distance)

            if offset_polygon and len(offset_polygon.points) >= 3:
                pass_path = PerimeterPath(
                    points=offset_polygon.points,
                    perimeter_type=PerimeterType.INTERNAL,
                    speed=self._calculate_pass_speed(pass_num),
                    extrusion_width=self._calculate_pass_width(pass_num)
                )

                multi_pass_paths.append(pass_path)

        return multi_pass_paths

    def _offset_polygon(self, polygon: LayerPolygon, distance: float) -> Optional[LayerPolygon]:
        if len(polygon.points) < 3:
            return None

        offset_points = []

        for i in range(len(polygon.points)):
            p1 = polygon.points[(i - 1) % len(polygon.points)]
            p2 = polygon.points[i]
            p3 = polygon.points[(i + 1) % len(polygon.points)]

            # Calculate normal vector
            v1 = Point2D(p2.x - p1.x, p2.y - p1.y)
            v2 = Point2D(p3.x - p2.x, p3.y - p2.y)

            # Perpendicular vector (rotate 90 degrees)
            perp = Point2D(-v1.y, v1.x)
            perp_len = math.sqrt(perp.x**2 + perp.y**2)

            if perp_len > 0:
                perp.x /= perp_len
                perp.y /= perp_len

                # Offset point
                offset_point = Point2D(
                    p2.x + perp.x * distance,
                    p2.y + perp.y * distance
                )
                offset_points.append(offset_point)

        if len(offset_points) >= 3:
            return LayerPolygon(points=offset_points, is_hole=polygon.is_hole)

        return None

    def _calculate_pass_speed(self, pass_num: int) -> float:
        base_speed = 50.0

        if pass_num == 0:
            return base_speed * 0.7  # First pass slower for adhesion
        elif pass_num == self.num_passes - 1:
            return base_speed * 0.8  # Last pass slower for finish
        else:
            return base_speed

    def _calculate_pass_width(self, pass_num: int) -> float:
        if pass_num == 0:
            return self.base_width * 1.1  # First pass slightly wider
        else:
            return self.base_width

class QualityEnhancementGenerator:

    def __init__(self, quality_level: str = "standard"):
        self.quality_level = quality_level
        self.smoothing_iterations = {"draft": 1, "standard": 2, "high": 3, "ultra": 5}.get(quality_level, 2)

    def enhance_perimeter_quality(self, perimeter_path: PerimeterPath) -> PerimeterPath:
        enhanced_points = perimeter_path.points.copy()

        # Apply smoothing
        for _ in range(self.smoothing_iterations):
            enhanced_points = self._smooth_path(enhanced_points)

        # Apply corner enhancement
        enhanced_points = self._enhance_corners(enhanced_points)

        # Create enhanced path
        enhanced_path = PerimeterPath(
            points=enhanced_points,
            perimeter_type=perimeter_path.perimeter_type,
            is_hole=perimeter_path.is_hole,
            speed=perimeter_path.speed,
            extrusion_width=perimeter_path.extrusion_width
        )

        return enhanced_path

    def _smooth_path(self, points: List[Point2D]) -> List[Point2D]:
        if len(points) < 3:
            return points

        smoothed = [points[0]]  # Keep first point

        for i in range(1, len(points) - 1):
            p0 = points[i - 1]
            p1 = points[i]
            p2 = points[i + 1]

            # Simple averaging smooth
            smooth_x = (p0.x + p1.x * 2 + p2.x) / 4
            smooth_y = (p0.y + p1.y * 2 + p2.y) / 4

            smoothed.append(Point2D(smooth_x, smooth_y))

        smoothed.append(points[-1])  # Keep last point

        return smoothed

    def _enhance_corners(self, points: List[Point2D]) -> List[Point2D]:
        if len(points) < 3:
            return points

        enhanced = []

        for i in range(len(points)):
            p0 = points[(i - 1) % len(points)]
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]

            # Calculate corner angle
            angle = self._calculate_corner_angle(p0, p1, p2)

            if abs(angle) > math.radians(30):  # Sharp corner
                # Add extra points for smoother corner
                corner_points = self._generate_corner_points(p0, p1, p2, angle)
                enhanced.extend(corner_points)
            else:
                enhanced.append(p1)

        return enhanced

    def _calculate_corner_angle(self, p0: Point2D, p1: Point2D, p2: Point2D) -> float:
        v1 = Point2D(p0.x - p1.x, p0.y - p1.y)
        v2 = Point2D(p2.x - p1.x, p2.y - p1.y)

        # Dot product
        dot = v1.x * v2.x + v1.y * v2.y
        len1 = math.sqrt(v1.x**2 + v1.y**2)
        len2 = math.sqrt(v2.x**2 + v2.y**2)

        if len1 < 1e-10 or len2 < 1e-10:
            return 0.0

        cos_angle = dot / (len1 * len2)
        cos_angle = max(-1.0, min(1.0, cos_angle))

        return math.acos(cos_angle)

    def _generate_corner_points(self, p0: Point2D, p1: Point2D, p2: Point2D,
                              angle: float) -> List[Point2D]:
        # Simple corner enhancement - could be more sophisticated
        return [p1]  # For now, just return the original point

class PerimeterGenerator:

    def __init__(self, settings: PrintSettings):
        self.settings = settings
        self.external_width = settings.extrusion_width
        self.internal_width = settings.extrusion_width

        # Advanced parameters
        self.min_perimeter_length = 3.0  # mm
        self.thin_wall_width = settings.extrusion_width * 1.5
        self.gap_fill_threshold = settings.extrusion_width * 0.7

        # Initialize enhancement modules
        self.variable_width_gen = VariableWidthPerimeterGenerator(self.external_width)
        self.overhang_compensation = OverhangCompensationGenerator()
        self.multi_pass_gen = MultiPassPerimeterGenerator(self.external_width)
        self.quality_enhancer = QualityEnhancementGenerator("standard")

        # Performance tracking
        self.generation_stats = {
            'total_perimeters_generated': 0,
            'average_generation_time': 0.0,
            'quality_enhancements_applied': 0,
            'overhang_regions_detected': 0
        }
    
    def generate_perimeters(self, polygon: LayerPolygon,
                          layer_height: float,
                          previous_layer: Optional[LayerPolygon] = None,
                          enable_advanced: bool = True) -> PerimeterLayer:
        import time
        start_time = time.time()

        perimeter_layer = PerimeterLayer(layer_height=layer_height)

        if not polygon.points or len(polygon.points) < 3:
            return perimeter_layer

        # Detect overhang regions if advanced features enabled
        overhang_regions = []
        if enable_advanced and previous_layer:
            overhang_regions = self.overhang_compensation.detect_overhang_regions(polygon, previous_layer)
            self.generation_stats['overhang_regions_detected'] += len(overhang_regions)

        # Generate multiple perimeter loops
        current_polygon = polygon

        for perimeter_idx in range(self.settings.perimeters):
            if not current_polygon or len(current_polygon.points) < 3:
                break

            # Determine perimeter type
            is_external = (perimeter_idx == 0)
            perimeter_type = PerimeterType.EXTERNAL if is_external else PerimeterType.INTERNAL

            # Create perimeter path with advanced features
            perimeter_path = self._create_advanced_perimeter_path(
                current_polygon,
                perimeter_type,
                layer_height,
                overhang_regions if is_external else [],
                enable_advanced
            )

            if perimeter_path and len(perimeter_path.points) >= 3:
                perimeter_layer.add_path(perimeter_path)

                # Create next inner polygon for next perimeter
                if perimeter_idx < self.settings.perimeters - 1:
                    offset_distance = -self.internal_width
                    current_polygon = self._offset_polygon(current_polygon, offset_distance)
                else:
                    current_polygon = None

        # Generate overhang-specific perimeters
        if enable_advanced and overhang_regions:
            overhang_paths = self.overhang_compensation.generate_overhang_perimeters(polygon, overhang_regions)
            for path in overhang_paths:
                perimeter_layer.add_path(path)

        # Apply quality enhancements
        if enable_advanced:
            for path in perimeter_layer.paths:
                enhanced_path = self.quality_enhancer.enhance_perimeter_quality(path)
                # Replace path with enhanced version (simplified)
                path.points = enhanced_path.points
                self.generation_stats['quality_enhancements_applied'] += 1

        # Optimize perimeter order
        self._optimize_perimeter_order(perimeter_layer)

        # Update statistics
        generation_time = time.time() - start_time
        self.generation_stats['total_perimeters_generated'] += len(perimeter_layer.paths)
        self.generation_stats['average_generation_time'] = (
            (self.generation_stats['average_generation_time'] *
             (self.generation_stats['total_perimeters_generated'] - len(perimeter_layer.paths)) +
             generation_time) / self.generation_stats['total_perimeters_generated']
        )

        return perimeter_layer

    def apply_wall_controls(self, perimeter_layer: PerimeterLayer,
                          wall_overlap: float = 15.0,
                          wall_order: str = "inner wall/outer wall/infill",
                          detect_thin_walls: bool = True,
                          only_one_wall_top: bool = True) -> PerimeterLayer:

        enhanced_layer = PerimeterLayer(layer_height=perimeter_layer.layer_height)

        # Apply wall overlap compensation
        enhanced_layer = self._apply_wall_overlap(perimeter_layer, wall_overlap)

        # Reorder walls according to specified order
        enhanced_layer = self._reorder_walls(enhanced_layer, wall_order)

        # Apply thin wall detection if enabled
        if detect_thin_walls:
            enhanced_layer = self._apply_thin_wall_detection(enhanced_layer)

        # Apply single wall for top layers if enabled
        if only_one_wall_top:
            enhanced_layer = self._apply_single_wall_top(enhanced_layer)

        return enhanced_layer

    def _apply_wall_overlap(self, perimeter_layer: PerimeterLayer, overlap_percentage: float) -> PerimeterLayer:

        if overlap_percentage <= 0:
            return perimeter_layer

        enhanced_layer = PerimeterLayer(layer_height=perimeter_layer.layer_height)

        overlap_factor = overlap_percentage / 100.0

        for path in perimeter_layer.paths:
            # Calculate overlap distance based on extrusion width
            overlap_distance = path.extrusion_width * overlap_factor

            # Offset the path inward by overlap distance
            overlapped_path = self._offset_perimeter_path(path, -overlap_distance)

            if overlapped_path and len(overlapped_path.points) >= 3:
                enhanced_layer.add_path(overlapped_path)

        return enhanced_layer

    def _offset_perimeter_path(self, path: PerimeterPath, offset_distance: float) -> Optional[PerimeterPath]:

        if len(path.points) < 3:
            return None

        # Create polygon from path points
        temp_polygon = LayerPolygon(points=path.points, is_hole=False)

        # Offset the polygon
        offset_polygon = self._offset_polygon(temp_polygon, offset_distance)

        if not offset_polygon or len(offset_polygon.points) < 3:
            return None

        # Create new path with offset points
        offset_path = PerimeterPath(
            points=offset_polygon.points,
            perimeter_type=path.perimeter_type,
            is_hole=path.is_hole,
            speed=path.speed,
            extrusion_width=path.extrusion_width
        )

        return offset_path

    def _reorder_walls(self, perimeter_layer: PerimeterLayer, wall_order: str) -> PerimeterLayer:

        reordered_layer = PerimeterLayer(layer_height=perimeter_layer.layer_height)

        if wall_order == "inner wall/outer wall/infill":
            # Default order: inner walls first, then outer walls
            inner_walls = [p for p in perimeter_layer.paths if p.perimeter_type == PerimeterType.INTERNAL]
            outer_walls = [p for p in perimeter_layer.paths if p.perimeter_type == PerimeterType.EXTERNAL]
            overhang_walls = [p for p in perimeter_layer.paths if p.perimeter_type == PerimeterType.OVERHANG]

            # Add walls in specified order
            reordered_layer.paths.extend(inner_walls)
            reordered_layer.paths.extend(outer_walls)
            reordered_layer.paths.extend(overhang_walls)

        elif wall_order == "outer wall/inner wall/infill":
            # Outer walls first
            outer_walls = [p for p in perimeter_layer.paths if p.perimeter_type == PerimeterType.EXTERNAL]
            inner_walls = [p for p in perimeter_layer.paths if p.perimeter_type == PerimeterType.INTERNAL]
            overhang_walls = [p for p in perimeter_layer.paths if p.perimeter_type == PerimeterType.OVERHANG]

            reordered_layer.paths.extend(outer_walls)
            reordered_layer.paths.extend(inner_walls)
            reordered_layer.paths.extend(overhang_walls)

        else:
            # Default: keep original order
            reordered_layer.paths = perimeter_layer.paths.copy()

        return reordered_layer

    def _apply_thin_wall_detection(self, perimeter_layer: PerimeterLayer) -> PerimeterLayer:

        enhanced_layer = PerimeterLayer(layer_height=perimeter_layer.layer_height)

        # Process each perimeter path
        for path in perimeter_layer.paths:
            # Check if this path represents a thin wall
            if self._is_thin_wall_path(path):
                # Apply thin wall optimizations
                thin_wall_path = self._optimize_thin_wall_path(path)
                if thin_wall_path:
                    enhanced_layer.add_path(thin_wall_path)
            else:
                enhanced_layer.add_path(path)

        return enhanced_layer

    def _is_thin_wall_path(self, path: PerimeterPath) -> bool:

        if len(path.points) < 2:
            return False

        # Calculate average wall thickness
        # For thin walls, the extrusion width should be close to the available space
        wall_thickness = path.extrusion_width

        # Check if path length suggests a thin wall
        path_length = path.length()
        if path_length < wall_thickness * 3:  # Very short paths might be thin walls
            return True

        # Check for sharp turns that might indicate thin wall geometry
        sharp_turns = 0
        for i in range(len(path.points) - 2):
            p1 = path.points[i]
            p2 = path.points[i + 1]
            p3 = path.points[i + 2]

            # Calculate angle at p2
            angle = self._calculate_path_angle(p1, p2, p3)
            if angle < 45:  # Sharp turn
                sharp_turns += 1

        # High number of sharp turns suggests thin wall geometry
        return sharp_turns > len(path.points) * 0.3

    def _calculate_path_angle(self, p1: Point2D, p2: Point2D, p3: Point2D) -> float:

        # Vector p1->p2
        v1 = (p2.x - p1.x, p2.y - p1.y)
        # Vector p2->p3
        v2 = (p3.x - p2.x, p3.y - p2.y)

        # Dot product
        dot = v1[0] * v2[0] + v1[1] * v2[1]

        # Magnitudes
        mag1 = math.sqrt(v1[0]**2 + v1[1]**2)
        mag2 = math.sqrt(v2[0]**2 + v2[1]**2)

        if mag1 == 0 or mag2 == 0:
            return 180.0

        # Cosine of angle
        cos_angle = dot / (mag1 * mag2)
        cos_angle = max(-1.0, min(1.0, cos_angle))

        # Convert to degrees
        angle = math.degrees(math.acos(cos_angle))

        return angle

    def _optimize_thin_wall_path(self, path: PerimeterPath) -> Optional[PerimeterPath]:

        if len(path.points) < 2:
            return None

        optimized_path = PerimeterPath(
            points=path.points.copy(),
            perimeter_type=path.perimeter_type,
            is_hole=path.is_hole,
            speed=path.speed * 0.8,  # Slower speed for thin walls
            extrusion_width=path.extrusion_width * 0.9  # Slightly reduced extrusion
        )

        # Smooth sharp corners in thin walls
        optimized_path.points = self._smooth_thin_wall_corners(optimized_path.points)

        return optimized_path

    def _smooth_thin_wall_corners(self, points: List[Point2D]) -> List[Point2D]:

        if len(points) < 3:
            return points

        smoothed_points = [points[0]]  # Keep start point

        for i in range(1, len(points) - 1):
            prev_point = points[i - 1]
            curr_point = points[i]
            next_point = points[i + 1]

            # Calculate angle
            angle = self._calculate_path_angle(prev_point, curr_point, next_point)

            if angle < 60:  # Sharp corner
                # Create smoothed corner by averaging points
                smoothed_x = (prev_point.x + curr_point.x * 2 + next_point.x) / 4
                smoothed_y = (prev_point.y + curr_point.y * 2 + next_point.y) / 4

                smoothed_points.append(Point2D(smoothed_x, smoothed_y))
            else:
                smoothed_points.append(curr_point)

        smoothed_points.append(points[-1])  # Keep end point

        return smoothed_points

    def _apply_single_wall_top(self, perimeter_layer: PerimeterLayer) -> PerimeterLayer:

        # For top layers, we might want to reduce wall count
        # This is a simplified implementation - in practice, this would be
        # determined by the layer position in the model

        optimized_layer = PerimeterLayer(layer_height=perimeter_layer.layer_height)

        # Keep all walls for now (full implementation would check layer position)
        optimized_layer.paths = perimeter_layer.paths.copy()

        return optimized_layer

    def generate_adaptive_perimeters(self, polygon: LayerPolygon,
                                   layer_height: float,
                                   complexity_score: float) -> PerimeterLayer:
        # Adjust perimeter count based on complexity
        base_perimeters = self.settings.perimeters

        if complexity_score > 0.8:
            adaptive_perimeters = min(base_perimeters + 2, 5)  # Complex geometry needs more perimeters
        elif complexity_score < 0.3:
            adaptive_perimeters = max(base_perimeters - 1, 1)  # Simple geometry can use fewer
        else:
            adaptive_perimeters = base_perimeters

        # Temporarily adjust settings
        original_perimeters = self.settings.perimeters
        self.settings.perimeters = adaptive_perimeters

        try:
            result = self.generate_perimeters(polygon, layer_height, enable_advanced=True)
        finally:
            # Restore original settings
            self.settings.perimeters = original_perimeters

        return result

    def generate_multi_pass_perimeters(self, polygon: LayerPolygon,
                                     layer_height: float,
                                     num_passes: int = 3) -> PerimeterLayer:
        perimeter_layer = PerimeterLayer(layer_height=layer_height)

        if not polygon.points or len(polygon.points) < 3:
            return perimeter_layer

        # Generate multi-pass perimeters for external perimeter
        multi_pass_paths = self.multi_pass_gen.generate_multi_pass_perimeters(polygon)

        for path in multi_pass_paths:
            perimeter_layer.add_path(path)

        # Generate standard internal perimeters
        current_polygon = self._offset_polygon(polygon, -self.external_width)

        for perimeter_idx in range(1, self.settings.perimeters):
            if not current_polygon or len(current_polygon.points) < 3:
                break

            perimeter_path = self._create_perimeter_path(
                current_polygon,
                PerimeterType.INTERNAL,
                layer_height
            )

            if perimeter_path and len(perimeter_path.points) >= 3:
                perimeter_layer.add_path(perimeter_path)

                if perimeter_idx < self.settings.perimeters - 1:
                    current_polygon = self._offset_polygon(current_polygon, -self.internal_width)

        return perimeter_layer

    def _create_advanced_perimeter_path(self, polygon: LayerPolygon,
                                      perimeter_type: PerimeterType,
                                      layer_height: float,
                                      overhang_regions: List[Tuple[int, float]],
                                      enable_advanced: bool) -> Optional[PerimeterPath]:
        if not polygon.points or len(polygon.points) < 3:
            return None

        # Optimize polygon point order
        optimized_points = self._optimize_polygon_path(polygon.points)

        # Apply variable width if enabled
        if enable_advanced and perimeter_type == PerimeterType.EXTERNAL:
            widths = self.variable_width_gen.compute_variable_widths(polygon)
            # In a full implementation, we'd use these widths in G-code generation
            # For now, we use average width
            avg_width = sum(widths) / len(widths) if widths else self.external_width
        else:
            avg_width = self.external_width if perimeter_type == PerimeterType.EXTERNAL else self.internal_width

        # Determine speed based on perimeter type and overhangs
        speed = (self.settings.external_perimeter_speed if perimeter_type == PerimeterType.EXTERNAL
                else self.settings.perimeter_speed)

        # Adjust speed for overhang regions
        if overhang_regions:
            max_overhang_angle = max(angle for _, angle in overhang_regions)
            overhang_speed_reduction = min(max_overhang_angle / math.pi * 0.5, 0.7)
            speed *= (1.0 - overhang_speed_reduction)

        # Check for overhang conditions
        if self._is_overhang_perimeter(polygon, layer_height) or overhang_regions:
            perimeter_type = PerimeterType.OVERHANG
            speed = min(speed, self.settings.external_perimeter_speed * 0.5)

        path = PerimeterPath(
            points=optimized_points,
            perimeter_type=perimeter_type,
            is_hole=polygon.is_hole,
            speed=speed,
            extrusion_width=avg_width
        )

        return path
    
    def _create_perimeter_path(self, polygon: LayerPolygon, 
                             perimeter_type: PerimeterType,
                             layer_height: float) -> Optional[PerimeterPath]:
        
        if not polygon.points or len(polygon.points) < 3:
            return None
        
        # Optimize polygon point order
        optimized_points = self._optimize_polygon_path(polygon.points)
        
        # Determine speed based on perimeter type
        speed = (self.settings.external_perimeter_speed if perimeter_type == PerimeterType.EXTERNAL 
                else self.settings.perimeter_speed)
        
        # Check for overhang conditions
        if self._is_overhang_perimeter(polygon, layer_height):
            perimeter_type = PerimeterType.OVERHANG
            speed = min(speed, self.settings.external_perimeter_speed * 0.5)  # Slower for overhangs
        
        path = PerimeterPath(
            points=optimized_points,
            perimeter_type=perimeter_type,
            is_hole=polygon.is_hole,
            speed=speed,
            extrusion_width=self.external_width if perimeter_type == PerimeterType.EXTERNAL else self.internal_width
        )
        
        return path
    
    def _optimize_polygon_path(self, points: List[Point2D]) -> List[Point2D]:
        if len(points) < 3:
            return points
        
        # Find best starting point (closest to origin or previous end point)
        best_start_idx = self._find_optimal_start_point(points)
        
        # Reorder points starting from best start
        optimized_points = points[best_start_idx:] + points[:best_start_idx]
        
        # Smooth sharp corners if needed
        smoothed_points = self._smooth_sharp_corners(optimized_points)
        
        return smoothed_points
    
    def _find_optimal_start_point(self, points: List[Point2D]) -> int:
        if not points:
            return 0
        
        # For now, find point closest to origin
        min_distance = float('inf')
        best_idx = 0
        
        for i, point in enumerate(points):
            distance = math.sqrt(point.x**2 + point.y**2)
            if distance < min_distance:
                min_distance = distance
                best_idx = i
        
        return best_idx
    
    def _smooth_sharp_corners(self, points: List[Point2D], 
                            max_angle: float = 20.0) -> List[Point2D]:
        if len(points) < 3:
            return points
        
        smoothed = []
        max_angle_rad = math.radians(max_angle)
        corner_radius = 0.2  # mm
        
        n = len(points)
        
        for i in range(n):
            p1 = points[(i - 1) % n]
            p2 = points[i]
            p3 = points[(i + 1) % n]
            
            # Calculate angle at p2
            angle = self._calculate_angle(p1, p2, p3)
            
            if angle < math.pi - max_angle_rad:  # Sharp corner detected
                # Add smoothed corner points
                smooth_points = self._create_corner_arc(p1, p2, p3, corner_radius)
                smoothed.extend(smooth_points)
            else:
                smoothed.append(p2)
        
        return smoothed
    
    def _calculate_angle(self, p1: Point2D, p2: Point2D, p3: Point2D) -> float:
        v1 = Point2D(p1.x - p2.x, p1.y - p2.y)
        v2 = Point2D(p3.x - p2.x, p3.y - p2.y)
        
        # Normalize vectors
        v1_len = math.sqrt(v1.x**2 + v1.y**2)
        v2_len = math.sqrt(v2.x**2 + v2.y**2)
        
        if v1_len < 1e-10 or v2_len < 1e-10:
            return math.pi
        
        v1_norm = Point2D(v1.x / v1_len, v1.y / v1_len)
        v2_norm = Point2D(v2.x / v2_len, v2.y / v2_len)
        
        # Calculate dot product
        dot_product = v1_norm.x * v2_norm.x + v1_norm.y * v2_norm.y
        dot_product = max(-1.0, min(1.0, dot_product))  # Clamp to valid range
        
        return math.acos(dot_product)
    
    def _create_corner_arc(self, p1: Point2D, p2: Point2D, p3: Point2D, 
                          radius: float) -> List[Point2D]:
        # Simplified corner smoothing - create a few points along an arc
        arc_points = []
        
        # Calculate vectors
        v1 = Point2D(p1.x - p2.x, p1.y - p2.y)
        v2 = Point2D(p3.x - p2.x, p3.y - p2.y)
        
        # Normalize
        v1_len = math.sqrt(v1.x**2 + v1.y**2)
        v2_len = math.sqrt(v2.x**2 + v2.y**2)
        
        if v1_len < 1e-10 or v2_len < 1e-10:
            return [p2]
        
        v1_norm = Point2D(v1.x / v1_len, v1.y / v1_len)
        v2_norm = Point2D(v2.x / v2_len, v2.y / v2_len)
        
        # Create arc points (simplified)
        num_arc_points = 3
        for i in range(num_arc_points):
            t = i / (num_arc_points - 1)
            
            # Linear interpolation between normalized vectors
            interp_x = v1_norm.x * (1 - t) + v2_norm.x * t
            interp_y = v1_norm.y * (1 - t) + v2_norm.y * t
            
            # Normalize interpolated vector
            interp_len = math.sqrt(interp_x**2 + interp_y**2)
            if interp_len > 1e-10:
                interp_x /= interp_len
                interp_y /= interp_len
            
            # Create arc point
            arc_point = Point2D(
                p2.x + interp_x * radius,
                p2.y + interp_y * radius
            )
            arc_points.append(arc_point)
        
        return arc_points
    
    def _is_overhang_perimeter(self, polygon: LayerPolygon, 
                              layer_height: float) -> bool:
        # Simplified overhang detection
        # In practice, this would compare with previous layer
        return False
    
    def _offset_polygon(self, polygon: LayerPolygon, 
                       distance: float) -> Optional[LayerPolygon]:
        if len(polygon.points) < 3:
            return None
        
        offset_points = []
        n = len(polygon.points)
        
        for i in range(n):
            p1 = polygon.points[(i - 1) % n]
            p2 = polygon.points[i]
            p3 = polygon.points[(i + 1) % n]
            
            # Calculate edge vectors
            v1 = Point2D(p2.x - p1.x, p2.y - p1.y)
            v2 = Point2D(p3.x - p2.x, p3.y - p2.y)
            
            # Normalize vectors
            v1_len = math.sqrt(v1.x**2 + v1.y**2)
            v2_len = math.sqrt(v2.x**2 + v2.y**2)
            
            if v1_len > 1e-10:
                v1.x /= v1_len
                v1.y /= v1_len
            if v2_len > 1e-10:
                v2.x /= v2_len
                v2.y /= v2_len
            
            # Calculate normal vectors (perpendicular)
            n1 = Point2D(-v1.y, v1.x)
            n2 = Point2D(-v2.y, v2.x)
            
            # Average normal for offset direction
            avg_normal = Point2D((n1.x + n2.x) / 2, (n1.y + n2.y) / 2)
            normal_len = math.sqrt(avg_normal.x**2 + avg_normal.y**2)
            
            if normal_len > 1e-10:
                avg_normal.x /= normal_len
                avg_normal.y /= normal_len
                
                # Calculate miter length to avoid self-intersection
                angle = self._calculate_angle(p1, p2, p3)
                miter_limit = 2.0  # Limit miter length
                
                if angle > 1e-6:
                    miter_length = abs(distance / math.sin(angle / 2))
                    if miter_length > miter_limit * abs(distance):
                        miter_length = miter_limit * abs(distance)
                else:
                    miter_length = abs(distance)
                
                # Create offset point
                offset_point = Point2D(
                    p2.x + avg_normal.x * miter_length,
                    p2.y + avg_normal.y * miter_length
                )
                offset_points.append(offset_point)
        
        # Check if offset polygon is valid
        if len(offset_points) >= 3:
            offset_polygon = LayerPolygon(points=offset_points, is_hole=polygon.is_hole)
            
            # Check if polygon area is reasonable
            if offset_polygon.area() > 0.01:  # Minimum area threshold
                return offset_polygon
        
        return None
    
    def _optimize_perimeter_order(self, perimeter_layer: PerimeterLayer):
        if not perimeter_layer.paths:
            return
        
        # Separate external and internal perimeters
        external_paths = perimeter_layer.get_external_perimeters()
        internal_paths = perimeter_layer.get_internal_perimeters()
        
        # Sort paths by area (larger first for external, smaller first for internal)
        external_paths.sort(key=lambda p: self._calculate_path_area(p), reverse=True)
        internal_paths.sort(key=lambda p: self._calculate_path_area(p), reverse=False)
        
        # Reorder for optimal printing (external -> internal)
        perimeter_layer.paths = external_paths + internal_paths
        
        # Optimize path directions
        self._optimize_path_directions(perimeter_layer)
    
    def _calculate_path_area(self, path: PerimeterPath) -> float:
        if len(path.points) < 3:
            return 0.0
        
        # Use shoelace formula
        area = 0.0
        n = len(path.points)
        
        for i in range(n):
            j = (i + 1) % n
            area += path.points[i].x * path.points[j].y
            area -= path.points[j].x * path.points[i].y
        
        return abs(area) / 2.0
    
    def _optimize_path_directions(self, perimeter_layer: PerimeterLayer):
        for path in perimeter_layer.paths:
            # External perimeters should be counterclockwise
            # Internal perimeters (holes) should be clockwise
            if path.perimeter_type == PerimeterType.EXTERNAL and not path.is_hole:
                if self._is_clockwise(path.points):
                    path.reverse()
            elif path.is_hole:
                if not self._is_clockwise(path.points):
                    path.reverse()
    
    def _is_clockwise(self, points: List[Point2D]) -> bool:
        if len(points) < 3:
            return False
        
        signed_area = 0.0
        n = len(points)
        
        for i in range(n):
            j = (i + 1) % n
            signed_area += (points[j].x - points[i].x) * (points[j].y + points[i].y)
        
        return signed_area > 0
    
    def generate_thin_walls(self, polygon: LayerPolygon, 
                           layer_height: float) -> List[PerimeterPath]:
        thin_wall_paths = []
        
        # Detect thin wall areas
        thin_areas = self._detect_thin_walls(polygon)
        
        for thin_area in thin_areas:
            # Create centerline path for thin wall
            centerline = self._generate_thin_wall_centerline(thin_area)
            
            if centerline and len(centerline) >= 2:
                thin_wall_path = PerimeterPath(
                    points=centerline,
                    perimeter_type=PerimeterType.INTERNAL,
                    speed=self.settings.perimeter_speed * 0.8,  # Slower for thin walls
                    extrusion_width=min(self.internal_width, thin_area.get('width', self.internal_width))
                )
                thin_wall_paths.append(thin_wall_path)
        
        return thin_wall_paths
    
    def _detect_thin_walls(self, polygon: LayerPolygon) -> List[Dict]:
        thin_areas = []
        
        # Simplified thin wall detection
        # Production implementation would use medial axis transform
        
        # Sample points along polygon edges
        edge_samples = self._sample_polygon_edges(polygon, 1.0)  # 1mm sampling
        
        for sample in edge_samples:
            # Calculate local width by finding opposite edge
            width = self._calculate_local_width(sample, polygon)
            
            if 0 < width <= self.thin_wall_width:
                thin_areas.append({
                    'center': sample,
                    'width': width,
                    'direction': self._calculate_width_direction(sample, polygon)
                })
        
        # Merge nearby thin areas
        merged_areas = self._merge_thin_areas(thin_areas)
        
        return merged_areas
    
    def _sample_polygon_edges(self, polygon: LayerPolygon, 
                            spacing: float) -> List[Point2D]:
        samples = []
        
        if len(polygon.points) < 2:
            return samples
        
        n = len(polygon.points)
        
        for i in range(n):
            p1 = polygon.points[i]
            p2 = polygon.points[(i + 1) % n]
            
            edge_length = p1.distance(p2)
            if edge_length <= 0:
                continue
            
            num_samples = max(1, int(edge_length / spacing))
            
            for j in range(num_samples):
                t = j / num_samples if num_samples > 1 else 0.5
                sample_x = p1.x + t * (p2.x - p1.x)
                sample_y = p1.y + t * (p2.y - p1.y)
                samples.append(Point2D(sample_x, sample_y))
        
        return samples
    
    def _calculate_local_width(self, point: Point2D, 
                             polygon: LayerPolygon) -> float:
        # Find nearest point on opposite side of polygon
        min_distance = float('inf')
        
        n = len(polygon.points)
        
        for i in range(n):
            p1 = polygon.points[i]
            p2 = polygon.points[(i + 1) % n]
            
            # Calculate distance from point to edge
            edge_distance = self._point_to_edge_distance(point, p1, p2)
            min_distance = min(min_distance, edge_distance)
        
        return min_distance * 2  # Width is twice the distance to nearest edge
    
    def _point_to_edge_distance(self, point: Point2D, 
                               edge_start: Point2D, edge_end: Point2D) -> float:
        # Vector from edge_start to edge_end
        edge_vec = Point2D(edge_end.x - edge_start.x, edge_end.y - edge_start.y)
        edge_length_sq = edge_vec.x**2 + edge_vec.y**2
        
        if edge_length_sq < 1e-10:
            return point.distance(edge_start)
        
        # Vector from edge_start to point
        point_vec = Point2D(point.x - edge_start.x, point.y - edge_start.y)
        
        # Project point onto edge
        t = (point_vec.x * edge_vec.x + point_vec.y * edge_vec.y) / edge_length_sq
        t = max(0, min(1, t))  # Clamp to edge segment
        
        # Find closest point on edge
        closest = Point2D(
            edge_start.x + t * edge_vec.x,
            edge_start.y + t * edge_vec.y
        )
        
        return point.distance(closest)
    
    def _calculate_width_direction(self, point: Point2D, 
                                 polygon: LayerPolygon) -> Point2D:
        # Simplified - return direction to polygon centroid
        centroid = self._calculate_polygon_centroid(polygon)
        
        direction = Point2D(centroid.x - point.x, centroid.y - point.y)
        length = math.sqrt(direction.x**2 + direction.y**2)
        
        if length > 1e-10:
            direction.x /= length
            direction.y /= length
        
        return direction
    
    def _calculate_polygon_centroid(self, polygon: LayerPolygon) -> Point2D:
        if not polygon.points:
            return Point2D(0, 0)
        
        cx = sum(p.x for p in polygon.points) / len(polygon.points)
        cy = sum(p.y for p in polygon.points) / len(polygon.points)
        
        return Point2D(cx, cy)
    
    def _merge_thin_areas(self, thin_areas: List[Dict]) -> List[Dict]:
        if not thin_areas:
            return []
        
        merged = []
        merge_distance = 2.0  # mm
        
        for area in thin_areas:
            merged_with_existing = False
            
            for existing in merged:
                if area['center'].distance(existing['center']) < merge_distance:
                    # Merge areas
                    existing['width'] = (existing['width'] + area['width']) / 2
                    merged_with_existing = True
                    break
            
            if not merged_with_existing:
                merged.append(area.copy())
        
        return merged
    
    def _generate_thin_wall_centerline(self, thin_area: Dict) -> List[Point2D]:
        # Simplified centerline generation
        # Production implementation would use proper medial axis
        
        center = thin_area['center']
        direction = thin_area['direction']
        width = thin_area['width']
        
        # Create short line segment for thin wall
        half_length = width
        
        start_point = Point2D(
            center.x - direction.x * half_length,
            center.y - direction.y * half_length
        )
        
        end_point = Point2D(
            center.x + direction.x * half_length,
            center.y + direction.y * half_length
        )
        
        return [start_point, end_point]
    
    def generate_gap_fill(self, polygon: LayerPolygon, 
                         perimeter_paths: List[PerimeterPath],
                         layer_height: float) -> List[PerimeterPath]:
        gap_fill_paths = []
        
        # Find gaps between perimeters
        gaps = self._detect_gaps(polygon, perimeter_paths)
        
        for gap in gaps:
            if gap['width'] > 0 and gap['width'] <= self.gap_fill_threshold:
                # Create gap fill path
                gap_path = self._create_gap_fill_path(gap)
                
                if gap_path:
                    gap_fill_paths.append(gap_path)
        
        return gap_fill_paths
    
    def _detect_gaps(self, polygon: LayerPolygon, 
                    perimeter_paths: List[PerimeterPath]) -> List[Dict]:
        gaps = []
        
        # Simplified gap detection
        # Production implementation would use proper geometric analysis
        
        # Sample polygon interior
        bounds = self._get_polygon_bounds(polygon)
        sample_spacing = 0.5  # mm
        
        x = bounds[0]
        while x <= bounds[2]:
            y = bounds[1]
            while y <= bounds[3]:
                sample_point = Point2D(x, y)
                
                if self._point_in_polygon(sample_point, polygon):
                    # Check if point is covered by any perimeter
                    covered = False
                    
                    for path in perimeter_paths:
                        if self._point_near_path(sample_point, path, path.extrusion_width / 2):
                            covered = True
                            break
                    
                    if not covered:
                        # Found uncovered area - potential gap
                        gap_width = self._estimate_gap_width(sample_point, perimeter_paths)
                        
                        if gap_width > 0:
                            gaps.append({
                                'center': sample_point,
                                'width': gap_width
                            })
                
                y += sample_spacing
            x += sample_spacing
        
        return gaps
    
    def _get_polygon_bounds(self, polygon: LayerPolygon) -> Tuple[float, float, float, float]:
        if not polygon.points:
            return 0, 0, 0, 0
        
        min_x = min(p.x for p in polygon.points)
        max_x = max(p.x for p in polygon.points)
        min_y = min(p.y for p in polygon.points)
        max_y = max(p.y for p in polygon.points)
        
        return min_x, min_y, max_x, max_y
    
    def _point_in_polygon(self, point: Point2D, polygon: LayerPolygon) -> bool:
        x, y = point.x, point.y
        n = len(polygon.points)
        inside = False
        
        p1x, p1y = polygon.points[0].x, polygon.points[0].y
        for i in range(1, n + 1):
            p2x, p2y = polygon.points[i % n].x, polygon.points[i % n].y
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def _point_near_path(self, point: Point2D, path: PerimeterPath, 
                        threshold: float) -> bool:
        for i in range(len(path.points) - 1):
            p1 = path.points[i]
            p2 = path.points[i + 1]
            
            distance = self._point_to_edge_distance(point, p1, p2)
            if distance <= threshold:
                return True
        
        return False
    
    def _estimate_gap_width(self, point: Point2D, 
                          perimeter_paths: List[PerimeterPath]) -> float:
        min_distance = float('inf')
        
        for path in perimeter_paths:
            for i in range(len(path.points) - 1):
                p1 = path.points[i]
                p2 = path.points[i + 1]
                
                distance = self._point_to_edge_distance(point, p1, p2)
                min_distance = min(min_distance, distance)
        
        return min_distance * 2  # Gap width is approximately twice distance to nearest perimeter
    
    def _create_gap_fill_path(self, gap: Dict) -> Optional[PerimeterPath]:
        center = gap['center']
        width = gap['width']

        # Create simple gap fill path (line segment)
        # Production implementation would create more sophisticated patterns

        half_width = width / 2

        path_points = [
            Point2D(center.x - half_width, center.y),
            Point2D(center.x + half_width, center.y)
        ]

        gap_path = PerimeterPath(
            points=path_points,
            perimeter_type=PerimeterType.INTERNAL,
            speed=self.settings.perimeter_speed * 0.6,  # Slower for gap fill
            extrusion_width=width
        )

        return gap_path

    # ===== ADVANCED PERIMETER OPTIMIZATION METHODS =====

    def optimize_perimeter_flow(self, perimeter_layer: PerimeterLayer) -> PerimeterLayer:
        if len(perimeter_layer.paths) <= 1:
            return perimeter_layer

        optimized_layer = PerimeterLayer(layer_height=perimeter_layer.layer_height)

        # Start with external perimeter
        external_perimeters = [p for p in perimeter_layer.paths if p.perimeter_type == PerimeterType.EXTERNAL]
        internal_perimeters = [p for p in perimeter_layer.paths if p.perimeter_type == PerimeterType.INTERNAL]
        overhang_perimeters = [p for p in perimeter_layer.paths if p.perimeter_type == PerimeterType.OVERHANG]

        # Optimize external perimeters first
        if external_perimeters:
            optimized_externals = self._optimize_perimeter_sequence(external_perimeters)
            optimized_layer.paths.extend(optimized_externals)

        # Then overhang perimeters
        if overhang_perimeters:
            optimized_overhangs = self._optimize_perimeter_sequence(overhang_perimeters)
            optimized_layer.paths.extend(optimized_overhangs)

        # Finally internal perimeters
        if internal_perimeters:
            optimized_internals = self._optimize_perimeter_sequence(internal_perimeters)
            optimized_layer.paths.extend(optimized_internals)

        return optimized_layer

    def _optimize_perimeter_sequence(self, perimeters: List[PerimeterPath]) -> List[PerimeterPath]:
        if len(perimeters) <= 1:
            return perimeters

        optimized = [perimeters[0]]  # Start with first perimeter
        remaining = perimeters[1:]

        while remaining:
            current_end = optimized[-1].points[-1]
            min_distance = float('inf')
            best_idx = 0

            # Find closest starting point
            for i, perimeter in enumerate(remaining):
                start_point = perimeter.points[0]
                distance = math.sqrt((current_end.x - start_point.x)**2 + (current_end.y - start_point.y)**2)

                if distance < min_distance:
                    min_distance = distance
                    best_idx = i

            optimized.append(remaining[best_idx])
            remaining.pop(best_idx)

        return optimized

    def generate_bridge_perimeters(self, polygon: LayerPolygon,
                                 bridge_directions: List[Point2D]) -> List[PerimeterPath]:
        bridge_paths = []

        for direction in bridge_directions:
            # Create bridge perimeter aligned with bridge direction
            bridge_path = self._create_bridge_path(polygon, direction)
            if bridge_path:
                bridge_paths.append(bridge_path)

        return bridge_paths

    def _create_bridge_path(self, polygon: LayerPolygon, direction: Point2D) -> Optional[PerimeterPath]:
        # Simplify polygon along bridge direction
        simplified_points = self._simplify_along_direction(polygon.points, direction)

        if len(simplified_points) < 2:
            return None

        bridge_path = PerimeterPath(
            points=simplified_points,
            perimeter_type=PerimeterType.EXTERNAL,
            speed=self.settings.perimeter_speed * 0.7,  # Slower for bridges
            extrusion_width=self.external_width * 1.2   # Wider for bridge strength
        )

        return bridge_path

    def _simplify_along_direction(self, points: List[Point2D], direction: Point2D) -> List[Point2D]:
        if len(points) < 3:
            return points

        # Project points onto direction vector
        projections = []
        for point in points:
            projection = point.x * direction.x + point.y * direction.y
            projections.append((projection, point))

        # Sort by projection
        projections.sort(key=lambda x: x[0])

        # Keep only significant points (simplified)
        simplified = []
        threshold = 0.5  # mm tolerance

        current_projection = projections[0][0]
        simplified.append(projections[0][1])

        for proj, point in projections[1:]:
            if proj - current_projection > threshold:
                simplified.append(point)
                current_projection = proj

        simplified.append(projections[-1][1])  # Always include last point

        return simplified

    def generate_temperature_tower_perimeters(self, polygon: LayerPolygon,
                                            temperature_range: Tuple[float, float],
                                            layer_height: float) -> List[PerimeterPath]:
        temp_paths = []

        start_temp, end_temp = temperature_range
        temp_steps = 10  # Number of temperature steps

        for step in range(temp_steps):
            temp_ratio = step / (temp_steps - 1)
            current_temp = start_temp + (end_temp - start_temp) * temp_ratio

            # Create perimeter with temperature metadata
            temp_path = self._create_perimeter_path(polygon, PerimeterType.EXTERNAL, layer_height)

            if temp_path:
                # Add temperature metadata (would be used in G-code generation)
                temp_path._temperature = current_temp
                temp_paths.append(temp_path)

        return temp_paths

    def analyze_perimeter_quality(self, perimeter_layer: PerimeterLayer) -> Dict[str, Any]:
        analysis = {
            'total_paths': len(perimeter_layer.paths),
            'total_length': 0.0,
            'external_perimeters': 0,
            'internal_perimeters': 0,
            'overhang_perimeters': 0,
            'average_speed': 0.0,
            'speed_variation': 0.0,
            'width_consistency': 0.0,
            'path_continuity': 0.0
        }

        speeds = []
        widths = []
        total_length = 0.0

        for path in perimeter_layer.paths:
            length = path.length()
            total_length += length

            speeds.append(path.speed)
            widths.append(path.extrusion_width)

            if path.perimeter_type == PerimeterType.EXTERNAL:
                analysis['external_perimeters'] += 1
            elif path.perimeter_type == PerimeterType.INTERNAL:
                analysis['internal_perimeters'] += 1
            elif path.perimeter_type == PerimeterType.OVERHANG:
                analysis['overhang_perimeters'] += 1

        analysis['total_length'] = total_length

        if speeds:
            analysis['average_speed'] = sum(speeds) / len(speeds)
            analysis['speed_variation'] = np.std(speeds) if len(speeds) > 1 else 0.0

        if widths:
            analysis['width_consistency'] = 1.0 - (np.std(widths) / np.mean(widths)) if np.mean(widths) > 0 else 0.0

        # Calculate path continuity (how well paths connect)
        analysis['path_continuity'] = self._calculate_path_continuity(perimeter_layer.paths)

        return analysis

    def _calculate_path_continuity(self, paths: List[PerimeterPath]) -> float:
        if len(paths) <= 1:
            return 1.0

        total_gap = 0.0
        max_reasonable_gap = 5.0  # mm

        for i in range(len(paths) - 1):
            end_point = paths[i].points[-1]
            start_point = paths[i + 1].points[0]

            gap = math.sqrt((end_point.x - start_point.x)**2 + (end_point.y - start_point.y)**2)
            total_gap += min(gap, max_reasonable_gap)  # Cap at reasonable maximum

        avg_gap = total_gap / (len(paths) - 1)
        continuity = 1.0 - (avg_gap / max_reasonable_gap)

        return max(0.0, continuity)

    def generate_perimeter_preview(self, perimeter_layer: PerimeterLayer,
                                 image_size: Tuple[int, int] = (800, 800)) -> Optional[Any]:
        try:
            import matplotlib.pyplot as plt
            from matplotlib.patches import Polygon
            import matplotlib.cm as cm

            fig, ax = plt.subplots(figsize=(10, 10))

            # Color map for different perimeter types
            colors = {
                PerimeterType.EXTERNAL: 'red',
                PerimeterType.INTERNAL: 'blue',
                PerimeterType.OVERHANG: 'orange'
            }

            for path in perimeter_layer.paths:
                if len(path.points) < 3:
                    continue

                # Convert points to coordinates
                x_coords = [p.x for p in path.points]
                y_coords = [p.y for p in path.points]

                # Plot path
                color = colors.get(path.perimeter_type, 'gray')
                ax.plot(x_coords + [x_coords[0]], y_coords + [y_coords[0]],
                       color=color, linewidth=2, alpha=0.7)

                # Fill polygon
                if len(path.points) >= 3:
                    polygon = Polygon([(p.x, p.y) for p in path.points],
                                     facecolor=color, alpha=0.3)
                    ax.add_patch(polygon)

            ax.set_aspect('equal')
            ax.set_title(f'Perimeter Preview - Layer {perimeter_layer.layer_height:.2f}mm')
            ax.grid(True, alpha=0.3)

            # Add legend
            legend_elements = []
            for ptype, color in colors.items():
                legend_elements.append(plt.Line2D([0], [0], color=color, label=ptype.value))
            ax.legend(handles=legend_elements)

            return fig

        except ImportError:
            # Matplotlib not available
            return None

    def export_perimeter_data(self, perimeter_layer: PerimeterLayer,
                            filename: str) -> bool:
        try:
            import json

            data = {
                'layer_height': perimeter_layer.layer_height,
                'perimeters': []
            }

            for i, path in enumerate(perimeter_layer.paths):
                path_data = {
                    'index': i,
                    'type': path.perimeter_type.value,
                    'is_hole': path.is_hole,
                    'speed': path.speed,
                    'width': path.extrusion_width,
                    'length': path.length(),
                    'point_count': len(path.points),
                    'points': [{'x': p.x, 'y': p.y} for p in path.points]
                }
                data['perimeters'].append(path_data)

            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)

            return True

        except Exception as e:
            print(f"Failed to export perimeter data: {e}")
            return False

    def get_generation_stats(self) -> Dict[str, Any]:
        return self.generation_stats.copy()

    def reset_stats(self):
        self.generation_stats = {
            'total_perimeters_generated': 0,
            'average_generation_time': 0.0,
            'quality_enhancements_applied': 0,
            'overhang_regions_detected': 0
        }

    # ===== ADDITIONAL UTILITY METHODS =====

    def validate_perimeter_integrity(self, perimeter_layer: PerimeterLayer) -> List[str]:
        issues = []

        for i, path in enumerate(perimeter_layer.paths):
            # Check for degenerate paths
            if len(path.points) < 3:
                issues.append(f"Path {i}: Too few points ({len(path.points)})")

            # Check for self-intersection (simplified)
            if self._has_self_intersection(path.points):
                issues.append(f"Path {i}: Self-intersecting")

            # Check for unreasonable speeds
            if path.speed <= 0 or path.speed > 200:
                issues.append(f"Path {i}: Invalid speed ({path.speed})")

            # Check for zero width
            if path.extrusion_width <= 0:
                issues.append(f"Path {i}: Invalid extrusion width ({path.extrusion_width})")

        # Check for overlapping perimeters
        for i in range(len(perimeter_layer.paths)):
            for j in range(i + 1, len(perimeter_layer.paths)):
                if self._perimeters_overlap(perimeter_layer.paths[i], perimeter_layer.paths[j]):
                    issues.append(f"Paths {i} and {j}: Overlapping perimeters")

        return issues

    def _has_self_intersection(self, points: List[Point2D]) -> bool:
        if len(points) < 4:
            return False

        # Simple check - compare each segment with non-adjacent segments
        for i in range(len(points)):
            seg1_start = points[i]
            seg1_end = points[(i + 1) % len(points)]

            for j in range(i + 2, len(points)):
                if j == len(points) - 1 and i == 0:  # Adjacent segments
                    continue

                seg2_start = points[j]
                seg2_end = points[(j + 1) % len(points)]

                if self._segments_intersect(seg1_start, seg1_end, seg2_start, seg2_end):
                    return True

        return False

    def _segments_intersect(self, p1: Point2D, p2: Point2D, p3: Point2D, p4: Point2D) -> bool:
        def orientation(p, q, r):
            val = (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y)
            if abs(val) < 1e-10: return 0  # collinear
            return 1 if val > 0 else 2  # clock or counterclock wise

        o1 = orientation(p1, p2, p3)
        o2 = orientation(p1, p2, p4)
        o3 = orientation(p3, p4, p1)
        o4 = orientation(p3, p4, p2)

        if o1 != o2 and o3 != o4:
            return True

        return False

    def _perimeters_overlap(self, path1: PerimeterPath, path2: PerimeterPath) -> bool:
        # Simple bounding box overlap check
        def get_bbox(path):
            if not path.points:
                return None
            min_x = min(p.x for p in path.points)
            max_x = max(p.x for p in path.points)
            min_y = min(p.y for p in path.points)
            max_y = max(p.y for p in path.points)
            return (min_x, min_y, max_x, max_y)

        bbox1 = get_bbox(path1)
        bbox2 = get_bbox(path2)

        if not bbox1 or not bbox2:
            return False

        # Check for overlap
        return not (bbox1[2] < bbox2[0] or bbox2[2] < bbox1[0] or
                   bbox1[3] < bbox2[1] or bbox2[3] < bbox1[1])

# Example usage
if __name__ == "__main__":
    from .slicer_core import PrintSettings, Point2D, LayerPolygon
    
    # Create test settings
    settings = PrintSettings(
        perimeters=3,
        external_perimeter_speed=40.0,
        perimeter_speed=50.0,
        extrusion_width=0.4
    )
    
    # Create test polygon (square with hole)
    outer_points = [
        Point2D(0, 0), Point2D(20, 0), Point2D(20, 20), Point2D(0, 20)
    ]
    outer_polygon = LayerPolygon(points=outer_points)
    
    # Generate perimeters
    generator = PerimeterGenerator(settings)
    perimeter_layer = generator.generate_perimeters(outer_polygon, 0.2)
    
    print(f"Generated {len(perimeter_layer.paths)} perimeter paths")
    
    for i, path in enumerate(perimeter_layer.paths):
        print(f"Path {i}: {path.perimeter_type.value}, {len(path.points)} points, "
              f"{path.length():.2f}mm length, {path.speed:.1f}mm/s speed")
    
    # Test thin wall detection
    thin_walls = generator.generate_thin_walls(outer_polygon, 0.2)
    print(f"Generated {len(thin_walls)} thin wall paths")
    
    # Test gap fill
    gap_fills = generator.generate_gap_fill(outer_polygon, perimeter_layer.paths, 0.2)
    print(f"Generated {len(gap_fills)} gap fill paths")
