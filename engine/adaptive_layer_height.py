# ------------------------------------------------------------------
# Copyright (c) 2026 Sleia Engine Development Team.
# This file is distributed under the MIT License. See LICENSE.
#
# Sleia Easy v 1.0.1 - Thermoplastic Python Slicer
#
# File: adaptive_layer_height.py
# Description: varies layer height with the shape.
# ------------------------------------------------------------------

import numpy as np
from typing import List, Tuple, Dict, Optional, Any
import math
import logging
from dataclasses import dataclass, field
from enum import Enum

from .slicer_core import Point2D, Point3D, Layer

logger = logging.getLogger(__name__)

class AdaptiveMode(Enum):
    DISABLED = "disabled"
    AUTO = "auto"  # Automatic based on geometry
    MANUAL = "manual"  # User-defined regions
    HYBRID = "hybrid"  # Auto + manual regions

class QualityLevel(Enum):
    DRAFT = "draft"
    STANDARD = "standard"
    FINE = "fine"
    ULTRA_FINE = "ultra_fine"

@dataclass
class AdaptiveRegion:
    center: Point2D
    radius: float
    min_layer_height: float
    max_layer_height: float
    priority: int = 1  # Higher priority overrides lower

@dataclass
class AdaptiveSettings:
    mode: AdaptiveMode = AdaptiveMode.AUTO
    min_layer_height: float = 0.05
    max_layer_height: float = 0.3
    base_layer_height: float = 0.2
    quality_level: QualityLevel = QualityLevel.STANDARD

    # Auto mode settings
    curvature_threshold: float = 0.1
    detail_size_threshold: float = 0.5
    overhang_angle_threshold: float = 45.0  # degrees
    smoothing_iterations: int = 3

    # Manual regions
    regions: List[AdaptiveRegion] = field(default_factory=list)

    # Performance settings
    max_layers_per_analysis: int = 1000
    analysis_resolution: float = 0.1  # mm

