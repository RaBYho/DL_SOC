import sqlite3
import time
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from dashboard.backend.config import DB_PATH, BASE, MODELS_DIR

logger = logging.getLogger(__name__)


_initialized_dbs = set()


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = str(db_path or DB_PATH)
    if path not in _initialized_dbs:
        _init_db_schema(path)
        _initialized_dbs.add(path)
    con = sqlite3.connect(path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def _init_db_schema(path: str) -> None:
    con = sqlite3.connect(path, check_same_thread=False)
    with con:
        con.execute(
            """CREATE TABLE IF NOT EXISTS flows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            received_at REAL,
            sensor_id TEXT,
            flow_start_ms REAL,
            src_ip TEXT,
            src_mac TEXT,
            src_port INTEGER,
            dst_ip TEXT,
            dst_port INTEGER,
            protocol INTEGER,
            pred TEXT,
            confiance REAL,
            mse_ae REAL,
            anomalie_ae INTEGER)"""
        )

        cols = [r[1] for r in con.execute("PRAGMA table_info(flows)").fetchall()]
        if "mse_ae" not in cols:
            con.execute("ALTER TABLE flows ADD COLUMN mse_ae REAL")
        if "anomalie_ae" not in cols:
            con.execute("ALTER TABLE flows ADD COLUMN anomalie_ae INTEGER")

        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_flows_received ON flows(received_at DESC)"
        )
        con.execute("CREATE INDEX IF NOT EXISTS idx_flows_pred ON flows(pred)")
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_flows_anomalie ON flows(anomalie_ae)"
        )
        con.execute("CREATE INDEX IF NOT EXISTS idx_flows_src_ip ON flows(src_ip)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_flows_dst_port ON flows(dst_port)")

        # Table Active Learning / Human-in-the-Loop Feedback
        con.execute(
            """CREATE TABLE IF NOT EXISTS feedback_flows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id TEXT UNIQUE,
            timestamp REAL,
            src_ip TEXT,
            dst_ip TEXT,
            src_port INTEGER,
            dst_port INTEGER,
            protocol TEXT,
            raw_features TEXT,
            model_predicted_label TEXT,
            model_mse_score REAL,
            human_verdict TEXT NOT NULL,
            corrected_attack_type TEXT,
            analyst_notes TEXT,
            status TEXT DEFAULT 'PENDING')"""
        )
        con.execute("CREATE INDEX IF NOT EXISTS idx_feedback_verdict ON feedback_flows(human_verdict)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_feedback_incident ON feedback_flows(incident_id)")
    con.close()


def init_db(db_path: Optional[str] = None) -> None:
    """Initialise le schéma de la base et crée les index pour des requêtes analytiques ultra-rapides."""
    path = str(db_path or DB_PATH)
    _init_db_schema(path)
    _initialized_dbs.add(path)
    try:
        sync_feedback_to_disk(path)
    except Exception as e:
        logger.warning(f"Initial feedback sync warning: {e}")



