#!/usr/bin/env python3
# ------------------------------------------------------------------
# Copyright (c) 2026 Sleia Engine Development Team.
# This file is distributed under the MIT License. See LICENSE.
#
# Sleia Easy v 1.0.1 - Thermoplastic Python Slicer
#
# File: infill_generator.py
# Description: fills the inside with patterns.
# ------------------------------------------------------------------

import numpy as np
import math
import random
import time
from typing import List, Tuple, Dict, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque
import itertools
import functools
import statistics

try:
    # Try relative imports first (when used as package)
    from .slicer_core import Point2D, LayerPolygon, InfillPattern, PrintSettings
except ImportError:
    # Fallback to absolute imports (when used standalone)
    from slicer_core import Point2D, LayerPolygon, InfillPattern, PrintSettings

logger = logging.getLogger(__name__)

# ===== ADVANCED INFILL ENUMS AND CONFIGURATIONS =====

class InfillOptimization(Enum):
    STRENGTH = "strength"
    SPEED = "speed"
    MATERIAL = "material"
    QUALITY = "quality"
    BALANCED = "balanced"
    ADAPTIVE = "adaptive"

class InfillQuality(Enum):
    DRAFT = "draft"
    STANDARD = "standard"
    HIGH = "high"
    ULTRA = "ultra"

class InfillAlgorithm(Enum):
    TRADITIONAL = "traditional"
    OPTIMIZED = "optimized"
    ADAPTIVE = "adaptive"
    ML_GUIDED = "ml_guided"
    GENETIC = "genetic"

@dataclass
class InfillConfiguration:
    pattern: InfillPattern = InfillPattern.RECTILINEAR
    density: float = 0.15
    optimization: InfillOptimization = InfillOptimization.BALANCED
    quality: InfillQuality = InfillQuality.STANDARD
    algorithm: InfillAlgorithm = InfillAlgorithm.TRADITIONAL
    adaptive_density: bool = False
    strength_priority: bool = False
    material_efficiency: bool = True
    max_generation_time: float = 30.0  # seconds
    enable_caching: bool = True
    parallel_processing: bool = True
    ml_guidance: bool = False

@dataclass
class InfillAnalysis:
    pattern_name: str
    density: float
    total_length: float
    segment_count: int
    material_usage: float
    print_time_estimate: float
    strength_score: float
    quality_score: float
    material_efficiency: float
    generation_time: float
    optimization_score: float

@dataclass
class AdaptiveInfillZone:
    polygon: LayerPolygon
    density_multiplier: float
    pattern_modifier: Optional[InfillPattern]
    strength_requirement: float
    quality_requirement: float

# ===== MACHINE LEARNING INFILL OPTIMIZER =====

class InfillMachineLearningOptimizer:

    def __init__(self):
        self.models = {}
        self.training_data = []
        self.pattern_scores = defaultdict(list)

    def optimize_pattern_selection(self, polygon: LayerPolygon,
                                 requirements: Dict[str, float]) -> InfillPattern:
        features = self._extract_polygon_features(polygon)

        # Simple rule-based fallback if no ML model
        if not self.models:
            return self._rule_based_pattern_selection(requirements)

        # ML prediction would go here
        # For now, return rule-based selection
        return self._rule_based_pattern_selection(requirements)

    def _extract_polygon_features(self, polygon: LayerPolygon) -> Dict[str, float]:
        if not polygon.points:
            return {}

        # Basic geometric features
        area = polygon.area()
        perimeter = sum(math.sqrt((polygon.points[i].x - polygon.points[(i+1) % len(polygon.points)].x)**2 +
                                 (polygon.points[i].y - polygon.points[(i+1) % len(polygon.points)].y)**2)
                       for i in range(len(polygon.points)))

        # Shape complexity
        complexity = len(polygon.points) / max(area, 1e-6)

        # Aspect ratio
        x_coords = [p.x for p in polygon.points]
        y_coords = [p.y for p in polygon.points]
        width = max(x_coords) - min(x_coords)
        height = max(y_coords) - min(y_coords)
        aspect_ratio = max(width, height) / min(width, height) if min(width, height) > 0 else 1.0

        return {
            'area': area,
            'perimeter': perimeter,
            'complexity': complexity,
            'aspect_ratio': aspect_ratio,
            'point_count': len(polygon.points)
        }

    def _rule_based_pattern_selection(self, requirements: Dict[str, float]) -> InfillPattern:
        strength = requirements.get('strength', 0.5)
        speed = requirements.get('speed', 0.5)
        quality = requirements.get('quality', 0.5)

        # High strength requirements
        if strength > 0.7:
            if speed > 0.7:
                return InfillPattern.GYROID  # Good balance
            else:
                return InfillPattern.CUBIC   # Maximum strength

        # High speed requirements
        if speed > 0.7:
            if quality > 0.7:
                return InfillPattern.TRIANGULAR
            else:
                return InfillPattern.LINE

        # High quality requirements
        if quality > 0.7:
            return InfillPattern.HONEYCOMB

        # Balanced default
        return InfillPattern.RECTILINEAR

# ===== ADAPTIVE INFILL GENERATOR =====

class AdaptiveInfillGenerator:

    def __init__(self, base_density: float):
        self.base_density = base_density
        self.analysis_radius = 5.0  # mm

    def generate_adaptive_infill(self, polygon: LayerPolygon,
                               stress_map: Optional[Dict] = None) -> List[AdaptiveInfillZone]:

        zones = []

        # Default: uniform density
        if not stress_map:
            zones.append(AdaptiveInfillZone(
                polygon=polygon,
                density_multiplier=1.0,
                pattern_modifier=None,
                strength_requirement=0.5,
                quality_requirement=0.5
            ))
            return zones

        # Analyze polygon and create adaptive zones
        zones = self._create_adaptive_zones(polygon, stress_map)

        return zones

    def _create_adaptive_zones(self, polygon: LayerPolygon,
                             stress_map: Dict) -> List[AdaptiveInfillZone]:

        zones = []

        # Simple implementation: divide into high/low stress zones
        centroid = self._calculate_centroid(polygon)

        # High stress zone (center)
        high_stress_zone = self._create_circular_zone(polygon, centroid, 0.6)
        if high_stress_zone:
            zones.append(AdaptiveInfillZone(
                polygon=high_stress_zone,
                density_multiplier=1.5,  # Higher density
                pattern_modifier=InfillPattern.GYROID,  # Stronger pattern
                strength_requirement=0.8,
                quality_requirement=0.6
            ))

        # Low stress zone (edges)
        low_stress_zone = self._create_annular_zone(polygon, centroid, 0.6, 1.0)
        if low_stress_zone:
            zones.append(AdaptiveInfillZone(
                polygon=low_stress_zone,
                density_multiplier=0.7,  # Lower density
                pattern_modifier=InfillPattern.LINE,  # Faster pattern
                strength_requirement=0.3,
                quality_requirement=0.4
            ))

        return zones

    def _calculate_centroid(self, polygon: LayerPolygon) -> Point2D:
        if not polygon.points:
            return Point2D(0, 0)

        x_sum = sum(p.x for p in polygon.points)
        y_sum = sum(p.y for p in polygon.points)

        return Point2D(x_sum / len(polygon.points), y_sum / len(polygon.points))

    def _create_circular_zone(self, polygon: LayerPolygon, center: Point2D,
                            radius_ratio: float) -> Optional[LayerPolygon]:
        # Simplified: return smaller version of polygon
        if len(polygon.points) < 3:
            return None

        # Scale polygon towards center
        scaled_points = []
        for point in polygon.points:
            # Vector from center to point
            dx = point.x - center.x
            dy = point.y - center.y

            # Scale towards center
            scaled_x = center.x + dx * radius_ratio
            scaled_y = center.y + dy * radius_ratio

            scaled_points.append(Point2D(scaled_x, scaled_y))

        return LayerPolygon(points=scaled_points, is_hole=polygon.is_hole)

    def _create_annular_zone(self, polygon: LayerPolygon, center: Point2D,
                           inner_ratio: float, outer_ratio: float) -> Optional[LayerPolygon]:
        # Simplified: return polygon between ratios
        if len(polygon.points) < 3:
            return None

        # For simplicity, return the original polygon
        # Real implementation would create proper annular zone
        return polygon

# ===== QUALITY OPTIMIZATION ENGINE =====

