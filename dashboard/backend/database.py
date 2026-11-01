import json
import sqlite3
import time
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
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
        if "incident_id" not in cols:
            con.execute("ALTER TABLE flows ADD COLUMN incident_id INTEGER")

        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_flows_received ON flows(received_at DESC)"
        )
        con.execute("CREATE INDEX IF NOT EXISTS idx_flows_pred ON flows(pred)")
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_flows_anomalie ON flows(anomalie_ae)"
        )
        con.execute("CREATE INDEX IF NOT EXISTS idx_flows_src_ip ON flows(src_ip)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_flows_dst_port ON flows(dst_port)")
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_flows_incident_id ON flows(incident_id)"
        )

        # Table Incidents (Corrélation SOC de niveau entreprise)
        con.execute(
            """CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_code TEXT UNIQUE,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            closed_at REAL,
            status TEXT DEFAULT 'OPEN',
            attack_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            src_ip TEXT NOT NULL,
            dst_ip TEXT NOT NULL,
            sensor_id TEXT,
            flow_count INTEGER DEFAULT 1,
            targeted_ports TEXT,
            ports_summary TEXT,
            max_confidence REAL DEFAULT 0.0,
            max_mse REAL DEFAULT 0.0,
            is_zero_day INTEGER DEFAULT 0,
            notified_open INTEGER DEFAULT 0,
            notified_close INTEGER DEFAULT 0)"""
        )
        con.execute("CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_incidents_updated ON incidents(updated_at DESC)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_incidents_corr ON incidents(src_ip, dst_ip, attack_type, status)")

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
    """Vide les tables flows et incidents, remet à zéro l'auto-incrément et optimise la base."""
    con = get_connection(db_path)
    with con:
        con.execute("DELETE FROM flows")
        con.execute("DELETE FROM incidents")
        try:
            con.execute("DELETE FROM sqlite_sequence WHERE name IN ('flows', 'incidents')")
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


# ---------------------------------------------------------------------------
# MOTEUR DE CORRÉLATION ET GESTION DES INCIDENTS SOC
# ---------------------------------------------------------------------------

SEVERITY_MAP = {
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
    "Zero-Day": "High",
}


def get_severity_for_attack(attack_type: str, is_anomaly: bool = False) -> str:
    """Détermine la sévérité d'un événement selon la nomenclature SOC."""
    if is_anomaly and attack_type in ("BENIGN", "Zero-Day"):
        return "High"
    return SEVERITY_MAP.get(attack_type, "High" if is_anomaly else "Medium")


def summarize_ports(ports: List[int]) -> str:
    """Synthétise une liste de ports ciblés en notation compacte lisible pour le SOC."""
    if not ports:
        return "-"
    unique_ports = sorted(set(int(p) for p in ports if p is not None and int(p) > 0))
    if not unique_ports:
        return "-"
    if len(unique_ports) == 1:
        return str(unique_ports[0])
    if len(unique_ports) <= 4:
        return ", ".join(str(p) for p in unique_ports)

    # Vérification si la plage est contiguë (ex: scan 20 à 1000)
    is_contiguous = True
    for i in range(len(unique_ports) - 1):
        if unique_ports[i + 1] != unique_ports[i] + 1:
            is_contiguous = False
            break

    if is_contiguous:
        return f"{unique_ports[0]}-{unique_ports[-1]} ({len(unique_ports)} ports)"

    top4 = ", ".join(str(p) for p in unique_ports[:4])
    return f"{top4} (+{len(unique_ports) - 4} autres)"