def get_kpis(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Calcule les métriques clés de surveillance en temps réel."""
    con = get_connection(db_path)
    cur = con.cursor()

    row = cur.execute(
        """SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN pred != 'BENIGN' THEN 1 ELSE 0 END) as attacks,
            SUM(CASE WHEN anomalie_ae = 1 THEN 1 ELSE 0 END) as anomalies,
            SUM(CASE WHEN pred = 'BENIGN' AND anomalie_ae = 0 THEN 1 ELSE 0 END) as benign
           FROM flows"""
    ).fetchone()

    total = row["total"] or 0
    attacks = row["attacks"] or 0
    anomalies = row["anomalies"] or 0
    benign = row["benign"] or 0
    malicious = attacks + anomalies

    # Débit calculé sur la dernière minute
    now = time.time()
    one_min_ago = now - 60.0
    recent_count = cur.execute(
        "SELECT COUNT(*) FROM flows WHERE received_at >= ?", (one_min_ago,)
    ).fetchone()[0]
    rate = round(recent_count / 60.0, 1)

    # Récupération de la moyenne récente de l'erreur MSE
    recent_mse = cur.execute(
        "SELECT AVG(mse_ae) FROM flows WHERE received_at >= ? AND mse_ae IS NOT NULL",
        (one_min_ago,),
    ).fetchone()[0]
    avg_mse = round(recent_mse, 3) if recent_mse is not None else 0.300

    benign_pct = round((benign / total * 100.0), 2) if total > 0 else 100.0
    malicious_pct = round((malicious / total * 100.0), 2) if total > 0 else 0.0

    con.close()
    return {
        "total_flows": total,
        "confirmed_attacks": attacks,
        "zero_day_anomalies": anomalies,
        "rate_flows_sec": rate,
        "current_mse": avg_mse,
        "benign_pct": benign_pct,
        "malicious_pct": malicious_pct,
    }


def get_attack_distribution(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retourne la répartition des attaques pour le Donut SVG."""
    con = get_connection(db_path)
    rows = con.execute(
        """SELECT pred as label, COUNT(*) as count 
           FROM flows 
           WHERE pred != 'BENIGN' 
           GROUP BY pred 
           ORDER BY count DESC"""
    ).fetchall()

    total_attacks = sum(r["count"] for r in rows)
    palette = {
        "DDoS": "#ff4d7e",
        "DoS-Hulk": "#ff8a4c",
        "DoS-GoldenEye": "#ff8a4c",
        "DoS-Slowhttptest": "#ffb547",
        "DoS-slowloris": "#ffb547",
        "PortScan": "#ffb547",
        "Scan-Vista": "#6c8cff",
        "FTP-Patator": "#4a57e0",
        "SSH-Patator": "#6c8cff",
        "WebAttack": "#b266ff",
        "Bot": "#ff4d7e",
    }

    result = []
    for r in rows:
        label = r["label"]
        cnt = r["count"]
        pct = round(cnt / total_attacks * 100.0, 1) if total_attacks > 0 else 0.0
        result.append(
            {
                "label": label,
                "count": cnt,
                "percentage": pct,
                "color": palette.get(label, "#a9abc6"),
            }
        )

    con.close()
    return result