class AdaptiveLayerHeightAnalyzer:

    def __init__(self, settings: AdaptiveSettings):
        self.settings = settings
        self.layer_cache: Dict[int, float] = {}

    def analyze_layer(self, layer: Layer, layer_index: int) -> float:
        if self.settings.mode == AdaptiveMode.DISABLED:
            return self.settings.base_layer_height

        # Check cache first
        if layer_index in self.layer_cache:
            return self.layer_cache[layer_index]

        optimal_height = self._calculate_optimal_height(layer, layer_index)
        optimal_height = self._clamp_height(optimal_height)

        # Apply smoothing if enabled
        if self.settings.smoothing_iterations > 0:
            optimal_height = self._smooth_height(layer_index, optimal_height)

        self.layer_cache[layer_index] = optimal_height
        return optimal_height

    def _calculate_optimal_height(self, layer: Layer, layer_index: int) -> float:
        if self.settings.mode == AdaptiveMode.MANUAL:
            return self._analyze_manual_regions(layer)
        elif self.settings.mode == AdaptiveMode.HYBRID:
            auto_height = self._analyze_auto(layer, layer_index)
            manual_height = self._analyze_manual_regions(layer)
            return min(auto_height, manual_height)  # Use more restrictive height
        else:  # AUTO mode
            return self._analyze_auto(layer, layer_index)

    def _analyze_auto(self, layer: Layer, layer_index: int) -> float:
        if not layer.polygons:
            return self.settings.base_layer_height

        # Analyze different geometric features
        curvature_complexity = self._calculate_curvature_complexity(layer)
        detail_density = self._calculate_detail_density(layer)
        overhang_factor = self._calculate_overhang_factor(layer)
        bridge_factor = self._calculate_bridge_factor(layer)

        # Combine factors with weights
        complexity_score = (
            curvature_complexity * 0.4 +
            detail_density * 0.3 +
            overhang_factor * 0.2 +
            bridge_factor * 0.1
        )

        # Map complexity to layer height
        # Higher complexity = smaller layer height
        if complexity_score < 0.2:
            return self.settings.max_layer_height  # Simple geometry
        elif complexity_score < 0.5:
            return self.settings.base_layer_height  # Moderate complexity
        elif complexity_score < 0.8:
            return (self.settings.base_layer_height + self.settings.min_layer_height) / 2
        else:
            return self.settings.min_layer_height  # High complexity

    def _analyze_manual_regions(self, layer: Layer) -> float:
        if not self.settings.regions:
            return self.settings.base_layer_height

        # Find applicable regions for this layer
        applicable_heights = []

        for region in self.settings.regions:
            # Check if layer intersects with region (simplified 2D check)
            layer_bounds = self._get_layer_bounds(layer)
            region_bounds = (
                region.center.x - region.radius,
                region.center.y - region.radius,
                region.center.x + region.radius,
                region.center.y + region.radius
            )

            # Simple bounding box intersection
            if (layer_bounds[0] < region_bounds[2] and
                layer_bounds[2] > region_bounds[0] and
                layer_bounds[1] < region_bounds[3] and
                layer_bounds[3] > region_bounds[1]):
                applicable_heights.append(region.min_layer_height)

        if applicable_heights:
            return min(applicable_heights)  # Use smallest height for safety

        return self.settings.base_layer_height

    def _calculate_curvature_complexity(self, layer: Layer) -> float:
        if not layer.polygons:
            return 0.0

        total_curvature = 0.0
        point_count = 0

        for polygon in layer.polygons:
            if len(polygon.points) < 3:
                continue

            points = [(p.x, p.y) for p in polygon.points]
            curvatures = self._calculate_polygon_curvature(points)
            total_curvature += sum(abs(c) for c in curvatures)
            point_count += len(curvatures)

        if point_count == 0:
            return 0.0

        avg_curvature = total_curvature / point_count
        # Normalize to 0-1 range (arbitrary scaling)
        return min(1.0, avg_curvature * 100.0)

    def _calculate_detail_density(self, layer: Layer) -> float:
        if not layer.polygons:
            return 0.0

        total_detail_score = 0.0
        polygon_count = 0

        for polygon in layer.polygons:
            if len(polygon.points) < 3:
                continue

            # Calculate perimeter length
            perimeter = 0.0
            points = [(p.x, p.y) for p in polygon.points]
            for i in range(len(points)):
                p1 = np.array(points[i])
                p2 = np.array(points[(i + 1) % len(points)])
                perimeter += np.linalg.norm(p2 - p1)

            # Calculate area
            area = self._calculate_polygon_area(points)

            if area > 0:
                # Compactness ratio (circle-like = high, complex shape = low)
                compactness = 4 * math.pi * area / (perimeter * perimeter)
                # Convert to detail score (lower compactness = higher detail)
                detail_score = 1.0 - compactness
                total_detail_score += detail_score
                polygon_count += 1

        if polygon_count == 0:
            return 0.0
            
        return total_detail_score / polygon_count

    def _calculate_overhang_factor(self, layer: Layer) -> float:
        # This would require analysis of layer above
        # For now, return moderate overhang factor
        return 0.3

    def _calculate_bridge_factor(self, layer: Layer) -> float:
        # This would analyze unsupported spans
        # For now, return low bridge factor
        return 0.1

    def _calculate_polygon_curvature(self, points: List[Tuple[float, float]]) -> List[float]:
        curvatures = []

        if len(points) < 3:
            return curvatures

        for i in range(len(points)):
            p_prev = np.array(points[(i - 1) % len(points)])
            p_curr = np.array(points[i])
            p_next = np.array(points[(i + 1) % len(points)])

            # Calculate angle at current point
            v1 = p_prev - p_curr
            v2 = p_next - p_curr

            # Handle collinear points
            if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
                curvatures.append(0.0)
                continue

            # Cosine of angle between vectors
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            cos_angle = np.clip(cos_angle, -1.0, 1.0)

            angle = math.acos(cos_angle)
            # Convert to curvature (higher angle = higher curvature)
            curvature = abs(angle - math.pi) / math.pi  # 0 to 1
            curvatures.append(curvature)
        
        return curvatures

    def _calculate_polygon_area(self, points: List[Tuple[float, float]]) -> float:
        if len(points) < 3:
            return 0.0
            
        area = 0.0
        n = len(points)

        for i in range(n):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % n]
            area += x1 * y2 - x2 * y1

        return abs(area) / 2.0

    def _get_layer_bounds(self, layer: Layer) -> Tuple[float, float, float, float]:
        if not layer.polygons:
            return (0, 0, 0, 0)

        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')

        for polygon in layer.polygons:
            for point in polygon.points:
                min_x = min(min_x, point.x)
                min_y = min(min_y, point.y)
                max_x = max(max_x, point.x)
                max_y = max(max_y, point.y)

        return (min_x, min_y, max_x, max_y)

    def _clamp_height(self, height: float) -> float:
        return max(self.settings.min_layer_height,
                  min(self.settings.max_layer_height, height))

    def _smooth_height(self, layer_index: int, height: float) -> float:
        if layer_index == 0:
            return height

        # Get previous heights for smoothing
        prev_heights = []
        for i in range(max(0, layer_index - self.settings.smoothing_iterations), layer_index):
            if i in self.layer_cache:
                prev_heights.append(self.layer_cache[i])

        if not prev_heights:
            return height

        # Weighted average with recent layers
        weights = [1.0 / (len(prev_heights) - i) for i in range(len(prev_heights))]
        total_weight = sum(weights)

        smoothed_height = sum(h * w for h, w in zip(prev_heights, weights)) / total_weight
        smoothed_height = smoothed_height * (1 - self.settings.smoothing_factor) + \
                         height * self.settings.smoothing_factor

        return smoothed_height

