"""Flow ingestion and forensics endpoints."""

from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from dashboard.backend.config import DB_PATH
from dashboard.backend.database import (
    get_attack_distribution,
    get_engine_distribution,
    get_flow_forensics,
    get_kpis,
    get_recent_flows,
    get_targeted_stats,
    get_threat_actors,
    get_timeline,
    get_traffic_summary,
    insert_and_correlate_flows,
    reset_database,
)
from dashboard.backend.models import FlowIngestPayload, FlowIngestResponse
from dashboard.backend.ws_manager import ws_manager

logger = logging.getLogger("dashboard.routes.flows")
router = APIRouter(tags=["Flows"])


@router.post("/flows/ingest", response_model=FlowIngestResponse)
async def ingest_flows(payload: FlowIngestPayload) -> FlowIngestResponse:
    """Ingests a micro-batch of flows from live capture or replay, correlates incidents, and broadcasts updates."""
    raw_list = payload.flow_records or payload.flows or []
    flows_dicts = []
    for f in raw_list:
        if isinstance(f, dict):
            flows_dicts.append(f)
        elif hasattr(f, "model_dump"):
            flows_dicts.append(f.model_dump(by_alias=True))
        else:
            flows_dicts.append(dict(f))

    inserted, incidents = insert_and_correlate_flows(
        flows_dicts,
        predictions=payload.predictions or None,
        confidences=payload.confidences or None,
        mse_values=payload.mse_values or None,
        anomaly_values=payload.anomaly_values or None,
        sensor_id=payload.sensor_id,
        db_path=DB_PATH,
    )

    # Broadcast real-time updates via WebSocket
    try:
        kpis = get_kpis(db_path=DB_PATH)
        traffic = get_traffic_summary(db_path=DB_PATH)
        timeline = get_timeline(window_minutes=15, buckets=20, db_path=DB_PATH)
        engine_dist = get_engine_distribution(db_path=DB_PATH)
        targeted_stats = get_targeted_stats(db_path=DB_PATH)
        attack_dist = get_attack_distribution(db_path=DB_PATH)

        await ws_manager.broadcast("telemetry_update", {
            "sensor_id": payload.sensor_id,
            "inserted_flows": inserted,
            "generated_incidents": incidents,
            "kpis": kpis,
            "traffic": traffic,
            "timeline": timeline,
            "engine_distribution": engine_dist,
            "targeted_stats": targeted_stats,
            "attack_distribution": attack_dist,
        })
        if incidents > 0:
            await ws_manager.broadcast("incident_alert", {
                "sensor_id": payload.sensor_id,
                "new_incidents_count": incidents,
            })
    except Exception as exc:
        logger.warning(f"Error broadcasting WebSocket updates after flow ingest: {exc}")

    return FlowIngestResponse(
        status="success",
        inserted=inserted,
        inserted_flows=inserted,
        alerts=incidents,
        generated_incidents=incidents,
        message=f"Successfully ingested {inserted} flows ({incidents} alerts created)",
    )


@router.get("/flows/recent")
async def list_recent_flows(
    limit: int = Query(100, ge=1, le=1000),
    threat_only: bool = Query(False),
    exclude_loopback: bool = Query(False),
    sensor_id: Optional[str] = Query(None),
) -> list[dict]:
    """Returns recent flows processed by the NIDS engine with technical features."""
    flows = get_recent_flows(limit=limit, exclude_loopback=exclude_loopback, db_path=DB_PATH)
    if threat_only:
        flows = [f for f in flows if f.get("threat_class") != "BENIGN"]
    if sensor_id:
        flows = [f for f in flows if f.get("sensor_id") == sensor_id]
    return flows


@router.get("/threat-actors")
async def list_threat_actors(
    limit: int = Query(50, ge=1, le=500),
    exclude_loopback: bool = Query(False),
) -> list[dict]:
    """Returns the ranked criminal / threat actor IP list with attack volumes and vectors."""
    return get_threat_actors(limit=limit, exclude_loopback=exclude_loopback, db_path=DB_PATH)


@router.get("/stats/targets")
async def get_target_statistics(
    exclude_loopback: bool = Query(False),
) -> dict:
    """Returns statistics for most targeted victim destination IPs and ports."""
    return get_targeted_stats(exclude_loopback=exclude_loopback, db_path=DB_PATH)


@router.get("/stats/timeline")
async def get_timeline_statistics(
    window_minutes: int = Query(15, ge=1, le=1440),
    buckets: int = Query(20, ge=5, le=100),
    exclude_loopback: bool = Query(False),
) -> list[dict]:
    """Returns real-time traffic & attack volume timeline buckets for charts."""
    return get_timeline(
        window_minutes=window_minutes,
        buckets=buckets,
        exclude_loopback=exclude_loopback,
        db_path=DB_PATH,
    )


@router.get("/stats/engine-distribution")
async def get_engine_distribution_statistics(
    exclude_loopback: bool = Query(False),
) -> list[dict]:
    """Returns detection engine distribution (DPI vs ML vs Kitsune vs Benign)."""
    return get_engine_distribution(exclude_loopback=exclude_loopback, db_path=DB_PATH)


@router.get("/flows/{flow_id}/forensics")
async def get_flow_forensics_detail(flow_id: int) -> dict:
    """Fetches full forensic inspection payload for a specific flow (5-tuple, ML scores, raw metrics)."""
    detail = get_flow_forensics(flow_id, db_path=DB_PATH)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Flow ID {flow_id} not found")
    
    # Format cleanly with five_tuple, ml_scores, raw_metrics for SOC forensics
    flow = detail.get("flow", {})
    metrics = detail.get("metrics", {})
    incident = detail.get("incident")
    
    return {
        "flow_id": flow_id,
        "five_tuple": {
            "src_ip": flow.get("src_ip"),
            "src_port": flow.get("src_port"),
            "dst_ip": flow.get("dst_ip"),
            "dst_port": flow.get("dst_port"),
            "protocol": flow.get("protocol") or flow.get("proto"),
        },
        "ml_scores": {
            "stage1_prediction": flow.get("pred"),
            "stage2_confidence": flow.get("confiance"),
            "kitsune_rmse": flow.get("mse_ae"),
            "is_anomaly": bool(flow.get("anomalie_ae")),
            "decision_engine": flow.get("engine", "DNN-1D / DPI"),
            "severity": flow.get("severity", "MEDIUM"),
        },
        "raw_metrics": metrics,
        "incident": incident,
        "ip_history": detail.get("ip_history", []),
    }


@router.post("/flows/reset")
async def reset_flows_and_alerts() -> dict:
    """Purges all flows, incidents, and statistics from the database (for clean test runs)."""
    reset_database(DB_PATH)
    await ws_manager.broadcast("db_reset", {"status": "reset_complete"})
    return {"status": "ok", "message": "Database successfully purged and reset"}
