# ------------------------------------------------------------------
# Copyright (c) 2026 Sleia Engine Development Team.
# This file is distributed under the MIT License. See LICENSE.
#
# Sleia Easy v 1.0.1 - Thermoplastic Python Slicer
#
# File: settings.py
# Description: Basic-tab print settings.
# ------------------------------------------------------------------

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional

from engine.slicer_core import InfillPattern, PrintSettings, SupportType
from app.presets import get_baseplate, get_material


INFILL_PATTERN_MAP = {
    "rectilinear": InfillPattern.RECTILINEAR,
    "concentric": InfillPattern.CONCENTRIC,
    "grid": InfillPattern.GRID,
    "line": InfillPattern.LINE,
    "cubic": InfillPattern.CUBIC,
    "triangles": InfillPattern.TRIANGULAR,
    "triangular": InfillPattern.TRIANGULAR,
    "tri-hexagon": InfillPattern.TRI_HEXAGON,
    "tri_hexagon": InfillPattern.TRI_HEXAGON,
    "gyroid": InfillPattern.GYROID,
    "honeycomb": InfillPattern.HONEYCOMB,
    "adaptive-cubic": InfillPattern.ADAPTIVE_CUBIC,
    "adaptive_cubic": InfillPattern.ADAPTIVE_CUBIC,
    "aligned-rectilinear": InfillPattern.ALIGNED_RECTILINEAR,
    "aligned_rectilinear": InfillPattern.ALIGNED_RECTILINEAR,
    "3d-honeycomb": InfillPattern.HONEYCOMB_3D,
    "honeycomb_3d": InfillPattern.HONEYCOMB_3D,
    "hilbert-curve": InfillPattern.HILBERT_CURVE,
    "hilbert_curve": InfillPattern.HILBERT_CURVE,
    "archimedean-chords": InfillPattern.ARCHIMEDEAN_CHORDS,
    "archimedean_chords": InfillPattern.ARCHIMEDEAN_CHORDS,
    "octagram-spiral": InfillPattern.OCTAGRAM_SPIRAL,
    "octagram_spiral": InfillPattern.OCTAGRAM_SPIRAL,
    "support-cubic": InfillPattern.SUPPORT_CUBIC,
    "support_cubic": InfillPattern.SUPPORT_CUBIC,
    "cross-hatch": InfillPattern.CROSS_HATCH,
    "cross_hatch": InfillPattern.CROSS_HATCH,
    "cross infill": InfillPattern.CROSS,
}

TREE_SUPPORT_VALUES = {"tree", "tree-auto", "tree-manual", "tree_auto", "tree_manual"}
NONE_SUPPORT_VALUES = {"none", "off", "disabled"}
NORMAL_SUPPORT_VALUES = {"normal", "normal-auto", "everywhere", "normal_auto"}


