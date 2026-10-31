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


if __name__ == "__main__":
    import argparse
    import os
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Sonde d'ingestion réseau DL_SOC (NFStream -> FastAPI)")
    parser.add_argument("--source", default=None, help="Interface réseau (ex: eth0, lo) ou chemin vers un fichier .pcap")
    parser.add_argument("--server", default="http://localhost:8000", help="URL du serveur NIDS (ex: http://192.168.1.100:8000)")
    parser.add_argument("--api-key", default="dev-secret-key", help="Clé secrète d'ingestion (x-api-key)")
    parser.add_argument("--sensor-id", default="sonde-edge-01", help="Identifiant unique de la sonde")
    parser.add_argument("--batch", type=int, default=200, help="Nombre de flux par lot envoyé")

    args = parser.parse_args()

    models_dir = Path(__file__).resolve().parent / "models"
    cols_file = models_dir / "feature_cols.json"
    if not cols_file.exists():
        print(f"Erreur : fichier {cols_file} introuvable.")
        exit(1)

    with open(cols_file, "r") as f:
        feature_cols = json.load(f)

    src = args.source
    if not src:
        print("Veuillez spécifier une source via --source <interface_ou_pcap> (ex: --source eth0 ou --source pcap/normal.pcap)")
        exit(1)

    print(f"[*] Démarrage de la sonde '{args.sensor_id}' sur la source '{src}'...")
    print(f"[*] Envoi vers : {args.server}/ingest (Lot : {args.batch} flux)")

    df = extract(src)
    print(f"[+] {len(df)} flux capturés. Envoi en cours...")
    res = send(df, feature_cols, args.server, args.api_key, sensor_id=args.sensor_id, batch=args.batch)
    print(f"[✓] Terminé avec succès. {len(res)} prédictions reçues du serveur.")

