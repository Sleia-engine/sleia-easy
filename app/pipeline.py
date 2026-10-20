# ------------------------------------------------------------------
# Copyright (c) 2026 Sleia Engine Development Team.
# This file is distributed under the MIT License. See LICENSE.
#
# Sleia Easy v 1.0.1 - Thermoplastic Python Slicer
#
# File: pipeline.py
# Description: load model, slice, write G-code.
# ------------------------------------------------------------------

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from engine.main_slicer import SlicerAPI
from app.settings import BasicThermoSettings

logger = logging.getLogger(__name__)

ProgressCallback = Optional[Callable[[int, str], None]]


def slice_to_gcode(
    model_path: str,
    output_path: str,
    settings: Optional[BasicThermoSettings] = None,
    progress_callback: ProgressCallback = None,
) -> Dict[str, Any]:
    settings = settings or BasicThermoSettings()
    model_path = str(Path(model_path).resolve())
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    def progress(pct: int, message: str) -> None:
        logger.info("%s (%s%%)", message, pct)
        if progress_callback:
            progress_callback(pct, message)

    progress(5, "Initializing basic thermoplastic slicer")
    slicer = SlicerAPI(settings.to_print_settings())

    progress(15, "Loading model")
    load_result = slicer.load_model(model_path, auto_orient=bool(settings.auto_orient))
    if not load_result.get("success"):
        raise RuntimeError(load_result.get("error") or "Failed to load model")

    progress(40, "Slicing model")
    slice_result = slicer.slice_model()
    if not slice_result.get("success"):
        raise RuntimeError(slice_result.get("error") or "Failed to slice model")

    progress(80, "Generating G-code")
    gcode_result = slicer.generate_gcode(str(output))
    if not gcode_result.get("success"):
        raise RuntimeError(gcode_result.get("error") or "Failed to generate G-code")
    if not output.exists():
        raise RuntimeError(f"G-code was not written to {output}")

    progress(100, "G-code saved")
    return {
        "success": True,
        "gcode_path": str(output.resolve()),
        "model_path": model_path,
        "settings": settings.to_dict(),
        "mesh_info": load_result.get("mesh_info"),
        "statistics": slice_result.get("statistics"),
        "gcode": {
            "line_count": gcode_result.get("line_count"),
            "gcode_length": gcode_result.get("gcode_length"),
            "generation_time": gcode_result.get("generation_time"),
            "infill_segments": (gcode_result.get("statistics") or {}).get("infill_segments"),
            "wall_segments": (gcode_result.get("statistics") or {}).get("wall_segments"),
        },
        "placement": {
            "auto_oriented": load_result.get("auto_oriented"),
            "material": settings.material,
            "baseplate": settings.baseplate,
            "bed_size": list(settings.bed_size),
        },
    }


def copy_gcode(source_path: str, destination_path: str) -> str:
    source = Path(source_path)
    if not source.exists():
        raise FileNotFoundError(f"G-code not found: {source_path}")
    dest = Path(destination_path)
    if dest.suffix.lower() not in {".gcode", ".gco", ".g"}:
        dest = dest.with_suffix(".gcode")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return str(dest.resolve())
