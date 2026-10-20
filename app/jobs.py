# ------------------------------------------------------------------
# Copyright (c) 2026 Sleia Engine Development Team.
# This file is distributed under the MIT License. See LICENSE.
#
# Sleia Easy v 1.0.1 - Thermoplastic Python Slicer
#
# File: jobs.py
# Description: tracks slice jobs in memory and on disk.
# ------------------------------------------------------------------

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from config.settings import Settings


_lock = threading.Lock()


def _jobs_dir() -> Path:
    path = Settings.DATA_DIR / "jobs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _job_path(job_id: str) -> Path:
    return _jobs_dir() / f"{job_id}.json"


def create_job(job_id: str, model_filename: str, model_path: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    job = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "message": "Queued",
        "model_filename": model_filename,
        "model_path": model_path,
        "gcode_path": None,
        "error": None,
        "settings": settings,
        "statistics": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "started_at": None,
        "completed_at": None,
    }
    save_job(job)
    return job


def save_job(job: Dict[str, Any]) -> None:
    with _lock:
        _job_path(job["job_id"]).write_text(json.dumps(job, indent=2), encoding="utf-8")


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    path = _job_path(job_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def update_job(job_id: str, **fields: Any) -> Optional[Dict[str, Any]]:
    with _lock:
        job = get_job(job_id)
        if not job:
            return None
        job.update(fields)
        _job_path(job_id).write_text(json.dumps(job, indent=2), encoding="utf-8")
        return job
