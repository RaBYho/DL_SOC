"""System health, threshold configuration, and initialization endpoints."""

from __future__ import annotations

import logging
from pathlib import Path
import time
from typing import Any
from fastapi import APIRouter
import yaml

from dashboard.backend.config import DB_PATH, REPO_ROOT
from dashboard.backend.database import (
    get_attack_distribution,
    get_consolidated_alerts,
    get_engine_distribution,
    get_kpis,
    get_recent_flows,
    get_sensors_list,
    get_targeted_stats,
    get_threat_actors,
    get_timeline,
    get_traffic_summary,
    log_system_event,
)
from dashboard.backend.models import SystemLogPayload, SystemLogResponse

logger = logging.getLogger("dashboard.routes.system")
router = APIRouter(tags=["System & Health"])


def _load_threshold_config() -> dict[str, Any]:
    """Reads thresholds from configs/live_guard.yaml or configs/thresholds.yaml."""
    live_guard_file = REPO_ROOT / "configs" / "live_guard.yaml"
    if live_guard_file.exists():
        try:
            with open(live_guard_file) as f:
                cfg = yaml.safe_load(f)
                th = cfg.get("thresholds", {})
                k_live = cfg.get("kitsune_live", {})
                return {
                    "t1": float(th.get("t1", 0.50)),
                    "t2": float(th.get("t2", 0.70)),
                    "t3": float(k_live.get("default_t3", 0.0100)),
                    "models": ["CatBoost (Stage 1)", "XGBoost (Stage 1)", "DNN-1D (Stage 2)", "KitNET (Kitsune)"],
                    "pre_filter_active": True,
                    "leaky_bucket_half_life": float(cfg.get("threat_scoring", {}).get("half_life_sec", 60.0)),
                }
        except Exception as exc:
            logger.warning(f"Failed to load live_guard.yaml: {exc}")

    return {
        "t1": 0.50,
        "t2": 0.70,
        "t3": 0.0100,
        "models": ["CatBoost", "XGBoost", "DNN-1D", "KitNET"],
        "pre_filter_active": True,
        "leaky_bucket_half_life": 60.0,
    }


@router.get("/healthz")
async def health_check() -> dict:
    """Operational health check verifying database and application availability."""
    db_ok = Path(DB_PATH).exists()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "missing",
        "timestamp": time.time(),
    }


@router.get("/init")
async def get_initial_soc_state() -> dict:
    """Consolidated state payload to hydrate the frontend store on single load."""
    kpis = get_kpis(exclude_loopback=False, db_path=DB_PATH)
    traffic = get_traffic_summary(db_path=DB_PATH)
    timeline = get_timeline(window_minutes=60, buckets=20, db_path=DB_PATH)
    engine_dist = get_engine_distribution(db_path=DB_PATH)
    attack_dist = get_attack_distribution(db_path=DB_PATH)
    alerts = get_consolidated_alerts(limit=50, db_path=DB_PATH)
    flows = get_recent_flows(limit=50, db_path=DB_PATH)
    sensors = get_sensors_list(db_path=DB_PATH)
    thresholds = _load_threshold_config()
    threat_actors = get_threat_actors(limit=50, exclude_loopback=False, db_path=DB_PATH)
    targeted_stats = get_targeted_stats(exclude_loopback=False, db_path=DB_PATH)

    return {
        "kpis": kpis,
        "traffic": traffic,
        "timeline": timeline,
        "engine_distribution": engine_dist,
        "attack_distribution": attack_dist,
        "recent_alerts": alerts,
        "recent_flows": flows,
        "sensors": sensors,
        "thresholds": thresholds,
        "threat_actors": threat_actors,
        "targeted_stats": targeted_stats,
        "server_time": time.time(),
    }


@router.get("/models")
async def get_model_specs() -> dict:
    """Returns technical specifications and operational thresholds of the NIDS pipeline."""
    return _load_threshold_config()


@router.post("/system/log", response_model=SystemLogResponse)
async def ingest_system_log(payload: SystemLogPayload) -> SystemLogResponse:
    """Logs technical audit events into the database."""
    log_system_event(
        source=payload.source or "system",
        message=payload.message,
        level=payload.level,
        details=payload.details,
        db_path=DB_PATH,
    )
    return SystemLogResponse(status="logged")
