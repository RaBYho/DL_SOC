import json, numpy as np, requests
from nfstream import NFStreamer

# Réglages d'extraction FIGÉS : identiques à l'entraînement
def extract(pcap):
    s = NFStreamer(source=pcap, statistical_analysis=True, n_dissections=0,
                   idle_timeout=120, active_timeout=1800, n_meters=0)
    return s.to_pandas()

def to_records(df, feature_cols):
    metadata_cols = ["bidirectional_first_seen_ms", "src_ip", "src_mac", "src_port", "dst_ip", "dst_port"]
    all_desired = list(dict.fromkeys(feature_cols + metadata_cols))
    available_cols = [c for c in all_desired if c in df.columns]
    d = df[available_cols].replace([np.inf, -np.inf], np.nan)       # inf -> NaN, le serveur met NaN -> 0
    return d.astype(object).where(d.notna(), None).to_dict("records")

def send(df, feature_cols, url, key, sensor_id="lab-replay", batch=500):
    preds = []
    recs = to_records(df, feature_cols)
    for i in range(0, len(recs), batch):
        body = json.dumps({"sensor_id": sensor_id, "flows": recs[i:i + batch]},
                          default=lambda o: o.item())
        r = requests.post(f"{url}/ingest", data=body,
                          headers={"x-api-key": key, "Content-Type": "application/json"}, timeout=60)
        r.raise_for_status()
        preds += r.json()["preds"]
    return preds
