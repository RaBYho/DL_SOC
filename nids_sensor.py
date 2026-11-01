import json
import os
from pathlib import Path
import time
import numpy as np
import pandas as pd
import requests
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
                          default=lambda o: o.item() if hasattr(o, "item") else o)
        r = requests.post(f"{url}/ingest", data=body,
                          headers={"x-api-key": key, "Content-Type": "application/json"}, timeout=60)
        r.raise_for_status()
        preds += r.json().get("preds", [])
    return preds


def stream_live(interface: str, feature_cols: list, url: str, key: str,
                sensor_id: str = "live-edge", batch: int = 5,
                idle_timeout: int = 1, active_timeout: int = 15,
                flush_interval: float = 0.3,
                promiscuous: bool = False):
    """
    Capture le trafic réseau en direct sur une interface (ex: eth0, enx3ecd36af7cdb)
    et diffuse les flux en temps réel vers le serveur NIDS / Dashboard SOC.
    """
    metadata_cols = ["bidirectional_first_seen_ms", "src_ip", "src_mac", "src_port", "dst_ip", "dst_port"]
    all_desired = list(dict.fromkeys(feature_cols + metadata_cols))

    print(f"\n" + "=" * 65)
    print(f"📡 SONDE NIDS TEMPS RÉEL (NFStream ➔ DL_SOC Engine)")
    print(f"=" * 65)
    print(f" • Interface réseau  : {interface}")
    print(f" • Identifiant Sonde : {sensor_id}")
    print(f" • Serveur cible     : {url}/ingest")
    print(f" • Timeout flux      : idle={idle_timeout}s, active={active_timeout}s")
    print(f" • Mode Ultra-Rapide : lot={batch} flux max (purge auto toutes les {int(flush_interval*1000)}ms)")
    print(f"=" * 65)
    print(f"[*] Démarrage du sniffer... (Appuyez sur Ctrl+C pour arrêter)\n")

    streamer = NFStreamer(
        source=interface,
        statistical_analysis=True,
        n_dissections=0,
        idle_timeout=idle_timeout,
        active_timeout=active_timeout,
        promiscuous_mode=promiscuous,
        n_meters=0
    )

    session = requests.Session()
    session.headers.update({"x-api-key": key, "Content-Type": "application/json"})

    buffer = []
    total_flows = 0
    total_alerts = 0
    last_send_time = time.time()

    def flush_buffer():
        nonlocal buffer, total_flows, total_alerts, last_send_time
        if not buffer:
            return
        count = len(buffer)
        body = json.dumps({"sensor_id": sensor_id, "flows": buffer},
                          default=lambda o: o.item() if hasattr(o, "item") else o)
        try:
            r = session.post(
                f"{url}/ingest",
                data=body,
                timeout=5
            )
            r.raise_for_status()
            res_data = r.json()
            alerts = res_data.get("alerts", 0)
            anoms = res_data.get("anomalies", 0)
            preds = res_data.get("preds", [])

            total_flows += count
            total_alerts += alerts + anoms

            # Alert status pill
            alert_str = ""
            if alerts > 0 or anoms > 0:
                attacks = [p for p in preds if p != "BENIGN"]
                alert_str = f" 🚨 \033[91m[{len(attacks)} ALERTE(S) : {', '.join(set(attacks))}]\033[0m"

            ts = time.strftime("%H:%M:%S")
            print(f"[{ts}] Lot envoyé : {count:2d} flux ➔ Total : {total_flows:5d} flux | Alertes cumulées : {total_alerts}{alert_str}")
        except Exception as e:
            print(f"[!] Erreur transmission vers {url}: {e}")
        finally:
            buffer = []
            last_send_time = time.time()

    try:
        for flow in streamer:
            rec = {}
            for col in all_desired:
                val = getattr(flow, col, None)
                if val is None or (isinstance(val, float) and (np.isnan(val) or np.isinf(val))):
                    rec[col] = None
                else:
                    rec[col] = val

            buffer.append(rec)
            # Envoi dès que le lot est atteint ou après le micro-délai de flush
            if len(buffer) >= batch or (time.time() - last_send_time >= flush_interval):
                flush_buffer()

    except KeyboardInterrupt:
        print("\n[*] Interruption utilisateur reçue. Vidage du tampon final...")
        flush_buffer()
        print(f"[✓] Sonde arrêtée proprement. Total flux envoyés : {total_flows}")
        session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sonde d'ingestion réseau DL_SOC (NFStream -> FastAPI)")
    parser.add_argument("--source", default=None, help="Interface réseau (ex: enx3ecd36af7cdb, eth0) ou chemin .pcap")
    parser.add_argument("--server", default="http://localhost:8000", help="URL du serveur NIDS (ex: http://localhost:8000)")
    parser.add_argument("--api-key", default="dev-secret-key", help="Clé secrète d'ingestion (x-api-key)")
    parser.add_argument("--sensor-id", default="live-edge-01", help="Identifiant unique de la sonde")
    parser.add_argument("--batch", type=int, default=5, help="Nombre de flux par lot envoyé (défaut: 5)")
    parser.add_argument("--idle-timeout", type=int, default=1, help="Délai d'inactivité avant émission d'un flux (s) (défaut: 1)")
    parser.add_argument("--active-timeout", type=int, default=15, help="Durée active max d'un flux avant émission (s)")
    parser.add_argument("--flush-interval", type=float, default=0.3, help="Intervalle max de purge du tampon en secondes (défaut: 0.3s)")
    parser.add_argument("--promiscuous", action="store_true", help="Activer le mode promiscuité sur l'interface")

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
        print("Veuillez spécifier une source via --source <interface_ou_pcap> (ex: --source enx3ecd36af7cdb ou --source pcap/normal.pcap)")
        exit(1)

    # Détection automatique du mode (Fichier PCAP vs Interface Réseau Live)
    is_pcap = Path(src).is_file() or src.endswith((".pcap", ".pcapng", ".cap"))

    if is_pcap:
        print(f"[*] Mode Rejeu Fichier : Analyse de '{src}'...")
        df = extract(src)
        print(f"[+] {len(df)} flux extraits. Envoi en cours vers {args.server}/ingest...")
        res = send(df, feature_cols, args.server, args.api_key, sensor_id=args.sensor_id, batch=args.batch if args.batch > 50 else 200)
        print(f"[✓] Terminé avec succès. {len(res)} prédictions reçues du serveur.")
    else:
        stream_live(
            interface=src,
            feature_cols=feature_cols,
            url=args.server,
            key=args.api_key,
            sensor_id=args.sensor_id,
            batch=args.batch,
            idle_timeout=args.idle_timeout,
            active_timeout=args.active_timeout,
            flush_interval=args.flush_interval,
            promiscuous=args.promiscuous
        )
