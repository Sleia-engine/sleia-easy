# ------------------------------------------------------------------
# Copyright (c) 2026 Sleia Engine Development Team.
# This file is distributed under the MIT License. See LICENSE.
#
# Sleia Easy v 1.0.1 - Thermoplastic Python Slicer
#
# File: converters.py
# Description: maps frontend settings into backend ones.
# ------------------------------------------------------------------

from app.settings import BasicThermoSettings


def frontend_to_backend_settings(frontend_settings):
    basic = BasicThermoSettings.from_payload(frontend_settings or {})
    return basic.to_dict()


def backend_to_frontend_response(backend_data):
    return backend_data