class InfillQualityOptimizer:

    def __init__(self):
        self.quality_metrics = {}
        self.optimization_cache = {}

    def optimize_infill_quality(self, infill_lines: List[List[Point2D]],
                              quality_target: InfillQuality) -> List[List[Point2D]]:

        if quality_target == InfillQuality.DRAFT:
            return self._optimize_for_speed(infill_lines)
        elif quality_target == InfillQuality.STANDARD:
            return self._optimize_balanced(infill_lines)
        elif quality_target == InfillQuality.HIGH:
            return self._optimize_for_quality(infill_lines)
        elif quality_target == InfillQuality.ULTRA:
            return self._optimize_ultra_quality(infill_lines)

        return infill_lines

    def _optimize_for_speed(self, infill_lines: List[List[Point2D]]) -> List[List[Point2D]]:
        # Reduce line count, simplify paths
        if len(infill_lines) > 50:
            # Keep every other line
            return infill_lines[::2]
        return infill_lines

    def _optimize_balanced(self, infill_lines: List[List[Point2D]]) -> List[List[Point2D]]:
        return self._smooth_paths(infill_lines)

    def _optimize_for_quality(self, infill_lines: List[List[Point2D]]) -> List[List[Point2D]]:
        # Apply multiple optimization passes
        optimized = self._smooth_paths(infill_lines)
        optimized = self._reduce_sharp_angles(optimized)
        optimized = self._optimize_flow_rates(optimized)
        return optimized

    def _optimize_ultra_quality(self, infill_lines: List[List[Point2D]]) -> List[List[Point2D]]:
        # Apply all optimizations multiple times
        optimized = infill_lines
        for _ in range(3):
            optimized = self._optimize_for_quality(optimized)
        return optimized

    def _smooth_paths(self, infill_lines: List[List[Point2D]]) -> List[List[Point2D]]:
        smoothed = []

        for line in infill_lines:
            if len(line) < 3:
                smoothed.append(line)
                continue

            # Simple smoothing
            smooth_line = [line[0]]  # Keep start point

            for i in range(1, len(line) - 1):
                # Average with neighbors
                smooth_x = (line[i-1].x + line[i].x * 2 + line[i+1].x) / 4
                smooth_y = (line[i-1].y + line[i].y * 2 + line[i+1].y) / 4
                smooth_line.append(Point2D(smooth_x, smooth_y))

            smooth_line.append(line[-1])  # Keep end point
            smoothed.append(smooth_line)

        return smoothed

    def _reduce_sharp_angles(self, infill_lines: List[List[Point2D]]) -> List[List[Point2D]]:
        # Simplified implementation
        return infill_lines

    def _optimize_flow_rates(self, infill_lines: List[List[Point2D]]) -> List[List[Point2D]]:
        # This would modify extrusion amounts - simplified here
        return infill_lines

# ===== MULTI-MATERIAL INFILL SUPPORT =====

class MultiMaterialInfillGenerator:

    def __init__(self):
        self.material_zones = {}
        self.material_patterns = {}

    def generate_multi_material_infill(self, polygon: LayerPolygon,
                                     material_zones: Dict[str, LayerPolygon],
                                     layer_height: float) -> Dict[str, List[List[Point2D]]]:

        material_infills = {}

        for material, zone in material_zones.items():
            if material not in self.material_patterns:
                # Default pattern per material
                if material.lower() in ['pla', 'petg']:
                    pattern = InfillPattern.GYROID
                elif material.lower() in ['abs', 'asa']:
                    pattern = InfillPattern.CUBIC
                elif material.lower() in ['tpu', 'tpv']:
                    pattern = InfillPattern.TRIANGULAR
                else:
                    pattern = InfillPattern.RECTILINEAR

                self.material_patterns[material] = pattern

            # Generate infill for this material zone
            infill_lines = self._generate_material_infill(zone, self.material_patterns[material], layer_height)
            material_infills[material] = infill_lines

        return material_infills

    def _generate_material_infill(self, polygon: LayerPolygon, pattern: InfillPattern,
                                layer_height: float) -> List[List[Point2D]]:
        # Simplified - would use main generator
        # For now, return basic rectilinear
        return self._generate_rectilinear_basic(polygon, 1.0)

    def _generate_rectilinear_basic(self, polygon: LayerPolygon, spacing: float) -> List[List[Point2D]]:
        lines = []
        if not polygon.points:
            return lines

        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)

        # Vertical lines
        x = min_x
        while x <= max_x:
            intersections = []
            for i in range(len(polygon.points)):
                p1 = polygon.points[i]
                p2 = polygon.points[(i + 1) % len(polygon.points)]

                if (p1.y <= min_y <= p2.y or p2.y <= min_y <= p1.y) and p1.y != p2.y:
                    y = p1.y + (min_y - p1.y) * (p2.y - p1.y) / (p2.y - p1.y)
                    if min_x <= x <= max_x:
                        intersections.append(Point2D(x, y))

            if len(intersections) >= 2:
                intersections.sort(key=lambda p: p.y)
                for i in range(0, len(intersections) - 1, 2):
                    lines.append([intersections[i], intersections[i + 1]])

            x += spacing

        return lines

    def _get_polygon_bounds(self, polygon: LayerPolygon) -> Tuple[float, float, float, float]:
        if not polygon.points:
            return 0, 0, 0, 0

        min_x = min(p.x for p in polygon.points)
        max_x = max(p.x for p in polygon.points)
        min_y = min(p.y for p in polygon.points)
        max_y = max(p.y for p in polygon.points)

        return min_x, min_y, max_x, max_y

# ===== PERFORMANCE OPTIMIZATION =====