def get_timeline(
    window_seconds: int = 900, buckets: int = 60, db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Génère la série temporelle du volume de flux et détecte les pics d'incidents."""
    con = get_connection(db_path)
    now = time.time()
    start_time = now - window_seconds
    bucket_size = window_seconds / float(buckets)

    rows = con.execute(
        """SELECT received_at, pred, anomalie_ae 
           FROM flows 
           WHERE received_at >= ? 
           ORDER BY received_at ASC""",
        (start_time,),
    ).fetchall()
    con.close()

    series = [0] * buckets
    attacks = [0] * buckets

    for r in rows:
        t = r["received_at"]
        idx = int((t - start_time) / bucket_size)
        if 0 <= idx < buckets:
            series[idx] += 1
            if r["pred"] != "BENIGN" or r["anomalie_ae"] == 1:
                attacks[idx] += 1

    # Détection de pic d'incident (seuil = 1.8 * moyenne)
    mean_val = (sum(series) / len(series)) if series else 0
    spike_threshold = max(mean_val * 1.8, 10)

    timeline_points = []
    for i in range(buckets):
        count = series[i]
        timeline_points.append(
            {
                "bucket": i,
                "count": count,
                "attacks": attacks[i],
                "is_spike": count > spike_threshold,
            }
        )

    return timeline_points


def get_threat_vectors(
    limit: int = 5, db_path: Optional[str] = None
) -> Dict[str, Any]:
    """Retourne le Top 5 des adresses IP assaillantes et le Top 5 des ports ciblés."""
    con = get_connection(db_path)

    top_ips = con.execute(
        """SELECT src_ip, COUNT(*) as count 
           FROM flows 
           WHERE (pred != 'BENIGN' OR anomalie_ae = 1) AND src_ip IS NOT NULL 
           GROUP BY src_ip 
           ORDER BY count DESC 
           LIMIT ?""",
        (limit,),
    ).fetchall()

    top_ports = con.execute(
        """SELECT dst_port, COUNT(*) as count 
           FROM flows 
           WHERE (pred != 'BENIGN' OR anomalie_ae = 1) AND dst_port IS NOT NULL 
           GROUP BY dst_port 
           ORDER BY count DESC 
           LIMIT ?""",
        (limit,),
    ).fetchall()

    port_names = {
        21: "FTP",
        22: "SSH",
        80: "HTTP",
        443: "HTTPS",
        445: "SMB",
        3389: "RDP",
        53: "DNS",
        8080: "HTTP-Alt",
    }

    result = {
        "top_ips": [{"ip": r["src_ip"], "count": r["count"]} for r in top_ips],
        "top_ports": [
            {
                "port": r["dst_port"],
                "service": port_names.get(r["dst_port"], "Unknown"),
                "count": r["count"],
            }
            for r in top_ports
        ],
    }

    con.close()
    return result


def get_total_alerts_count(
    search_ip: Optional[str] = None,
    category: Optional[str] = None,
    min_conf: float = 0.0,
    anomalies_only: bool = False,
    db_path: Optional[str] = None,
) -> int:
    """Retourne le nombre total d'alertes correspondant aux filtres en base SQLite."""
    con = get_connection(db_path)
    query = """SELECT COUNT(*) FROM flows 
               WHERE (pred != 'BENIGN' OR anomalie_ae = 1)"""
    params: List[Any] = []

    if search_ip:
        query += " AND (src_ip LIKE ? OR dst_ip LIKE ?)"
        params.extend([f"%{search_ip}%", f"%{search_ip}%"])

    if category:
        query += " AND pred = ?"
        params.append(category)

    if min_conf > 0.0:
        query += " AND confiance >= ?"
        params.append(min_conf / 100.0)

    if anomalies_only:
        query += " AND anomalie_ae = 1"

    count = con.execute(query, params).fetchone()[0] or 0
    con.close()
    return int(count)


def get_recent_alerts(
    limit: int = 100,
    offset: int = 0,
    search_ip: Optional[str] = None,
    category: Optional[str] = None,
    min_conf: float = 0.0,
    anomalies_only: bool = False,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retourne la liste filtrée et paginée des alertes pour le tableau du SOC."""
    con = get_connection(db_path)

    query = """SELECT id, received_at, sensor_id, src_ip, src_port, dst_ip, dst_port, 
                      protocol, pred, confiance, mse_ae, anomalie_ae 
               FROM flows 
               WHERE (pred != 'BENIGN' OR anomalie_ae = 1)"""
    params: List[Any] = []

    if search_ip:
        query += " AND (src_ip LIKE ? OR dst_ip LIKE ?)"
        params.extend([f"%{search_ip}%", f"%{search_ip}%"])

    if category:
        query += " AND pred = ?"
        params.append(category)

    if min_conf > 0.0:
        query += " AND confiance >= ?"
        params.append(min_conf / 100.0)

    if anomalies_only:
        query += " AND anomalie_ae = 1"

    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = con.execute(query, params).fetchall()

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

    alerts = []
    for r in rows:
        pred = r["pred"]
        sev = severity_map.get(pred, "High" if r["anomalie_ae"] == 1 else "Medium")
        t_str = time.strftime("%H:%M:%S", time.localtime(r["received_at"]))
        conf_float = float(r["confiance"] or 0.0)
        anom_int = int(r["anomalie_ae"] or 0)
        sid = r["sensor_id"] or "sensor-edge-01"

        alerts.append(
            {
                "id": r["id"],
                "timestamp": t_str,
                "received_at": t_str,
                "sensor": sid,
                "sensor_id": sid,
                "src_ip": r["src_ip"] or "0.0.0.0",
                "src_port": r["src_port"] or 0,
                "dst_ip": r["dst_ip"] or "0.0.0.0",
                "dst_port": r["dst_port"] or 0,
                "protocol": "TCP" if r["protocol"] == 6 else "UDP",
                "classification": pred,
                "pred": pred,
                "confidence": round(conf_float * 100.0, 1),
                "confiance": conf_float,
                "mse_ae": round(r["mse_ae"], 3) if r["mse_ae"] is not None else 0.0,
                "anomalie_ae": anom_int,
                "is_anomaly": bool(anom_int),
                "severity": sev,
            }
        )

    con.close()
    return alerts


def get_active_sensors(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Récupère la liste des sondes réellement enregistrées et leur état d'activité."""
    con = get_connection(db_path)
    try:
        rows = con.execute(
            """SELECT 
                sensor_id,
                COUNT(*) as total_flows,
                SUM(CASE WHEN pred != 'BENIGN' OR anomalie_ae = 1 THEN 1 ELSE 0 END) as total_attacks,
                MAX(received_at) as last_seen,
                MIN(received_at) as first_seen
            FROM flows 
            WHERE sensor_id IS NOT NULL AND sensor_id != ''
            GROUP BY sensor_id
            ORDER BY last_seen DESC"""
        ).fetchall()

        now = time.time()
        sensors = []
        for r in rows:
            sid = r["sensor_id"]
            last_seen = float(r["last_seen"]) if r["last_seen"] else 0.0
            elapsed = now - last_seen if last_seen > 0 else 999999.0

            if elapsed < 45.0:
                status = "Online"
                status_label = "En direct"
            elif elapsed < 300.0:
                status = "Idle"
                status_label = "En attente"
            else:
                status = "Offline"
                status_label = "Inactif"

            last_seen_str = (
                time.strftime("%H:%M:%S", time.localtime(last_seen))
                if last_seen > 0
                else "N/A"
            )

            is_lab_replay = (sid == "lab-replay")
            sensors.append(
                {
                    "id": sid,
                    "name": "Simulateur Lab (PCAP)" if is_lab_replay else sid,
                    "type": "replay" if is_lab_replay else "edge_sensor",
                    "interface": "PCAP Replay Engine" if is_lab_replay else "Capture Réseau",
                    "status": status,
                    "status_label": status_label,
                    "total_flows": int(r["total_flows"] or 0),
                    "total_attacks": int(r["total_attacks"] or 0),
                    "last_seen": last_seen_str,
                    "last_seen_epoch": last_seen,
                    "elapsed_sec": round(elapsed, 1),
                }
            )
        return sensors
    finally:
        con.close()


def reset_database(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Vide la table flows, remet à zéro l'auto-incrément et optimise la base."""
    con = get_connection(db_path)
    with con:
        con.execute("DELETE FROM flows")
        try:
            con.execute("DELETE FROM sqlite_sequence WHERE name='flows'")
        except Exception:
            pass
    try:
        con.isolation_level = None
        con.execute("VACUUM")
    except Exception:
        pass
    finally:
        con.close()
    return {
        "status": "success",
        "message": "Base de données réinitialisée avec succès",
        "flows_remaining": 0,
    }


def record_feedback(
    incident_id: str,
    human_verdict: str,
    corrected_attack_type: Optional[str] = None,
    analyst_notes: Optional[str] = None,
    flow_data: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Enregistre ou met à jour la qualification humaine d'un incident."""
    import json
    con = get_connection(db_path)
    cur = con.cursor()
    now = time.time()

    flow_data = flow_data or {}
    raw_features_str = json.dumps(flow_data.get("raw_features", flow_data))

    cur.execute(
        """INSERT INTO feedback_flows (
            incident_id, timestamp, src_ip, dst_ip, src_port, dst_port, protocol,
            raw_features, model_predicted_label, model_mse_score,
            human_verdict, corrected_attack_type, analyst_notes, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')
        ON CONFLICT(incident_id) DO UPDATE SET
            timestamp=excluded.timestamp,
            human_verdict=excluded.human_verdict,
            corrected_attack_type=excluded.corrected_attack_type,
            analyst_notes=excluded.analyst_notes""",
        (
            str(incident_id),
            now,
            str(flow_data.get("src_ip", "")),
            str(flow_data.get("dst_ip", "")),
            flow_data.get("src_port"),
            flow_data.get("dst_port"),
            str(flow_data.get("protocol", "")),
            raw_features_str,
            str(flow_data.get("pred", flow_data.get("classification", ""))),
            float(flow_data.get("mse_ae", 0.0) or 0.0),
            str(human_verdict),
            str(corrected_attack_type or ""),
            str(analyst_notes or ""),
        ),
    )
    con.commit()
    con.close()

    try:
        sync_feedback_to_disk(db_path)
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation feedback sur disque: {e}")

    return {
        "status": "success",
        "incident_id": incident_id,
        "human_verdict": human_verdict,
        "corrected_attack_type": corrected_attack_type,
        "timestamp": now,
    }


def record_batch_feedback(
    incident_ids: List[str],
    human_verdict: str,
    corrected_attack_type: Optional[str] = None,
    analyst_notes: Optional[str] = None,
    flows_map: Optional[Dict[str, Dict[str, Any]]] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Enregistre ou met à jour la qualification humaine groupée d'un lot d'incidents."""
    import json
    con = get_connection(db_path)
    cur = con.cursor()
    now = time.time()
    flows_map = flows_map or {}

    rows = []
    for inc_id in incident_ids:
        flow = flows_map.get(str(inc_id), {})
        raw_features_str = json.dumps(flow.get("raw_features", flow))
        rows.append((
            str(inc_id),
            now,
            str(flow.get("src_ip", "")),
            str(flow.get("dst_ip", "")),
            flow.get("src_port"),
            flow.get("dst_port"),
            str(flow.get("protocol", "")),
            raw_features_str,
            str(flow.get("pred", flow.get("classification", ""))),
            float(flow.get("mse_ae", 0.0) or 0.0),
            str(human_verdict),
            str(corrected_attack_type or ""),
            str(analyst_notes or ""),
        ))

    if rows:
        cur.executemany(
            """INSERT INTO feedback_flows (
                incident_id, timestamp, src_ip, dst_ip, src_port, dst_port, protocol,
                raw_features, model_predicted_label, model_mse_score,
                human_verdict, corrected_attack_type, analyst_notes, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')
            ON CONFLICT(incident_id) DO UPDATE SET
                timestamp=excluded.timestamp,
                human_verdict=excluded.human_verdict,
                corrected_attack_type=excluded.corrected_attack_type,
                analyst_notes=excluded.analyst_notes""",
            rows,
        )
        con.commit()
    con.close()

    try:
        sync_feedback_to_disk(db_path)
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation feedback sur disque: {e}")

    return {
        "status": "success",
        "count": len(incident_ids),
        "incident_ids": incident_ids,
        "human_verdict": human_verdict,
        "corrected_attack_type": corrected_attack_type,
        "timestamp": now,
    }


def get_feedback(incident_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Récupère la qualification humaine existante pour un incident donné."""
    import json
    con = get_connection(db_path)
    cur = con.cursor()
    row = cur.execute(
        "SELECT * FROM feedback_flows WHERE incident_id = ?", (str(incident_id),)
    ).fetchone()
    con.close()

    if not row:
        return None

    res = dict(row)
    if res.get("raw_features"):
        try:
            res["raw_features"] = json.loads(res["raw_features"])
        except Exception:
            pass
    return res


def get_feedback_summary(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Calcule les statistiques globales du programme Active Learning."""
    con = get_connection(db_path)
    cur = con.cursor()
    rows = cur.execute(
        """SELECT 
            COUNT(*) as total_feedback,
            SUM(CASE WHEN human_verdict = 'FALSE_POSITIVE' THEN 1 ELSE 0 END) as false_positives,
            SUM(CASE WHEN human_verdict = 'KNOWN_ATTACK' THEN 1 ELSE 0 END) as reclassified_attacks,
            SUM(CASE WHEN human_verdict = 'CONFIRMED_ZERODAY' THEN 1 ELSE 0 END) as confirmed_zerodays
           FROM feedback_flows"""
    ).fetchone()

    total = rows["total_feedback"] or 0
    fp = rows["false_positives"] or 0
    reclass = rows["reclassified_attacks"] or 0
    zd = rows["confirmed_zerodays"] or 0

    # Top attaques reclassifiées
    top_reclassified = cur.execute(
        """SELECT corrected_attack_type, COUNT(*) as count 
           FROM feedback_flows 
           WHERE corrected_attack_type != '' AND corrected_attack_type IS NOT NULL
           GROUP BY corrected_attack_type ORDER BY count DESC LIMIT 5"""
    ).fetchall()

    con.close()
    return {
        "total_feedback": total,
        "false_positives": fp,
        "reclassified_attacks": reclass,
        "confirmed_zerodays": zd,
        "top_reclassified": [{"attack": r[0], "count": r[1]} for r in top_reclassified],
    }


def export_feedback_dataset(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Exporte l'ensemble des flux qualifiés pour le ré-entraînement PyTorch / Scikit-Learn."""
    import json
    con = get_connection(db_path)
    cur = con.cursor()
    rows = cur.execute("SELECT * FROM feedback_flows ORDER BY timestamp DESC").fetchall()
    con.close()

    dataset = []
    for r in rows:
        item = dict(r)
        # Détermination du label d'entraînement officiel
        if item.get("human_verdict") == "FALSE_POSITIVE":
            item["label"] = "BENIGN"
            item["analyst_verdict"] = "BENIGN"
        else:
            lbl = item.get("corrected_attack_type") or item.get("model_predicted_label") or "BENIGN"
            item["label"] = lbl
            item["analyst_verdict"] = lbl

        if item.get("raw_features"):
            try:
                feats = json.loads(item["raw_features"])
                item["raw_features"] = feats
                if isinstance(feats, dict):
                    for k, v in feats.items():
                        if k not in item:
                            item[k] = v
            except Exception:
                pass
        dataset.append(item)
    return dataset


def sync_feedback_to_disk(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Exporte automatiquement la table feedback_flows vers feedback_flows.json et feedback_flows.csv sur disque."""
    import json
    import csv

    dataset = export_feedback_dataset(db_path)
    base_dir = Path(BASE)
    models_dir = Path(MODELS_DIR)

    json_paths = [base_dir / "feedback_flows.json", models_dir / "feedback_flows.json"]
    csv_paths = [base_dir / "feedback_flows.csv", models_dir / "feedback_flows.csv"]

    # 1. Écriture JSON
    json_str = json.dumps(dataset, indent=2, ensure_ascii=False)
    for p in json_paths:
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json_str, encoding="utf-8")
        except Exception as e:
            logger.error(f"Erreur écriture JSON {p}: {e}")

    # 2. Écriture CSV
    if dataset:
        keys = [
            "id", "incident_id", "timestamp", "src_ip", "dst_ip",
            "src_port", "dst_port", "protocol", "model_predicted_label",
            "model_mse_score", "human_verdict", "corrected_attack_type",
            "label", "analyst_verdict", "analyst_notes", "status"
        ]
        first_item = dataset[0]
        extra_keys = [k for k in first_item.keys() if k not in keys and k != "raw_features"]
        all_csv_keys = keys + extra_keys

        for p in csv_paths:
            try:
                p.parent.mkdir(parents=True, exist_ok=True)
                with open(p, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=all_csv_keys, extrasaction="ignore")
                    writer.writeheader()
                    for row in dataset:
                        writer.writerow(row)
            except Exception as e:
                logger.error(f"Erreur écriture CSV {p}: {e}")

    logger.info(f"[Active Learning] Synchronisé {len(dataset)} flux qualifiés sur disque (JSON et CSV).")
    return {"count": len(dataset), "files": [str(p) for p in json_paths + csv_paths]}


def get_model_classes(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Récupère dynamiquement les classes définies par le modèle actif et observées en base (jamais figées)."""
    import json
    from dashboard.backend.config import MODELS_DIR, ACTIVE_DNN_VERSION, ACTIVE_AE_VERSION

    # 1. Classes définies par l'artéfact du modèle actif (classes.json)
    model_classes: List[str] = []
    classes_file = MODELS_DIR / "classes.json"
    if classes_file.exists():
        try:
            with open(classes_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                model_classes = list(data.keys()) if isinstance(data, dict) else list(data)
        except Exception:
            pass

    if not model_classes:
        model_classes = ["BENIGN", "DDoS", "PortScan", "Bot", "WebAttack"]

    # 2. Classes dynamiquement observées dans la base de données (flux réels et active learning)
    observed_classes = set()
    try:
        con = get_connection(db_path)
        cur = con.cursor()
        rows_pred = cur.execute("SELECT DISTINCT pred FROM flows WHERE pred IS NOT NULL AND pred != ''").fetchall()
        for r in rows_pred:
            if r[0]:
                observed_classes.add(str(r[0]))

        rows_fb = cur.execute(
            "SELECT DISTINCT corrected_attack_type FROM feedback_flows WHERE corrected_attack_type IS NOT NULL AND corrected_attack_type != ''"
        ).fetchall()
        for r in rows_fb:
            if r[0]:
                observed_classes.add(str(r[0]))
        con.close()
    except Exception:
        pass

    # Fusion ordonnée : les classes du modèle en tête, puis les classes dynamiquement qualifiées/observées
    all_known = list(model_classes)
    for c in sorted(observed_classes):
        if c not in all_known:
            all_known.append(c)

    attack_classes = [c for c in all_known if c.upper() != "BENIGN"]
    all_categories = list(attack_classes)
    if "Unknown (anomaly)" not in all_categories:
        all_categories.append("Unknown (anomaly)")

    return {
        "model_version": ACTIVE_DNN_VERSION,
        "ae_version": ACTIVE_AE_VERSION,
        "total_classes": len(model_classes),
        "classes": model_classes,
        "attack_classes": attack_classes,
        "all_categories": all_categories,
    }

