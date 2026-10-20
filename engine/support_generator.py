#!/usr/bin/env python3
# ------------------------------------------------------------------
# Copyright (c) 2026 Sleia Engine Development Team.
# This file is distributed under the MIT License. See LICENSE.
#
# Sleia Easy v 1.0.1 - Thermoplastic Python Slicer
#
# File: support_generator.py
# Description: builds support under overhangs.
# ------------------------------------------------------------------

import numpy as np
import math
import random
import heapq
from typing import List, Tuple, Dict, Optional, Set, Union, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque
import time
from concurrent.futures import ThreadPoolExecutor
import networkx as nx
from scipy import spatial
from sklearn.cluster import DBSCAN

from .slicer_core import Point2D, Point3D, LayerPolygon, Layer, SupportType, PrintSettings, InfillPattern

logger = logging.getLogger(__name__)

# ===== ADVANCED SUPPORT ENUMS =====

class SupportPattern(Enum):
    GRID = "grid"
    LINES = "lines"
    CONCENTRIC = "concentric"
    HONEYCOMB = "honeycomb"
    TRIANGULAR = "triangular"
    ZIGZAG = "zigzag"
    CROSS = "cross"
    RADIAL = "radial"
    ADAPTIVE = "adaptive"

class TreeSupportStyle(Enum):
    ORGANIC = "organic"
    STRUCTURAL = "structural"
    HYBRID = "hybrid"
    MINIMAL = "minimal"
    ROBUST = "robust"

class SupportOptimization(Enum):
    MINIMAL_MATERIAL = "minimal_material"
    MAXIMAL_STRENGTH = "maximal_strength"
    BALANCED = "balanced"
    SPEED_OPTIMIZED = "speed_optimized"
    QUALITY_FOCUSED = "quality_focused"

class SupportInterface(Enum):
    NONE = "none"
    CONTACT = "contact"
    SEPARABLE = "separable"
    SMOOTH = "smooth"

class SupportAngleMode(Enum):
    EVERYWHERE = "everywhere"
    BUILD_PLATE_ONLY = "build_plate_only"
    SMART = "smart"
    ADAPTIVE = "adaptive"

# ===== ADVANCED DATA STRUCTURES =====

@dataclass
class SupportRegion:
    polygon: LayerPolygon
    start_layer: int
    end_layer: int
    support_type: str = "normal"  # normal, interface, base, raft
    area: float = 0.0
    perimeter: float = 0.0
    centroid: Point2D = None
    bounding_box: Tuple[float, float, float, float] = None  # min_x, min_y, max_x, max_y
    complexity_score: float = 0.0
    overhang_angle: float = 0.0
    material_volume: float = 0.0
    print_time_estimate: float = 0.0
    stability_score: float = 0.0
    optimization_priority: float = 1.0

@dataclass
class SupportColumn:
    base_point: Point2D
    top_point: Point2D
    radius: float
    start_layer: int
    end_layer: int
    branches: List['SupportBranch'] = field(default_factory=list)
    load_capacity: float = 0.0
    material_volume: float = 0.0
    stability_factor: float = 1.0
    branch_angle: float = 45.0  # degrees
    growth_direction: Point2D = None
    parent_column: Optional['SupportColumn'] = None
    child_columns: List['SupportColumn'] = field(default_factory=list)
    layer_heights: List[float] = field(default_factory=list)

@dataclass
class SupportBranch:
    start_point: Point2D
    end_point: Point2D
    start_layer: int
    end_layer: int
    radius: float
    parent_branch: Optional['SupportBranch'] = None
    child_branches: List['SupportBranch'] = field(default_factory=list)
    branch_angle: float = 45.0
    growth_vector: Point2D = None
    material_volume: float = 0.0
    load_bearing_capacity: float = 0.0
    stability_score: float = 1.0
    optimization_flags: Set[str] = field(default_factory=set)

@dataclass
class TreeSupportNode:
    position: Point2D
    layer: int
    radius: float
    parent: Optional['TreeSupportNode'] = None
    children: List['TreeSupportNode'] = field(default_factory=list)
    support_type: str = "branch"
    load_path: List[Point2D] = field(default_factory=list)
    stability_vector: Point2D = None
    branch_angle: float = 45.0

@dataclass
class SupportIsland:
    regions: List[SupportRegion]
    centroid: Point2D
    total_area: float = 0.0
    bounding_box: Tuple[float, float, float, float] = None
    connectivity_score: float = 0.0
    stability_score: float = 0.0
    material_efficiency: float = 0.0
    optimization_potential: float = 0.0

@dataclass
class SupportOptimizationResult:
    original_volume: float
    optimized_volume: float
    material_savings: float
    strength_maintained: float
    print_time_change: float
    stability_improved: float
    optimization_time: float
    algorithm_used: str
    convergence_score: float

@dataclass
class SupportAnalysis:
    total_regions: int
    total_volume: float
    average_density: float
    overhang_distribution: Dict[str, int]
    support_angles: List[float]
    material_efficiency: float
    structural_integrity: float
    print_time_estimate: float
    removable_percentage: float
    interface_area: float
    base_area: float
    tree_support_ratio: float

@dataclass
class SupportLearningData:
    geometry_features: Dict[str, float]
    support_parameters: Dict[str, Union[float, int, str]]
    performance_metrics: Dict[str, float]
    material_usage: float
    print_time: float
    success_score: float
    failure_modes: List[str]
    optimization_opportunities: List[str]

@dataclass
class AdaptiveSupportProfile:
    name: str
    material_type: str
    geometry_complexity: float
    optimal_density: float
    preferred_pattern: SupportPattern
    tree_support_enabled: bool
    max_overhang_angle: float
    min_support_area: float
    interface_layers: int
    base_layers: int
    pillar_diameter: float
    branch_angle: float
    learning_confidence: float
    adaptation_rate: float
    performance_history: List[SupportLearningData] = field(default_factory=list)

