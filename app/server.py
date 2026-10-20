# ------------------------------------------------------------------
# Copyright (c) 2026 Sleia Engine Development Team.
# This file is distributed under the MIT License. See LICENSE.
#
# Sleia Easy v 1.0.1 - Thermoplastic Python Slicer
#
# File: server.py
# Description: local HTTP API for slice and G-code save.
# ------------------------------------------------------------------

from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

from app import jobs
from app.pipeline import copy_gcode, slice_to_gcode
from app.settings import BasicThermoSettings
from config.settings import Settings

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".stl", ".obj", ".3mf", ".amf"}


def create_app() -> Flask:
    Settings.init_directories()
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})
    app.config["MAX_CONTENT_LENGTH"] = Settings.MAX_UPLOAD_SIZE

    @app.get("/health")
    def health():
        return jsonify({"status": "healthy", "mode": "basic-thermoplastic"})

    @app.get("/api/features/basic")
    def basic_features():
        return jsonify({
            "success": True,
            "process": "thermoplastic",
            "tabs": ["Layers", "Infill", "Support", "Motion"],
            "can_save_gcode": True,
        })

    @app.post("/api/slice")
    @app.post("/api/slice/")
    def slice_model():
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
        upload = request.files["file"]
        if not upload.filename:
            return jsonify({"success": False, "error": "No file selected"}), 400
        suffix = Path(upload.filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            return jsonify({"success": False, "error": f"Unsupported file type: {suffix}"}), 400

        payload = _read_settings(request)
        settings = BasicThermoSettings.from_payload(payload)
        job_id = str(uuid.uuid4())
        filename = secure_filename(upload.filename)
        model_path = Settings.UPLOAD_DIR / f"{job_id}_{filename}"
        upload.save(model_path)

        jobs.create_job(job_id, filename, str(model_path), settings.to_dict())
        thread = threading.Thread(
            target=_run_slice_job,
            args=(job_id, str(model_path), settings),
            daemon=True,
        )
        thread.start()
        return jsonify({
            "success": True,
            "job_id": job_id,
            "message": "Slicing started",
        })

    @app.get("/api/jobs/<job_id>")
    def job_status(job_id: str):
        job = jobs.get_job(job_id)
        if not job:
            return jsonify({"success": False, "error": "Job not found"}), 404
        return jsonify({"success": True, **job})

    @app.get("/api/jobs/<job_id>/gcode")
    def download_job_gcode(job_id: str):
        job = jobs.get_job(job_id)
        if not job:
            return jsonify({"success": False, "error": "Job not found"}), 404
        if job.get("status") != "completed" or not job.get("gcode_path"):
            return jsonify({"success": False, "error": "G-code is not ready"}), 409
        path = Path(job["gcode_path"])
        if not path.exists():
            return jsonify({"success": False, "error": "G-code file missing on disk"}), 404
        download_name = Path(job.get("model_filename") or "model").stem + ".gcode"
        return send_file(path, as_attachment=True, download_name=download_name, mimetype="text/plain")

    @app.post("/api/gcode/save")
    def save_gcode():
        data = request.get_json(silent=True) or {}
        job_id = data.get("job_id")
        destination = data.get("destination") or data.get("path")
        if not job_id or not destination:
            return jsonify({"success": False, "error": "job_id and destination are required"}), 400
        job = jobs.get_job(job_id)
        if not job or not job.get("gcode_path"):
            return jsonify({"success": False, "error": "G-code is not ready"}), 404
        saved = copy_gcode(job["gcode_path"], destination)
        jobs.update_job(job_id, saved_path=saved)
        return jsonify({"success": True, "saved_path": saved})

    return app


def _read_settings(req) -> dict:
    if req.is_json and isinstance(req.json, dict):
        return req.json.get("settings") or req.json
    raw = req.form.get("settings", "{}")
    try:
        parsed = json.loads(raw) if raw else {}
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid settings JSON: {exc}") from exc


def _run_slice_job(job_id: str, model_path: str, settings: BasicThermoSettings) -> None:
    jobs.update_job(
        job_id,
        status="processing",
        progress=5,
        message="Slicing",
        started_at=datetime.now(timezone.utc).isoformat(),
    )
    try:
        gcode_path = Settings.GCODE_DIR / f"{job_id}.gcode"

        def on_progress(pct: int, message: str) -> None:
            jobs.update_job(job_id, progress=pct, message=message)

        result = slice_to_gcode(model_path, str(gcode_path), settings, on_progress)
        jobs.update_job(
            job_id,
            status="completed",
            progress=100,
            message="G-code saved",
            gcode_path=result["gcode_path"],
            statistics=result.get("statistics"),
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
        logger.info("Job %s completed: %s", job_id, result["gcode_path"])
    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        jobs.update_job(
            job_id,
            status="failed",
            error=str(exc),
            message="Failed",
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
