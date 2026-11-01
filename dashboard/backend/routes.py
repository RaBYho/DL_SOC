import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query, Request, Response, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from dashboard.backend.config import AE_THRESHOLD, PCAP_DIR
from dashboard.backend.database import (
    export_feedback_dataset,
    get_active_sensors,
    get_attack_distribution,
    get_feedback,
    get_feedback_summary,
    get_incident_flows,
    get_incidents,
    get_incidents_summary,
    get_kpis,
    get_model_classes,
    get_recent_alerts,
    get_threat_vectors,
    get_timeline,
    get_total_alerts_count,
    get_total_incidents_count,
    record_feedback,
    record_batch_feedback,
    reset_database,
)
from dashboard.backend.model_logger import clear_logs, get_recent_logs, MODEL_LOG_FILE
from dashboard.backend.replay_service import replay_service
from dashboard.backend.services.health_service import health_service
from dashboard.backend.services.ai_analyzer import (
    AiAnalyzerService,
    build_forensic_prompt,
    build_campaign_forensic_prompt,
    compute_campaign_correlations,
    get_ai_config,
    get_masked_ai_config,
    save_ai_config,
)
from dashboard.backend.services.notifications import (
    get_masked_config,
    get_notifications_config,
    save_notifications_config,
    TelegramNotifier,
    EmailNotifier,
)
from dashboard.backend.ws_manager import ws_manager

logger = logging.getLogger("dashboard.routes")
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class ReplayRequest(BaseModel):
    pcap_name: Optional[str] = None
    rate_per_sec: int = 25
    speed: Optional[float] = 1.0
    sensor_id: str = "lab-replay"


PCAP_METADATA = {
    "PortScan.pcap": {
        "title": "Scan de Ports Réseau (Nmap)",
        "category": "PortScan",
        "severity": "Medium",
        "description": "Balayage méthodique de ports TCP/UDP pour cartographier les services ouverts.",
    },
    "portscan(1).pcap": {
        "title": "Scan de Ports Réseau (Variante)",
        "category": "PortScan",
        "severity": "Medium",
        "description": "Balayage rapide de ports avec drapeaux TCP furtifs.",
    },
    "DDoS.pcap": {
        "title": "Attaque DDoS Volumétrique",
        "category": "DDoS",
        "severity": "Critical",
        "description": "Inondation distribuée de paquets ciblant la saturation de la bande passante.",
    },
    "DoS.pcap": {
        "title": "Déni de Service (DoS Applicatif)",
        "category": "DoS",
        "severity": "High",
        "description": "Épuisement des connexions du serveur web par requêtes lentes et incomplètes.",
    },
    "dos(1).pcap": {
        "title": "Déni de Service (Variante)",
        "category": "DoS",
        "severity": "High",
        "description": "Attaque DoS ciblée contre les services applicatifs.",
    },
    "Bot.pcap": {
        "title": "Trafic de Botnet (C2)",
        "category": "Bot",
        "severity": "Critical",
        "description": "Canal de commande et contrôle chiffré et exfiltration de données.",
    },
    "BruteForce.pcap": {
        "title": "Force Brute Authentification",
        "category": "BruteForce",
        "severity": "High",
        "description": "Tentatives massives de connexion par dictionnaire (SSH / FTP Patator).",
    },
    "WebAttack.pcap": {
        "title": "Attaques Applicatives Web",
        "category": "WebAttack",
        "severity": "High",
        "description": "Tentatives d'injection SQL, Cross-Site Scripting (XSS) et directory traversal.",
    },
    "normal.pcap": {
        "title": "Trafic Nominal Bénin",
        "category": "BENIGN",
        "severity": "Info",
        "description": "Trafic bureautique légitime (navigation web HTTPS, DNS, requêtes API standard).",
    },
    "Normal_dell.pcap": {
        "title": "Trafic d'Entreprise Nominal",
        "category": "BENIGN",
        "severity": "Info",
        "description": "Activité réseau standard d'un poste de travail bureautique.",
    },
}