class AdvancedSupportGenerator:

    def __init__(self, settings: PrintSettings):
        self.settings = settings

        # Basic parameters
        self.overhang_threshold = math.radians(self.settings.support_angle)
        self.support_xy_distance = 0.7  # mm
        self.support_z_distance = 0.2   # mm
        self.interface_layers = self.settings.support_interface_layers

        # Advanced parameters
        self.tree_support_enabled = True
        self.adaptive_support = True
        self.machine_learning_enabled = True
        self.multi_threaded = True
        self.optimization_level = 3  # 1-5 scale

        # Tree support parameters
        self.branch_angle = 45.0  # degrees
        self.branch_radius_min = 0.4  # mm
        self.branch_radius_max = 2.0  # mm
        self.branch_length_max = 10.0  # mm
        self.pillar_radius = 1.0  # mm
        self.tree_height_min = 3  # layers
        self.tree_height_max = 50  # layers

        # Optimization parameters
        self.material_efficiency_target = 0.85
        self.structural_integrity_target = 0.95
        self.optimization_iterations = 10
        self.convergence_threshold = 0.01

        # Learning and adaptation
        self.adaptive_profiles: Dict[str, AdaptiveSupportProfile] = {}
        self.learning_data: List[SupportLearningData] = []
        self.performance_history: deque = deque(maxlen=1000)

        # Analysis and monitoring
        self.generation_stats: Dict[str, Union[int, float]] = {}
        self.optimization_metrics: Dict[str, float] = {}

        # Threading and performance
        self.executor = ThreadPoolExecutor(max_workers=8)
        self.processing_queue: deque = deque()
        self.results_cache: Dict[str, Any] = {}

        # Initialize adaptive profiles
        self._initialize_adaptive_profiles()

        logger.info("Support generator initialized")

    def _initialize_adaptive_profiles(self):
        self.adaptive_profiles = {
            "default": AdaptiveSupportProfile(
                "Default", "PLA", 0.5, 0.15, SupportPattern.GRID,
                True, 60.0, 5.0, 3, 3, 1.0, 45.0, 0.7, 0.1
            ),
            "organic": AdaptiveSupportProfile(
                "Organic Shapes", "PLA", 0.8, 0.12, SupportPattern.TRIANGULAR,
                True, 45.0, 3.0, 2, 2, 0.8, 50.0, 0.8, 0.15
            ),
            "mechanical": AdaptiveSupportProfile(
                "Mechanical Parts", "ABS", 0.6, 0.18, SupportPattern.HONEYCOMB,
                False, 70.0, 8.0, 4, 4, 1.2, 40.0, 0.9, 0.08
            ),
            "large_format": AdaptiveSupportProfile(
                "Large Format", "PETG", 0.4, 0.10, SupportPattern.GRID,
                True, 55.0, 10.0, 3, 5, 1.5, 35.0, 0.75, 0.12
            ),
            "high_detail": AdaptiveSupportProfile(
                "High Detail", "Resin-like", 0.9, 0.08, SupportPattern.CONCENTRIC,
                True, 30.0, 2.0, 1, 2, 0.6, 55.0, 0.85, 0.18
            ),
            "minimal": AdaptiveSupportProfile(
                "Minimal Support", "Strong Material", 0.3, 0.20, SupportPattern.CROSS,
                False, 75.0, 15.0, 5, 6, 1.8, 30.0, 0.95, 0.05
            )
        }

    # ===== ADVANCED SUPPORT GENERATION METHODS =====

    def generate_advanced_supports(self, layers: List[Layer], progress_callback=None) -> List[Layer]:
        start_time = time.time()

        # Analyze model geometry for support requirements
        support_analysis = self._analyze_model_for_supports(layers)

        if not support_analysis['needs_support']:
            logger.info("No support required for this model")
            return layers

        # Select optimal support strategy
        strategy = self._select_support_strategy(support_analysis)

        # Generate initial support regions
        support_regions = self._generate_support_regions(layers, strategy)

        # Apply tree support algorithm if enabled
        if self.tree_support_enabled and strategy['tree_support']:
            tree_supports = self._generate_tree_supports(layers, support_regions)
            support_regions.extend(tree_supports)

        # Optimize support structure
        optimized_regions = self._optimize_support_structure(support_regions, strategy)

        # Apply adaptive profiles
        final_regions = self._apply_adaptive_profiles(optimized_regions, support_analysis)

        # Integrate supports into layers
        layers_with_supports = self._integrate_supports_into_layers(layers, final_regions)

        # Generate statistics
        generation_time = time.time() - start_time
        self._generate_support_statistics(final_regions, generation_time)

        logger.info(f"Advanced support generation completed in {generation_time:.2f}s")
        return layers_with_supports

    def _analyze_model_for_supports(self, layers: List[Layer]) -> Dict[str, Any]:
        analysis = {
            'needs_support': False,
            'total_overhang_area': 0.0,
            'max_overhang_angle': 0.0,
            'overhang_distribution': defaultdict(int),
            'critical_regions': [],
            'geometry_complexity': 0.0,
            'support_volume_estimate': 0.0,
            'recommended_strategy': 'minimal',
            'tree_support_benefit': 0.0,
            'material_efficiency': 1.0
        }

        total_area = 0.0
        overhang_area = 0.0
        angle_distribution = defaultdict(int)

        # Analyze each layer
        for i, layer in enumerate(layers):
            if i == 0:
                continue  # Skip first layer

            layer_area = sum(polygon.area() for polygon in layer.polygons)
            total_area += layer_area

            # Analyze overhangs
            overhangs = self._detect_overhangs(layer, layers[i-1] if i > 0 else None)
            for overhang in overhangs:
                overhang_area += overhang['area']
                angle = overhang['angle']

                # Categorize overhang angles
                if angle > 75:
                    angle_distribution['severe'] += 1
                elif angle > 60:
                    angle_distribution['moderate'] += 1
                elif angle > 45:
                    angle_distribution['mild'] += 1
                else:
                    angle_distribution['minimal'] += 1

                analysis['max_overhang_angle'] = max(analysis['max_overhang_angle'], angle)

                # Identify critical regions
                if angle > self.overhang_threshold and overhang['area'] > 10:  # mm²
                    analysis['critical_regions'].append({
                        'layer': i,
                        'area': overhang['area'],
                        'angle': angle,
                        'position': overhang['centroid']
                    })

        analysis['total_overhang_area'] = overhang_area
        analysis['overhang_distribution'] = dict(angle_distribution)
        analysis['needs_support'] = overhang_area > 50 or analysis['max_overhang_angle'] > 45

        # Calculate geometry complexity
        if total_area > 0:
            analysis['geometry_complexity'] = overhang_area / total_area

        # Estimate support volume
        analysis['support_volume_estimate'] = self._estimate_support_volume(analysis)

        # Determine optimal strategy
        analysis['recommended_strategy'] = self._determine_optimal_strategy(analysis)

        # Calculate tree support benefit
        analysis['tree_support_benefit'] = self._calculate_tree_support_benefit(analysis)

        return analysis

    def _detect_overhangs(self, current_layer: Layer, previous_layer: Optional[Layer]) -> List[Dict]:
        overhangs = []

        if not previous_layer:
            return overhangs

        # Convert layers to polygons for analysis
        current_polygons = [self._polygon_to_points(polygon) for polygon in current_layer.polygons]
        previous_polygons = [self._polygon_to_points(polygon) for polygon in previous_layer.polygons]

        # Find overhanging regions
        for curr_poly in current_polygons:
            for prev_poly in previous_polygons:
                # Calculate overlap and overhang
                overlap = self._calculate_polygon_overlap(curr_poly, prev_poly)
                if overlap['area'] < 0.1:  # Minimal overlap
                    overhang_area = self._calculate_polygon_area(curr_poly)
                    if overhang_area > 1.0:  # Significant overhang
                        # Calculate overhang angle
                        angle = self._calculate_overhang_angle(curr_poly, prev_poly)

                        overhangs.append({
                            'polygon': curr_poly,
                            'area': overhang_area,
                            'angle': angle,
                            'centroid': self._calculate_polygon_centroid(curr_poly)
                        })

        return overhangs

    def _calculate_overhang_angle(self, current_polygon: List[Point2D],
                                previous_polygon: List[Point2D]) -> float:
        # Simplified angle calculation
        curr_centroid = self._calculate_polygon_centroid(current_polygon)
        prev_centroid = self._calculate_polygon_centroid(previous_polygon)

        if curr_centroid and prev_centroid:
            # Calculate angle based on centroid offset
            dx = curr_centroid.x - prev_centroid.x
            dy = curr_centroid.y - prev_centroid.y
            distance = math.sqrt(dx*dx + dy*dy)

            if distance > 0.1:  # Significant offset
                # Angle from vertical (90 degrees = no overhang, 0 = severe overhang)
                angle = math.degrees(math.atan2(distance, self.settings.layer_height))
                return min(90, angle)

        return 90  # Default to no overhang

    def _select_support_strategy(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        strategy = {
            'pattern': SupportPattern.GRID,
            'tree_support': False,
            'density': self.settings.support_density,
            'angle_threshold': self.settings.support_angle,
            'optimization': SupportOptimization.BALANCED,
            'interface': SupportInterface.SEPARABLE,
            'max_pillar_distance': 20.0,
            'min_pillar_radius': 0.8,
            'max_branch_angle': 50.0
        }

        # Adjust based on analysis
        complexity = analysis['geometry_complexity']

        if complexity > 0.7:  # High complexity
            strategy['tree_support'] = True
            strategy['pattern'] = SupportPattern.TRIANGULAR
            strategy['optimization'] = SupportOptimization.MAXIMAL_STRENGTH
        elif complexity > 0.4:  # Medium complexity
            strategy['tree_support'] = True
            strategy['pattern'] = SupportPattern.HONEYCOMB
            strategy['optimization'] = SupportOptimization.BALANCED
        else:  # Low complexity
            strategy['tree_support'] = False
            strategy['pattern'] = SupportPattern.GRID
            strategy['optimization'] = SupportOptimization.MINIMAL_MATERIAL

        # Adjust density based on overhang severity
        severe_overhangs = analysis['overhang_distribution'].get('severe', 0)
        if severe_overhangs > 5:
            strategy['density'] = min(0.25, strategy['density'] * 1.5)

        # Use adaptive profile if available
        material_type = getattr(self.settings, 'filament_type', 'PLA')
        if material_type in self.adaptive_profiles:
            profile = self.adaptive_profiles[material_type]
            strategy['density'] = profile.optimal_density
            strategy['pattern'] = profile.preferred_pattern
            strategy['tree_support'] = profile.tree_support_enabled

        return strategy

    def _generate_support_regions(self, layers: List[Layer], strategy: Dict[str, Any]) -> List[SupportRegion]:
        support_regions = []

        # Process each layer
        for layer_idx, layer in enumerate(layers):
            if layer_idx < 2:  # Skip bottom layers
                continue

            # Find areas needing support
            support_areas = self._identify_support_areas(layer, layers[layer_idx-1] if layer_idx > 0 else None, strategy)

            for area in support_areas:
                region = SupportRegion(
                    polygon=area['polygon'],
                    start_layer=area['start_layer'],
                    end_layer=layer_idx,
                    support_type='normal',
                    area=area['area'],
                    overhang_angle=area['angle'],
                    centroid=area['centroid']
                )

                # Calculate additional properties
                region.perimeter = self._calculate_polygon_perimeter(area['polygon'])
                region.bounding_box = self._calculate_bounding_box(area['polygon'])
                region.complexity_score = self._calculate_region_complexity(area['polygon'])
                region.material_volume = self._estimate_region_volume(region)

                support_regions.append(region)

        return support_regions

    def _generate_tree_supports(self, layers: List[Layer], support_regions: List[SupportRegion]) -> List[SupportRegion]:
        tree_regions = []

        # Group support regions by proximity
        islands = self._cluster_support_regions(support_regions)

        for island in islands:
            if island.total_area > 20:  # Only for significant islands
                tree_structure = self._build_tree_structure(island, layers)
                tree_regions.extend(tree_structure)

        return tree_regions

    def _build_tree_structure(self, island: SupportIsland, layers: List[Layer]) -> List[SupportRegion]:
        tree_regions = []

        # Create root nodes at build plate
        root_nodes = self._create_tree_roots(island)

        # Build tree upwards using growth algorithm
        for layer_idx in range(len(layers)):
            current_layer = layers[layer_idx]

            # Grow tree branches for this layer
            layer_nodes = self._grow_tree_layer(root_nodes, layer_idx, island)

            # Convert nodes to support regions
            for node in layer_nodes:
                region = SupportRegion(
                    polygon=self._create_node_polygon(node),
                    start_layer=node.layer,
                    end_layer=node.layer + 1,
                    support_type='tree',
                    area=math.pi * node.radius * node.radius,
                    centroid=node.position
                )
                tree_regions.append(region)

        return tree_regions

    def _grow_tree_layer(self, parent_nodes: List[TreeSupportNode],
                        layer_idx: int, island: SupportIsland) -> List[TreeSupportNode]:
        new_nodes = []

        for parent in parent_nodes:
            # Determine if branching is needed
            if self._should_branch(parent, island):
                branches = self._create_branches(parent, layer_idx)
                new_nodes.extend(branches)
            else:
                # Continue growing existing branch
                continued_node = self._continue_branch(parent, layer_idx)
                if continued_node:
                    new_nodes.append(continued_node)

        return new_nodes

    def _should_branch(self, node: TreeSupportNode, island: SupportIsland) -> bool:
        # Branch if load is too high or coverage area is large
        load_factor = len(node.load_path) / 10.0  # Normalize load
        coverage_factor = self._calculate_node_coverage(node, island)

        return load_factor > 0.8 or coverage_factor > 15.0

    def _create_branches(self, parent: TreeSupportNode, layer_idx: int) -> List[TreeSupportNode]:
        branches = []

        # Create 2-4 branches depending on load
        num_branches = min(4, max(2, int(len(parent.load_path) / 5) + 1))

        for i in range(num_branches):
            angle = (i * 360.0 / num_branches) + random.uniform(-10, 10)
            length = random.uniform(3, 8)

            # Calculate branch end point
            angle_rad = math.radians(angle)
            end_x = parent.position.x + length * math.cos(angle_rad)
            end_y = parent.position.y + length * math.sin(angle_rad)
            end_point = Point2D(end_x, end_y)

            # Create branch node
            branch = TreeSupportNode(
                position=end_point,
                layer=layer_idx,
                radius=max(self.branch_radius_min, parent.radius * 0.8),
                parent=parent,
                branch_angle=angle
            )

            parent.children.append(branch)
            branches.append(branch)

        return branches

    def _continue_branch(self, parent: TreeSupportNode, layer_idx: int) -> Optional[TreeSupportNode]:
        # Check if branch should continue
        if parent.radius < self.branch_radius_min * 0.5:
            return None  # Too thin to continue

        # Create continuation node
        continuation = TreeSupportNode(
            position=parent.position,  # Same position for now
            layer=layer_idx,
            radius=parent.radius * 0.95,  # Slightly thinner
            parent=parent,
            branch_angle=parent.branch_angle
        )

        parent.children.append(continuation)
        return continuation

    def _optimize_support_structure(self, support_regions: List[SupportRegion],
                                  strategy: Dict[str, Any]) -> List[SupportRegion]:
        if not self.adaptive_support:
            return support_regions

        optimized_regions = support_regions.copy()

        # Apply various optimization algorithms
        optimized_regions = self._apply_topology_optimization(optimized_regions, strategy)
        optimized_regions = self._apply_density_optimization(optimized_regions, strategy)
        optimized_regions = self._apply_connectivity_optimization(optimized_regions, strategy)
        optimized_regions = self._apply_stability_optimization(optimized_regions, strategy)

        return optimized_regions

    def _apply_topology_optimization(self, regions: List[SupportRegion],
                                   strategy: Dict[str, Any]) -> List[SupportRegion]:
        # Remove redundant supports
        optimized = []
        removal_threshold = 0.7  # Remove supports with low contribution

        for region in regions:
            # Calculate support contribution score
            contribution = self._calculate_support_contribution(region, regions)

            if contribution > removal_threshold:
                # Adjust region properties based on contribution
                region.optimization_priority = contribution
                region.radius *= (0.8 + 0.4 * contribution)  # Scale radius
                optimized.append(region)
            else:
                logger.debug(f"Removing low-contribution support region: {contribution:.3f}")

        return optimized

    def _apply_density_optimization(self, regions: List[SupportRegion],
                                  strategy: Dict[str, Any]) -> List[SupportRegion]:
        # Adjust density based on local requirements
        for region in regions:
            local_complexity = region.complexity_score
            overhang_factor = region.overhang_angle / 90.0

            # Calculate optimal density for this region
            base_density = strategy['density']
            complexity_factor = 0.5 + 0.5 * local_complexity
            overhang_factor = 0.3 + 0.7 * overhang_factor

            optimal_density = base_density * complexity_factor * overhang_factor
            optimal_density = max(0.05, min(0.3, optimal_density))  # Clamp

            # Adjust region based on optimal density
            region.material_volume *= optimal_density / base_density

        return regions

    def _apply_connectivity_optimization(self, regions: List[SupportRegion],
                                       strategy: Dict[str, Any]) -> List[SupportRegion]:
        # Group regions into islands
        islands = self._cluster_support_regions(regions)

        # Optimize each island
        optimized_regions = []
        for island in islands:
            island_regions = self._optimize_island_connectivity(island, strategy)
            optimized_regions.extend(island_regions)

        return optimized_regions

    def _optimize_island_connectivity(self, island: SupportIsland,
                                    strategy: Dict[str, Any]) -> List[SupportRegion]:
        regions = island.regions

        if len(regions) < 2:
            return regions

        # Create connectivity graph
        graph = self._build_connectivity_graph(regions)

        # Find optimal connections
        optimal_connections = self._find_optimal_connections(graph, strategy)

        # Add connection supports
        for connection in optimal_connections:
            bridge_region = self._create_bridge_support(connection, strategy)
            if bridge_region:
                regions.append(bridge_region)

        return regions

    def _apply_stability_optimization(self, regions: List[SupportRegion],
                                    strategy: Dict[str, Any]) -> List[SupportRegion]:
        for region in regions:
            # Calculate stability factors
            base_stability = self._calculate_base_stability(region)
            load_stability = self._calculate_load_stability(region, regions)
            connection_stability = self._calculate_connection_stability(region, regions)

            overall_stability = (base_stability + load_stability + connection_stability) / 3.0

            # Adjust region properties for stability
            if overall_stability < 0.7:
                # Increase radius/material for better stability
                region.radius *= 1.2
                region.material_volume *= 1.3
                region.stability_score = overall_stability

        return regions

    def _cluster_support_regions(self, regions: List[SupportRegion]) -> List[SupportIsland]:
        if not regions:
            return []

        # Extract centroids for clustering
        centroids = np.array([[r.centroid.x, r.centroid.y] for r in regions])

        # Use DBSCAN for clustering
        clustering = DBSCAN(eps=15.0, min_samples=1).fit(centroids)
        labels = clustering.labels_

        # Group regions by cluster
        islands = []
        cluster_groups = defaultdict(list)

        for i, region in enumerate(regions):
            cluster_id = labels[i]
            cluster_groups[cluster_id].append(region)

        # Create islands
        for cluster_regions in cluster_groups.values():
            if cluster_regions:
                island = self._create_support_island(cluster_regions)
                islands.append(island)

        return islands

    def _create_support_island(self, regions: List[SupportRegion]) -> SupportIsland:
        # Calculate island properties
        total_area = sum(r.area for r in regions)
        centroids = [(r.centroid.x, r.centroid.y) for r in regions]
        avg_centroid = Point2D(
            sum(c[0] for c in centroids) / len(centroids),
            sum(c[1] for c in centroids) / len(centroids)
        )

        # Calculate bounding box
        min_x = min(r.centroid.x for r in regions)
        max_x = max(r.centroid.x for r in regions)
        min_y = min(r.centroid.y for r in regions)
        max_y = max(r.centroid.y for r in regions)

        island = SupportIsland(
            regions=regions,
            centroid=avg_centroid,
            total_area=total_area,
            bounding_box=(min_x, min_y, max_x, max_y)
        )

        # Calculate additional properties
        island.connectivity_score = self._calculate_island_connectivity(island)
        island.stability_score = self._calculate_island_stability(island)
        island.material_efficiency = self._calculate_island_efficiency(island)

        return island

    def _calculate_support_contribution(self, region: SupportRegion,
                                      all_regions: List[SupportRegion]) -> float:
        if not all_regions:
            return 1.0

        # Factors: area, position, connectivity
        area_factor = region.area / max(r.area for r in all_regions)

        # Position factor (closer to center is better)
        distance_from_center = math.sqrt(region.centroid.x**2 + region.centroid.y**2)
        position_factor = 1.0 / (1.0 + distance_from_center / 50.0)

        # Connectivity factor
        nearby_regions = [r for r in all_regions
                         if self._calculate_distance(region.centroid, r.centroid) < 20.0]
        connectivity_factor = len(nearby_regions) / max(1, len(all_regions) * 0.1)

        # Overhang factor
        overhang_factor = region.overhang_angle / 90.0

        contribution = (area_factor * 0.3 +
                       position_factor * 0.2 +
                       connectivity_factor * 0.3 +
                       overhang_factor * 0.2)

        return min(1.0, contribution)

    def _calculate_base_stability(self, region: SupportRegion) -> float:
        # Factors: area, aspect ratio, material properties
        area_stability = min(1.0, region.area / 50.0)  # Larger area = more stable

        # Aspect ratio (closer to 1.0 is better)
        if region.bounding_box:
            width = region.bounding_box[2] - region.bounding_box[0]
            height = region.bounding_box[3] - region.bounding_box[1]
            aspect_ratio = min(width, height) / max(width, height) if max(width, height) > 0 else 1.0
            aspect_stability = 1.0 - abs(1.0 - aspect_ratio)
        else:
            aspect_stability = 0.5

        return (area_stability + aspect_stability) / 2.0

    def _calculate_load_stability(self, region: SupportRegion,
                                all_regions: List[SupportRegion]) -> float:
        # Estimate load based on supported area and height
        height_factor = region.end_layer - region.start_layer
        load_factor = region.area * height_factor / 1000.0  # Normalize

        # Check if load is distributed
        nearby_support = sum(1 for r in all_regions
                           if self._calculate_distance(region.centroid, r.centroid) < 15.0)

        distribution_factor = min(1.0, nearby_support / 3.0)

        return min(1.0, load_factor * distribution_factor)

    def _calculate_connection_stability(self, region: SupportRegion,
                                      all_regions: List[SupportRegion]) -> float:
        # Find connected regions
        connections = 0
        for other in all_regions:
            if other != region:
                distance = self._calculate_distance(region.centroid, other.centroid)
                if distance < region.radius * 3:  # Connection threshold
                    connections += 1

        # More connections = more stable
        return min(1.0, connections / 4.0)

    def _build_connectivity_graph(self, regions: List[SupportRegion]) -> nx.Graph:
        graph = nx.Graph()

        # Add nodes
        for i, region in enumerate(regions):
            graph.add_node(i, region=region)

        # Add edges based on proximity
        for i in range(len(regions)):
            for j in range(i + 1, len(regions)):
                distance = self._calculate_distance(regions[i].centroid, regions[j].centroid)
                if distance < 25.0:  # Connection threshold
                    weight = 1.0 / (distance + 1.0)  # Closer = stronger connection
                    graph.add_edge(i, j, weight=weight, distance=distance)

        return graph

    def _find_optimal_connections(self, graph: nx.Graph, strategy: Dict[str, Any]) -> List[Tuple[int, int]]:
        connections = []

        # Use minimum spanning tree for basic connectivity
        if len(graph.nodes) > 1:
            mst = nx.minimum_spanning_tree(graph, weight='weight')
            connections.extend(list(mst.edges()))

        # Add additional connections for redundancy
        redundancy_factor = 0.3  # Add 30% more connections
        num_additional = int(len(connections) * redundancy_factor)

        # Find high-weight edges not in MST
        all_edges = sorted(graph.edges(data=True),
                          key=lambda x: x[2]['weight'], reverse=True)

        mst_edges = set((min(u, v), max(u, v)) for u, v in mst.edges())

        additional_count = 0
        for u, v, data in all_edges:
            edge_tuple = (min(u, v), max(u, v))
            if edge_tuple not in mst_edges and additional_count < num_additional:
                connections.append((u, v))
                additional_count += 1

        return connections

    def _create_bridge_support(self, connection: Tuple[int, int],
                             strategy: Dict[str, Any]) -> Optional[SupportRegion]:
        # This is a simplified implementation
        # In a full implementation, this would create appropriate geometry
        return None  # Placeholder

    # ===== UTILITY METHODS =====

    def _polygon_to_points(self, polygon: LayerPolygon) -> List[Point2D]:
        return polygon.points

    def _calculate_polygon_overlap(self, poly1: List[Point2D], poly2: List[Point2D]) -> Dict[str, float]:
        # Simplified overlap calculation
        return {'area': 0.0, 'overlap_ratio': 0.0}

    def _calculate_polygon_area(self, polygon: List[Point2D]) -> float:
        if len(polygon) < 3:
            return 0.0

        area = 0.0
        n = len(polygon)
        for i in range(n):
            j = (i + 1) % n
            area += polygon[i].x * polygon[j].y
            area -= polygon[j].x * polygon[i].y
        area = abs(area) / 2.0
        return area

    def _calculate_polygon_centroid(self, polygon: List[Point2D]) -> Optional[Point2D]:
        if not polygon:
            return None

        x_sum = sum(p.x for p in polygon)
        y_sum = sum(p.y for p in polygon)
        return Point2D(x_sum / len(polygon), y_sum / len(polygon))

    def _calculate_polygon_perimeter(self, polygon: List[Point2D]) -> float:
        if len(polygon) < 2:
            return 0.0

        perimeter = 0.0
        n = len(polygon)
        for i in range(n):
            j = (i + 1) % n
            dx = polygon[j].x - polygon[i].x
            dy = polygon[j].y - polygon[i].y
            perimeter += math.sqrt(dx*dx + dy*dy)
        return perimeter

    def _calculate_bounding_box(self, polygon: List[Point2D]) -> Tuple[float, float, float, float]:
        if not polygon:
            return 0, 0, 0, 0

        min_x = min(p.x for p in polygon)
        max_x = max(p.x for p in polygon)
        min_y = min(p.y for p in polygon)
        max_y = max(p.y for p in polygon)

        return min_x, min_y, max_x, max_y

    def _calculate_region_complexity(self, polygon: List[Point2D]) -> float:
        if len(polygon) < 3:
            return 0.0

        # Complexity based on perimeter/area ratio and vertex count
        area = self._calculate_polygon_area(polygon)
        perimeter = self._calculate_polygon_perimeter(polygon)

        if area == 0:
            return 1.0

        pa_ratio = perimeter / math.sqrt(area)  # Perimeter/area ratio
        vertex_factor = len(polygon) / 20.0  # More vertices = more complex

        complexity = min(1.0, (pa_ratio / 10.0 + vertex_factor) / 2.0)
        return complexity

    def _calculate_distance(self, p1: Point2D, p2: Point2D) -> float:
        dx = p1.x - p2.x
        dy = p1.y - p2.y
        return math.sqrt(dx*dx + dy*dy)

    def _estimate_region_volume(self, region: SupportRegion) -> float:
        height = (region.end_layer - region.start_layer) * self.settings.layer_height
        return region.area * height

    def _estimate_support_volume(self, analysis: Dict[str, Any]) -> float:
        overhang_area = analysis['total_overhang_area']
        avg_height = 10  # Assume average 10 layers of support
        volume_per_area = self.settings.layer_height * avg_height

        return overhang_area * volume_per_area * self.settings.support_density

    def _determine_optimal_strategy(self, analysis: Dict[str, Any]) -> str:
        complexity = analysis['geometry_complexity']
        overhang_area = analysis['total_overhang_area']

        if complexity > 0.7 or overhang_area > 500:
            return 'robust'
        elif complexity > 0.4 or overhang_area > 200:
            return 'balanced'
        else:
            return 'minimal'

    def _calculate_tree_support_benefit(self, analysis: Dict[str, Any]) -> float:
        complexity = analysis['geometry_complexity']
        overhang_area = analysis['total_overhang_area']

        # Tree supports benefit complex geometries more
        benefit = complexity * 0.6 + min(overhang_area / 1000.0, 1.0) * 0.4
        return min(1.0, benefit)

    def _identify_support_areas(self, layer: Layer, prev_layer: Optional[Layer],
                              strategy: Dict[str, Any]) -> List[Dict]:
        support_areas = []

        # Simplified implementation - in full version would analyze overhangs
        for polygon in layer.polygons:
            area = self._calculate_polygon_area(polygon.points)
            if area > strategy.get('min_pillar_radius', 5.0) ** 2 * math.pi:
                support_areas.append({
                    'polygon': polygon,
                    'area': area,
                    'start_layer': 0,  # Would be calculated properly
                    'angle': 60.0,     # Would be calculated from overhang analysis
                    'centroid': self._calculate_polygon_centroid(polygon.points)
                })

        return support_areas

    def _create_tree_roots(self, island: SupportIsland) -> List[TreeSupportNode]:
        roots = []

        # Create roots at strategic positions
        num_roots = max(1, int(island.total_area / 100))  # One root per 100mm²

        for i in range(num_roots):
            # Position roots within island bounds
            if island.bounding_box:
                min_x, min_y, max_x, max_y = island.bounding_box
                x = min_x + (max_x - min_x) * (i + 0.5) / num_roots
                y = min_y + (max_y - min_y) * 0.5
            else:
                x, y = island.centroid.x, island.centroid.y

            root = TreeSupportNode(
                position=Point2D(x, y),
                layer=0,
                radius=self.pillar_radius,
                support_type="pillar"
            )
            roots.append(root)

        return roots

    def _create_node_polygon(self, node: TreeSupportNode) -> LayerPolygon:
        # Create circular polygon for node
        points = []
        num_points = 8
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            x = node.position.x + node.radius * math.cos(angle)
            y = node.position.y + node.radius * math.sin(angle)
            points.append(Point2D(x, y))

        return LayerPolygon(points=points, is_hole=False)

    def _calculate_island_connectivity(self, island: SupportIsland) -> float:
        if len(island.regions) < 2:
            return 1.0

        # Calculate average distance between regions
        total_distance = 0.0
        count = 0

        for i, region1 in enumerate(island.regions):
            for j, region2 in enumerate(island.regions[i+1:], i+1):
                distance = self._calculate_distance(region1.centroid, region2.centroid)
                total_distance += distance
                count += 1

        avg_distance = total_distance / count if count > 0 else 0

        # Lower average distance = better connectivity
        connectivity = 1.0 / (1.0 + avg_distance / 20.0)
        return min(1.0, connectivity)

    def _calculate_island_stability(self, island: SupportIsland) -> float:
        # Based on size, shape, and support distribution
        size_factor = min(1.0, island.total_area / 200.0)  # Larger islands are more stable

        # Shape factor (closer to square is better)
        if island.bounding_box:
            width = island.bounding_box[2] - island.bounding_box[0]
            height = island.bounding_box[3] - island.bounding_box[1]
            aspect_ratio = min(width, height) / max(width, height) if max(width, height) > 0 else 1.0
            shape_factor = 1.0 - abs(1.0 - aspect_ratio)
        else:
            shape_factor = 0.5

        return (size_factor + shape_factor) / 2.0

    def _calculate_island_efficiency(self, island: SupportIsland) -> float:
        # Efficiency based on area vs perimeter
        total_perimeter = sum(r.perimeter for r in island.regions)
        if total_perimeter == 0:
            return 1.0

        efficiency = island.total_area / total_perimeter
        return min(1.0, efficiency * 10)  # Normalize

    def _integrate_supports_into_layers(self, layers: List[Layer],
                                      support_regions: List[SupportRegion]) -> List[Layer]:
        # Group supports by layer
        supports_by_layer = defaultdict(list)
        for region in support_regions:
            for layer_idx in range(region.start_layer, region.end_layer):
                if layer_idx < len(layers):
                    supports_by_layer[layer_idx].append(region)

        # Add supports to layers
        for layer_idx, layer in enumerate(layers):
            support_polygons = supports_by_layer.get(layer_idx, [])
            for support in support_polygons:
                layer.support_polygons.append(support.polygon)

        return layers

    def _generate_support_statistics(self, regions: List[SupportRegion], generation_time: float):
        self.generation_stats = {
            'total_regions': len(regions),
            'total_volume': sum(r.material_volume for r in regions),
            'generation_time': generation_time,
            'average_region_area': np.mean([r.area for r in regions]) if regions else 0,
            'max_region_area': max([r.area for r in regions]) if regions else 0,
            'support_types': defaultdict(int)
        }

        for region in regions:
            self.generation_stats['support_types'][region.support_type] += 1

        logger.info(f"Support generation stats: {self.generation_stats}")

    def _apply_adaptive_profiles(self, regions: List[SupportRegion],
                               analysis: Dict[str, Any]) -> List[SupportRegion]:
        # Select appropriate profile
        material_type = getattr(self.settings, 'filament_type', 'PLA')
        profile = self.adaptive_profiles.get(material_type, self.adaptive_profiles['default'])

        # Adjust regions based on profile
        for region in regions:
            # Adjust density
            density_factor = profile.optimal_density / self.settings.support_density
            region.material_volume *= density_factor

            # Adjust interface layers
            if hasattr(region, 'interface_layers'):
                region.interface_layers = profile.interface_layers

        return regions

    # ===== MACHINE LEARNING AND ADAPTATION =====

    def learn_from_print_results(self, print_data: Dict[str, Any]):
        if not self.machine_learning_enabled:
            return

        # Create learning data point
        learning_data = SupportLearningData(
            geometry_features=self._extract_geometry_features(print_data),
            support_parameters=self._extract_support_parameters(),
            performance_metrics=self._extract_performance_metrics(print_data),
            material_usage=print_data.get('material_used', 0),
            print_time=print_data.get('print_time', 0),
            success_score=print_data.get('success_score', 0.5),
            failure_modes=print_data.get('failure_modes', []),
            optimization_opportunities=print_data.get('optimization_opportunities', [])
        )

        self.learning_data.append(learning_data)

        # Update adaptive profiles
        self._update_adaptive_profiles(learning_data)

        logger.info("Learned from print results")

    def _extract_geometry_features(self, print_data: Dict[str, Any]) -> Dict[str, float]:
        return {
            'complexity': print_data.get('geometry_complexity', 0.5),
            'overhang_area': print_data.get('overhang_area', 0),
            'total_volume': print_data.get('total_volume', 0),
            'surface_area': print_data.get('surface_area', 0),
            'bounding_box_volume': print_data.get('bounding_box_volume', 0)
        }

    def _extract_support_parameters(self) -> Dict[str, Union[float, int, str]]:
        return {
            'density': self.settings.support_density,
            'angle': self.settings.support_angle,
            'tree_support': self.tree_support_enabled,
            'interface_layers': self.interface_layers,
            'pattern': self.settings.fill_pattern.value
        }

    def _extract_performance_metrics(self, print_data: Dict[str, Any]) -> Dict[str, float]:
        return {
            'success_rate': print_data.get('success_rate', 1.0),
            'support_removal_difficulty': print_data.get('support_removal_difficulty', 0.5),
            'surface_quality': print_data.get('surface_quality', 0.8),
            'structural_integrity': print_data.get('structural_integrity', 0.9),
            'material_efficiency': print_data.get('material_efficiency', 0.7)
        }

    def _update_adaptive_profiles(self, learning_data: SupportLearningData):
        material_type = getattr(self.settings, 'filament_type', 'PLA')

        if material_type not in self.adaptive_profiles:
            return

        profile = self.adaptive_profiles[material_type]

        # Update profile based on performance
        success_score = learning_data.success_score

        if success_score > 0.8:  # Good performance
            # Reinforce successful parameters
            adaptation_rate = profile.adaptation_rate * 0.95  # Reduce adaptation rate
        else:  # Poor performance
            # Increase adaptation for more learning
            adaptation_rate = profile.adaptation_rate * 1.1

        profile.adaptation_rate = max(0.01, min(0.2, adaptation_rate))

        # Add to performance history
        profile.performance_history.append(learning_data)

        # Limit history size
        max_history = 20
        if len(profile.performance_history) > max_history:
            profile.performance_history = profile.performance_history[-max_history:]

    # ===== LEGACY COMPATIBILITY METHODS =====

    def generate_supports(self, layers: List[Layer]) -> List[Layer]:
        return self.generate_advanced_supports(layers)
        
    def generate_supports(self, layers: List[Layer]) -> List[Layer]:
        if not self.settings.support_material:
            return layers
        
        print(f"Generating supports with type: {self.settings.support_type}")
        
        # Detect overhangs
        overhang_regions = self._detect_overhangs(layers)
        
        if self.settings.support_type == SupportType.TREE:
            return self._generate_tree_supports(layers, overhang_regions)
        else:
            return self._generate_normal_supports(layers, overhang_regions)
    
    def _detect_overhangs(self, layers: List[Layer]) -> Dict[int, List[LayerPolygon]]:
        overhang_regions = {}
        
        for i in range(1, len(layers)):
            current_layer = layers[i]
            previous_layer = layers[i - 1]
            
            overhangs = []
            
            for current_polygon in current_layer.polygons:
                overhang_areas = self._find_overhang_areas(
                    current_polygon, 
                    previous_layer.polygons
                )
                overhangs.extend(overhang_areas)
            
            if overhangs:
                overhang_regions[i] = overhangs
        
        return overhang_regions
    
    def _find_overhang_areas(self, current_polygon: LayerPolygon, 
                           previous_polygons: List[LayerPolygon]) -> List[LayerPolygon]:
        overhang_areas = []
        
        # Simplified overhang detection
        # In production, this would use proper polygon boolean operations
        
        # Check if current polygon extends beyond previous polygons
        unsupported_areas = self._subtract_polygons(current_polygon, previous_polygons)
        
        # Filter by overhang angle (simplified)
        for area in unsupported_areas:
            if self._needs_support(area, previous_polygons):
                overhang_areas.append(area)
        
        return overhang_areas
    
    def _subtract_polygons(self, polygon: LayerPolygon, 
                          subtract_polygons: List[LayerPolygon]) -> List[LayerPolygon]:
        # Simplified polygon subtraction
        # Production version would use proper boolean operations library like Clipper
        
        if not subtract_polygons:
            return [polygon]
        
        # For now, return areas that don't overlap significantly
        result = []
        
        # Simple approach: check if polygon points are supported
        unsupported_points = []
        
        for point in polygon.points:
            supported = False
            for support_polygon in subtract_polygons:
                if self._point_in_polygon_with_offset(point, support_polygon, 0.1):
                    supported = True
                    break
            
            if not supported:
                unsupported_points.append(point)
        
        # Create overhang polygon from unsupported points
        if len(unsupported_points) >= 3:
            overhang_polygon = LayerPolygon(points=unsupported_points)
            result.append(overhang_polygon)
        
        return result
    
    def _point_in_polygon_with_offset(self, point: Point2D, polygon: LayerPolygon, 
                                    offset: float) -> bool:
        # Create slightly larger polygon for offset check
        offset_polygon = self._offset_polygon(polygon, offset)
        if offset_polygon:
            return self._point_in_polygon(point, offset_polygon)
        return self._point_in_polygon(point, polygon)
    
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
    
    def _offset_polygon(self, polygon: LayerPolygon, distance: float) -> Optional[LayerPolygon]:
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
            
            # Normalize
            v1_len = math.sqrt(v1.x**2 + v1.y**2)
            v2_len = math.sqrt(v2.x**2 + v2.y**2)
            
            if v1_len > 0:
                v1.x /= v1_len
                v1.y /= v1_len
            if v2_len > 0:
                v2.x /= v2_len
                v2.y /= v2_len
            
            # Calculate normals
            n1 = Point2D(-v1.y, v1.x)
            n2 = Point2D(-v2.y, v2.x)
            
            # Average normal
            avg_normal = Point2D((n1.x + n2.x) / 2, (n1.y + n2.y) / 2)
            normal_len = math.sqrt(avg_normal.x**2 + avg_normal.y**2)
            
            if normal_len > 0:
                avg_normal.x /= normal_len
                avg_normal.y /= normal_len
            
            # Create offset point
            offset_point = Point2D(
                p2.x + avg_normal.x * distance,
                p2.y + avg_normal.y * distance
            )
            offset_points.append(offset_point)
        
        return LayerPolygon(points=offset_points) if offset_points else None
    
    def _needs_support(self, polygon: LayerPolygon, 
                      previous_polygons: List[LayerPolygon]) -> bool:
        # Check minimum area threshold
        min_support_area = 1.0  # mm²
        if polygon.area() < min_support_area:
            return False
        
        # For simplified implementation, assume it needs support if it's an overhang
        return True
    
    def _generate_normal_supports(self, layers: List[Layer], 
                                overhang_regions: Dict[int, List[LayerPolygon]]) -> List[Layer]:
        print("Generating normal support pillars...")
        
        # Create support regions that span from bed/supported layer to overhang
        support_regions = self._create_support_regions(layers, overhang_regions)
        
        # Generate support polygons for each layer
        for layer_idx, layer in enumerate(layers):
            support_polygons = self._generate_support_polygons_for_layer(
                layer_idx, support_regions
            )
            
            for support_polygon in support_polygons:
                layer.add_support_polygon(support_polygon)
        
        return layers
    
    def _create_support_regions(self, layers: List[Layer], 
                              overhang_regions: Dict[int, List[LayerPolygon]]) -> List[SupportRegion]:
        support_regions = []
        
        for layer_idx, overhangs in overhang_regions.items():
            for overhang in overhangs:
                # Find where support should start
                start_layer = self._find_support_start_layer(
                    layers, layer_idx, overhang
                )
                
                # Create support region
                support_region = SupportRegion(
                    polygon=overhang,
                    start_layer=start_layer,
                    end_layer=layer_idx - 1,  # Support up to layer before overhang
                    support_type="normal"
                )
                
                support_regions.append(support_region)
        
        return support_regions
    
    def _find_support_start_layer(self, layers: List[Layer], 
                                 overhang_layer: int, 
                                 overhang_polygon: LayerPolygon) -> int:
        if self.settings.support_type == SupportType.BUILD_PLATE_ONLY:
            return 0
        
        # For "everywhere" support, start from the last layer that can support
        for layer_idx in range(overhang_layer - 1, -1, -1):
            layer = layers[layer_idx]
            
            # Check if this layer can support the overhang
            if self._can_layer_support_overhang(layer, overhang_polygon):
                return layer_idx + 1
        
        return 0  # Fall back to build plate
    
    def _can_layer_support_overhang(self, layer: Layer, 
                                   overhang_polygon: LayerPolygon) -> bool:
        # Check if layer polygons overlap sufficiently with overhang
        min_overlap = 0.7  # 70% overlap required
        
        overhang_area = overhang_polygon.area()
        if overhang_area <= 0:
            return False
        
        supported_area = 0.0
        
        for polygon in layer.polygons:
            # Calculate overlap area (simplified)
            overlap = self._calculate_polygon_overlap(overhang_polygon, polygon)
            supported_area += overlap
        
        overlap_ratio = supported_area / overhang_area
        return overlap_ratio >= min_overlap
    
    def _calculate_polygon_perimeter(self, polygon: LayerPolygon) -> float:
        if len(polygon.points) < 2:
            return 0.0
        
        perimeter = 0.0
        n = len(polygon.points)
        
        for i in range(n):
            p1 = polygon.points[i]
            p2 = polygon.points[(i + 1) % n]
            perimeter += p1.distance(p2)
        
        return perimeter
    
    def _calculate_polygon_centroid(self, polygon: LayerPolygon) -> Point2D:
        if not polygon.points:
            return Point2D(0, 0)
        
        cx = sum(p.x for p in polygon.points) / len(polygon.points)
        cy = sum(p.y for p in polygon.points) / len(polygon.points)
        
        return Point2D(cx, cy)
    
    def _sample_polygon_perimeter(self, polygon: LayerPolygon, num_points: int) -> List[Point2D]:
        if len(polygon.points) < 2:
            return []
        
        points = []
        perimeter = self._calculate_polygon_perimeter(polygon)
        
        if perimeter <= 0:
            return []
        
        target_spacing = perimeter / num_points
        current_distance = 0.0
        current_segment = 0
        
        n = len(polygon.points)
        
        while len(points) < num_points and current_segment < n:
            p1 = polygon.points[current_segment]
            p2 = polygon.points[(current_segment + 1) % n]
            
            segment_length = p1.distance(p2)
            
            if current_distance + segment_length >= target_spacing:
                # Interpolate point on current segment
                remaining_distance = target_spacing - current_distance
                t = remaining_distance / segment_length if segment_length > 0 else 0
                
                interpolated_point = Point2D(
                    p1.x + t * (p2.x - p1.x),
                    p1.y + t * (p2.y - p1.y)
                )
                
                points.append(interpolated_point)
                current_distance = 0.0
            else:
                current_distance += segment_length
                current_segment += 1
        
        return points
    
    def _create_support_trees(self, support_points: List[Tuple[Point2D, int]], 
                            layers: List[Layer]) -> List[SupportColumn]:
        support_trees = []
        
        for support_point, layer_idx in support_points:
            # Find path to build plate or supported layer
            path = self._find_support_path(support_point, layer_idx, layers)
            
            if path:
                # Create support column
                column = SupportColumn(
                    base_point=path[-1],  # Bottom point
                    top_point=path[0],    # Top point
                    radius=1.0,  # Initial radius
                    start_layer=0,
                    end_layer=layer_idx,
                    branches=[]
                )
                
                # Add branches for path segments
                for i in range(len(path) - 1):
                    branch = SupportBranch(
                        start_point=path[i],
                        end_point=path[i + 1],
                        start_layer=int(layers[i].z_height / self.settings.layer_height) if i < len(layers) else 0,
                        end_layer=int(layers[i + 1].z_height / self.settings.layer_height) if i + 1 < len(layers) else layer_idx,
                        radius=max(0.5, 1.0 - i * 0.1)  # Tapering radius
                    )
                    column.branches.append(branch)
                
                support_trees.append(column)
        
        return support_trees
    
    def _find_support_path(self, start_point: Point2D, start_layer: int, 
                          layers: List[Layer]) -> List[Point2D]:
        path = [start_point]
        current_point = start_point
        
        # Simple path finding - move down with slight randomization
        for layer_idx in range(start_layer - 1, -1, -1):
            if layer_idx >= len(layers):
                continue
            
            layer = layers[layer_idx]
            
            # Try to move straight down
            next_point = Point2D(current_point.x, current_point.y)
            
            # Check for collisions and adjust path
            if self._point_collides_with_layer(next_point, layer):
                # Find alternative path around obstacles
                next_point = self._find_alternative_path_point(
                    current_point, layer, 2.0  # 2mm search radius
                )
            
            path.append(next_point)
            current_point = next_point
        
        return path
    
    def _point_collides_with_layer(self, point: Point2D, layer: Layer) -> bool:
        collision_radius = 1.0  # mm
        
        for polygon in layer.polygons:
            for poly_point in polygon.points:
                if point.distance(poly_point) < collision_radius:
                    return True
        
        return False
    
    def _find_alternative_path_point(self, current_point: Point2D, 
                                   layer: Layer, search_radius: float) -> Point2D:
        # Try points in a circle around current point
        num_attempts = 8
        
        for i in range(num_attempts):
            angle = 2 * math.pi * i / num_attempts
            test_point = Point2D(
                current_point.x + search_radius * math.cos(angle),
                current_point.y + search_radius * math.sin(angle)
            )
            
            if not self._point_collides_with_layer(test_point, layer):
                return test_point
        
        # If no alternative found, return original point
        return current_point
    
    def _generate_tree_polygons_for_layer(self, layer_idx: int, 
                                        support_trees: List[SupportColumn]) -> List[LayerPolygon]:
        tree_polygons = []
        
        for tree in support_trees:
            if tree.start_layer <= layer_idx <= tree.end_layer:
                # Generate polygon for tree trunk/branches at this layer
                tree_polygon = self._create_tree_polygon_at_layer(tree, layer_idx)
                if tree_polygon:
                    tree_polygons.append(tree_polygon)
        
        return tree_polygons
    
    def _create_tree_polygon_at_layer(self, tree: SupportColumn, 
                                    layer_idx: int) -> Optional[LayerPolygon]:
        
        # Find relevant branches for this layer
        active_branches = []
        
        for branch in tree.branches:
            if branch.start_layer <= layer_idx <= branch.end_layer:
                active_branches.append(branch)
        
        if not active_branches:
            # No active branches, create trunk polygon
            center_point = self._interpolate_tree_position(tree, layer_idx)
            radius = self._calculate_tree_radius_at_layer(tree, layer_idx)
            return self._create_circular_polygon(center_point, radius, 8)
        
        # Create polygon encompassing all active branches
        all_points = []
        
        for branch in active_branches:
            branch_center = self._interpolate_branch_position(branch, layer_idx)
            branch_radius = branch.radius
            
            # Create circular points around branch
            circle_points = self._create_circular_points(branch_center, branch_radius, 6)
            all_points.extend(circle_points)
        
        if len(all_points) >= 3:
            # Create convex hull of all branch points (simplified)
            hull_points = self._convex_hull(all_points)
            return LayerPolygon(points=hull_points)
        
        return None
    
    def _interpolate_tree_position(self, tree: SupportColumn, layer_idx: int) -> Point2D:
        if layer_idx <= tree.start_layer:
            return tree.base_point
        elif layer_idx >= tree.end_layer:
            return tree.top_point
        else:
            # Linear interpolation
            t = (layer_idx - tree.start_layer) / (tree.end_layer - tree.start_layer)
            return Point2D(
                tree.base_point.x + t * (tree.top_point.x - tree.base_point.x),
                tree.base_point.y + t * (tree.top_point.y - tree.base_point.y)
            )
    
    def _calculate_tree_radius_at_layer(self, tree: SupportColumn, layer_idx: int) -> float:
        base_radius = tree.radius
        
        # Taper from base to top
        if tree.end_layer <= tree.start_layer:
            return base_radius
        
        t = (layer_idx - tree.start_layer) / (tree.end_layer - tree.start_layer)
        min_radius = 0.5
        
        return base_radius * (1 - t) + min_radius * t
    
    def _interpolate_branch_position(self, branch: SupportBranch, layer_idx: int) -> Point2D:
        if layer_idx <= branch.start_layer:
            return branch.start_point
        elif layer_idx >= branch.end_layer:
            return branch.end_point
        else:
            t = (layer_idx - branch.start_layer) / (branch.end_layer - branch.start_layer)
            return Point2D(
                branch.start_point.x + t * (branch.end_point.x - branch.start_point.x),
                branch.start_point.y + t * (branch.end_point.y - branch.start_point.y)
            )
    
    def _create_circular_polygon(self, center: Point2D, radius: float, 
                               num_points: int) -> LayerPolygon:
        points = self._create_circular_points(center, radius, num_points)
        return LayerPolygon(points=points)
    
    def _create_circular_points(self, center: Point2D, radius: float, 
                              num_points: int) -> List[Point2D]:
        points = []
        
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            x = center.x + radius * math.cos(angle)
            y = center.y + radius * math.sin(angle)
            points.append(Point2D(x, y))
        
        return points
    
    def _convex_hull(self, points: List[Point2D]) -> List[Point2D]:
        if len(points) < 3:
            return points
        
        # Sort points lexicographically
        sorted_points = sorted(points, key=lambda p: (p.x, p.y))
        
        # Build lower hull
        lower = []
        for p in sorted_points:
            while len(lower) >= 2 and self._cross_product(lower[-2], lower[-1], p) <= 0:
                lower.pop()
            lower.append(p)
        
        # Build upper hull
        upper = []
        for p in reversed(sorted_points):
            while len(upper) >= 2 and self._cross_product(upper[-2], upper[-1], p) <= 0:
                upper.pop()
            upper.append(p)
        
        # Remove last point of each half because it's repeated
        return lower[:-1] + upper[:-1]
    
    def _cross_product(self, o: Point2D, a: Point2D, b: Point2D) -> float:
        return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x)

