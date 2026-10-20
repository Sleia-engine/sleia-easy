#!/usr/bin/env python3
# ------------------------------------------------------------------
# Copyright (c) 2026 Sleia Engine Development Team.
# This file is distributed under the MIT License. See LICENSE.
#
# Sleia Easy v 1.0.1 - Thermoplastic Python Slicer
#
# File: start.py
# Description: kicks off the CLI from the project root.
# ------------------------------------------------------------------

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.cli import run_cli

if __name__ == "__main__":
    raise SystemExit(run_cli())
