import os, sqlite3, time
import pandas as pd
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from nids_core import Scorer

BASE = os.environ["NIDS_BASE"]
DB = os.environ.get("NIDS_DB", "/content/nids.db")
API_KEY = os.environ["NIDS_API_KEY"]

scorer = Scorer(BASE)
app = FastAPI()

class Batch(BaseModel):
    sensor_id: str
    flows: list[dict]

def db():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS flows (
        id INTEGER PRIMARY KEY AUTOINCREMENT, received_at REAL, sensor_id TEXT,
        flow_start_ms REAL, src_ip TEXT, src_mac TEXT, src_port INTEGER,
        dst_ip TEXT, dst_port INTEGER, protocol INTEGER, pred TEXT, confiance REAL)""")
    return con

@app.get("/health")
def health():
    return {"ok": True, "classes": scorer.classes}

@app.post("/ingest")
def ingest(batch: Batch, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="clé invalide")
    if not batch.flows:
        return {"received": 0, "alerts": 0, "preds": []}
    df = pd.DataFrame(batch.flows)
    try:
        df[scorer.feature_cols] = df[scorer.feature_cols].apply(pd.to_numeric, errors="raise")
        res = scorer.predict_df(df)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    now = time.time()
    rows = [(now, batch.sensor_id, r.get("bidirectional_first_seen_ms"), r.get("src_ip"),
             r.get("src_mac"), r.get("src_port"), r.get("dst_ip"), r.get("dst_port"),
             r.get("protocol"), p, float(c))
            for r, p, c in zip(batch.flows, res["pred"], res["confiance"])]
    con = db()
    with con:
        con.executemany("""INSERT INTO flows (received_at, sensor_id, flow_start_ms, src_ip, src_mac,
            src_port, dst_ip, dst_port, protocol, pred, confiance) VALUES (?,?,?,?,?,?,?,?,?,?,?)""", rows)
    con.close()
    return {"received": len(df), "alerts": int((res["pred"] != "BENIGN").sum()),
            "preds": res["pred"].tolist()}

@app.get("/stats")
def stats(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="clé invalide")
    con = db()
    out = dict(con.execute("SELECT pred, COUNT(*) FROM flows GROUP BY pred").fetchall())
    con.close()
    return out
