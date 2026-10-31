import os
from pathlib import Path
import sqlite3
import time
from fastapi import FastAPI, Header, HTTPException
import pandas as pd
from pydantic import BaseModel
from nids_core import Scorer

DEFAULT_BASE = str(Path(__file__).resolve().parent)
BASE = os.environ.get("NIDS_BASE", DEFAULT_BASE)
DB = os.environ.get("NIDS_DB", str(Path(BASE) / "nids.db"))
API_KEY = os.environ.get("NIDS_API_KEY", "dev-secret-key")

scorer = Scorer(BASE)
app = FastAPI(title="DL_SOC NIDS Server", version="1.1.0")


class Batch(BaseModel):
    sensor_id: str
    flows: list[dict]


def db():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS flows (
        id INTEGER PRIMARY KEY AUTOINCREMENT, received_at REAL, sensor_id TEXT,
        flow_start_ms REAL, src_ip TEXT, src_mac TEXT, src_port INTEGER,
        dst_ip TEXT, dst_port INTEGER, protocol INTEGER, pred TEXT, confiance REAL,
        mse_ae REAL, anomalie_ae INTEGER)""")

    # Migration à chaud si les colonnes de l'auto-encodeur n'existent pas encore
    cols = [r[1] for r in con.execute("PRAGMA table_info(flows)").fetchall()]
    if "mse_ae" not in cols:
        con.execute("ALTER TABLE flows ADD COLUMN mse_ae REAL")
    if "anomalie_ae" not in cols:
        con.execute("ALTER TABLE flows ADD COLUMN anomalie_ae INTEGER")

    return con


@app.get("/health")
def health():
    return {
        "ok": True,
        "classes": scorer.classes,
        "ae_enabled": scorer.has_ae,
        "ae_threshold": scorer.ae_seuil,
    }


@app.post("/ingest")
def ingest(batch: Batch, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="clé invalide")
    if not batch.flows:
        return {"received": 0, "alerts": 0, "anomalies": 0, "preds": []}

    df = pd.DataFrame(batch.flows)
    try:
        df[scorer.feature_cols] = df[scorer.feature_cols].apply(pd.to_numeric, errors="raise")
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
    return {
        "received": len(df),
        "alerts": int((res["pred"] != "BENIGN").sum()),
        "anomalies": anomalies_count,
        "preds": res["pred"].tolist(),
    }


@app.get("/stats")
def stats(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="clé invalide")
    con = db()
    out = dict(con.execute("SELECT pred, COUNT(*) FROM flows GROUP BY pred").fetchall())
    con.close()
    return out


@app.get("/stats/anomalies")
def stats_anomalies(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="clé invalide")
    con = db()
    total_anomalies = con.execute("SELECT COUNT(*) FROM flows WHERE anomalie_ae = 1").fetchone()[0]
    total_flows = con.execute("SELECT COUNT(*) FROM flows").fetchone()[0]
    con.close()
    return {"total_flows": total_flows, "anomalies": total_anomalies}
