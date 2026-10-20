# ------------------------------------------------------------------
# Copyright (c) 2026 Sleia Engine Development Team.
# This file is distributed under the MIT License. See LICENSE.
#
# Sleia Easy v 1.0.1 - Thermoplastic Python Slicer
#
# File: settings.py
# Description: folders, upload limits, and CORS.
# ------------------------------------------------------------------

import os
from pathlib import Path

class Settings:

    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / 'data'
    UPLOAD_DIR = DATA_DIR / 'uploads'
    OUTPUT_DIR = DATA_DIR / 'output'
    GCODE_DIR = DATA_DIR / 'gcode'

    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB
    ALLOWED_EXTENSIONS = {'.stl', '.obj', '.3mf', '.amf'}

    @classmethod
    def init_directories(cls):
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.UPLOAD_DIR.mkdir(exist_ok=True)
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
        cls.GCODE_DIR.mkdir(exist_ok=True)