class AdaptiveLayerHeightController:

    def __init__(self, settings: AdaptiveSettings = None):
        self.settings = settings or AdaptiveSettings()
        self.analyzer = AdaptiveLayerHeightAnalyzer(self.settings)
        self.height_map: Dict[int, float] = {}

    def analyze_model(self, layers: List[Layer]) -> Dict[int, float]:
        logger.info(f"Analyzing {len(layers)} layers for adaptive layer heights")

        height_map = {}

        for i, layer in enumerate(layers):
            if i >= self.settings.max_layers_per_analysis:
                logger.warning(f"Reached max layers per analysis ({self.settings.max_layers_per_analysis})")
                break

            optimal_height = self.analyzer.analyze_layer(layer, i)
            height_map[i] = optimal_height

        self.height_map = height_map
        logger.info(f"Generated adaptive heights for {len(height_map)} layers")
        return height_map

    def get_layer_height(self, layer_index: int) -> float:
        return self.height_map.get(layer_index, self.settings.base_layer_height)

    def add_manual_region(self, region: AdaptiveRegion):
        self.settings.regions.append(region)
        # Re-analyze if we have cached results
        if self.height_map:
            logger.info("Manual region added, consider re-analyzing model")

    def get_statistics(self) -> Dict[str, Any]:
        if not self.height_map:
            return {}

        heights = list(self.height_map.values())
        return {
            'total_layers_analyzed': len(heights),
            'min_height_used': min(heights),
            'max_height_used': max(heights),
            'avg_height_used': sum(heights) / len(heights),
            'height_variance': np.var(heights),
            'manual_regions': len(self.settings.regions),
            'mode': self.settings.mode.value,
            'quality_level': self.settings.quality_level.value
        }

    def export_height_map(self, filename: str):
        import json

        data = {
            'settings': {
                'mode': self.settings.mode.value,
                'min_layer_height': self.settings.min_layer_height,
                'max_layer_height': self.settings.max_layer_height,
                'base_layer_height': self.settings.base_layer_height,
                'quality_level': self.settings.quality_level.value
            },
            'height_map': self.height_map,
            'statistics': self.get_statistics()
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Height map exported to {filename}")

    def import_height_map(self, filename: str):
        import json

        with open(filename, 'r') as f:
            data = json.load(f)

        # Restore settings
        settings_data = data.get('settings', {})
        self.settings.mode = AdaptiveMode(settings_data.get('mode', 'auto'))
        self.settings.min_layer_height = settings_data.get('min_layer_height', 0.05)
        self.settings.max_layer_height = settings_data.get('max_layer_height', 0.3)
        self.settings.base_layer_height = settings_data.get('base_layer_height', 0.2)
        self.settings.quality_level = QualityLevel(settings_data.get('quality_level', 'standard'))

        # Restore height map
        self.height_map = data.get('height_map', {})

        logger.info(f"Height map imported from {filename}")

# Convenience functions for creating adaptive settings
def create_draft_settings() -> AdaptiveSettings:
    return AdaptiveSettings(
        mode=AdaptiveMode.AUTO,
        quality_level=QualityLevel.DRAFT,
        min_layer_height=0.15,
        max_layer_height=0.4,
        base_layer_height=0.3,
        curvature_threshold=0.05,
        smoothing_iterations=1
    )

def create_standard_settings() -> AdaptiveSettings:
    return AdaptiveSettings(
        mode=AdaptiveMode.AUTO,
        quality_level=QualityLevel.STANDARD,
        min_layer_height=0.1,
        max_layer_height=0.3,
        base_layer_height=0.2,
        curvature_threshold=0.1,
        smoothing_iterations=2
    )

def create_fine_settings() -> AdaptiveSettings:
    return AdaptiveSettings(
        mode=AdaptiveMode.AUTO,
        quality_level=QualityLevel.FINE,
        min_layer_height=0.05,
        max_layer_height=0.2,
        base_layer_height=0.15,
        curvature_threshold=0.15,
        smoothing_iterations=3
    )

def create_ultra_fine_settings() -> AdaptiveSettings:
    return AdaptiveSettings(
        mode=AdaptiveMode.AUTO,
        quality_level=QualityLevel.ULTRA_FINE,
        min_layer_height=0.02,
        max_layer_height=0.15,
        base_layer_height=0.1,
        curvature_threshold=0.2,
        smoothing_iterations=4
    )