# Example usage
if __name__ == "__main__":
    from .slicer_core import PrintSettings, Layer, LayerPolygon, Point2D, SupportType
    
    # Create test settings
    settings = PrintSettings(
        support_material=True,
        support_type=SupportType.TREE,
        support_angle=45.0,
        support_interface_layers=3
    )
    
    # Create test layers with overhang
    layers = []
    
    # Layer 0 - base
    layer0 = Layer(z_height=0.2)
    base_polygon = LayerPolygon(points=[
        Point2D(0, 0), Point2D(10, 0), Point2D(10, 5), Point2D(0, 5)
    ])
    layer0.add_polygon(base_polygon)
    layers.append(layer0)
    
    # Layer 1 - overhang
    layer1 = Layer(z_height=0.4)
    overhang_polygon = LayerPolygon(points=[
        Point2D(0, 0), Point2D(15, 0), Point2D(15, 5), Point2D(0, 5)  # Extends 5mm
    ])
    layer1.add_polygon(overhang_polygon)
    layers.append(layer1)
    
    # Generate supports
    generator = SupportGenerator(settings)
    layers_with_support = generator.generate_supports(layers)
    
    # Print results
    for i, layer in enumerate(layers_with_support):
        support_count = len(layer.support_polygons)
        print(f"Layer {i}: {support_count} support polygons")
        
        for j, support in enumerate(layer.support_polygons):
            area = support.area()
            print(f"  Support {j}: {area:.2f} mm² area")

    def _polygon_overlap(self, poly1: LayerPolygon, 
                         poly2: LayerPolygon) -> float:
        # Simplified overlap calculation
        # Production version would use proper polygon intersection
        
        overlap_points = []
        
        # Check which points of poly1 are inside poly2
        for point in poly1.points:
            if self._point_in_polygon(point, poly2):
                overlap_points.append(point)
        
        # Check which points of poly2 are inside poly1
        for point in poly2.points:
            if self._point_in_polygon(point, poly1):
                overlap_points.append(point)
        
        if len(overlap_points) >= 3:
            overlap_polygon = LayerPolygon(points=overlap_points)
            return overlap_polygon.area()
        
        return 0.0
    
    def _generate_support_polygons_for_layer(self, layer_idx: int, 
                                           support_regions: List[SupportRegion]) -> List[LayerPolygon]:
        support_polygons = []
        
        for region in support_regions:
            if region.start_layer <= layer_idx <= region.end_layer:
                # Create support polygon for this layer
                support_polygon = self._create_support_polygon(
                    region.polygon, layer_idx, region
                )
                
                if support_polygon:
                    support_polygons.append(support_polygon)
        
        return support_polygons
    
    def _create_support_polygon(self, base_polygon: LayerPolygon, 
                              layer_idx: int, 
                              region: SupportRegion) -> Optional[LayerPolygon]:
        
        # Apply XY distance offset
        support_polygon = self._offset_polygon(base_polygon, -self.support_xy_distance)
        
        if not support_polygon or support_polygon.area() < 0.1:
            return None
        
        # Check if this should be interface layer
        layers_from_top = region.end_layer - layer_idx
        if layers_from_top < self.interface_layers:
            # Interface layer - denser support
            return self._create_interface_support_polygon(support_polygon)
        else:
            # Normal support layer
            return self._create_normal_support_polygon(support_polygon)
    
    def _create_interface_support_polygon(self, polygon: LayerPolygon) -> LayerPolygon:
        # Interface support is typically solid or very dense
        # For now, return the polygon as-is
        return polygon
    
    def _create_normal_support_polygon(self, polygon: LayerPolygon) -> LayerPolygon:
        # Normal support uses sparse infill pattern
        # For simplified implementation, return offset polygon
        return polygon
    
    def _generate_tree_supports(self, layers: List[Layer], 
                              overhang_regions: Dict[int, List[LayerPolygon]]) -> List[Layer]:
        print("Generating tree supports...")
        
        # Generate support points
        support_points = self._generate_support_points(overhang_regions)
        
        # Create tree structure
        support_trees = self._create_support_trees(support_points, layers)
        
        # Generate support polygons from trees
        for layer_idx, layer in enumerate(layers):
            tree_polygons = self._generate_tree_polygons_for_layer(
                layer_idx, support_trees
            )
            
            for tree_polygon in tree_polygons:
                layer.add_support_polygon(tree_polygon)
        
        return layers
    
    def _generate_support_points(self, overhang_regions: Dict[int, List[LayerPolygon]]) -> List[Tuple[Point2D, int]]:
        support_points = []
        
        for layer_idx, overhangs in overhang_regions.items():
            for overhang in overhangs:
                # Generate points around overhang perimeter
                points = self._generate_perimeter_support_points(overhang, layer_idx)
                support_points.extend(points)
        
        return support_points
    
    def _generate_perimeter_support_points(self, polygon: LayerPolygon, 
                                         layer_idx: int) -> List[Tuple[Point2D, int]]:
        points = []
        support_spacing = 3.0  # mm between support points
        
        perimeter = self._calculate_polygon_perimeter(polygon)
        num_points = max(1, int(perimeter / support_spacing))
        
        if num_points == 1:
            # Single support point at centroid
            centroid = self._calculate_polygon_centroid(polygon)
            points.append((centroid, layer_idx))
        else:
            # Multiple points around perimeter
            perimeter_points = self._sample_polygon_perimeter(polygon, num_points)
            for point in perimeter_points:
                points.append((point, layer_idx))

        return points

