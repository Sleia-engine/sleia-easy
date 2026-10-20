# ------------------------------------------------------------------
# Copyright (c) 2026 Sleia Engine Development Team.
# This file is distributed under the MIT License. See LICENSE.
#
# Sleia Easy v 1.0.1 - Thermoplastic Python Slicer
#
# File: presets.py
# Description: material and printer bed presets.
# ------------------------------------------------------------------

from __future__ import annotations

from typing import Any, Dict

MATERIALS: Dict[str, Dict[str, Any]] = {
    "PLA": {
        "name": "PLA",
        "nozzle_temp": 200.0,
        "bed_temp": 60.0,
        "fan_speed": 100.0,
        "filament_diameter": 1.75,
        "density_g_cm3": 1.24,
        "retraction_distance": 0.8,
        "retraction_speed": 40.0,
    },
    "PETG": {
        "name": "PETG",
        "nozzle_temp": 240.0,
        "bed_temp": 80.0,
        "fan_speed": 50.0,
        "filament_diameter": 1.75,
        "density_g_cm3": 1.27,
        "retraction_distance": 1.2,
        "retraction_speed": 35.0,
    },
    "ABS": {
        "name": "ABS",
        "nozzle_temp": 245.0,
        "bed_temp": 100.0,
        "fan_speed": 0.0,
        "filament_diameter": 1.75,
        "density_g_cm3": 1.04,
        "retraction_distance": 1.0,
        "retraction_speed": 40.0,
    },
    "TPU": {
        "name": "TPU",
        "nozzle_temp": 220.0,
        "bed_temp": 50.0,
        "fan_speed": 100.0,
        "filament_diameter": 1.75,
        "density_g_cm3": 1.21,
        "retraction_distance": 0.4,
        "retraction_speed": 25.0,
    },
}

BASEPLATES: Dict[str, Dict[str, Any]] = {
    "generic": {
        "name": "Generic",
        "bed_size": (220.0, 220.0),
        "surface": "generic",
    },
    "ender3": {
        "name": "Ender 3",
        "bed_size": (220.0, 220.0),
        "surface": "PEI",
    },
    "prusa-mk4": {
        "name": "Prusa MK4",
        "bed_size": (250.0, 210.0),
        "surface": "textured PEI",
    },
    "bambu-p1s": {
        "name": "Bambu P1S",
        "bed_size": (256.0, 256.0),
        "surface": "textured PEI",
    },
}


def get_material(name: str) -> Dict[str, Any]:
    key = (name or "PLA").strip().upper()
    if key not in MATERIALS:
        raise ValueError(f"Unknown material '{name}'. Available: {', '.join(sorted(MATERIALS))}")
    return dict(MATERIALS[key])


def get_baseplate(name: str) -> Dict[str, Any]:
    key = (name or "generic").strip().lower()
    if key not in BASEPLATES:
        raise ValueError(f"Unknown baseplate '{name}'. Available: {', '.join(sorted(BASEPLATES))}")
    return dict(BASEPLATES[key])
