#!/usr/bin/env python3
# ------------------------------------------------------------------
# Copyright (c) 2026 Sleia Engine Development Team.
# This file is distributed under the MIT License. See LICENSE.
#
# Sleia Easy v 1.0.1 - Thermoplastic Python Slicer
#
# File: main_slicer.py
# Description: wires the engine pieces into one slice job.
# ------------------------------------------------------------------

import json
import time
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import asdict

try:
    from .slicer_core import SlicerCore, PrintSettings, InfillPattern, SupportType
    from .mesh_processor import MeshProcessor, Mesh
    from .infill_generator import InfillGenerator
    from .support_generator import AdvancedSupportGenerator as SupportGenerator
    from .perimeter_generator import PerimeterGenerator
    from .gcode_generator import GCodeGenerator
except ImportError:
    from slicer_core import SlicerCore, PrintSettings, InfillPattern, SupportType
    from mesh_processor import MeshProcessor, Mesh
    from infill_generator import InfillGenerator
    from support_generator import AdvancedSupportGenerator as SupportGenerator
    from perimeter_generator import PerimeterGenerator
    from gcode_generator import GCodeGenerator

try:
    from .adaptive_layer_height import AdaptiveLayerHeightController, AdaptiveSettings, AdaptiveMode, QualityLevel
except ImportError:
    try:
        from adaptive_layer_height import AdaptiveLayerHeightController, AdaptiveSettings, AdaptiveMode, QualityLevel
    except ImportError:
        AdaptiveLayerHeightController = None
        AdaptiveSettings = None
        AdaptiveMode = None
        QualityLevel = None

logger = logging.getLogger(__name__)


