import asyncio
import logging
from typing import Optional
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from dashboard.backend.config import PCAP_DIR
from dashboard.backend.database import (
    get_attack_distribution,
    get_kpis,
    get_recent_alerts,
    get_threat_vectors,
    get_timeline,
)
from dashboard.backend.replay_service import replay_service
from dashboard.backend.ws_manager import ws_manager

logger = logging.getLogger("dashboard.routes")
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class ReplayRequest(BaseModel):
    pcap_name: str
    rate_per_sec: int = 25
    sensor_id: str = "lab-replay"


@router.get("/init")
def get_initial_dashboard_state():
    """Fournit l'état complet initial du tableau de bord au chargement de la page."""
    return {
        "kpis": get_kpis(),
        "distribution": get_attack_distribution(),
        "timeline": get_timeline(window_seconds=900, buckets=60),
        "threat_vectors": get_threat_vectors(limit=5),
        "recent_alerts": get_recent_alerts(limit=60),
        "replay_status": replay_service.get_status(),
    }


@router.get("/stats")
def get_stats():
    """Retourne les métriques clés et la distribution actuelle."""
    return {
        "kpis": get_kpis(),
        "distribution": get_attack_distribution(),
        "threat_vectors": get_threat_vectors(limit=5),
    }


@router.get("/alerts")
def get_alerts(
    limit: int = Query(60, ge=1, le=500),
    search_ip: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    min_conf: float = Query(0.0, ge=0.0, le=100.0),
    anomalies_only: bool = Query(False),
):
    """Retourne la liste filtrée des alertes."""
    return get_recent_alerts(
        limit=limit,
        search_ip=search_ip,
        category=category,
        min_conf=min_conf,
        anomalies_only=anomalies_only,
    )


@router.get("/pcaps")
def list_pcaps():
    """Liste les fichiers PCAP disponibles pour le rejeu."""
    if not PCAP_DIR.exists():
        return {"pcaps": []}
    files = sorted([f.name for f in PCAP_DIR.glob("*.pcap")])
    return {"pcaps": files}


@router.post("/replay/start")
async def start_replay(req: ReplayRequest):
    """Démarre le rejeu d'un fichier PCAP en arrière-plan."""
    return await replay_service.start_replay(
        pcap_name=req.pcap_name,
        rate_per_sec=req.rate_per_sec,
        sensor_id=req.sensor_id,
    )


@router.post("/replay/pause")
def pause_replay():
    """Met en pause le rejeu PCAP en cours."""
    return replay_service.pause_replay()


@router.post("/replay/resume")
def resume_replay():
    """Reprend le rejeu PCAP mis en pause."""
    return replay_service.resume_replay()


@router.post("/replay/stop")
def stop_replay():
    """Interrompt définitivement le rejeu PCAP."""
    return replay_service.stop_replay()


@router.get("/replay/status")
def replay_status():
    """Retourne l'état d'avancement du rejeu."""
    return replay_service.get_status()


async def websocket_endpoint(websocket: WebSocket):
    """Canal WebSocket temps réel pour pousser les alertes et les métriques sans recharger la page."""
    await ws_manager.connect(websocket)
    try:
        # Envoi immédiat de l'état d'initialisation
        init_data = {
            "type": "init",
            "kpis": get_kpis(),
            "distribution": get_attack_distribution(),
            "timeline": get_timeline(),
            "threat_vectors": get_threat_vectors(),
            "recent_alerts": get_recent_alerts(limit=30),
            "replay_status": replay_service.get_status(),
        }
        await ws_manager.send_personal_message(init_data, websocket)

        while True:
            # Réception d'éventuels messages du client (ping / heartbeat / pause / resume)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"Erreur WebSocket: {e}")
        ws_manager.disconnect(websocket)