# ===== ADVANCED MACHINE LEARNING SUPPORT OPTIMIZATION =====

class SupportMachineLearningOptimizer:

    def __init__(self):
        self.models = {}
        self.training_data = []
        self.support_patterns = defaultdict(list)

    def optimize_support_placement(self, overhang_regions: Dict[int, List[LayerPolygon]],
                                 print_settings: PrintSettings) -> Dict[str, Any]:

        features = self._extract_support_features(overhang_regions, print_settings)

        if not self.models:
            # Fallback to rule-based optimization
            return self._rule_based_support_optimization(overhang_regions, print_settings)

        # ML prediction would go here
        optimization = self._rule_based_support_optimization(overhang_regions, print_settings)

        return optimization

    def _extract_support_features(self, overhang_regions: Dict[int, List[LayerPolygon]],
                                print_settings: PrintSettings) -> Dict[str, float]:

        total_overhang_area = 0
        max_overhang_height = 0
        avg_overhang_angle = 0
        total_overhangs = 0

        for layer_idx, overhangs in overhang_regions.items():
            max_overhang_height = max(max_overhang_height, layer_idx)

            for overhang in overhangs:
                area = overhang.area()
                total_overhang_area += area
                total_overhangs += 1

                # Estimate overhang angle (simplified)
                angle = self._estimate_overhang_angle(overhang)
                avg_overhang_angle += angle

        if total_overhangs > 0:
            avg_overhang_angle /= total_overhangs

        return {
            'total_overhang_area': total_overhang_area,
            'max_overhang_height': max_overhang_height,
            'avg_overhang_angle': avg_overhang_angle,
            'total_overhangs': total_overhangs,
            'layer_height': print_settings.layer_height,
            'nozzle_diameter': print_settings.nozzle_diameter,
            'support_density': print_settings.support_density
        }

    def _estimate_overhang_angle(self, polygon: LayerPolygon) -> float:
        # Simplified: assume 45 degrees for now
        # Real implementation would analyze previous layers
        return 45.0

    def _rule_based_support_optimization(self, overhang_regions: Dict[int, List[LayerPolygon]],
                                       print_settings: PrintSettings) -> Dict[str, Any]:

        recommendations = []

        # Analyze overhang characteristics
        features = self._extract_support_features(overhang_regions, print_settings)

        if features['total_overhang_area'] > 1000:  # Large overhang area
            recommendations.append("Consider using tree supports for better material efficiency")
        elif features['max_overhang_height'] > 20:  # Tall supports
            recommendations.append("Consider increasing support density for stability")
        elif features['avg_overhang_angle'] < 30:  # Steep overhangs
            recommendations.append("Use denser support pattern for steep overhangs")

        return {
            'support_type': SupportType.TREE if features['total_overhang_area'] > 500 else SupportType.BUILD_PLATE_ONLY,
            'density': min(0.3, features['total_overhang_area'] / 2000),
            'pattern': SupportPattern.HONEYCOMB,
            'recommendations': recommendations
        }

# ===== DEMONSTRATION =====

def demonstrate_advanced_support_generation():

    print("=== Advanced Support Generation Demonstration ===")

    # Create sample overhang regions
    overhang_regions = {
        10: [LayerPolygon(points=[
            Point2D(10, 10), Point2D(20, 10), Point2D(20, 20), Point2D(10, 20)
        ])],
        15: [LayerPolygon(points=[
            Point2D(30, 30), Point2D(40, 30), Point2D(40, 40), Point2D(30, 40)
        ])]
    }

    # Create sample layers
    layers = []
    for i in range(20):
        layer = Layer(z_height=i * 0.2)
        layers.append(layer)

    # Print settings
    from .slicer_core import PrintSettings
    settings = PrintSettings(support_material=True, support_type=SupportType.TREE)

    # Advanced support generation
    coordinator = AdvancedSupportGenerationCoordinator({})
    result = coordinator.generate_advanced_supports(layers, overhang_regions, settings)

    print(f"Generated supports for {len(layers)} layers")
    print(f"Analysis: {result['analysis']['basic_metrics']}")
    print(f"ML Optimization: {result['ml_optimization']}")

if __name__ == "__main__":
    demonstrate_advanced_support_generation()
    