class SlicerAPI:

    def __init__(self, settings: PrintSettings = None):
        self.settings = settings or PrintSettings()
        self.mesh: Optional[Mesh] = None
        self.sliced_model = None
        self.slicer_core = SlicerCore(self.settings)
        self.mesh_processor = MeshProcessor()
        self.infill_generator = InfillGenerator(self.settings)
        self.support_generator = SupportGenerator(self.settings)
        self.perimeter_generator = PerimeterGenerator(self.settings)
        self.gcode_generator = GCodeGenerator(self.settings)
        self.adaptive_controller = self._create_adaptive_controller()
        logger.info("Basic slicer initialized")

    def _create_adaptive_controller(self):
        if AdaptiveLayerHeightController is None or not self.settings.adaptive_layer_height_enabled:
            return None
        quality_map = {
            "draft": QualityLevel.DRAFT,
            "standard": QualityLevel.STANDARD,
            "fine": QualityLevel.FINE,
            "ultra_fine": QualityLevel.ULTRA_FINE,
        }
        quality_level = quality_map.get(self.settings.adaptive_quality_level, QualityLevel.STANDARD)
        return AdaptiveLayerHeightController(AdaptiveSettings(
            mode=AdaptiveMode.AUTO,
            min_layer_height=self.settings.adaptive_min_layer_height,
            max_layer_height=self.settings.adaptive_max_layer_height,
            base_layer_height=self.settings.adaptive_base_layer_height,
            quality_level=quality_level,
            curvature_threshold=self.settings.adaptive_curvature_threshold,
            smoothing_iterations=self.settings.adaptive_smoothing_iterations,
        ))

    def load_model(self, file_path: str, auto_repair: bool = True,
                   center_model: bool = True, place_on_bed: bool = True,
                   auto_orient: bool = True) -> Dict[str, Any]:
        logger.info(f"Loading model: {file_path}")
        try:
            self.mesh = self.mesh_processor.load_mesh(file_path)
            issues = self.mesh_processor.validate_mesh_for_printing(self.mesh)
            if auto_repair and issues:
                self.mesh = self.mesh_processor.repair_mesh(self.mesh)
                issues = self.mesh_processor.validate_mesh_for_printing(self.mesh)
            from .auto_orient import auto_orient_and_place, place_on_baseplate
            bed = getattr(self.settings, "bed_size", (220.0, 220.0))
            center = getattr(self.settings, "print_center", (bed[0] / 2.0, bed[1] / 2.0))
            if auto_orient:
                self.mesh = auto_orient_and_place(self.mesh, bed, center)
            else:
                if center_model or place_on_bed:
                    self.mesh = place_on_baseplate(self.mesh, bed, center)
            return {
                "success": True,
                "mesh_info": self.mesh_processor.get_mesh_info(self.mesh),
                "issues": issues,
                "auto_repaired": auto_repair and len(issues) > 0,
                "auto_oriented": bool(auto_orient),
            }
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return {"success": False, "error": str(e)}

    def slice_model(self, progress_callback=None) -> Dict[str, Any]:
        if self.mesh is None:
            return {"success": False, "error": "No model loaded"}
        logger.info("Starting model slicing...")
        start_time = time.time()
        try:
            self.sliced_model = self.slicer_core.slice_model(
                self.mesh.vertices,
                self.mesh.faces,
                use_adaptive=bool(self.settings.adaptive_layer_height_enabled),
                use_parallel=False,
                optimize_quality=False,
            )
            if progress_callback:
                progress_callback(50, "Slicing complete")
            if self.settings.support_material:
                self.sliced_model.layers = self.support_generator.generate_supports(
                    self.sliced_model.layers
                )
            if progress_callback:
                progress_callback(100, "Slicing complete")
            return {
                "success": True,
                "statistics": {
                    "layer_count": self.sliced_model.get_layer_count(),
                    "slice_time": time.time() - start_time,
                    "estimated_print_time": self.sliced_model.get_print_time_estimate(),
                    "estimated_material_usage": self.sliced_model.get_material_usage(),
                },
            }
        except Exception as e:
            logger.error(f"Slicing failed: {e}")
            return {"success": False, "error": str(e)}

    def generate_gcode(self, output_file: str = None, progress_callback=None) -> Dict[str, Any]:
        if self.sliced_model is None:
            return {"success": False, "error": "No sliced model available"}
        logger.info("Generating G-code...")
        start_time = time.time()
        try:
            gcode_content = self.gcode_generator.generate_gcode(self.sliced_model, output_file)
            result = {
                "success": True,
                "gcode_length": len(gcode_content),
                "line_count": len(gcode_content.splitlines()),
                "generation_time": time.time() - start_time,
                "statistics": self.gcode_generator.get_statistics(),
            }
            if output_file:
                result["output_file"] = output_file
            else:
                result["gcode_content"] = gcode_content
            return result
        except Exception as e:
            logger.error(f"G-code generation failed: {e}")
            return {"success": False, "error": str(e)}

    def slice_and_generate(self, input_file: str, output_file: str = None,
                          progress_callback=None) -> Dict[str, Any]:
        load_result = self.load_model(input_file)
        if not load_result["success"]:
            return load_result
        slice_result = self.slice_model(progress_callback)
        if not slice_result["success"]:
            return slice_result
        if output_file is None:
            output_file = str(Path(input_file).with_suffix(".gcode"))
        gcode_result = self.generate_gcode(output_file, progress_callback)
        if not gcode_result["success"]:
            return gcode_result
        return {
            "success": True,
            "input_file": input_file,
            "output_file": output_file,
            "model_info": load_result["mesh_info"],
            "slice_statistics": slice_result["statistics"],
            "gcode_statistics": gcode_result["statistics"],
        }

    def _serialize_settings(self) -> Dict[str, Any]:
        settings_dict = asdict(self.settings)
        if "fill_pattern" in settings_dict:
            settings_dict["fill_pattern"] = settings_dict["fill_pattern"].value
        if "support_type" in settings_dict:
            settings_dict["support_type"] = settings_dict["support_type"].value
        return settings_dict
