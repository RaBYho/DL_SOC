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
from dashboard.backend.routes import router as dashboard_router, websocket_endpoint
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
        res = scorer.predict_df(df)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    now = time.time()
    has_ae = "anomalie_ae" in res.columns
    mse_vals = res["mse_ae"] if has_ae else [None] * len(res)
    anom_vals = res["anomalie_ae"] if has_ae else [0] * len(res)

    rows = [
        (
            now,
            batch.sensor_id,
            r.get("bidirectional_first_seen_ms"),
            r.get("src_ip"),
            r.get("src_mac"),
            r.get("src_port"),
            r.get("dst_ip"),
            r.get("dst_port"),
            r.get("protocol"),
            p,
            float(c),
            float(m) if m is not None else None,
            int(a) if a is not None else 0,
        )
        for r, p, c, m, a in zip(
            batch.flows, res["pred"], res["confiance"], mse_vals, anom_vals
        )
    ]

    con = db()
    with con:
        con.executemany(
            """INSERT INTO flows (received_at, sensor_id, flow_start_ms, src_ip, src_mac,
            src_port, dst_ip, dst_port, protocol, pred, confiance, mse_ae, anomalie_ae)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            rows,
        )
    con.close()

    anomalies_count = int(res["anomalie_ae"].sum()) if has_ae else 0
    alerts_count = int((res["pred"] != "BENIGN").sum())

    # Notification en temps réel sur le canal WebSocket du Dashboard
    if ws_manager.active_connections:
        severity_map = {
            "DDoS": "Critical",
            "Bot": "Critical",
            "DoS-Hulk": "High",
            "DoS-GoldenEye": "High",
            "DoS-slowloris": "High",
            "SSH-Patator": "High",
            "WebAttack": "High",
            "DoS-Slowhttptest": "Medium",
            "PortScan": "Medium",
            "FTP-Patator": "Medium",
            "Scan-Vista": "Low",
        }
        alert_rows = [
            {
                "timestamp": time.strftime("%H:%M:%S", time.localtime(now)),
                "sensor": batch.sensor_id,
                "src_ip": r.get("src_ip", "0.0.0.0"),
                "src_port": r.get("src_port", 0),
                "dst_ip": r.get("dst_ip", "0.0.0.0"),
                "dst_port": r.get("dst_port", 0),
                "protocol": "TCP" if r.get("protocol") == 6 else "UDP",
                "classification": p,
                "confidence": round(float(c) * 100.0, 1),
                "mse_ae": round(float(m), 3) if m is not None else 0.0,
                "is_anomaly": bool(a),
                "severity": severity_map.get(
                    p, "High" if bool(a) else "Medium"
                ),
            }
            for r, p, c, m, a in zip(
                batch.flows, res["pred"], res["confiance"], mse_vals, anom_vals
            )
            if p != "BENIGN" or (a and a == 1)
        ]
        asyncio.create_task(
            ws_manager.broadcast(
                {
                    "type": "new_flows",
                    "received": len(df),
                    "alerts_count": alerts_count,
                    "anomalies_count": anomalies_count,
                    "recent_alerts": alert_rows,
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