def _get_pcap_list() -> List[Dict[str, Any]]:
    if not PCAP_DIR.exists():
        return []
    pcaps = []
    for f in sorted(PCAP_DIR.glob("*.pcap")):
        try:
            size_mb = round(f.stat().st_size / (1024 * 1024), 2)
        except Exception:
            size_mb = 0.0
        meta = PCAP_METADATA.get(
            f.name,
            {
                "title": f.stem,
                "category": "Inconnu",
                "severity": "Medium",
                "description": "Fichier de capture réseau PCAP.",
            },
        )
        pcaps.append(
            {
                "filename": f.name,
                "size_mb": size_mb,
                "title": meta["title"],
                "category": meta["category"],
                "severity": meta["severity"],
                "description": meta["description"],
            }
        )
    return pcaps


def _format_kpis(kpis: Dict[str, Any]) -> Dict[str, Any]:
    """Assure la compatibilité des clés entre le frontend et le backend."""
    total = kpis.get("total_flows", 0)
    attacks = kpis.get("confirmed_attacks", 0)
    anomalies = kpis.get("zero_day_anomalies", 0)
    rate = kpis.get("rate_flows_sec", 0.0)
    benign_pct = kpis.get("benign_pct", 100.0)
    malicious_pct = kpis.get("malicious_pct", 0.0)
    current_mse = kpis.get("current_mse", 0.0)

    return {
        "total_flows": total,
        "confirmed_attacks": attacks,
        "attacks": attacks,
        "zero_day_anomalies": anomalies,
        "anomalies": anomalies,
        "rate_flows_sec": rate,
        "flow_rate_sec": rate,
        "bandwidth_mbps": round(rate * 0.0035, 1),
        "benign_pct": benign_pct,
        "malicious_pct": malicious_pct,
        "attack_pct": malicious_pct,
        "current_mse": current_mse,
    }