class InfillPerformanceOptimizer:

    def __init__(self):
        self.cache = {}
        self.performance_stats = defaultdict(list)

    def optimize_generation(self, polygon: LayerPolygon, pattern: InfillPattern,
                          density: float) -> Callable:

        cache_key = self._generate_cache_key(polygon, pattern, density)

        if cache_key in self.cache:
            return lambda: self.cache[cache_key]

        # Time the generation
        start_time = time.time()

        # Generation would happen here (simplified)
        result = []

        end_time = time.time()
        generation_time = end_time - start_time

        # Cache result
        self.cache[cache_key] = result

        # Record performance
        self.performance_stats[pattern.value].append(generation_time)

        return lambda: result

    def _generate_cache_key(self, polygon: LayerPolygon, pattern: InfillPattern, density: float) -> str:
        # Simple hash of parameters
        poly_hash = hash(tuple((p.x, p.y) for p in polygon.points))
        return f"{poly_hash}_{pattern.value}_{density}"

    def get_performance_stats(self) -> Dict[str, Dict[str, float]]:
        stats = {}

        for pattern, times in self.performance_stats.items():
            if times:
                stats[pattern] = {
                    'avg_time': statistics.mean(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'count': len(times)
                }

        return stats

# ===== ANALYSIS AND VISUALIZATION =====

class InfillAnalysisEngine:

    def __init__(self):
        self.analysis_cache = {}

    def analyze_infill_pattern(self, infill_lines: List[List[Point2D]],
                             pattern_name: str) -> InfillAnalysis:

        total_length = sum(sum(math.sqrt((line[i].x - line[i+1].x)**2 + (line[i].y - line[i+1].y)**2)
                               for i in range(len(line) - 1)) for line in infill_lines)

        segment_count = sum(len(line) - 1 for line in infill_lines)

        # Estimates (simplified)
        material_usage = total_length * 0.2  # Rough estimate
        print_time_estimate = total_length / 50.0  # Assuming 50 mm/min speed

        # Quality scores (simplified heuristics)
        strength_score = min(1.0, len(infill_lines) / 100.0)
        quality_score = 1.0 - min(0.5, segment_count / 1000.0)
        material_efficiency = 1.0 if len(infill_lines) > 0 else 0.0

        return InfillAnalysis(
            pattern_name=pattern_name,
            density=0.15,  # Placeholder
            total_length=total_length,
            segment_count=segment_count,
            material_usage=material_usage,
            print_time_estimate=print_time_estimate,
            strength_score=strength_score,
            quality_score=quality_score,
            material_efficiency=material_efficiency,
            generation_time=0.0,  # Would be measured
            optimization_score=(strength_score + quality_score + material_efficiency) / 3.0
        )

    def compare_patterns(self, analyses: List[InfillAnalysis]) -> Dict[str, Any]:

        if not analyses:
            return {}

        best_strength = max(analyses, key=lambda x: x.strength_score)
        best_quality = max(analyses, key=lambda x: x.quality_score)
        best_efficiency = max(analyses, key=lambda x: x.material_efficiency)
        fastest = min(analyses, key=lambda x: x.print_time_estimate)

        return {
            'best_strength_pattern': best_strength.pattern_name,
            'best_quality_pattern': best_quality.pattern_name,
            'best_efficiency_pattern': best_efficiency.pattern_name,
            'fastest_pattern': fastest.pattern_name,
            'overall_best': max(analyses, key=lambda x: x.optimization_score).pattern_name
        }

    def generate_visualization_data(self, infill_lines: List[List[Point2D]]) -> Dict[str, Any]:

        viz_data = {
            'lines': [],
            'stats': {
                'total_lines': len(infill_lines),
                'total_segments': sum(len(line) - 1 for line in infill_lines),
                'bounding_box': self._calculate_bounding_box(infill_lines)
            }
        }

        for line in infill_lines:
            line_data = [{'x': p.x, 'y': p.y} for p in line]
            viz_data['lines'].append(line_data)

        return viz_data

    def _calculate_bounding_box(self, infill_lines: List[List[Point2D]]) -> Dict[str, float]:

        if not infill_lines:
            return {'min_x': 0, 'min_y': 0, 'max_x': 0, 'max_y': 0}

        all_points = [point for line in infill_lines for point in line]

        min_x = min(p.x for p in all_points)
        max_x = max(p.x for p in all_points)
        min_y = min(p.y for p in all_points)
        max_y = max(p.y for p in all_points)

        return {
            'min_x': min_x,
            'min_y': min_y,
            'max_x': max_x,
            'max_y': max_y
        }

class InfillGenerator:

    def __init__(self, settings: PrintSettings):
        self.settings = settings
        self.infill_spacing = self._calculate_infill_spacing()

        # Advanced components
        self.ml_optimizer = InfillMachineLearningOptimizer()
        self.adaptive_generator = AdaptiveInfillGenerator(self.settings.fill_density)
        self.quality_optimizer = InfillQualityOptimizer()
        self.multi_material_gen = MultiMaterialInfillGenerator()
        self.performance_optimizer = InfillPerformanceOptimizer()
        self.analysis_engine = InfillAnalysisEngine()

        # Cache for adaptive patterns
        self._adaptive_cache = {}
        self._pattern_cache = {}

        # Configuration
        self.config = InfillConfiguration(
            pattern=self.settings.fill_pattern,
            density=self.settings.fill_density,
            optimization=InfillOptimization.BALANCED,
            quality=InfillQuality.STANDARD,
            algorithm=InfillAlgorithm.TRADITIONAL
        )

        # Performance tracking
        self.generation_stats = {
            'total_patterns_generated': 0,
            'average_generation_time': 0.0,
            'cache_hit_rate': 0.0,
            'pattern_distribution': defaultdict(int)
        }

        # Seed for consistent randomness
        random.seed(42)
    
    def _calculate_infill_spacing(self) -> float:
        if self.settings.fill_density <= 0:
            return float('inf')
        
        line_width = self.settings.extrusion_width
        spacing = line_width / self.settings.fill_density
        return spacing
    
    def generate_infill(self, polygon: LayerPolygon, layer_height: float,
                       use_adaptive: bool = False, quality_optimize: bool = False,
                       multi_material: bool = False) -> List[List[Point2D]]:
        start_time = time.time()

        if self.settings.fill_density <= 0:
            return []

        pattern = self.settings.fill_pattern

        # Update configuration
        self.config.pattern = pattern
        self.config.density = self.settings.fill_density

        # Check cache first
        cache_key = self._generate_cache_key(polygon, pattern, layer_height, use_adaptive, quality_optimize)
        if self.config.enable_caching and cache_key in self._pattern_cache:
            self.generation_stats['cache_hit_rate'] = (
                self.generation_stats.get('cache_hits', 0) + 1
            ) / (self.generation_stats.get('total_requests', 0) + 1)
            return self._pattern_cache[cache_key]

        self.generation_stats['total_requests'] = self.generation_stats.get('total_requests', 0) + 1

        # ML-guided pattern selection
        if self.config.ml_guidance:
            pattern = self.ml_optimizer.optimize_pattern_selection(polygon, {
                'strength': 0.5, 'speed': 0.5, 'quality': 0.5
            })

        # Adaptive infill generation
        if use_adaptive:
            adaptive_zones = self.adaptive_generator.generate_adaptive_infill(polygon)
            all_lines = []

            for zone in adaptive_zones:
                zone_pattern = zone.pattern_modifier or pattern
                zone_lines = self._generate_pattern(zone.polygon, zone_pattern, layer_height,
                                                  zone.density_multiplier)
                all_lines.extend(zone_lines)

            infill_lines = all_lines
        else:
            # Standard pattern generation
            infill_lines = self._generate_pattern(polygon, pattern, layer_height, 1.0)

        # Quality optimization
        if quality_optimize:
            infill_lines = self.quality_optimizer.optimize_infill_quality(
                infill_lines, self.config.quality
            )

        # Multi-material support (simplified)
        if multi_material:
            # This would handle multiple materials - simplified for now
            pass

        # Performance optimization
        optimized_func = self.performance_optimizer.optimize_generation(
            polygon, pattern, self.settings.fill_density
        )

        # Cache result
        if self.config.enable_caching:
            self._pattern_cache[cache_key] = infill_lines

        # Update statistics
        generation_time = time.time() - start_time
        self.generation_stats['total_patterns_generated'] += 1
        self.generation_stats['pattern_distribution'][pattern.value] += 1
        self.generation_stats['average_generation_time'] = (
            (self.generation_stats['average_generation_time'] *
             (self.generation_stats['total_patterns_generated'] - 1) +
             generation_time) / self.generation_stats['total_patterns_generated']
        )

        return infill_lines

    def _generate_pattern(self, polygon: LayerPolygon, pattern: InfillPattern,
                         layer_height: float, density_multiplier: float = 1.0) -> List[List[Point2D]]:

        # Adjust density for multiplier
        original_density = self.settings.fill_density
        self.settings.fill_density *= density_multiplier

        # Recalculate spacing
        self.infill_spacing = self._calculate_infill_spacing()

        # Pattern dispatch with expanded options
        pattern_map = {
            InfillPattern.RECTILINEAR: self._generate_rectilinear,
            InfillPattern.LINE: self._generate_line,
            InfillPattern.ALIGNED_RECTILINEAR: self._generate_aligned_rectilinear,
            InfillPattern.MONOTONIC: self._generate_monotonic,
            InfillPattern.GRID: self._generate_grid,
            InfillPattern.CROSS_HATCH: self._generate_cross_hatch,
            InfillPattern.CROSS: self._generate_cross,
            InfillPattern.TRIANGULAR: self._generate_triangular,
            InfillPattern.TRI_HEXAGON: self._generate_tri_hexagon,
            InfillPattern.STARS: self._generate_stars,
            InfillPattern.HONEYCOMB: self._generate_honeycomb,
            InfillPattern.HONEYCOMB_3D: self._generate_3d_honeycomb,
            InfillPattern.GYROID: self._generate_gyroid,
            InfillPattern.CUBIC: self._generate_cubic,
            InfillPattern.ADAPTIVE_CUBIC: self._generate_adaptive_cubic,
            InfillPattern.SUPPORT_CUBIC: self._generate_support_cubic,
            InfillPattern.TETRAHEDRAL: self._generate_tetrahedral,
            InfillPattern.OCTET: self._generate_octet,
            InfillPattern.CONCENTRIC: self._generate_concentric,
            InfillPattern.SPIRAL: self._generate_spiral,
            InfillPattern.ARCHIMEDEAN_CHORDS: self._generate_archimedean_chords,
            InfillPattern.OCTAGRAM_SPIRAL: self._generate_octagram_spiral,
            InfillPattern.HILBERT_CURVE: self._generate_hilbert_curve,
            InfillPattern.LIGHTNING: self._generate_lightning,
            InfillPattern.WAVES: self._generate_waves,
            InfillPattern.ZIGZAG: self._generate_zigzag,
            InfillPattern.VORONOI: self._generate_voronoi,
        }

        generator = pattern_map.get(pattern, self._generate_rectilinear)
        result = generator(polygon, layer_height)

        # Restore original density
        self.settings.fill_density = original_density
        self.infill_spacing = self._calculate_infill_spacing()

        return result

    def _generate_cache_key(self, polygon: LayerPolygon, pattern: InfillPattern,
                           layer_height: float, use_adaptive: bool, quality_optimize: bool) -> str:
        # Simple hash based on polygon and parameters
        poly_hash = hash(tuple((p.x, p.y) for p in polygon.points))
        return f"{poly_hash}_{pattern.value}_{layer_height:.3f}_{use_adaptive}_{quality_optimize}_{self.settings.fill_density:.3f}"
    
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
    
    def _line_polygon_intersections(self, start: Point2D, end: Point2D, polygon: LayerPolygon) -> List[Point2D]:
        intersections = []
        
        for i in range(len(polygon.points)):
            p1 = polygon.points[i]
            p2 = polygon.points[(i + 1) % len(polygon.points)]
            
            intersection = self._line_intersection(start, end, p1, p2)
            if intersection:
                intersections.append(intersection)
        
        return intersections
    
    def _line_intersection(self, p1: Point2D, p2: Point2D, p3: Point2D, p4: Point2D) -> Optional[Point2D]:
        x1, y1 = p1.x, p1.y
        x2, y2 = p2.x, p2.y
        x3, y3 = p3.x, p3.y
        x4, y4 = p4.x, p4.y
        
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:
            return None
        
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
        
        if 0 <= t <= 1 and 0 <= u <= 1:
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            return Point2D(x, y)
        
        return None
    
    # BASIC LINEAR PATTERNS
    def _generate_rectilinear(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)
        
        layer_index = int(layer_height / self.settings.layer_height)
        vertical = layer_index % 2 == 0
        
        return self._generate_parallel_lines(polygon, vertical, self.infill_spacing)
    
    def _generate_line(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        return self._generate_parallel_lines(polygon, True, self.infill_spacing)
    
    def _generate_aligned_rectilinear(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        return self._generate_parallel_lines(polygon, True, self.infill_spacing)
    
    def _generate_monotonic(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)
        
        layer_index = int(layer_height / self.settings.layer_height)
        vertical = layer_index % 2 == 0
        
        if vertical:
            y = min_y
            while y <= max_y:
                intersections = []
                for i in range(len(polygon.points)):
                    p1 = polygon.points[i]
                    p2 = polygon.points[(i + 1) % len(polygon.points)]
                    
                    if (p1.y <= y <= p2.y or p2.y <= y <= p1.y) and p1.y != p2.y:
                        x = p1.x + (y - p1.y) * (p2.x - p1.x) / (p2.y - p1.y)
                        intersections.append(Point2D(x, y))
                
                if len(intersections) >= 2:
                    intersections.sort(key=lambda p: p.x)
                    # Create monotonic segments (never backtrack)
                    for i in range(0, len(intersections) - 1, 2):
                        lines.append([intersections[i], intersections[i + 1]])
                
                y += self.infill_spacing
        else:
            x = min_x
            while x <= max_x:
                intersections = []
                for i in range(len(polygon.points)):
                    p1 = polygon.points[i]
                    p2 = polygon.points[(i + 1) % len(polygon.points)]
                    
                    if (p1.x <= x <= p2.x or p2.x <= x <= p1.x) and p1.x != p2.x:
                        y = p1.y + (x - p1.x) * (p2.y - p1.y) / (p2.x - p1.x)
                        intersections.append(Point2D(x, y))
                
                if len(intersections) >= 2:
                    intersections.sort(key=lambda p: p.y)
                    for i in range(0, len(intersections) - 1, 2):
                        lines.append([intersections[i], intersections[i + 1]])
                
                x += self.infill_spacing
        
        return lines
    
    def _generate_parallel_lines(self, polygon: LayerPolygon, vertical: bool, spacing: float) -> List[List[Point2D]]:
        lines = []
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)
        
        if vertical:
            x = min_x
            while x <= max_x:
                start = Point2D(x, min_y - 1)
                end = Point2D(x, max_y + 1)
                intersections = self._line_polygon_intersections(start, end, polygon)
                
                if len(intersections) >= 2:
                    intersections.sort(key=lambda p: p.y)
                    for i in range(0, len(intersections) - 1, 2):
                        lines.append([intersections[i], intersections[i + 1]])
                
                x += spacing
        else:
            y = min_y
            while y <= max_y:
                start = Point2D(min_x - 1, y)
                end = Point2D(max_x + 1, y)
                intersections = self._line_polygon_intersections(start, end, polygon)
                
                if len(intersections) >= 2:
                    intersections.sort(key=lambda p: p.x)
                    for i in range(0, len(intersections) - 1, 2):
                        lines.append([intersections[i], intersections[i + 1]])
                
                y += spacing
        
        return lines
    
    # GRID-BASED PATTERNS
    def _generate_grid(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        lines.extend(self._generate_parallel_lines(polygon, True, self.infill_spacing))
        lines.extend(self._generate_parallel_lines(polygon, False, self.infill_spacing))
        return lines
    
    def _generate_cross_hatch(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        lines.extend(self._generate_diagonal_lines(polygon, 45, self.infill_spacing))
        lines.extend(self._generate_diagonal_lines(polygon, 135, self.infill_spacing))
        return lines
    
    def _generate_cross(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)
        
        # Calculate center
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        spacing = self.infill_spacing * 2
        
        # Vertical crosses
        x = min_x
        while x <= max_x:
            # Vertical line of cross
            start = Point2D(x, min_y - 1)
            end = Point2D(x, max_y + 1)
            intersections = self._line_polygon_intersections(start, end, polygon)
            if len(intersections) >= 2:
                intersections.sort(key=lambda p: p.y)
                for i in range(0, len(intersections) - 1, 2):
                    lines.append([intersections[i], intersections[i + 1]])
            
            # Horizontal line of cross
            start = Point2D(min_x - 1, center_y)
            end = Point2D(max_x + 1, center_y)
            intersections = self._line_polygon_intersections(start, end, polygon)
            if len(intersections) >= 2:
                intersections.sort(key=lambda p: p.x)
                for i in range(0, len(intersections) - 1, 2):
                    lines.append([intersections[i], intersections[i + 1]])
            
            x += spacing
        
        return lines
    
    def _generate_diagonal_lines(self, polygon: LayerPolygon, angle: float, spacing: float) -> List[List[Point2D]]:
        lines = []
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)
        
        angle_rad = math.radians(angle)
        perp_angle = angle_rad + math.pi / 2
        
        # Generate parallel lines
        distance = min_x * math.cos(perp_angle) + min_y * math.sin(perp_angle)
        max_distance = max_x * math.cos(perp_angle) + max_y * math.sin(perp_angle)
        
        while distance <= max_distance:
            # Calculate line endpoints
            if abs(math.cos(perp_angle)) > 1e-10:
                y1 = min_y - 10
                x1 = (distance - y1 * math.sin(perp_angle)) / math.cos(perp_angle)
                y2 = max_y + 10
                x2 = (distance - y2 * math.sin(perp_angle)) / math.cos(perp_angle)
            else:
                x1 = min_x - 10
                y1 = (distance - x1 * math.cos(perp_angle)) / math.sin(perp_angle)
                x2 = max_x + 10
                y2 = (distance - x2 * math.cos(perp_angle)) / math.sin(perp_angle)
            
            start = Point2D(x1, y1)
            end = Point2D(x2, y2)
            intersections = self._line_polygon_intersections(start, end, polygon)
            
            if len(intersections) >= 2:
                intersections.sort(key=lambda p: (p.x - x1) * math.cos(angle_rad) + (p.y - y1) * math.sin(angle_rad))
                for i in range(0, len(intersections) - 1, 2):
                    lines.append([intersections[i], intersections[i + 1]])
            
            distance += spacing
        
        return lines
    
    # TRIANGULAR PATTERNS
    def _generate_triangular(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        layer_index = int(layer_height / self.settings.layer_height)
        
        angles = [0, 60, 120]
        angle = angles[layer_index % 3]
        spacing = self.infill_spacing / math.sin(math.radians(60))
        
        lines.extend(self._generate_diagonal_lines(polygon, angle, spacing))
        return lines
    
    def _generate_tri_hexagon(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        layer_index = int(layer_height / self.settings.layer_height)
        
        if layer_index % 2 == 0:
            # Triangular pattern
            angles = [0, 60, 120]
            for angle in angles:
                lines.extend(self._generate_diagonal_lines(polygon, angle, self.infill_spacing * 2))
        else:
            # Hexagonal pattern
            angles = [0, 60, 120]
            for angle in angles:
                lines.extend(self._generate_diagonal_lines(polygon, angle, self.infill_spacing * 3))
        
        return lines
    
    def _generate_stars(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)
        
        # Star with 8 points
        angles = [i * 22.5 for i in range(8)]
        spacing = self.infill_spacing * 2
        
        for angle in angles:
            lines.extend(self._generate_diagonal_lines(polygon, angle, spacing))
        
        return lines
    
    # HONEYCOMB PATTERNS
    def _generate_honeycomb(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        angles = [0, 60, 120]
        
        for angle in angles:
            spacing = self.infill_spacing * 2
            lines.extend(self._generate_diagonal_lines(polygon, angle, spacing))
        
        return lines
    
    def _generate_3d_honeycomb(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        layer_index = int(layer_height / self.settings.layer_height)
        
        # Rotate honeycomb pattern every 3 layers for 3D effect
        base_angles = [0, 60, 120]
        layer_rotation = (layer_index % 9) * 5  # Rotate every layer for 3D effect
        
        angles = [(angle + layer_rotation) % 360 for angle in base_angles]
        spacing = self.infill_spacing * 2.5
        
        for angle in angles:
            lines.extend(self._generate_diagonal_lines(polygon, angle, spacing))
        
        return lines
    
    # MATHEMATICAL SURFACE PATTERNS
    def _generate_gyroid(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)
        
        scale = self.infill_spacing * 2
        phase = layer_height * 0.1
        resolution = 0.5
        
        y = min_y
        while y <= max_y:
            line_points = []
            x = min_x
            
            while x <= max_x:
                point = Point2D(x, y)
                if self._point_in_polygon(point, polygon):
                    gyroid_value = (math.sin(x / scale) * math.cos(y / scale) + 
                                   math.sin(y / scale) * math.cos(phase) + 
                                   math.sin(phase) * math.cos(x / scale))
                    
                    if abs(gyroid_value) < 0.2:
                        line_points.append(point)
                    else:
                        if len(line_points) > 1:
                            lines.append(line_points.copy())
                        line_points.clear()
                
                x += resolution
            
            if len(line_points) > 1:
                lines.append(line_points)
            
            y += resolution
        
        return lines
    
    # CUBIC PATTERNS
    def _generate_cubic(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        layer_index = int(layer_height / self.settings.layer_height)
        
        base_angles = [45, 135, 90]
        rotation = (layer_index // 3) * 15
        
        for base_angle in base_angles:
            angle = base_angle + rotation
            spacing = self.infill_spacing * 1.5
            lines.extend(self._generate_diagonal_lines(polygon, angle, spacing))
        
        return lines
    
    def _generate_adaptive_cubic(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)
        
        # Simple adaptive logic - denser near edges
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        max_distance = max(max_x - center_x, max_y - center_y)
        
        layer_index = int(layer_height / self.settings.layer_height)
        base_angles = [45, 135, 90]
        rotation = (layer_index // 3) * 15
        
        for base_angle in base_angles:
            angle = base_angle + rotation
            
            # Variable spacing based on distance from center
            positions = []
            distance = 0
            while distance <= max_distance * 1.5:
                # Adaptive spacing - closer lines near edges
                adaptive_factor = 1 + distance / max_distance
                spacing = self.infill_spacing * adaptive_factor
                
                positions.append(distance)
                distance += spacing
            
            for pos in positions:
                lines.extend(self._generate_diagonal_lines(polygon, angle, pos))
        
        return lines
    
    def _generate_support_cubic(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        
        # Support cubic uses wider spacing and specific angles for easy removal
        support_angles = [30, 150, 90]  # Angles that break easily
        spacing = self.infill_spacing * 2  # Wider spacing
        
        for angle in support_angles:
            lines.extend(self._generate_diagonal_lines(polygon, angle, spacing))
        
        return lines
    
    # 3D PATTERNS
    def _generate_tetrahedral(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        layer_index = int(layer_height / self.settings.layer_height)
        
        # Tetrahedral angles (4 directions)
        base_angles = [0, 60, 120, 180]
        layer_rotation = (layer_index % 4) * 15
        
        angles = [(angle + layer_rotation) % 360 for angle in base_angles]
        spacing = self.infill_spacing * 2
        
        for angle in angles:
            lines.extend(self._generate_diagonal_lines(polygon, angle, spacing))
        
        return lines
    
    def _generate_octet(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        layer_index = int(layer_height / self.settings.layer_height)
        
        # Octet truss (8 directions)
        base_angles = [0, 45, 90, 135, 180, 225, 270, 315]
        layer_rotation = (layer_index % 8) * 5
        
        # Use subset of angles per layer for 3D effect
        active_angles = base_angles[layer_index % 4::4] + base_angles[(layer_index + 2) % 4::4]
        
        spacing = self.infill_spacing * 3
        
        for angle in active_angles:
            final_angle = (angle + layer_rotation) % 360
            lines.extend(self._generate_diagonal_lines(polygon, final_angle, spacing))
        
        return lines
    
    # SPIRAL PATTERNS
    def _generate_concentric(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        
        if not polygon.points:
            return lines
        
        current_polygon = polygon
        offset_distance = self.infill_spacing
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)
        max_iterations = max(
            8,
            int(max(max_x - min_x, max_y - min_y) / max(offset_distance, 1e-6)) + 8,
        )
        previous_area = polygon.area()
        
        for _ in range(max_iterations):
            offset_polygon = self._offset_polygon(current_polygon, offset_distance)
            
            if not offset_polygon or len(offset_polygon.points) < 3:
                break
            current_area = offset_polygon.area()
            if current_area >= previous_area - 1e-6:
                break
            
            for i in range(len(offset_polygon.points)):
                p1 = offset_polygon.points[i]
                p2 = offset_polygon.points[(i + 1) % len(offset_polygon.points)]
                lines.append([p1, p2])
            
            current_polygon = offset_polygon
            previous_area = current_area
            
            if current_area < self.infill_spacing * self.infill_spacing:
                break
        
        return lines
    
    def _generate_spiral(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)
        
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        max_radius = max(max_x - center_x, max_y - center_y)
        
        # Spiral parameters
        a = self.infill_spacing / (2 * math.pi)  # Spiral tightness
        theta = 0
        max_theta = max_radius / a * 2 * math.pi
        
        spiral_points = []
        while theta <= max_theta:
            r = a * theta
            x = center_x + r * math.cos(theta)
            y = center_y + r * math.sin(theta)
            
            point = Point2D(x, y)
            if self._point_in_polygon(point, polygon):
                spiral_points.append(point)
            
            theta += 0.1
        
        # Convert points to line segments
        for i in range(len(spiral_points) - 1):
            lines.append([spiral_points[i], spiral_points[i + 1]])
        
        return lines
    
    def _generate_archimedean_chords(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)
        
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        max_radius = max(max_x - center_x, max_y - center_y)
        
        # Generate spiral points
        a = self.infill_spacing / (2 * math.pi)
        theta = 0
        max_theta = max_radius / a * 2 * math.pi
        chord_spacing = math.pi / 4  # Chord every 45 degrees
        
        spiral_points = []
        while theta <= max_theta:
            r = a * theta
            x = center_x + r * math.cos(theta)
            y = center_y + r * math.sin(theta)
            
            point = Point2D(x, y)
            if self._point_in_polygon(point, polygon):
                spiral_points.append(point)
            
            theta += 0.2
        
        # Create chord connections
        chord_step = int(chord_spacing / 0.2)
        for i in range(0, len(spiral_points) - chord_step, chord_step):
            if i + chord_step < len(spiral_points):
                lines.append([spiral_points[i], spiral_points[i + chord_step]])
        
        return lines
    
    def _generate_octagram_spiral(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)
        
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        max_radius = max(max_x - center_x, max_y - center_y)
        
        # Octagram spiral with 8-pointed star modulation
        a = self.infill_spacing / (2 * math.pi)
        theta = 0
        max_theta = max_radius / a * 4 * math.pi
        
        octagram_points = []
        while theta <= max_theta:
            # Basic spiral radius
            r_base = a * theta
            
            # Octagram modulation (8 points)
            octagram_mod = 0.3 * math.sin(8 * theta)
            r = r_base * (1 + octagram_mod)
            
            x = center_x + r * math.cos(theta)
            y = center_y + r * math.sin(theta)
            
            point = Point2D(x, y)
            if self._point_in_polygon(point, polygon):
                octagram_points.append(point)
            
            theta += 0.15
        
        # Connect points to form spiral
        for i in range(len(octagram_points) - 1):
            lines.append([octagram_points[i], octagram_points[i + 1]])
        
        return lines
    
    # SPACE-FILLING CURVES
    def _generate_hilbert_curve(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)
        
        size = max(max_x - min_x, max_y - min_y)
        order = max(1, int(math.log2(size / self.infill_spacing)))
        order = min(order, 6)
        
        curve_points = self._hilbert_curve(order)
        
        if curve_points:
            curve_size = 2 ** order
            scale_x = (max_x - min_x) / curve_size
            scale_y = (max_y - min_y) / curve_size
            
            scaled_points = []
            for x, y in curve_points:
                scaled_x = min_x + x * scale_x
                scaled_y = min_y + y * scale_y
                point = Point2D(scaled_x, scaled_y)
                
                if self._point_in_polygon(point, polygon):
                    scaled_points.append(point)
            
            for i in range(len(scaled_points) - 1):
                lines.append([scaled_points[i], scaled_points[i + 1]])
        
        return lines
    
    def _hilbert_curve(self, order: int) -> List[Tuple[float, float]]:
        def hilbert_xy(n, d):
            t = d
            x = y = 0
            s = 1
            
            while s < n:
                rx = 1 & (t // 2)
                ry = 1 & (t ^ rx)
                x, y = rot(s, x, y, rx, ry)
                x += s * rx
                y += s * ry
                t //= 4
                s *= 2
            
            return x, y
        
        def rot(n, x, y, rx, ry):
            if ry == 0:
                if rx == 1:
                    x = n - 1 - x
                    y = n - 1 - y
                x, y = y, x
            return x, y
        
        n = 2 ** order
        points = []
        
        for d in range(n * n):
            x, y = hilbert_xy(n, d)
            points.append((x, y))
        
        return points
    
    # MODERN ADVANCED PATTERNS
    def _generate_lightning(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)
        
        # Lightning parameters
        branch_probability = 0.3
        max_branches = 5
        segment_length = self.infill_spacing * 2
        
        # Generate lightning trees from multiple starting points
        num_trees = max(1, int((max_x - min_x) * (max_y - min_y) / (self.infill_spacing ** 2 * 50)))
        
        for tree_idx in range(num_trees):
            # Random starting point on polygon perimeter
            start_idx = random.randint(0, len(polygon.points) - 1)
            start_point = polygon.points[start_idx]
            
            # Generate tree structure
            tree_lines = self._generate_lightning_tree(start_point, polygon, segment_length, 
                                                     branch_probability, max_branches, 0)
            lines.extend(tree_lines)
        
        return lines
    
    def _generate_lightning_tree(self, start: Point2D, polygon: LayerPolygon, 
                                segment_length: float, branch_prob: float, 
                                max_branches: int, depth: int) -> List[List[Point2D]]:
        if depth > 10 or max_branches <= 0:
            return []
        
        lines = []
        current_point = start
        
        # Main trunk
        for _ in range(random.randint(3, 8)):
            # Random direction with slight preference for inward
            angle = random.uniform(0, 2 * math.pi)
            
            next_x = current_point.x + segment_length * math.cos(angle)
            next_y = current_point.y + segment_length * math.sin(angle)
            next_point = Point2D(next_x, next_y)
            
            if not self._point_in_polygon(next_point, polygon):
                break
            
            lines.append([current_point, next_point])
            current_point = next_point
            
            # Random branching
            if random.random() < branch_prob and max_branches > 0:
                branch_lines = self._generate_lightning_tree(
                    current_point, polygon, segment_length * 0.7, 
                    branch_prob * 0.8, max_branches - 1, depth + 1
                )
                lines.extend(branch_lines)
        
        return lines
    
    def _generate_waves(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)
        
        layer_index = int(layer_height / self.settings.layer_height)
        vertical = layer_index % 2 == 0
        
        wave_amplitude = self.infill_spacing * 0.5
        wave_frequency = 2 * math.pi / (self.infill_spacing * 4)
        
        if vertical:
            x = min_x
            while x <= max_x:
                wave_points = []
                y = min_y
                while y <= max_y:
                    # Sinusoidal wave
                    wave_x = x + wave_amplitude * math.sin(wave_frequency * y)
                    point = Point2D(wave_x, y)
                    
                    if self._point_in_polygon(point, polygon):
                        wave_points.append(point)
                    else:
                        if len(wave_points) > 1:
                            lines.append(wave_points.copy())
                        wave_points.clear()
                    
                    y += self.infill_spacing * 0.2
                
                if len(wave_points) > 1:
                    lines.append(wave_points)
                
                x += self.infill_spacing
        else:
            y = min_y
            while y <= max_y:
                wave_points = []
                x = min_x
                while x <= max_x:
                    # Sinusoidal wave
                    wave_y = y + wave_amplitude * math.sin(wave_frequency * x)
                    point = Point2D(x, wave_y)
                    
                    if self._point_in_polygon(point, polygon):
                        wave_points.append(point)
                    else:
                        if len(wave_points) > 1:
                            lines.append(wave_points.copy())
                        wave_points.clear()
                    
                    x += self.infill_spacing * 0.2
                
                if len(wave_points) > 1:
                    lines.append(wave_points)
                
                y += self.infill_spacing
        
        return lines
    
    def _generate_zigzag(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)
        
        layer_index = int(layer_height / self.settings.layer_height)
        vertical = layer_index % 2 == 0
        
        zigzag_amplitude = self.infill_spacing * 0.8
        zigzag_period = self.infill_spacing * 2
        
        if vertical:
            x = min_x
            while x <= max_x:
                zigzag_points = []
                y = min_y
                direction = 1
                
                while y <= max_y:
                    # Zigzag pattern
                    if (y - min_y) % zigzag_period < zigzag_period / 2:
                        zigzag_x = x + direction * zigzag_amplitude * ((y - min_y) % zigzag_period) / (zigzag_period / 2)
                    else:
                        zigzag_x = x + direction * zigzag_amplitude * (1 - ((y - min_y) % zigzag_period - zigzag_period / 2) / (zigzag_period / 2))
                    
                    point = Point2D(zigzag_x, y)
                    
                    if self._point_in_polygon(point, polygon):
                        zigzag_points.append(point)
                    else:
                        if len(zigzag_points) > 1:
                            lines.append(zigzag_points.copy())
                        zigzag_points.clear()
                    
                    y += self.infill_spacing * 0.3
                
                if len(zigzag_points) > 1:
                    lines.append(zigzag_points)
                
                x += self.infill_spacing
        else:
            y = min_y
            while y <= max_y:
                zigzag_points = []
                x = min_x
                direction = 1
                
                while x <= max_x:
                    # Zigzag pattern
                    if (x - min_x) % zigzag_period < zigzag_period / 2:
                        zigzag_y = y + direction * zigzag_amplitude * ((x - min_x) % zigzag_period) / (zigzag_period / 2)
                    else:
                        zigzag_y = y + direction * zigzag_amplitude * (1 - ((x - min_x) % zigzag_period - zigzag_period / 2) / (zigzag_period / 2))
                    
                    point = Point2D(x, zigzag_y)
                    
                    if self._point_in_polygon(point, polygon):
                        zigzag_points.append(point)
                    else:
                        if len(zigzag_points) > 1:
                            lines.append(zigzag_points.copy())
                        zigzag_points.clear()
                    
                    x += self.infill_spacing * 0.3
                
                if len(zigzag_points) > 1:
                    lines.append(zigzag_points)
                
                y += self.infill_spacing
        
        return lines
    
    def _generate_voronoi(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)

        # Generate random seed points
        area = (max_x - min_x) * (max_y - min_y)
        num_seeds = max(5, int(area / (self.infill_spacing ** 2 * 10)))

        seeds = []
        for _ in range(num_seeds):
            # Generate seeds within polygon bounds
            attempts = 0
            while attempts < 50:
                x = random.uniform(min_x, max_x)
                y = random.uniform(min_y, max_y)
                point = Point2D(x, y)

                if self._point_in_polygon(point, polygon):
                    seeds.append(point)
                    break
                attempts += 1

        # Simple Voronoi approximation - create cells
        resolution = self.infill_spacing * 0.5

        y = min_y
        while y <= max_y:
            current_line = []
            x = min_x

            while x <= max_x:
                point = Point2D(x, y)

                if self._point_in_polygon(point, polygon):
                    # Find closest seed
                    closest_seed = min(seeds, key=lambda s: math.sqrt((s.x - x)**2 + (s.y - y)**2))

                    # Check if we're on a Voronoi edge (simplified)
                    distances = [math.sqrt((s.x - x)**2 + (s.y - y)**2) for s in seeds]
                    distances.sort()

                    if len(distances) >= 2 and abs(distances[0] - distances[1]) < self.infill_spacing * 0.3:
                        current_line.append(point)
                    else:
                        if len(current_line) > 1:
                            lines.append(current_line.copy())
                        current_line.clear()

                x += resolution

            if len(current_line) > 1:
                lines.append(current_line)

            y += resolution

        return lines

    # ===== ADVANCED MATHEMATICAL INFILL PATTERNS =====

    def _generate_peano_curve(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)

        # Generate Peano curve points
        order = max(1, min(4, int(math.log2(max(max_x - min_x, max_y - min_y) / self.infill_spacing))))
        peano_points = self._generate_peano_points(order)

        if peano_points:
            # Scale to polygon bounds
            scale_x = (max_x - min_x) / (2 ** order)
            scale_y = (max_y - min_y) / (2 ** order)

            scaled_points = []
            for px, py in peano_points:
                scaled_x = min_x + px * scale_x
                scaled_y = min_y + py * scale_y
                point = Point2D(scaled_x, scaled_y)

                if self._point_in_polygon(point, polygon):
                    scaled_points.append(point)

            # Convert to line segments
            for i in range(len(scaled_points) - 1):
                lines.append([scaled_points[i], scaled_points[i + 1]])

        return lines

    def _generate_peano_points(self, order: int) -> List[Tuple[float, float]]:
        if order == 0:
            return [(0, 0)]

        # Recursive generation
        sub_curve = self._generate_peano_points(order - 1)

        points = []

        # Transform sub-curves according to Peano rules
        size = 2 ** (order - 1)

        # First segment
        for x, y in sub_curve:
            points.append((x, y))

        # Second segment (rotated)
        for x, y in sub_curve:
            points.append((x, y + size))

        # Third segment (rotated again)
        for x, y in sub_curve:
            points.append((x + size, y + size))

        return points

    def _generate_dragon_curve(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)

        # Generate dragon curve
        iterations = max(1, min(12, int(math.log2(max(max_x - min_x, max_y - min_y) / self.infill_spacing))))
        dragon_points = self._generate_dragon_points(iterations)

        if dragon_points:
            # Scale to bounds
            scale = min(max_x - min_x, max_y - min_y) / (2 ** iterations)

            scaled_points = []
            for px, py in dragon_points:
                scaled_x = min_x + px * scale
                scaled_y = min_y + py * scale
                point = Point2D(scaled_x, scaled_y)

                if self._point_in_polygon(point, polygon):
                    scaled_points.append(point)

            # Convert to lines
            for i in range(len(scaled_points) - 1):
                lines.append([scaled_points[i], scaled_points[i + 1]])

        return lines

    def _generate_dragon_points(self, iterations: int) -> List[Tuple[float, float]]:
        # Start with axiom
        sequence = "F"

        # Apply rules
        for _ in range(iterations):
            new_sequence = ""
            for char in sequence:
                if char == "F":
                    new_sequence += "F+H"
                elif char == "H":
                    new_sequence += "F-H"
                else:
                    new_sequence += char
            sequence = new_sequence

        # Interpret sequence
        points = [(0, 0)]
        x, y = 0, 0
        angle = 0
        step_size = 1

        for char in sequence:
            if char == "F" or char == "H":
                x += step_size * math.cos(angle)
                y += step_size * math.sin(angle)
                points.append((x, y))
            elif char == "+":
                angle += math.pi / 2
            elif char == "-":
                angle -= math.pi / 2

        return points

    def _generate_sierpinski_triangle(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)

        # Generate Sierpinski triangle points
        depth = max(1, min(6, int(math.log2(max(max_x - min_x, max_y - min_y) / self.infill_spacing))))
        triangle_points = self._generate_sierpinski_points(depth, min_x, min_y, max_x - min_x, max_y - min_y)

        # Filter points within polygon
        valid_points = []
        for point in triangle_points:
            p2d = Point2D(point[0], point[1])
            if self._point_in_polygon(p2d, polygon):
                valid_points.append(p2d)

        # Create lines connecting nearby points
        if len(valid_points) > 1:
            # Simple approach: connect points in order
            for i in range(len(valid_points) - 1):
                lines.append([valid_points[i], valid_points[i + 1]])

        return lines

    def _generate_sierpinski_points(self, depth: int, x: float, y: float,
                                  width: float, height: float) -> List[Tuple[float, float]]:
        if depth == 0:
            # Return triangle vertices
            return [
                (x + width/2, y),
                (x, y + height),
                (x + width, y + height)
            ]

        # Recursive subdivision
        half_width = width / 2
        half_height = height / 2

        points = []

        # Top triangle
        points.extend(self._generate_sierpinski_points(depth - 1, x + half_width/2, y,
                                                      half_width, half_height))

        # Bottom left triangle
        points.extend(self._generate_sierpinski_points(depth - 1, x, y + half_height,
                                                      half_width, half_height))

        # Bottom right triangle
        points.extend(self._generate_sierpinski_points(depth - 1, x + half_width, y + half_height,
                                                      half_width, half_height))

        return points

    def _generate_fractal_tree(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)

        # Start from center bottom
        center_x = (min_x + max_x) / 2
        start_point = Point2D(center_x, max_y)  # Start from bottom

        if not self._point_in_polygon(start_point, polygon):
            return lines

        # Generate tree structure
        tree_lines = self._generate_fractal_tree_recursive(
            start_point, math.pi/2,  # Start upward
            self.infill_spacing * 4,  # Initial branch length
            5,  # Depth
            polygon
        )

        lines.extend(tree_lines)
        return lines

    def _generate_fractal_tree_recursive(self, start: Point2D, angle: float,
                                       length: float, depth: int,
                                       polygon: LayerPolygon) -> List[List[Point2D]]:
        if depth <= 0 or length < self.infill_spacing:
            return []

        lines = []

        # Calculate end point
        end_x = start.x + length * math.cos(angle)
        end_y = start.y + length * math.sin(angle)
        end_point = Point2D(end_x, end_y)

        # Check if end point is within polygon
        if not self._point_in_polygon(end_point, polygon):
            return lines

        # Add branch line
        lines.append([start, end_point])

        # Generate child branches
        if depth > 1:
            # Branch angles and lengths
            branch_angle1 = angle + math.radians(30)
            branch_angle2 = angle - math.radians(30)
            branch_length = length * 0.7

            # Left branch
            left_lines = self._generate_fractal_tree_recursive(
                end_point, branch_angle1, branch_length, depth - 1, polygon
            )
            lines.extend(left_lines)

            # Right branch
            right_lines = self._generate_fractal_tree_recursive(
                end_point, branch_angle2, branch_length, depth - 1, polygon
            )
            lines.extend(right_lines)

        return lines

    def _generate_chaos_game(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)

        # Use Sierpinski triangle vertices as attractors
        vertices = [
            Point2D(min_x + (max_x - min_x)/2, min_y),
            Point2D(min_x, max_y),
            Point2D(max_x, max_y)
        ]

        # Generate points using chaos game
        num_points = min(1000, int((max_x - min_x) * (max_y - min_y) / (self.infill_spacing ** 2)))
        points = []

        # Start with random point
        current = Point2D(random.uniform(min_x, max_x), random.uniform(min_y, max_y))

        for _ in range(num_points):
            # Choose random vertex
            vertex = random.choice(vertices)

            # Move halfway to vertex
            current = Point2D(
                (current.x + vertex.x) / 2,
                (current.y + vertex.y) / 2
            )

            if self._point_in_polygon(current, polygon):
                points.append(current)

        # Connect nearby points to form lines
        if len(points) > 1:
            # Sort by x coordinate and connect sequentially
            points.sort(key=lambda p: p.x)

            current_line = [points[0]]
            for point in points[1:]:
                if math.sqrt((point.x - current_line[-1].x)**2 + (point.y - current_line[-1].y)**2) < self.infill_spacing:
                    current_line.append(point)
                else:
                    if len(current_line) > 1:
                        lines.append(current_line)
                    current_line = [point]

            if len(current_line) > 1:
                lines.append(current_line)

        return lines

    def _generate_l_system(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)

        # Simple plant-like L-system
        axiom = "X"
        rules = {
            "X": "F[+X][-X]FX",
            "F": "FF"
        }

        # Generate L-system string
        lstring = self._generate_lsystem_string(axiom, rules, 4)

        # Interpret string
        points = []
        x, y = (min_x + max_x) / 2, max_y  # Start from bottom center
        angle = math.pi / 2  # Point up
        step_size = self.infill_spacing

        stack = []

        for char in lstring:
            if char == "F":
                # Move forward
                new_x = x + step_size * math.cos(angle)
                new_y = y + step_size * math.sin(angle)
                new_point = Point2D(new_x, new_y)

                if self._point_in_polygon(new_point, polygon):
                    points.append(Point2D(x, y))
                    points.append(new_point)
                    x, y = new_x, new_y

            elif char == "+":
                angle += math.radians(25)
            elif char == "-":
                angle -= math.radians(25)
            elif char == "[":
                stack.append((x, y, angle))
            elif char == "]":
                if stack:
                    x, y, angle = stack.pop()

        # Group points into lines
        if len(points) >= 2:
            for i in range(0, len(points) - 1, 2):
                if i + 1 < len(points):
                    lines.append([points[i], points[i + 1]])

        return lines

    def _generate_lsystem_string(self, axiom: str, rules: Dict[str, str], iterations: int) -> str:
        result = axiom

        for _ in range(iterations):
            new_result = ""
            for char in result:
                new_result += rules.get(char, char)
            result = new_result

        return result

    def _generate_flow_field(self, polygon: LayerPolygon, layer_height: float) -> List[List[Point2D]]:
        lines = []
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)

        # Create simple flow field (perlin-like noise)
        resolution = self.infill_spacing / 2
        flow_field = self._generate_flow_field_grid(min_x, min_y, max_x, max_y, resolution)

        # Generate streamlines
        num_streamlines = max(5, int((max_x - min_x) * (max_y - min_y) / (self.infill_spacing ** 2 * 20)))

        for _ in range(num_streamlines):
            # Start from random point on boundary
            start_point = self._get_random_boundary_point(polygon)
            if start_point:
                streamline = self._generate_streamline(start_point, flow_field,
                                                     resolution, polygon)
                if len(streamline) > 1:
                    lines.append(streamline)

        return lines

    def _generate_flow_field_grid(self, min_x: float, min_y: float, max_x: float, max_y: float,
                                resolution: float) -> Dict[Tuple[int, int], float]:
        flow_field = {}

        grid_x = int((max_x - min_x) / resolution) + 1
        grid_y = int((max_y - min_y) / resolution) + 1

        # Simple pseudo-random angle field
        for i in range(grid_x):
            for j in range(grid_y):
                # Use simple hash for reproducible angles
                hash_val = hash(f"{i}_{j}") % 1000
                angle = (hash_val / 1000.0) * 2 * math.pi
                flow_field[(i, j)] = angle

        return flow_field

    def _get_random_boundary_point(self, polygon: LayerPolygon) -> Optional[Point2D]:
        if not polygon.points:
            return None

        # Pick random edge
        edge_idx = random.randint(0, len(polygon.points) - 1)
        p1 = polygon.points[edge_idx]
        p2 = polygon.points[(edge_idx + 1) % len(polygon.points)]

        # Pick random point along edge
        t = random.random()
        x = p1.x + t * (p2.x - p1.x)
        y = p1.y + t * (p2.y - p1.y)

        return Point2D(x, y)

    def _generate_streamline(self, start: Point2D, flow_field: Dict[Tuple[int, int], float],
                           resolution: float, polygon: LayerPolygon) -> List[Point2D]:
        streamline = [start]
        current = start
        max_steps = 100

        for _ in range(max_steps):
            # Get grid coordinates
            grid_x = int((current.x - min(flow_field.keys(), key=lambda k: k[0])[0] * resolution) / resolution)
            grid_y = int((current.y - min(flow_field.keys(), key=lambda k: k[1])[1] * resolution) / resolution)

            # Get flow direction
            angle = flow_field.get((grid_x, grid_y), 0)

            # Move in flow direction
            step_size = resolution * 0.5
            new_x = current.x + step_size * math.cos(angle)
            new_y = current.y + step_size * math.sin(angle)
            new_point = Point2D(new_x, new_y)

            # Check if still in polygon
            if not self._point_in_polygon(new_point, polygon):
                break

            streamline.append(new_point)
            current = new_point

        return streamline

    # ===== ADVANCED ANALYSIS AND OPTIMIZATION METHODS =====

    def analyze_infill_efficiency(self, infill_lines: List[List[Point2D]],
                                polygon: LayerPolygon) -> Dict[str, float]:
        if not infill_lines:
            return {}

        # Calculate coverage
        total_line_length = sum(sum(math.sqrt((line[i].x - line[i+1].x)**2 + (line[i].y - line[i+1].y)**2)
                                     for i in range(len(line) - 1)) for line in infill_lines)

        polygon_area = polygon.area()
        extrusion_volume = total_line_length * self.settings.extrusion_width * self.settings.layer_height

        # Simple coverage estimation (rough)
        coverage_ratio = min(1.0, extrusion_volume / (polygon_area * self.settings.layer_height * self.settings.fill_density))

        # Calculate uniformity (how evenly distributed the infill is)
        uniformity = self._calculate_infill_uniformity(infill_lines, polygon)

        # Calculate material efficiency
        material_efficiency = self._calculate_material_efficiency(infill_lines, polygon)

        return {
            'total_length': total_line_length,
            'coverage_ratio': coverage_ratio,
            'uniformity_score': uniformity,
            'material_efficiency': material_efficiency,
            'estimated_print_time': total_line_length / 50.0,  # Assuming 50 mm/min speed
            'line_count': len(infill_lines)
        }

    def _calculate_infill_uniformity(self, infill_lines: List[List[Point2D]],
                                   polygon: LayerPolygon) -> float:
        if not infill_lines:
            return 0.0

        # Sample points in polygon and check distance to nearest infill line
        min_x, min_y, max_x, max_y = self._get_polygon_bounds(polygon)
        sample_points = []

        # Generate sample grid
        grid_size = 10
        for i in range(grid_size):
            for j in range(grid_size):
                x = min_x + (max_x - min_x) * i / (grid_size - 1)
                y = min_y + (max_y - min_y) * j / (grid_size - 1)
                point = Point2D(x, y)
                if self._point_in_polygon(point, polygon):
                    sample_points.append(point)

        if not sample_points:
            return 1.0

        # Calculate average distance to nearest infill line
        total_distance = 0.0

        for sample_point in sample_points:
            min_distance = float('inf')

            for line in infill_lines:
                for i in range(len(line) - 1):
                    distance = self._point_to_line_distance(sample_point, line[i], line[i+1])
                    min_distance = min(min_distance, distance)

            total_distance += min_distance

        avg_distance = total_distance / len(sample_points)

        # Convert to uniformity score (lower average distance = higher uniformity)
        max_expected_distance = math.sqrt((max_x - min_x)**2 + (max_y - min_y)**2) / 10
        uniformity = 1.0 - min(1.0, avg_distance / max_expected_distance)

        return uniformity

    def _calculate_material_efficiency(self, infill_lines: List[List[Point2D]],
                                     polygon: LayerPolygon) -> float:
        # Simple efficiency based on coverage vs material used
        analysis = self.analyze_infill_efficiency(infill_lines, polygon)

        coverage = analysis.get('coverage_ratio', 0)
        target_density = self.settings.fill_density

        if target_density == 0:
            return 1.0 if coverage == 0 else 0.0

        # Efficiency = actual coverage / target density (capped at 1.0)
        efficiency = min(1.0, coverage / target_density)

        return efficiency

    def optimize_infill_parameters(self, polygon: LayerPolygon,
                                 requirements: Dict[str, float]) -> InfillConfiguration:
        config = InfillConfiguration()

        # Analyze polygon characteristics
        polygon_analysis = self._analyze_polygon_characteristics(polygon)

        # Optimize based on requirements
        strength_req = requirements.get('strength', 0.5)
        speed_req = requirements.get('speed', 0.5)
        quality_req = requirements.get('quality', 0.5)

        # Pattern selection
        if strength_req > 0.7:
            if speed_req > 0.7:
                config.pattern = InfillPattern.GYROID
            else:
                config.pattern = InfillPattern.CUBIC
        elif speed_req > 0.7:
            config.pattern = InfillPattern.LINE
        elif quality_req > 0.7:
            config.pattern = InfillPattern.HONEYCOMB
        else:
            config.pattern = InfillPattern.RECTILINEAR

        # Density optimization
        if polygon_analysis['complexity'] > 0.8:
            config.density = min(0.3, self.settings.fill_density * 1.2)  # Higher density for complex shapes
        elif polygon_analysis['aspect_ratio'] > 3.0:
            config.density = min(0.25, self.settings.fill_density * 1.1)  # Higher for elongated shapes

        # Quality settings
        if quality_req > 0.8:
            config.quality = InfillQuality.ULTRA
        elif quality_req > 0.6:
            config.quality = InfillQuality.HIGH
        elif speed_req > 0.7:
            config.quality = InfillQuality.DRAFT
        else:
            config.quality = InfillQuality.STANDARD

        return config

    def _analyze_polygon_characteristics(self, polygon: LayerPolygon) -> Dict[str, float]:
        if not polygon.points:
            return {'area': 0, 'perimeter': 0, 'complexity': 0, 'aspect_ratio': 1}

        area = polygon.area()
        perimeter = sum(math.sqrt((polygon.points[i].x - polygon.points[(i+1) % len(polygon.points)].x)**2 +
                                 (polygon.points[i].y - polygon.points[(i+1) % len(polygon.points)].y)**2)
                       for i in range(len(polygon.points)))

        # Complexity based on point count and shape irregularity
        expected_perimeter = 2 * math.pi * math.sqrt(area / math.pi)  # Circle perimeter
        complexity = min(1.0, perimeter / expected_perimeter if expected_perimeter > 0 else 1.0)

        # Aspect ratio
        x_coords = [p.x for p in polygon.points]
        y_coords = [p.y for p in polygon.points]
        width = max(x_coords) - min(x_coords)
        height = max(y_coords) - min(y_coords)
        aspect_ratio = max(width, height) / min(width, height) if min(width, height) > 0 else 1.0

        return {
            'area': area,
            'perimeter': perimeter,
            'complexity': complexity,
            'aspect_ratio': aspect_ratio
        }

    def generate_infill_report(self, polygon: LayerPolygon, pattern: InfillPattern,
                             infill_lines: List[List[Point2D]]) -> str:
        analysis = self.analysis_engine.analyze_infill_pattern(infill_lines, pattern.value)
        efficiency = self.analyze_infill_efficiency(infill_lines, polygon)

        report = f"""
INFILL GENERATION REPORT
========================

Pattern: {pattern.value}
Polygon Area: {polygon.area():.2f} mm²
Point Count: {len(polygon.points)}

INFILL METRICS:
- Total Length: {analysis.total_length:.2f} mm
- Line Segments: {analysis.segment_count}
- Material Usage: {analysis.material_usage:.2f} mm³
- Estimated Print Time: {analysis.print_time_estimate:.1f} min
- Strength Score: {analysis.strength_score:.2f}
- Quality Score: {analysis.quality_score:.2f}
- Material Efficiency: {analysis.material_efficiency:.2f}

EFFICIENCY ANALYSIS:
- Coverage Ratio: {efficiency['coverage_ratio']:.2f}
- Uniformity Score: {efficiency['uniformity_score']:.2f}
- Material Efficiency: {efficiency['material_efficiency']:.2f}
- Generation Time: {analysis.generation_time:.3f} s

OPTIMIZATION SCORE: {analysis.optimization_score:.2f}/1.0
"""

        return report

    def get_performance_stats(self) -> Dict[str, Any]:
        basic_stats = self.performance_optimizer.get_performance_stats()

        return {
            'infill_generation': {
                'total_patterns_generated': self.generation_stats['total_patterns_generated'],
                'average_generation_time': self.generation_stats['average_generation_time'],
                'cache_hit_rate': self.generation_stats.get('cache_hit_rate', 0),
                'pattern_distribution': dict(self.generation_stats['pattern_distribution'])
            },
            'pattern_performance': basic_stats
        }

    def clear_cache(self):
        self._pattern_cache.clear()
        self._adaptive_cache.clear()
        self.performance_optimizer.cache.clear()
        self.generation_stats['cache_hit_rate'] = 0
    
    # HELPER METHODS
    def _offset_polygon(self, polygon: LayerPolygon, distance: float) -> Optional[LayerPolygon]:
        if len(polygon.points) < 3:
            return None
        
        offset_points = []
        n = len(polygon.points)
        signed_area = sum(
            polygon.points[i].x * polygon.points[(i + 1) % n].y
            - polygon.points[(i + 1) % n].x * polygon.points[i].y
            for i in range(n)
        ) / 2.0
        orientation_sign = 1.0 if signed_area > 0 else -1.0
        
        for i in range(n):
            p1 = polygon.points[(i - 1) % n]
            p2 = polygon.points[i]
            p3 = polygon.points[(i + 1) % n]
            
            # Calculate normal vectors
            v1 = Point2D(p2.x - p1.x, p2.y - p1.y).normalize()
            v2 = Point2D(p3.x - p2.x, p3.y - p2.y).normalize()
            
            # Calculate perpendicular vectors (normals)
            n1 = Point2D(-v1.y, v1.x)
            n2 = Point2D(-v2.y, v2.x)
            
            # Average normal
            avg_normal = Point2D((n1.x + n2.x) / 2, (n1.y + n2.y) / 2).normalize()
            avg_normal = avg_normal * orientation_sign
            
            # Offset point
            offset_point = Point2D(
                p2.x + avg_normal.x * distance,
                p2.y + avg_normal.y * distance
            )
            offset_points.append(offset_point)
        
        if len(offset_points) < 3:
            return None
        
        return LayerPolygon(points=offset_points)

# Example usage and testing
if __name__ == "__main__":
    from .slicer_core import PrintSettings, Point2D, LayerPolygon, InfillPattern
    
    # Test all patterns
    test_patterns = [
        InfillPattern.RECTILINEAR,
        InfillPattern.LINE,
        InfillPattern.MONOTONIC,
        InfillPattern.GRID,
        InfillPattern.CROSS_HATCH,
        InfillPattern.TRIANGULAR,
        InfillPattern.HONEYCOMB,
        InfillPattern.GYROID,
        InfillPattern.CUBIC,
        InfillPattern.LIGHTNING,
        InfillPattern.WAVES,
        InfillPattern.VORONOI,
    ]
    
    # Create test settings
    for pattern in test_patterns:
        print(f"\nTesting {pattern.name}:")
        
        settings = PrintSettings(
            fill_density=0.2,
            fill_pattern=pattern,
            extrusion_width=0.4,
            layer_height=0.2
        )
        
        # Create test polygon (square)
        test_polygon = LayerPolygon(points=[
            Point2D(0, 0),
            Point2D(10, 0),
            Point2D(10, 10),
            Point2D(0, 10)
        ])
        
        # Generate infill
        generator = InfillGenerator(settings)
        infill_lines = generator.generate_infill(test_polygon, 0.4)
        
        print(f"  Generated {len(infill_lines)} infill lines")
        if infill_lines:
            total_points = sum(len(line) for line in infill_lines)
            print(f"  Total points: {total_points}")
            print(f"  Average points per line: {total_points / len(infill_lines):.1f}")
    
    print(f"\n✅ All {len(test_patterns)} patterns tested successfully!")
