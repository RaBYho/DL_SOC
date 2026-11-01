import asyncio
import os
from pathlib import Path
import sqlite3
import time
from fastapi import FastAPI, Header, HTTPException
import pandas as pd
from pydantic import BaseModel
from nids_core import Scorer

from dashboard.backend import database as db_mod
from dashboard.backend.formatters import (
    format_distribution,
    format_kpis,
    format_threat_vectors,
)
from dashboard.backend.routes import router as dashboard_router, websocket_endpoint
from dashboard.backend.services.health_service import health_service
from dashboard.backend.services.notifications import notification_dispatcher
from dashboard.backend.ws_manager import ws_manager

DEFAULT_BASE = str(Path(__file__).resolve().parent)
BASE = os.environ.get("NIDS_BASE", DEFAULT_BASE)
DB = os.environ.get("NIDS_DB", str(Path(BASE) / "nids.db"))
API_KEY = os.environ.get("NIDS_API_KEY", "dev-secret-key")

# Initialisation du modèle et de la base avec indexation
scorer = Scorer(BASE)
app = FastAPI(title="DL_SOC NIDS Server", version="1.2.0")

# Inclusion des routes du Dashboard et du canal WebSocket
app.include_router(dashboard_router)
app.add_api_websocket_route("/ws", websocket_endpoint)


async def periodic_health_worker():
    """Diffuse l'état de santé système toutes les 10s aux analystes connectés."""
    while True:
        try:
            await asyncio.sleep(10.0)
            if ws_manager.active_connections:
                await ws_manager.broadcast({
                    "type": "system_health",
                    "system_health": health_service.get_health_status(),
                })
        except asyncio.CancelledError:
            break
        except Exception as e:
            pass


@app.on_event("startup")
async def on_startup():
    notification_dispatcher.start_digest_worker()
    asyncio.create_task(periodic_health_worker())
    asyncio.create_task(periodic_incident_worker())


async def periodic_incident_worker():
    """Vérifie et clôture périodiquement les incidents inactifs (> 45s de silence)."""
    while True:
        try:
            await asyncio.sleep(10.0)
            closed = db_mod.close_inactive_incidents(inactivity_seconds=45.0, db_path=DB)
            if closed:
                for inc in closed:
                    if not inc.get("notified_close"):
                        asyncio.create_task(notification_dispatcher.notify_incident_closed(inc))
                        db_mod.mark_incident_notified(inc["id"], close_notified=True, db_path=DB)
                if ws_manager.active_connections:
                    await ws_manager.broadcast({
                        "type": "incidents_closed",
                        "closed_incidents": closed,
                        "incidents_summary": db_mod.get_incidents_summary(DB),
                    })
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Erreur dans le worker périodique d'incidents: {e}")


class Batch(BaseModel):
    sensor_id: str
    flows: list[dict]


def db():
    db_mod.init_db(DB)
    return db_mod.get_connection(DB)


@app.get("/health")
def health():
    return {
        "ok": True,
        "classes": scorer.classes,
        "ae_enabled": scorer.has_ae,
        "ae_threshold": scorer.ae_seuil,
    }


@app.get("/api/system/health")
def system_health_alias():
    return health_service.get_health_status()


@app.post("/ingest")
async def ingest(batch: Batch, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="clé invalide")
    if not batch.flows:
        return {"received": 0, "alerts": 0, "anomalies": 0, "preds": []}

    df = pd.DataFrame(batch.flows)
    try:
        df[scorer.feature_cols] = df[scorer.feature_cols].apply(
            pd.to_numeric, errors="raise"
        )
        t_start = time.perf_counter()
        res = scorer.predict_df(df)
        inf_latency_ms = (time.perf_counter() - t_start) * 1000.0
        health_service.record_inference_latency(inf_latency_ms)
    except (ValueError, KeyError) as e:
        health_service.log_system_event("ERROR", "AI-Engine", f"Échec d'inférence lot: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    now = time.time()
    has_ae = "anomalie_ae" in res.columns
    mse_vals = res["mse_ae"] if has_ae else [None] * len(res)
    anom_vals = res["anomalie_ae"] if has_ae else [0] * len(res)

    corr_res = db_mod.insert_and_correlate_flows(
        flow_records=batch.flows,
        predictions=res["pred"].tolist(),
        confidences=res["confiance"].tolist(),
        mse_values=mse_vals.tolist() if hasattr(mse_vals, "tolist") else list(mse_vals),
        anomaly_values=anom_vals.tolist() if hasattr(anom_vals, "tolist") else list(anom_vals),
        sensor_id=batch.sensor_id,
        received_at=now,
        inactivity_window=45.0,
        db_path=DB,
    )

    alert_rows = corr_res["alert_rows"]
    alerts_count = corr_res["alerts_count"]
    anomalies_count = corr_res["anomalies_count"]

    # Notification immédiate pour chaque nouvel incident ouvert (Anti-Fatigue)
    for new_inc in corr_res.get("new_incidents", []):
        asyncio.create_task(notification_dispatcher.notify_incident_opened(new_inc))
        db_mod.mark_incident_notified(new_inc["id"], open_notified=True, db_path=DB)

    # Notification en temps réel sur le canal WebSocket du Dashboard
    if ws_manager.active_connections:
        raw_kpis = db_mod.get_kpis(DB)
        raw_dist = db_mod.get_attack_distribution(DB)
        raw_tv = db_mod.get_threat_vectors(limit=5, db_path=DB)
        raw_tl = db_mod.get_timeline(window_seconds=900, buckets=60, db_path=DB)
        recent_incidents = db_mod.get_incidents(limit=25, db_path=DB)
        incidents_summary = db_mod.get_incidents_summary(DB)

        asyncio.create_task(
            ws_manager.broadcast(
                {
                    "type": "new_flows",
                    "received": len(df),
                    "alerts_count": alerts_count,
                    "anomalies_count": anomalies_count,
                    "recent_alerts": alert_rows,
                    "recent_incidents": recent_incidents,
                    "incidents_summary": incidents_summary,
                    "kpis": format_kpis(raw_kpis),
                    "distribution": format_distribution(raw_dist),
                    "timeline": raw_tl,
                    "threat_vectors": format_threat_vectors(raw_tv),
                }
            )
        )

    return {
        "received": len(df),
        "alerts": alerts_count,
        "anomalies": anomalies_count,
        "preds": res["pred"].tolist(),
    }


@app.get("/stats")
def stats(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="clé invalide")
    con = db()
    out = dict(
        con.execute(
            "SELECT pred, COUNT(*) FROM flows GROUP BY pred"
        ).fetchall()
    )
    con.close()
    return out


@app.get("/stats/anomalies")
def stats_anomalies(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="clé invalide")
    con = db()
    total_anomalies = con.execute(
        "SELECT COUNT(*) FROM flows WHERE anomalie_ae = 1"
    ).fetchone()[0]
    total_flows = con.execute("SELECT COUNT(*) FROM flows").fetchone()[0]
    con.close()
    return {"total_flows": total_flows, "anomalies": total_anomalies}


# Montage des fichiers statiques du Dashboard (SPA Vue 3)
DIST_DIR = Path(BASE) / "dashboard" / "dist"
if DIST_DIR.is_dir():
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    assets_dir = DIST_DIR / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="spa_assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        target = DIST_DIR / full_path
        if full_path and target.is_file():
            return FileResponse(target)
        index_file = DIST_DIR / "index.html"
        if index_file.is_file():
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Dashboard non trouvé")

