# ------------------------------------------------------------------
# Copyright (c) 2026 Sleia Engine Development Team.
# This file is distributed under the MIT License. See LICENSE.
#
# Sleia Easy v 1.0.1 - Thermoplastic Python Slicer
#
# File: cli.py
# Description: command line for serve and slice.
# ------------------------------------------------------------------

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from app.pipeline import slice_to_gcode
from app.settings import BasicThermoSettings
from config.settings import Settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sleia Easy — basic thermoplastic slicer (Python, standalone)"
    )
    sub = parser.add_subparsers(dest="command")

    serve = sub.add_parser("serve", help="Run the local slice API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=5000)
    serve.add_argument("--debug", action="store_true")

    slice_cmd = sub.add_parser("slice", help="Slice a model and save G-code")
    slice_cmd.add_argument("model", help="Path to STL/OBJ/3MF")
    slice_cmd.add_argument("-o", "--output", help="Output .gcode path")
    slice_cmd.add_argument("--layer-height", type=float, default=0.2)
    slice_cmd.add_argument("--first-layer-height", type=float, default=0.3)
    slice_cmd.add_argument("--infill", type=float, default=20, help="Sparse infill density percent")
    slice_cmd.add_argument("--pattern", default="rectilinear")
    slice_cmd.add_argument("--walls", type=int, default=2)
    slice_cmd.add_argument("--support", action="store_true")
    slice_cmd.add_argument("--support-type", default="normal-auto")
    slice_cmd.add_argument("--print-speed", type=float, default=50)
    slice_cmd.add_argument("--travel-speed", type=float, default=120)
    slice_cmd.add_argument("--first-layer-speed", type=float, default=30)
    slice_cmd.add_argument("--material", default="PLA", help="PLA, PETG, ABS, or TPU")
    slice_cmd.add_argument("--baseplate", default="generic", help="generic, ender3, prusa-mk4, bambu-p1s")
    slice_cmd.add_argument("--bed-x", type=float, help="Build plate width in mm")
    slice_cmd.add_argument("--bed-y", type=float, help="Build plate depth in mm")
    slice_cmd.add_argument("--no-auto-orient", action="store_true", help="Skip auto-orient; still place on bed")
    slice_cmd.add_argument("--settings-json", help="Optional JSON file of Basic-tab settings")
    return parser


def run_cli(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command or "serve"

    if command == "serve":
        from app.server import create_app

        Settings.init_directories()
        app = create_app()
        host = getattr(args, "host", "127.0.0.1")
        port = getattr(args, "port", 5000)
        debug = getattr(args, "debug", False)
        print(f"Sleia Easy basic slicer: http://{host}:{port}")
        print("POST /api/slice  GET /api/jobs/<id>  GET /api/jobs/<id>/gcode  POST /api/gcode/save")
        app.run(host=host, port=port, debug=debug)
        return 0

    if command == "slice":
        Settings.init_directories()
        payload = {}
        if args.settings_json:
            payload = json.loads(Path(args.settings_json).read_text(encoding="utf-8"))
        payload.update({
            "layerHeight": args.layer_height,
            "firstLayerHeight": args.first_layer_height,
            "infillDensity": args.infill,
            "sparseInfillPattern": args.pattern,
            "wallLoops": args.walls,
            "supportEnabled": args.support,
            "supportType": args.support_type,
            "printSpeed": args.print_speed,
            "travelSpeed": args.travel_speed,
            "firstLayerSpeed": args.first_layer_speed,
            "material": args.material,
            "baseplate": args.baseplate,
            "autoOrient": not args.no_auto_orient,
        })
        if args.bed_x is not None:
            payload["bedSizeX"] = args.bed_x
        if args.bed_y is not None:
            payload["bedSizeY"] = args.bed_y
        settings = BasicThermoSettings.from_payload(payload)
        model = Path(args.model)
        output = Path(args.output) if args.output else Settings.GCODE_DIR / f"{model.stem}.gcode"
        result = slice_to_gcode(str(model), str(output), settings)
        print(json.dumps({
            "success": True,
            "gcode_path": result["gcode_path"],
            "statistics": result.get("statistics"),
            "gcode": result.get("gcode"),
            "placement": result.get("placement"),
        }, indent=2, default=str))
        return 0

    parser.print_help()
    return 1
