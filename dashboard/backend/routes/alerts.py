"""Consolidated incident alerts and triage endpoints."""

from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from dashboard.backend.config import DB_PATH
from dashboard.backend.database import (
    get_consolidated_alerts,
    get_incident_by_id,
    update_incident_status,
)
from dashboard.backend.models import IncidentStatusUpdate
from dashboard.backend.ws_manager import ws_manager

logger = logging.getLogger("dashboard.routes.alerts")
router = APIRouter(tags=["Alerts & Incidents"])


@router.get("/alerts")
@router.get("/incidents")
async def list_alerts(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    exclude_loopback: bool = Query(False),
) -> list[dict]:
    """Retrieves consolidated security incidents filtered by severity, status, or search query."""
    return get_consolidated_alerts(
        limit=limit,
        offset=offset,
        severity=severity,
        status=status,
        search=search,
        exclude_loopback=exclude_loopback,
        db_path=DB_PATH,
    )


@router.get("/alerts/{incident_id}")
@router.get("/incidents/{incident_id}")
async def get_incident(incident_id: str) -> dict:
    """Retrieves detailed forensic information for a specific consolidated incident."""
    incident = get_incident_by_id(incident_id, db_path=DB_PATH)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return incident


@router.post("/alerts/{incident_id}/status")
@router.post("/incidents/{incident_id}/status")
async def update_status(incident_id: str, payload: IncidentStatusUpdate) -> dict:
    """Updates the workflow status of an incident (OPEN, INVESTIGATING, RESOLVED, FALSE_POSITIVE)."""
    success = update_incident_status(incident_id, payload.status, db_path=DB_PATH)
    if not success:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    await ws_manager.broadcast("incident_status_changed", {
        "incident_id": incident_id,
        "new_status": payload.status,
        "notes": payload.notes or payload.comment,
    })

    return {
        "status": "success",
        "incident_id": incident_id,
        "new_status": payload.status,
    }