def _format_distribution(dist: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not dist:
        return []
    out = []
    tot = sum(d.get("count", 0) for d in dist) or 1
    for d in dist:
        label = d.get("label") or d.get("name") or "Attack"
        cnt = d.get("count", 0)
        out.append({
            "label": label,
            "name": label,
            "count": cnt,
            "pct": d.get("pct", round(cnt / tot * 100, 1)),
            "color": d.get("color", "var(--ac)"),
        })
    return out


def _format_threat_vectors(tv: Dict[str, Any]) -> Dict[str, Any]:
    top_ips = tv.get("top_ips", [])
    top_ports = tv.get("top_ports", [])
    return {
        "top_ips": top_ips,
        "top_source_ips": top_ips,
        "top_ports": top_ports,
        "top_dest_ports": top_ports,
    }


def _enrich_alert(alert: Dict[str, Any]) -> Dict[str, Any]:
    a = dict(alert)
    pred = a.get("pred", "BENIGN")
    anom = a.get("anomalie_ae", 0)
    if pred in ("DDoS", "Bot"):
        sev = "Critical"
    elif pred.startswith("DoS") or pred == "WebAttack" or (anom == 1 and pred != "BENIGN"):
        sev = "High"
    elif anom == 1 and pred == "BENIGN":
        sev = "High"
    elif "Patator" in pred or pred == "PortScan":
        sev = "Medium"
    elif pred == "BENIGN" and anom == 0:
        sev = "Benign"
    else:
        sev = "Low"
    a["severity"] = sev
    return a


def _get_baseline_alerts() -> List[Dict[str, Any]]:
    """Génère un flux d'alerte de démonstration réaliste lorsque la base est vide."""
    return [
        {
            "id": 1,
            "received_at": "11:48:12",
            "sensor_id": "sensor-edge-01",
            "src_ip": "185.220.101.5",
            "src_port": 44120,
            "dst_ip": "10.0.1.50",
            "dst_port": 80,
            "protocol": 6,
            "pred": "DDoS",
            "confiance": 0.994,
            "mse_ae": 0.342,
            "anomalie_ae": 0,
            "severity": "Critical",
        },
        {
            "id": 2,
            "received_at": "11:47:55",
            "sensor_id": "sensor-dmz-01",
            "src_ip": "45.154.255.89",
            "src_port": 51240,
            "dst_ip": "10.0.2.14",
            "dst_port": 22,
            "protocol": 6,
            "pred": "SSH-Patator",
            "confiance": 0.978,
            "mse_ae": 0.281,
            "anomalie_ae": 0,
            "severity": "Medium",
        },
        {
            "id": 3,
            "received_at": "11:47:30",
            "sensor_id": "sensor-edge-02",
            "src_ip": "194.26.29.112",
            "src_port": 39812,
            "dst_ip": "10.0.1.99",
            "dst_port": 443,
            "protocol": 6,
            "pred": "BENIGN",
            "confiance": 0.621,
            "mse_ae": 0.748,
            "anomalie_ae": 1,
            "severity": "High",
        },
        {
            "id": 4,
            "received_at": "11:46:18",
            "sensor_id": "sensor-edge-01",
            "src_ip": "91.240.118.44",
            "src_port": 48102,
            "dst_ip": "10.0.1.22",
            "dst_port": 8080,
            "protocol": 6,
            "pred": "WebAttack",
            "confiance": 0.965,
            "mse_ae": 0.412,
            "anomalie_ae": 0,
            "severity": "High",
        },
        {
            "id": 5,
            "received_at": "11:45:02",
            "sensor_id": "sensor-core-01",
            "src_ip": "103.145.13.2",
            "src_port": 60124,
            "dst_ip": "10.0.0.8",
            "dst_port": 80,
            "protocol": 6,
            "pred": "DoS-Hulk",
            "confiance": 0.989,
            "mse_ae": 0.395,
            "anomalie_ae": 0,
            "severity": "High",
        },
    ]


@router.get("/init")
def get_initial_dashboard_state(time_range: str = Query("15m")):
    """Fournit l'état complet initial du tableau de bord au chargement de la page."""
    kpis = _format_kpis(get_kpis())
    dist = _format_distribution(get_attack_distribution())
    tv = _format_threat_vectors(get_threat_vectors(limit=5))
    alerts_raw = get_recent_alerts(limit=150, offset=0)
    alerts = [_enrich_alert(a) for a in alerts_raw]
    total_alerts_count = get_total_alerts_count()
    recent_incidents = get_incidents(limit=50, offset=0)
    incidents_summary = get_incidents_summary()
    total_incidents_count = get_total_incidents_count()
    pcaps = _get_pcap_list()
    model_classes_info = get_model_classes()

    return {
        "kpis": kpis,
        "distribution": dist,
        "attack_distribution": dist,
        "timeline": get_timeline(window_seconds=900, buckets=60),
        "threat_vectors": tv,
        "recent_alerts": alerts,
        "total_alerts_count": total_alerts_count,
        "recent_incidents": recent_incidents,
        "incidents_summary": incidents_summary,
        "total_incidents_count": total_incidents_count,
        "sensors": get_active_sensors(),
        "pcap_files": pcaps,
        "replay_status": replay_service.get_status(),
        "ae_threshold": AE_THRESHOLD,
        "system_health": health_service.get_health_status(),
        "time_range": time_range,
        "model_classes": model_classes_info.get("classes", []),
        "attack_categories": model_classes_info.get("all_categories", []),
        "model_meta": model_classes_info,
    }


@router.get("/stats")
def get_stats():
    """Retourne les métriques clés et la distribution actuelle."""
    kpis = _format_kpis(get_kpis())
    dist = _format_distribution(get_attack_distribution())
    tv = _format_threat_vectors(get_threat_vectors(limit=5))
    return {
        "kpis": kpis,
        "distribution": dist,
        "attack_distribution": dist,
        "threat_vectors": tv,
    }


@router.get("/alerts")
def get_alerts(
    response: Response,
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    search_ip: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    min_conf: float = Query(0.0, ge=0.0, le=100.0),
    anomalies_only: bool = Query(False),
):
    """Retourne la liste filtrée et paginée des alertes depuis la base SQLite."""
    total = get_total_alerts_count(
        search_ip=search_ip,
        category=category,
        min_conf=min_conf,
        anomalies_only=anomalies_only,
    )
    raw = get_recent_alerts(
        limit=limit,
        offset=offset,
        search_ip=search_ip,
        category=category,
        min_conf=min_conf,
        anomalies_only=anomalies_only,
    )
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Limit"] = str(limit)
    response.headers["X-Offset"] = str(offset)

    if not raw and offset == 0 and not search_ip and not category and min_conf == 0.0:
        return _get_baseline_alerts()
    return [_enrich_alert(a) for a in raw]


@router.get("/incidents")
def get_incidents_route(
    response: Response,
    status: Optional[str] = Query("ALL"),
    severity: Optional[str] = Query(None),
    search_ip: Optional[str] = Query(None),
    attack_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Retourne la liste filtrée et paginée des incidents de sécurité corrélés."""
    total = get_total_incidents_count(
        status=status,
        severity=severity,
        search_ip=search_ip,
        attack_type=attack_type,
    )
    incidents = get_incidents(
        status=status,
        severity=severity,
        search_ip=search_ip,
        attack_type=attack_type,
        limit=limit,
        offset=offset,
    )
    summary = get_incidents_summary()
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Open-Count"] = str(summary.get("open", 0))
    response.headers["X-Closed-Count"] = str(summary.get("closed", 0))
    return incidents


@router.get("/incidents/summary")
def get_incidents_summary_route():
    """Retourne la synthèse globale des incidents (total, en cours, clos, critiques)."""
    return get_incidents_summary()


@router.get("/incidents/{incident_id}/flows")
def get_incident_flows_route(
    incident_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Retourne les flux réseau individuels constitutifs d'un incident corrélé."""
    return get_incident_flows(incident_id=incident_id, limit=limit, offset=offset)


@router.get("/sensors")
def list_sensors():
    """Liste les sondes réseau réelles enregistrées en base SQLite."""
    sensors = get_active_sensors()
    return {
        "sensors": sensors,
        "total": len(sensors),
        "online_count": sum(1 for s in sensors if s["status"] == "Online"),
    }


@router.get("/pcaps")
def list_pcaps():
    """Liste les fichiers PCAP disponibles pour le rejeu."""
    pcaps = _get_pcap_list()
    # Retourne à la fois la liste simple de noms et la liste d'objets avec métadonnées
    return {
        "pcaps": [p["filename"] for p in pcaps],
        "pcap_files": pcaps,
    }


@router.post("/replay/start")
async def start_replay(
    request: Request,
    pcap_name: Optional[str] = Query(None),
    speed: Optional[float] = Query(1.0),
):
    """Démarre le rejeu d'un fichier PCAP (supporte JSON body ou Query parameters)."""
    # Tenter de lire le body JSON si présent
    body_data = {}
    try:
        body_data = await request.json()
    except Exception:
        pass

    target_name = body_data.get("pcap_name") or pcap_name
    target_speed = float(body_data.get("speed") or speed or 1.0)
    sensor_id = body_data.get("sensor_id") or "lab-replay"

    if not target_name:
        return {"error": "Paramètre pcap_name obligatoire"}

    rate_per_sec = int(25 * target_speed)

    return await replay_service.start_replay(
        pcap_name=target_name,
        rate_per_sec=rate_per_sec,
        sensor_id=sensor_id,
    )


@router.post("/replay/pause")
def pause_replay():
    return replay_service.pause_replay()


@router.post("/replay/resume")
def resume_replay():
    return replay_service.resume_replay()


@router.post("/replay/stop")
def stop_replay():
    return replay_service.stop_replay()


@router.get("/replay/status")
def replay_status():
    return replay_service.get_status()


class SettingsUpdateRequest(BaseModel):
    ae_threshold: Optional[float] = None
    min_confidence: Optional[float] = None


class NotificationsUpdateRequest(BaseModel):
    telegram_enabled: Optional[bool] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    email_enabled: Optional[bool] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: Optional[bool] = None
    email_from: Optional[str] = None
    email_to: Optional[str] = None
    notify_critical_only: Optional[bool] = None
    notify_zero_day: Optional[bool] = None
    notify_traffic_burst: Optional[bool] = None


class TelegramTestRequest(BaseModel):
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None


class EmailTestRequest(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: Optional[bool] = None
    email_from: Optional[str] = None
    email_to: Optional[str] = None


class FeedbackSubmissionRequest(BaseModel):
    human_verdict: str  # 'FALSE_POSITIVE', 'KNOWN_ATTACK', 'CONFIRMED_ZERODAY'
    corrected_attack_type: Optional[str] = None
    analyst_notes: Optional[str] = None
    flow_data: Optional[Dict[str, Any]] = None


class BatchFeedbackSubmissionRequest(BaseModel):
    incident_ids: List[str]
    human_verdict: str  # 'FALSE_POSITIVE', 'KNOWN_ATTACK', 'CONFIRMED_ZERODAY'
    corrected_attack_type: Optional[str] = None
    analyst_notes: Optional[str] = None
    flows: Optional[List[Dict[str, Any]]] = None


class BatchAnalysisRequest(BaseModel):
    flows: List[Dict[str, Any]]


class BatchPromptRequest(BaseModel):
    flows: List[Dict[str, Any]]


class AiSettingsUpdateRequest(BaseModel):
    provider: Optional[str] = None
    ollama_url: Optional[str] = None
    ollama_model: Optional[str] = None
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None


class AiAnalysisRequest(BaseModel):
    flow: Optional[Dict[str, Any]] = None


@router.post("/database/reset")
async def reset_db_endpoint():
    """Réinitialise la base de données (supprime tous les flux enregistrés) et notifie les clients."""
    replay_service.stop_replay()
    res = reset_database()
    reset_event = {
        "type": "database_reset",
        "kpis": _format_kpis(get_kpis()),
        "distribution": _format_distribution(get_attack_distribution()),
        "timeline": get_timeline(),
        "threat_vectors": _format_threat_vectors(get_threat_vectors()),
        "recent_alerts": [],
        "ae_threshold": AE_THRESHOLD,
    }
    await ws_manager.broadcast(reset_event)
    return res


@router.post("/settings")
async def update_settings_endpoint(req: SettingsUpdateRequest):
    """Met à jour les paramètres opérationnels et le seuil de détection."""
    import dashboard.backend.config as cfg
    if req.ae_threshold is not None:
        cfg.AE_THRESHOLD = float(req.ae_threshold)
    return {
        "status": "success",
        "ae_threshold": cfg.AE_THRESHOLD,
        "min_confidence": req.min_confidence,
    }


@router.get("/settings/notifications")
def get_notifications_settings():
    """Récupère la configuration des notifications (avec secrets masqués)."""
    return get_masked_config()


@router.post("/settings/notifications")
def update_notifications_settings(req: NotificationsUpdateRequest):
    """Enregistre les paramètres d'alerte Telegram et Email."""
    data = req.model_dump(exclude_unset=True) if hasattr(req, "model_dump") else req.dict(exclude_unset=True)
    save_notifications_config(data)
    health_service.record_log("notifications", "Paramètres de notification mis à jour", "INFO")
    return {
        "status": "success",
        "config": get_masked_config(),
    }


@router.post("/notifications/test-telegram")
async def test_telegram_endpoint(req: TelegramTestRequest):
    """Teste la connexion et l'envoi d'alerte Telegram."""
    cfg = get_notifications_config()
    token = req.bot_token or cfg.telegram_bot_token
    chat = req.chat_id or cfg.telegram_chat_id
    if not token or not chat:
        return {"success": False, "message": "Bot token et Chat ID requis pour le test"}
    success, msg = await TelegramNotifier.send_test(token, chat)
    health_service.record_log("notifications", f"Test Telegram: {msg}", "INFO" if success else "WARN")
    return {"success": success, "message": msg}


@router.post("/notifications/test-email")
async def test_email_endpoint(req: EmailTestRequest):
    """Teste la connexion et l'envoi d'email SMTP."""
    cfg = get_notifications_config()
    test_cfg = type(
        "TestCfg",
        (),
        {
            "smtp_host": req.smtp_host or cfg.smtp_host,
            "smtp_port": req.smtp_port or cfg.smtp_port,
            "smtp_user": req.smtp_user if req.smtp_user is not None else cfg.smtp_user,
            "smtp_password": req.smtp_password if req.smtp_password is not None else cfg.smtp_password,
            "smtp_use_tls": req.smtp_use_tls if req.smtp_use_tls is not None else cfg.smtp_use_tls,
            "email_from": req.email_from or cfg.email_from,
            "email_to": req.email_to or cfg.email_to,
        },
    )()
    if not test_cfg.smtp_host or not test_cfg.email_from or not test_cfg.email_to:
        return {"success": False, "message": "Hôte SMTP, expéditeur et destinataire requis"}
    success, msg = await EmailNotifier.send_test(test_cfg)
    health_service.record_log("notifications", f"Test Email: {msg}", "INFO" if success else "WARN")
    return {"success": success, "message": msg}


@router.post("/incidents/{incident_id}/feedback")
async def record_incident_feedback(incident_id: str, req: FeedbackSubmissionRequest):
    """Enregistre la qualification humaine (Human-in-the-Loop) d'un incident."""
    res = record_feedback(
        incident_id=incident_id,
        human_verdict=req.human_verdict,
        corrected_attack_type=req.corrected_attack_type,
        analyst_notes=req.analyst_notes,
        flow_data=req.flow_data,
    )
    health_service.record_log(
        "active_learning",
        f"Incident {incident_id} qualifié par analyste : {req.human_verdict}"
        + (f" ({req.corrected_attack_type})" if req.corrected_attack_type else ""),
        "INFO",
    )
    await ws_manager.broadcast({
        "type": "incident_feedback",
        "incident_id": incident_id,
        "human_verdict": req.human_verdict,
        "corrected_attack_type": req.corrected_attack_type,
    })
    return res


@router.get("/incidents/{incident_id}/feedback")
def get_incident_feedback(incident_id: str):
    """Récupère la qualification humaine existante pour un incident donné."""
    fb = get_feedback(incident_id)
    return {"incident_id": incident_id, "feedback": fb}


@router.get("/feedback/summary")
def get_feedback_summary_endpoint():
    """Retourne la synthèse des qualifications Active Learning."""
    return get_feedback_summary()


@router.get("/feedback/export")
def export_feedback_endpoint(
    format: str = Query("json", pattern="^(json|csv)$"),
    download: bool = Query(False),
):
    """Télécharge le jeu de données qualifié au format JSON ou CSV prêt pour l'entraînement."""
    data = export_feedback_dataset()
    if format == "csv":
        import io
        import csv
        from fastapi.responses import Response

        output = io.StringIO()
        if data:
            keys = [
                "id", "incident_id", "timestamp", "src_ip", "dst_ip",
                "src_port", "dst_port", "protocol", "model_predicted_label",
                "model_mse_score", "human_verdict", "corrected_attack_type",
                "label", "analyst_verdict", "analyst_notes", "status"
            ]
            first_item = data[0] if data else {}
            extra_keys = [k for k in first_item.keys() if k not in keys and k != "raw_features"]
            all_csv_keys = keys + extra_keys
            writer = csv.DictWriter(output, fieldnames=all_csv_keys, extrasaction="ignore")
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        csv_bytes = output.getvalue().encode("utf-8")
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=feedback_flows.csv"},
        )
    if download:
        import json
        from fastapi.responses import Response
        json_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        return Response(
            content=json_bytes,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=feedback_flows.json"},
        )
    return {"count": len(data), "dataset": data}


@router.post("/incidents/{incident_id}/ai-analysis")
async def analyze_incident_ai(incident_id: str, req: AiAnalysisRequest):
    """Analyse un incident via l'Assistant IA (Ollama / Gemini / Moteur Expert)."""
    flow = req.flow or {"id": incident_id}
    res = await AiAnalyzerService.analyze_incident(flow)
    health_service.record_log(
        "ai_assistant",
        f"Analyse IA générée pour incident {incident_id} via {res.get('provider', 'IA')}",
        "INFO" if res.get("success") else "WARN",
    )
    return res


@router.post("/incidents/batch-analysis")
async def analyze_batch_incidents_ai(req: BatchAnalysisRequest):
    """Analyse un lot de télémétries sélectionnées (ex: tous les Zero-Days) pour détecter des patterns de campagne."""
    if not req.flows:
        return {"success": False, "error": "Aucun flux fourni pour l'analyse de campagne"}
    res = await AiAnalyzerService.analyze_campaign(req.flows)
    health_service.record_log(
        "ai_assistant",
        f"Analyse de campagne ({len(req.flows)} flux) exécutée via {res.get('provider', 'IA')} : {res.get('campaign_type')}",
        "INFO" if res.get("success") else "WARN",
    )
    return res


@router.post("/incidents/batch-feedback")
async def record_batch_incident_feedback(req: BatchFeedbackSubmissionRequest):
    """Enregistre la qualification humaine en masse (Active Learning) pour un lot de flux."""
    if not req.incident_ids:
        return {"success": False, "error": "Aucun identifiant d'incident fourni"}

    flows_map = {}
    if req.flows:
        for f in req.flows:
            fid = str(f.get("id", f.get("incident_id", "")))
            if fid:
                flows_map[fid] = f

    res = record_batch_feedback(
        incident_ids=req.incident_ids,
        human_verdict=req.human_verdict,
        corrected_attack_type=req.corrected_attack_type,
        analyst_notes=req.analyst_notes,
        flows_map=flows_map,
    )

    health_service.record_log(
        "active_learning",
        f"Qualification groupée de {len(req.incident_ids)} flux par analyste : {req.human_verdict}"
        + (f" ({req.corrected_attack_type})" if req.corrected_attack_type else ""),
        "INFO",
    )

    await ws_manager.broadcast({
        "type": "batch_incident_feedback",
        "incident_ids": req.incident_ids,
        "human_verdict": req.human_verdict,
        "corrected_attack_type": req.corrected_attack_type,
    })

    return res


@router.post("/incidents/campaign-prompt")
def generate_campaign_prompt_endpoint(req: BatchPromptRequest):
    """Génère le prompt forensique d'analyse de pattern et les statistiques de corrélation."""
    if not req.flows:
        return {"success": False, "error": "Aucun flux fourni"}
    prompt = build_campaign_forensic_prompt(req.flows)
    corr = compute_campaign_correlations(req.flows)
    return {
        "success": True,
        "prompt": prompt,
        "correlation_summary": corr,
    }


@router.get("/settings/ai")
def get_ai_settings():
    """Récupère les paramètres de l'Assistant IA (avec clé API masquée)."""
    return get_masked_ai_config()


@router.post("/settings/ai")
def update_ai_settings(req: AiSettingsUpdateRequest):
    """Enregistre la configuration du fournisseur IA (Ollama, Gemini, Expert)."""
    data = req.model_dump(exclude_unset=True) if hasattr(req, "model_dump") else req.dict(exclude_unset=True)
    saved = save_ai_config(data)
    health_service.record_log("ai_assistant", f"Configuration IA mise à jour: {saved.get('provider')}", "INFO")
    return {
        "status": "success",
        "config": get_masked_ai_config(),
    }


@router.post("/ai/test")
async def test_ai_connection_endpoint(req: AiSettingsUpdateRequest):
    """Teste la connectivité du fournisseur IA (Ollama / Gemini)."""
    cfg = get_ai_config()
    test_cfg = {**cfg, **req.model_dump(exclude_unset=True)}
    success, msg = await AiAnalyzerService.test_connection(test_cfg)
    return {"success": success, "message": msg}


@router.get("/models/logs")
def get_model_logs(limit: int = 100):
    """Retourne les derniers événements d'inférence du modèle."""
    return {
        "logs": get_recent_logs(limit=limit),
        "log_file": str(MODEL_LOG_FILE),
    }


@router.post("/models/logs/clear")
def clear_model_logs():
    """Efface les logs du modèle en mémoire et sur disque."""
    success = clear_logs()
    return {"status": "cleared" if success else "error"}


@router.get("/models/logs/raw")
def get_raw_model_log():
    """Télécharge le fichier brut .log."""
    from fastapi.responses import PlainTextResponse
    if MODEL_LOG_FILE.exists():
        content = MODEL_LOG_FILE.read_text(encoding="utf-8", errors="ignore")
    else:
        content = ""
    return PlainTextResponse(content)


@router.get("/models/classes")
def get_model_classes_endpoint():
    """Retourne dynamiquement les classes définies par le modèle actif et observées en base."""
    return get_model_classes()


@router.get("/system/health")
def get_system_health():
    """Diagnostic consolidé de santé système (pannes infrastructure vs sécurité)."""
    return health_service.get_health_status()


@router.get("/system/logs")
def get_system_logs(limit: int = 50, level: Optional[str] = None):
    """Logs techniques d'infrastructure et d'erreurs système."""
    return health_service.get_system_logs(limit=limit, level=level)


@router.post("/system/optimize-db")
def optimize_database():
    """Optimisation et purge du journal WAL SQLite."""
    return health_service.optimize_database()


@router.post("/system/test-component")
def test_system_component(request: Dict[str, Any]):
    """Teste la réactivité d'un composant système individuel."""
    import time
    comp = request.get("component", "all")
    start = time.perf_counter()
    if comp == "database":
        res = health_service._check_database()
    elif comp == "ai_engine":
        res = health_service._check_ai_engine()
    elif comp == "sensors":
        res = health_service._check_sensors()
    elif comp == "websocket":
        res = health_service._check_websocket()
    else:
        res = health_service.get_health_status()
    latency_ms = round((time.perf_counter() - start) * 1000, 2)
    return {"component": comp, "result": res, "latency_ms": latency_ms}


async def websocket_endpoint(websocket: WebSocket):
    """Canal WebSocket temps réel pour pousser les alertes et les métriques sans recharger la page."""
    await ws_manager.connect(websocket)
    try:
        model_classes_info = get_model_classes()
        init_data = {
            "type": "init",
            "kpis": _format_kpis(get_kpis()),
            "distribution": _format_distribution(get_attack_distribution()),
            "timeline": get_timeline(),
            "threat_vectors": _format_threat_vectors(get_threat_vectors()),
            "recent_alerts": [_enrich_alert(a) for a in get_recent_alerts(limit=30)],
            "recent_model_logs": get_recent_logs(limit=50),
            "replay_status": replay_service.get_status(),
            "ae_threshold": AE_THRESHOLD,
            "system_health": health_service.get_health_status(),
            "model_classes": model_classes_info.get("classes", []),
            "attack_categories": model_classes_info.get("all_categories", []),
            "model_meta": model_classes_info,
        }
        await ws_manager.send_personal_message(init_data, websocket)

        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"Erreur WebSocket: {e}")
        ws_manager.disconnect(websocket)