def insert_and_correlate_flows(
    flow_records: List[Dict[str, Any]],
    predictions: List[str],
    confidences: List[float],
    mse_values: List[Optional[float]],
    anomaly_values: List[int],
    sensor_id: str = "sensor-01",
    received_at: Optional[float] = None,
    inactivity_window: float = 45.0,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Insère un lot de flux dans SQLite et corrèle les flux malveillants
    en incidents parents de sécurité selon la clé (src_ip, dst_ip, attack_type).
    """
    now = float(received_at if received_at is not None else time.time())
    con = get_connection(db_path)

    new_incidents: List[Dict[str, Any]] = []
    updated_incidents: List[Dict[str, Any]] = []
    corr_cache: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    flow_incident_ids: List[Optional[int]] = []
    alert_rows: List[Dict[str, Any]] = []

    # 1. Analyse et groupement en mémoire des flux de ce lot
    for idx, (r, pred, conf, mse_val, anom_val) in enumerate(
        zip(flow_records, predictions, confidences, mse_values, anomaly_values)
    ):
        is_anom = bool(anom_val == 1)
        is_attack = bool(pred != "BENIGN")

        if not is_attack and not is_anom:
            flow_incident_ids.append(None)
            continue

        attack_type = "Zero-Day" if (not is_attack and is_anom) else pred
        src_ip = str(r.get("src_ip") or "0.0.0.0")
        dst_ip = str(r.get("dst_ip") or "0.0.0.0")
        dst_port = int(r.get("dst_port") or 0)
        c_val = float(conf or 0.0)
        m_val = float(mse_val or 0.0) if mse_val is not None else 0.0

        key = (src_ip, dst_ip, attack_type)

        if key not in corr_cache:
            # Recherche d'un incident OUVERT actif dans la fenêtre d'inactivité
            row = con.execute(
                """SELECT id, incident_code, created_at, updated_at, flow_count, targeted_ports,
                          ports_summary, max_confidence, max_mse, is_zero_day, severity
                   FROM incidents
                   WHERE status = 'OPEN' AND src_ip = ? AND dst_ip = ? AND attack_type = ?
                     AND (? - updated_at) <= ?
                   ORDER BY id DESC LIMIT 1""",
                (src_ip, dst_ip, attack_type, now, inactivity_window),
            ).fetchone()

            if row:
                try:
                    ports_loaded = set(json.loads(row["targeted_ports"] or "[]"))
                except Exception:
                    ports_loaded = set()
                corr_cache[key] = {
                    "id": row["id"],
                    "incident_code": row["incident_code"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "status": "OPEN",
                    "attack_type": attack_type,
                    "severity": row["severity"],
                    "src_ip": src_ip,
                    "dst_ip": dst_ip,
                    "sensor_id": sensor_id,
                    "flow_count": int(row["flow_count"] or 0),
                    "targeted_ports": ports_loaded,
                    "ports_summary": row["ports_summary"],
                    "max_confidence": float(row["max_confidence"] or 0.0),
                    "max_mse": float(row["max_mse"] or 0.0),
                    "is_zero_day": int(row["is_zero_day"] or 0),
                    "is_new": False,
                    "is_modified": False,
                }
            else:
                sev = get_severity_for_attack(attack_type, is_anom)
                ports_set = {dst_port} if dst_port > 0 else set()
                ports_list = sorted(ports_set)
                p_sum = summarize_ports(ports_list)
                cur = con.execute(
                    """INSERT INTO incidents (
                        incident_code, created_at, updated_at, status, attack_type, severity,
                        src_ip, dst_ip, sensor_id, flow_count, targeted_ports, ports_summary,
                        max_confidence, max_mse, is_zero_day, notified_open, notified_close
                    ) VALUES (?, ?, ?, 'OPEN', ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, 0, 0)""",
                    (
                        "",
                        now,
                        now,
                        attack_type,
                        sev,
                        src_ip,
                        dst_ip,
                        sensor_id,
                        json.dumps(ports_list),
                        p_sum,
                        c_val,
                        m_val,
                        1 if is_anom else 0,
                    ),
                )
                new_id = cur.lastrowid
                inc_code = f"INC-{new_id:04d}"
                con.execute("UPDATE incidents SET incident_code = ? WHERE id = ?", (inc_code, new_id))
                corr_cache[key] = {
                    "id": new_id,
                    "incident_code": inc_code,
                    "created_at": now,
                    "updated_at": now,
                    "status": "OPEN",
                    "attack_type": attack_type,
                    "severity": sev,
                    "src_ip": src_ip,
                    "dst_ip": dst_ip,
                    "sensor_id": sensor_id,
                    "flow_count": 0,
                    "targeted_ports": ports_set,
                    "ports_summary": p_sum,
                    "max_confidence": c_val,
                    "max_mse": m_val,
                    "is_zero_day": 1 if is_anom else 0,
                    "is_new": True,
                    "is_modified": True,
                }

        inc = corr_cache[key]
        inc["flow_count"] += 1
        if dst_port > 0:
            inc["targeted_ports"].add(dst_port)
        inc["max_confidence"] = max(inc["max_confidence"], c_val)
        inc["max_mse"] = max(inc["max_mse"], m_val)
        if is_anom:
            inc["is_zero_day"] = 1
        inc["updated_at"] = now
        inc["is_modified"] = True

        flow_incident_ids.append(inc["id"])

        # Enregistrement pour l'alerte unitaire
        t_str = time.strftime("%H:%M:%S", time.localtime(now))
        alert_rows.append(
            {
                "id": int(now * 1000) + idx,
                "incident_id": inc["id"],
                "incident_code": inc["incident_code"],
                "timestamp": t_str,
                "received_at": t_str,
                "sensor": sensor_id,
                "sensor_id": sensor_id,
                "src_ip": src_ip,
                "src_port": r.get("src_port", 0),
                "dst_ip": dst_ip,
                "dst_port": dst_port,
                "protocol": "TCP" if r.get("protocol") == 6 else "UDP",
                "classification": pred,
                "pred": pred,
                "confidence": round(c_val * 100.0, 1),
                "confiance": c_val,
                "mse_ae": round(m_val, 3) if mse_val is not None else 0.0,
                "anomalie_ae": int(anom_val or 0),
                "is_anomaly": is_anom,
                "severity": inc["severity"],
            }
        )

    # 2. Mise à jour en base des incidents modifiés
    for key, inc in corr_cache.items():
        if inc["is_modified"]:
            p_list = sorted(inc["targeted_ports"])
            p_sum = summarize_ports(p_list)
            inc["ports_summary"] = p_sum
            con.execute(
                """UPDATE incidents
                   SET updated_at = ?, flow_count = ?, targeted_ports = ?, ports_summary = ?,
                       max_confidence = ?, max_mse = ?, is_zero_day = ?
                   WHERE id = ?""",
                (
                    inc["updated_at"],
                    inc["flow_count"],
                    json.dumps(p_list[:500]),
                    p_sum,
                    inc["max_confidence"],
                    inc["max_mse"],
                    inc["is_zero_day"],
                    inc["id"],
                ),
            )
            export_inc = {
                "id": inc["id"],
                "incident_code": inc["incident_code"],
                "created_at": inc["created_at"],
                "updated_at": inc["updated_at"],
                "status": "OPEN",
                "attack_type": inc["attack_type"],
                "severity": inc["severity"],
                "src_ip": inc["src_ip"],
                "dst_ip": inc["dst_ip"],
                "sensor_id": inc["sensor_id"],
                "flow_count": inc["flow_count"],
                "ports_summary": p_sum,
                "max_confidence": inc["max_confidence"],
                "max_mse": inc["max_mse"],
                "is_zero_day": inc["is_zero_day"],
                "duration_sec": max(1, int(inc["updated_at"] - inc["created_at"])),
            }
            if inc["is_new"]:
                new_incidents.append(export_inc)
            else:
                updated_incidents.append(export_inc)

    # 3. Insertion par lot des flux avec leur incident_id
    rows = [
        (
            now,
            sensor_id,
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
            inc_id,
        )
        for r, p, c, m, a, inc_id in zip(
            flow_records, predictions, confidences, mse_values, anomaly_values, flow_incident_ids
        )
    ]

    with con:
        con.executemany(
            """INSERT INTO flows (
                received_at, sensor_id, flow_start_ms, src_ip, src_mac, src_port,
                dst_ip, dst_port, protocol, pred, confiance, mse_ae, anomalie_ae, incident_id
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            rows,
        )
    con.close()

    return {
        "new_incidents": new_incidents,
        "updated_incidents": updated_incidents,
        "total_flows": len(flow_records),
        "alerts_count": len(alert_rows),
        "anomalies_count": sum(1 for a in anomaly_values if a == 1),
        "alert_rows": alert_rows,
    }


def get_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    search_ip: Optional[str] = None,
    attack_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retourne la liste paginée et enrichie des incidents pour le SOC."""
    con = get_connection(db_path)
    query = """SELECT id, incident_code, created_at, updated_at, closed_at, status,
                      attack_type, severity, src_ip, dst_ip, sensor_id, flow_count,
                      targeted_ports, ports_summary, max_confidence, max_mse,
                      is_zero_day, notified_open, notified_close
               FROM incidents WHERE 1=1"""
    params: List[Any] = []

    if status and status.upper() != "ALL":
        query += " AND status = ?"
        params.append(status.upper())

    if severity:
        query += " AND severity = ?"
        params.append(severity)

    if search_ip:
        query += " AND (src_ip LIKE ? OR dst_ip LIKE ?)"
        params.extend([f"%{search_ip}%", f"%{search_ip}%"])

    if attack_type:
        query += " AND attack_type = ?"
        params.append(attack_type)

    query += " ORDER BY updated_at DESC, id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = con.execute(query, params).fetchall()
    incidents = []
    for r in rows:
        created = float(r["created_at"])
        updated = float(r["updated_at"])
        dur = max(1, int(updated - created))
        conf = float(r["max_confidence"] or 0.0)
        conf_pct = round(conf * 100.0, 1) if conf <= 1.0 else round(conf, 1)

        try:
            ports_list = json.loads(r["targeted_ports"] or "[]")
        except Exception:
            ports_list = []

        incidents.append(
            {
                "id": r["id"],
                "incident_code": r["incident_code"] or f"INC-{r['id']:04d}",
                "status": r["status"] or "OPEN",
                "attack_type": r["attack_type"],
                "severity": r["severity"],
                "src_ip": r["src_ip"],
                "dst_ip": r["dst_ip"],
                "sensor_id": r["sensor_id"] or "sensor-01",
                "flow_count": int(r["flow_count"] or 1),
                "targeted_ports": ports_list,
                "ports_summary": r["ports_summary"] or summarize_ports(ports_list),
                "ports_count": len(ports_list),
                "max_confidence": conf,
                "confidence": conf_pct,
                "max_mse": round(float(r["max_mse"] or 0.0), 3),
                "is_zero_day": bool(r["is_zero_day"]),
                "created_at": created,
                "updated_at": updated,
                "closed_at": r["closed_at"],
                "duration_sec": dur,
                "timestamp": time.strftime("%H:%M:%S", time.localtime(created)),
                "updated_time": time.strftime("%H:%M:%S", time.localtime(updated)),
                "notified_open": bool(r["notified_open"]),
                "notified_close": bool(r["notified_close"]),
            }
        )
    con.close()
    return incidents


def get_total_incidents_count(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    search_ip: Optional[str] = None,
    attack_type: Optional[str] = None,
    db_path: Optional[str] = None,
) -> int:
    """Compte le nombre total d'incidents répondant aux filtres."""
    con = get_connection(db_path)
    query = "SELECT COUNT(*) FROM incidents WHERE 1=1"
    params: List[Any] = []

    if status and status.upper() != "ALL":
        query += " AND status = ?"
        params.append(status.upper())

    if severity:
        query += " AND severity = ?"
        params.append(severity)

    if search_ip:
        query += " AND (src_ip LIKE ? OR dst_ip LIKE ?)"
        params.extend([f"%{search_ip}%", f"%{search_ip}%"])

    if attack_type:
        query += " AND attack_type = ?"
        params.append(attack_type)

    count = con.execute(query, params).fetchone()[0]
    con.close()
    return int(count or 0)


def get_incidents_summary(db_path: Optional[str] = None) -> Dict[str, int]:
    """Retourne la synthèse globale des incidents (total, ouverts, clos, critiques)."""
    con = get_connection(db_path)
    cur = con.cursor()
    total = cur.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
    open_count = cur.execute("SELECT COUNT(*) FROM incidents WHERE status = 'OPEN'").fetchone()[0]
    closed_count = cur.execute("SELECT COUNT(*) FROM incidents WHERE status = 'CLOSED'").fetchone()[0]
    critical_count = cur.execute("SELECT COUNT(*) FROM incidents WHERE severity = 'Critical'").fetchone()[0]
    con.close()
    return {
        "total": int(total or 0),
        "open": int(open_count or 0),
        "closed": int(closed_count or 0),
        "critical": int(critical_count or 0),
    }


def get_incident_flows(
    incident_id: int,
    limit: int = 50,
    offset: int = 0,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retourne les flux élémentaires rattachés à un incident donné."""
    con = get_connection(db_path)
    rows = con.execute(
        """SELECT id, received_at, sensor_id, src_ip, src_port, dst_ip, dst_port,
                  protocol, pred, confiance, mse_ae, anomalie_ae, incident_id
           FROM flows
           WHERE incident_id = ?
           ORDER BY id DESC LIMIT ? OFFSET ?""",
        (incident_id, limit, offset),
    ).fetchall()

    flows = []
    for r in rows:
        pred = r["pred"]
        sev = SEVERITY_MAP.get(pred, "High" if r["anomalie_ae"] == 1 else "Medium")
        t_str = time.strftime("%H:%M:%S", time.localtime(r["received_at"]))
        conf_float = float(r["confiance"] or 0.0)
        anom_int = int(r["anomalie_ae"] or 0)
        flows.append(
            {
                "id": r["id"],
                "incident_id": r["incident_id"],
                "timestamp": t_str,
                "received_at": t_str,
                "sensor_id": r["sensor_id"] or "sensor-01",
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
    return flows


def close_inactive_incidents(
    inactivity_seconds: float = 45.0,
    now: Optional[float] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Identifie et clôture les incidents dont aucun nouveau flux
    n'a été reçu depuis plus de `inactivity_seconds`.
    Retourne la liste des incidents nouvellement clos pour notification de synthèse.
    """
    current_time = float(now if now is not None else time.time())
    threshold = current_time - inactivity_seconds

    con = get_connection(db_path)
    cur = con.cursor()
    rows = cur.execute(
        """SELECT id, incident_code, created_at, updated_at, attack_type, severity,
                  src_ip, dst_ip, sensor_id, flow_count, targeted_ports, ports_summary,
                  max_confidence, max_mse, is_zero_day, notified_open, notified_close
           FROM incidents
           WHERE status = 'OPEN' AND updated_at < ?""",
        (threshold,),
    ).fetchall()

    closed_incidents: List[Dict[str, Any]] = []
    if rows:
        ids_to_close = [r["id"] for r in rows]
        cur.execute(
            f"UPDATE incidents SET status = 'CLOSED', closed_at = ? WHERE id IN ({','.join('?' for _ in ids_to_close)})",
            [current_time] + ids_to_close,
        )
        con.commit()

        for r in rows:
            created = float(r["created_at"])
            updated = float(r["updated_at"])
            try:
                ports_list = json.loads(r["targeted_ports"] or "[]")
            except Exception:
                ports_list = []
            closed_incidents.append(
                {
                    "id": r["id"],
                    "incident_code": r["incident_code"] or f"INC-{r['id']:04d}",
                    "status": "CLOSED",
                    "attack_type": r["attack_type"],
                    "severity": r["severity"],
                    "src_ip": r["src_ip"],
                    "dst_ip": r["dst_ip"],
                    "sensor_id": r["sensor_id"],
                    "flow_count": int(r["flow_count"] or 1),
                    "targeted_ports": ports_list,
                    "ports_summary": r["ports_summary"] or summarize_ports(ports_list),
                    "max_confidence": float(r["max_confidence"] or 0.0),
                    "max_mse": float(r["max_mse"] or 0.0),
                    "is_zero_day": bool(r["is_zero_day"]),
                    "created_at": created,
                    "updated_at": updated,
                    "closed_at": current_time,
                    "duration_sec": max(1, int(updated - created)),
                    "notified_close": bool(r["notified_close"]),
                }
            )

    con.close()
    return closed_incidents


def mark_incident_notified(
    incident_id: int,
    open_notified: Optional[bool] = None,
    close_notified: Optional[bool] = None,
    db_path: Optional[str] = None,
) -> None:
    """Met à jour les indicateurs de notification d'ouverture et de fermeture."""
    con = get_connection(db_path)
    with con:
        if open_notified is not None:
            con.execute("UPDATE incidents SET notified_open = ? WHERE id = ?", (1 if open_notified else 0, incident_id))
        if close_notified is not None:
            con.execute("UPDATE incidents SET notified_close = ? WHERE id = ?", (1 if close_notified else 0, incident_id))
    con.close()