@dataclass
class BasicThermoSettings:

    # Layers
    layer_height: float = 0.2
    first_layer_height: float = 0.3
    adaptive_height: bool = False
    max_variation: float = 0.1
    seam_position: str = "aligned"
    staggered_inner_seams: bool = False
    seam_gap: float = 0.0
    wipe_on_loops: bool = False
    wipe_speed: float = 80.0
    wipe_distance: float = 0.0
    enable_ironing: bool = True
    ironing_surface: str = "top"
    ironing_speed: float = 20.0
    ironing_flow: float = 10.0

    # Infill / walls
    wall_loops: int = 2
    order_of_walls: str = "inner-outer"
    detect_thin_walls: bool = False
    top_surface_pattern: str = "concentric"
    top_shell_layers: int = 3
    top_shell_thickness: float = 0.60
    bottom_surface_pattern: str = "rectilinear"
    bottom_shell_layers: int = 3
    bottom_shell_thickness: float = 0.60
    infill_density: float = 20.0
    infill_pattern: str = "rectilinear"

    # Support
    support_enabled: bool = False
    support_type: str = "normal-auto"
    threshold_angle: float = 40.0
    on_build_plate_only: bool = False
    support_infill_pattern: str = "rectilinear"
    support_density: float = 15.0
    remove_small_overhangs: bool = False

    # Motion
    print_speed: float = 50.0
    travel_speed: float = 120.0
    first_layer_speed: float = 30.0
    fan_speed: float = 100.0
    min_layer_time: float = 10.0
    retraction_distance: float = 2.0
    retraction_speed: float = 40.0
    adhesion_type: str = "skirt"
    skirt_loops: int = 2
    skirt_height: int = 1
    skirt_distance: float = 2.0
    brim_width: float = 5.0
    brim_object_gap: float = 0.15
    raft_layers: int = 3
    raft_margin: float = 3.0
    timelapse: str = "off"
    timelapse_interval_s: float = 10.0
    start_gcode: str = ""
    end_gcode: str = ""
    before_layer_change_gcode: str = ""
    layer_change_gcode: str = ""
    tool_change_gcode: str = ""
    brim_type: str = "outer-only"

    # Hidden filament/printer defaults (Basic tab keeps these off-screen)
    filament_type: str = "PLA"
    filament_softening_temp: float = 60.0
    nozzle_temp_min: float = 190.0
    nozzle_temp_max: float = 230.0
    chamber_temp_min: float = 0.0
    chamber_temp: float = 0.0
    first_layer_nozzle_temp: float = 205.0
    bed_smooth_first: float = 60.0
    bed_smooth_other: float = 60.0
    bed_textured_first: float = 60.0
    bed_textured_other: float = 60.0
    bed_engineering_first: float = 90.0
    bed_engineering_other: float = 90.0
    bed_cool_first: float = 0.0
    bed_cool_other: float = 0.0
    nozzle_temp: float = 200.0
    bed_temp: float = 60.0
    nozzle_diameter: float = 0.4
    filament_diameter: float = 1.75
    filament_density: float = 1.24
    default_line_width: float = 0.42
    first_layer_line_width: float = 0.50
    outer_wall_line_width: float = 0.42
    inner_wall_line_width: float = 0.45
    sparse_infill_line_width: float = 0.45
    support_line_width: float = 0.40
    bed_size: tuple = (220.0, 220.0)
    printable_height: float = 250.0
    bed_origin: str = "corner"
    gcode_flavor: str = "marlin-legacy"
    use_relative_e_distances: bool = False
    use_firmware_retraction: bool = False
    printer_name: str = ""
    material: str = "PLA"
    baseplate: str = "generic"
    auto_orient: bool = True

    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Optional[Dict[str, Any]] = None) -> "BasicThermoSettings":
        payload = payload or {}
        material_name = str(_first(payload, "material", default="PLA"))
        baseplate_name = str(_first(payload, "baseplate", "buildPlate", default="generic"))
        try:
            material = get_material(material_name)
        except ValueError:
            material = get_material("PLA")
            material_name = "PLA"
        try:
            plate = get_baseplate(baseplate_name)
        except ValueError:
            plate = get_baseplate("generic")
            baseplate_name = "generic"

        bed_x = _first(
            payload,
            "bed_size_x",
            "bedSizeX",
            "printerBuildPlateWidth",
            "buildPlateWidth",
            default=plate["bed_size"][0],
        )
        bed_y = _first(
            payload,
            "bed_size_y",
            "bedSizeY",
            "printerBuildPlateDepth",
            "buildPlateDepth",
            default=plate["bed_size"][1],
        )

        known = {f.name for f in cls.__dataclass_fields__.values()}
        mapped = {
            "layer_height": _first(payload, "layer_height", "layerHeight", default=0.2),
            "first_layer_height": _first(payload, "first_layer_height", "firstLayerHeight", default=0.3),
            "adaptive_height": _truthy(_first(payload, "adaptive_height", "adaptiveHeight", default=False)),
            "max_variation": _first(payload, "max_variation", "maxVariation", default=0.1),
            "seam_position": str(_first(payload, "seam_position", "seamPosition", default="aligned")),
            "staggered_inner_seams": _truthy(_first(payload, "staggered_inner_seams", "staggeredInnerSeams", default=False)),
            "seam_gap": _first(payload, "seam_gap", "seamGap", default=0),
            "wipe_on_loops": _truthy(_first(payload, "wipe_on_loops", "wipeOnLoops", default=False)),
            "wipe_speed": _first(payload, "wipe_speed", "wipeSpeed", default=80),
            "enable_ironing": _truthy(_first(payload, "enable_ironing", "enableIroning", default=True)),
            "ironing_surface": str(_first(payload, "ironing_surface", "ironingSurface", default="top")),
            "ironing_speed": _first(payload, "ironing_speed", "ironingSpeed", default=20),
            "ironing_flow": _first(payload, "ironing_flow", "ironingFlow", "ironingFlowrate", default=10),
            "wall_loops": int(_first(payload, "wall_loops", "wallLoops", default=2)),
            "order_of_walls": str(_first(payload, "order_of_walls", "orderOfWalls", default="inner-outer")),
            "detect_thin_walls": _truthy(_first(payload, "detect_thin_walls", "detectThinWalls", default=False)),
            "top_surface_pattern": str(_first(payload, "top_surface_pattern", "topSurfacePattern", default="concentric")),
            "top_shell_layers": int(_first(payload, "top_shell_layers", "topShellLayers", default=3)),
            "top_shell_thickness": _first(payload, "top_shell_thickness", "topShellThickness", default=0.60),
            "bottom_surface_pattern": str(_first(payload, "bottom_surface_pattern", "bottomSurfacePattern", default="rectilinear")),
            "bottom_shell_layers": int(_first(payload, "bottom_shell_layers", "bottomShellLayers", default=3)),
            "bottom_shell_thickness": _first(payload, "bottom_shell_thickness", "bottomShellThickness", default=0.60),
            "infill_density": _first(payload, "infill_density", "infillDensity", default=20),
            "infill_pattern": str(_first(payload, "infill_pattern", "sparseInfillPattern", "sparse_infill_pattern", default="rectilinear")),
            "support_enabled": _truthy(_first(payload, "support_enabled", "supportEnabled", default=False)),
            "support_type": str(_first(payload, "support_type", "supportType", default="normal-auto")),
            "threshold_angle": _first(payload, "threshold_angle", "thresholdAngle", default=40),
            "on_build_plate_only": _truthy(_first(payload, "on_build_plate_only", "onBuildPlateOnly", default=False)),
            "support_infill_pattern": str(_first(payload, "support_infill_pattern", "supportInfillPattern", default="rectilinear")),
            "support_density": _first(payload, "support_density", "supportDensity", default=15),
            "remove_small_overhangs": _truthy(_first(payload, "remove_small_overhangs", "removeSmallOverhangs", default=False)),
            "print_speed": _first(payload, "print_speed", "printSpeed", default=50),
            "travel_speed": _first(payload, "travel_speed", "travelSpeed", default=120),
            "first_layer_speed": _first(payload, "first_layer_speed", "firstLayerSpeed", default=30),
            "min_layer_time": _first(payload, "min_layer_time", "minLayerTime", default=10),
            "nozzle_diameter": _first(payload, "nozzle_diameter", "nozzleDiameter", default=0.4),
            "filament_diameter": _first(payload, "filament_diameter", "filamentDiameter", default=material["filament_diameter"]),
            "filament_density": _first(payload, "filament_density", "filamentDensity", default=material["density_g_cm3"]),
            "default_line_width": _first(payload, "default_line_width", "defaultLineWidth", default=0.42),
            "first_layer_line_width": _first(payload, "first_layer_line_width", "firstLayerLineWidth", default=0.50),
            "outer_wall_line_width": _first(payload, "outer_wall_line_width", "outerWallLineWidth", default=0.42),
            "inner_wall_line_width": _first(payload, "inner_wall_line_width", "innerWallLineWidth", default=0.45),
            "sparse_infill_line_width": _first(payload, "sparse_infill_line_width", "sparseInfillLineWidth", default=0.45),
            "support_line_width": _first(payload, "support_line_width", "supportLineWidth", default=0.40),
            "fan_speed": _first(payload, "fan_speed", "fanSpeed", default=material["fan_speed"]),
            "retraction_distance": _first(payload, "retraction_distance", "retractionDistance", default=material["retraction_distance"]),
            "retraction_speed": _first(payload, "retraction_speed", "retractionSpeed", default=material["retraction_speed"]),
            "wipe_distance": _first(payload, "wipe_distance", "wipeDistance", default=0),
            "adhesion_type": str(_first(payload, "adhesion_type", "adhesionType", default="skirt")),
            "skirt_loops": int(_first(payload, "skirt_loops", "skirtLoops", default=2)),
            "skirt_height": int(_first(payload, "skirt_height", "skirtHeight", default=1)),
            "skirt_distance": _first(payload, "skirt_distance", "skirtDistanceBasic", "skirtDistance", default=2),
            "brim_width": _first(payload, "brim_width", "brimWidth", default=5),
            "brim_object_gap": _first(payload, "brim_object_gap", "brimObjectGapBasic", "brimObjectGap", default=0.15),
            "brim_type": str(_first(payload, "brim_type", "brimType", default="outer-only")),
            "raft_layers": int(_first(payload, "raft_layers", "raftLayers", default=3)),
            "raft_margin": _first(payload, "raft_margin", "raftMargin", default=3),
            "timelapse": str(_first(payload, "timelapse", "timelapseType", default="off")),
            "timelapse_interval_s": _first(payload, "timelapse_interval_s", "timelapseIntervalS", default=10),
            "start_gcode": str(_first(payload, "start_gcode", "startGcode", "printerStartGcode", default="")),
            "end_gcode": str(_first(payload, "end_gcode", "endGcode", "printerEndGcode", default="")),
            "before_layer_change_gcode": str(_first(payload, "before_layer_change_gcode", "beforeLayerGcode", "printerBeforeLayerGcode", default="")),
            "layer_change_gcode": str(_first(payload, "layer_change_gcode", "layerChangeGcode", "printerLayerChangeGcode", default="")),
            "tool_change_gcode": str(_first(payload, "tool_change_gcode", "toolChangeGcode", "printerToolChangeGcode", default="")),
            "filament_type": str(_first(payload, "filament_type", "filamentType", default=material_name)),
            "filament_softening_temp": _first(payload, "filament_softening_temp", "filamentSofteningTemp", default=60),
            "nozzle_temp_min": _first(payload, "nozzle_temp_min", "nozzleTempMin", "filamentNozzleTempMin", default=190),
            "nozzle_temp_max": _first(payload, "nozzle_temp_max", "nozzleTempMax", "filamentNozzleTempMax", default=230),
            "chamber_temp_min": _first(payload, "chamber_temp_min", "chamberTempMin", default=0),
            "chamber_temp": _first(payload, "chamber_temp", "chamberTemp", default=0),
            "first_layer_nozzle_temp": _first(payload, "first_layer_nozzle_temp", "firstLayerNozzleTemp", "filamentNozzleFirstLayer", default=material["nozzle_temp"] + 5),
            "nozzle_temp": _first(payload, "nozzle_temp", "nozzleTemp", "filamentNozzleOtherLayers", default=material["nozzle_temp"]),
            "bed_temp": _first(payload, "bed_temp", "bedTemp", default=material["bed_temp"]),
            "bed_smooth_first": _first(payload, "bed_smooth_first", "bedSmoothFirstLayer", "filamentBedSmoothFirstLayer", default=material["bed_temp"]),
            "bed_smooth_other": _first(payload, "bed_smooth_other", "bedSmoothOtherLayers", "filamentBedSmoothOtherLayers", default=material["bed_temp"]),
            "bed_textured_first": _first(payload, "bed_textured_first", "bedTexturedFirstLayer", "filamentBedTexturedFirstLayer", default=material["bed_temp"]),
            "bed_textured_other": _first(payload, "bed_textured_other", "bedTexturedOtherLayers", "filamentBedTexturedOtherLayers", default=material["bed_temp"]),
            "bed_engineering_first": _first(payload, "bed_engineering_first", "bedEngineeringFirstLayer", "filamentBedEngineeringFirstLayer", default=material["bed_temp"]),
            "bed_engineering_other": _first(payload, "bed_engineering_other", "bedEngineeringOtherLayers", "filamentBedEngineeringOtherLayers", default=material["bed_temp"]),
            "bed_cool_first": _first(payload, "bed_cool_first", "bedCoolFirstLayer", "filamentBedCoolFirstLayer", default=0),
            "bed_cool_other": _first(payload, "bed_cool_other", "bedCoolOtherLayers", "filamentBedCoolOtherLayers", default=0),
            "printable_height": _first(payload, "printable_height", "printableHeight", default=250),
            "bed_origin": str(_first(payload, "bed_origin", "bedOrigin", "originPosition", default="corner")),
            "gcode_flavor": str(_first(payload, "gcode_flavor", "gcodeFlavor", default="marlin-legacy")),
            "use_relative_e_distances": _truthy(_first(payload, "use_relative_e_distances", "useRelativeEDistances", default=False)),
            "use_firmware_retraction": _truthy(_first(payload, "use_firmware_retraction", "useFirmwareRetraction", default=False)),
            "printer_name": str(_first(payload, "printer_name", "printerName", default="")),
            "material": material_name,
            "baseplate": baseplate_name,
            "auto_orient": _truthy(_first(payload, "auto_orient", "autoOrient", default=True)),
            "bed_size": (float(bed_x), float(bed_y)),
        }
        extra = {k: v for k, v in payload.items() if k not in known and k not in mapped}
        mapped["extra"] = extra
        return cls(**mapped)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["bed_size"] = list(self.bed_size)
        return data

    def to_print_settings(self) -> PrintSettings:
        density = float(self.infill_density)
        fill_density = density / 100.0 if density > 1.0 else density
        support_density = float(self.support_density)
        support_density = support_density / 100.0 if support_density > 1.0 else support_density

        support_enum = self._map_support_type()
        support_material = bool(self.support_enabled) and support_enum != SupportType.NONE
        adhesion = (self.adhesion_type or "skirt").lower()
        surface = str(get_baseplate(self.baseplate).get("surface", "generic")).lower()
        if "engineering" in surface:
            selected_bed_first = self.bed_engineering_first
            selected_bed_other = self.bed_engineering_other
        elif "textured" in surface:
            selected_bed_first = self.bed_textured_first
            selected_bed_other = self.bed_textured_other
        elif "cool" in surface:
            selected_bed_first = self.bed_cool_first
            selected_bed_other = self.bed_cool_other
        else:
            selected_bed_first = self.bed_smooth_first
            selected_bed_other = self.bed_smooth_other

        mapped = {
            "layer_height": float(self.layer_height),
            "first_layer_height": float(self.first_layer_height),
            "perimeters": int(self.wall_loops),
            "external_perimeter_speed": float(self.print_speed),
            "perimeter_speed": float(self.print_speed),
            "print_speed": float(self.print_speed),
            "order_of_walls": str(self.order_of_walls),
            "detect_thin_walls": bool(self.detect_thin_walls),
            "seam_position": str(self.seam_position),
            "staggered_inner_seams": bool(self.staggered_inner_seams),
            "seam_gap": float(self.seam_gap),
            "wipe_on_loops": bool(self.wipe_on_loops),
            "wipe_speed": float(self.wipe_speed),
            "fill_density": fill_density,
            "fill_pattern": INFILL_PATTERN_MAP.get(self.infill_pattern.lower(), InfillPattern.RECTILINEAR),
            "infill_speed": float(self.print_speed),
            "top_surface_pattern": str(self.top_surface_pattern),
            "top_shell_layers": int(self.top_shell_layers),
            "top_shell_thickness": float(self.top_shell_thickness),
            "bottom_surface_pattern": str(self.bottom_surface_pattern),
            "bottom_shell_layers": int(self.bottom_shell_layers),
            "bottom_shell_thickness": float(self.bottom_shell_thickness),
            "enable_ironing": bool(self.enable_ironing),
            "ironing_surface": str(self.ironing_surface),
            "ironing_speed": float(self.ironing_speed),
            "ironing_flow": float(self.ironing_flow),
            "support_material": support_material,
            "support_type": support_enum,
            "support_angle": float(self.threshold_angle),
            "support_density": support_density,
            "support_infill_pattern": str(self.support_infill_pattern),
            "on_build_plate_only": bool(self.on_build_plate_only),
            "remove_small_overhangs": bool(self.remove_small_overhangs),
            "travel_speed": float(self.travel_speed),
            "first_layer_speed": float(self.first_layer_speed),
            "min_layer_time": float(self.min_layer_time),
            "slow_down_layers": True,
            "fan_speed": float(self.fan_speed),
            "nozzle_temperature": float(self.nozzle_temp),
            "bed_temperature": float(selected_bed_other if selected_bed_other is not None else self.bed_temp),
            "first_layer_nozzle_temp": float(self.first_layer_nozzle_temp),
            "first_layer_bed_temp": float(selected_bed_first if selected_bed_first is not None else self.bed_temp),
            "nozzle_diameter": float(self.nozzle_diameter),
            "filament_diameter": float(self.filament_diameter),
            "extrusion_width": float(self.nozzle_diameter) * 1.125,
            "default_line_width": float(self.default_line_width),
            "first_layer_line_width": float(self.first_layer_line_width),
            "outer_wall_line_width": float(self.outer_wall_line_width),
            "inner_wall_line_width": float(self.inner_wall_line_width),
            "sparse_infill_line_width": float(self.sparse_infill_line_width),
            "support_line_width": float(self.support_line_width),
            "retract_length": float(self.retraction_distance),
            "retract_speed": float(self.retraction_speed),
            "wipe_distance": float(self.wipe_distance),
            "bed_size": self.bed_size,
            "print_center": (self.bed_size[0] / 2.0, self.bed_size[1] / 2.0),
            "adaptive_layer_height_enabled": bool(self.adaptive_height),
            "adaptive_max_layer_height": float(self.layer_height) + float(self.max_variation),
            "adaptive_min_layer_height": max(0.05, float(self.layer_height) - float(self.max_variation)),
            "adaptive_base_layer_height": float(self.layer_height),
            "fan_enabled": float(self.fan_speed) > 0,
            "fan_default_speed": float(self.fan_speed),
            "fan_max_speed": float(self.fan_speed),
            "adhesion_type": adhesion,
            "skirt_enabled": adhesion == "skirt" or adhesion == "brim_draft_shield",
            "skirt_lines": int(self.skirt_loops),
            "skirt_height": int(self.skirt_height),
            "skirt_distance": float(self.skirt_distance),
            "skirt_speed": float(self.first_layer_speed),
            "brim_enabled": adhesion.startswith("brim"),
            "brim_type": str(self.brim_type),
            "brim_width": float(self.brim_width),
            "brim_object_gap": float(self.brim_object_gap),
            "raft_enabled": "raft" in adhesion,
            "raft_layers": int(self.raft_layers),
            "raft_extra_margin": float(self.raft_margin),
            "timelapse_type": str(self.timelapse),
            "timelapse_interval_s": float(self.timelapse_interval_s),
            "filament_density": float(self.filament_density),
            "start_gcode": str(self.start_gcode or ""),
            "end_gcode": str(self.end_gcode or ""),
            "before_layer_change_gcode": str(self.before_layer_change_gcode or ""),
            "layer_change_gcode": str(self.layer_change_gcode or ""),
            "tool_change_gcode": str(self.tool_change_gcode or ""),
            "gcode_flavor": str(self.gcode_flavor),
            "use_relative_e_distances": bool(self.use_relative_e_distances),
            "use_firmware_retraction": bool(self.use_firmware_retraction),
            "printable_height": float(self.printable_height),
        }
        print_settings = PrintSettings()
        for key, value in mapped.items():
            if hasattr(print_settings, key):
                setattr(print_settings, key, value)
        return print_settings

    def _map_support_type(self) -> SupportType:
        value = (self.support_type or "").lower()
        if not self.support_enabled or value in NONE_SUPPORT_VALUES:
            return SupportType.NONE
        if self.on_build_plate_only:
            return SupportType.BUILD_PLATE_ONLY
        if value in TREE_SUPPORT_VALUES:
            return SupportType.TREE
        if value in NORMAL_SUPPORT_VALUES:
            return SupportType.EVERYWHERE
        return SupportType.EVERYWHERE


def _first(payload: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return default


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)
