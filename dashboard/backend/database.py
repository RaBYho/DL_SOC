import sqlite3
import time
from typing import Any, Dict, List, Optional
from dashboard.backend.config import DB_PATH


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = str(db_path or DB_PATH)
    con = sqlite3.connect(path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def init_db(db_path: Optional[str] = None) -> None:
    """Initialise le schéma de la base et crée les index pour des requêtes analytiques ultra-rapides."""
    con = get_connection(db_path)
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

        # Migration à chaud des colonnes de l'auto-encodeur si manquantes
        cols = [r[1] for r in con.execute("PRAGMA table_info(flows)").fetchall()]
        if "mse_ae" not in cols:
            con.execute("ALTER TABLE flows ADD COLUMN mse_ae REAL")
        if "anomalie_ae" not in cols:
            con.execute("ALTER TABLE flows ADD COLUMN anomalie_ae INTEGER")

        # Index pour optimiser les requêtes du Dashboard SOC (< 5 ms)
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_flows_received ON flows(received_at DESC)"
        )
        con.execute("CREATE INDEX IF NOT EXISTS idx_flows_pred ON flows(pred)")
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_flows_anomalie ON flows(anomalie_ae)"
        )
        con.execute("CREATE INDEX IF NOT EXISTS idx_flows_src_ip ON flows(src_ip)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_flows_dst_port ON flows(dst_port)")
    con.close()


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


def get_recent_alerts(
    limit: int = 60,
    search_ip: Optional[str] = None,
    category: Optional[str] = None,
    min_conf: float = 0.0,
    anomalies_only: bool = False,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retourne la liste filtrée des dernières alertes pour le tableau en direct."""
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

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

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
        alerts.append(
            {
                "id": r["id"],
                "timestamp": time.strftime(
                    "%H:%M:%S", time.localtime(r["received_at"])
                ),
                "sensor": r["sensor_id"] or "sensor-edge-01",
                "src_ip": r["src_ip"] or "0.0.0.0",
                "src_port": r["src_port"] or 0,
                "dst_ip": r["dst_ip"] or "0.0.0.0",
                "dst_port": r["dst_port"] or 0,
                "protocol": "TCP" if r["protocol"] == 6 else "UDP",
                "classification": pred,
                "confidence": round((r["confiance"] or 0.0) * 100.0, 1),
                "mse_ae": round(r["mse_ae"], 3) if r["mse_ae"] is not None else 0.0,
                "is_anomaly": bool(r["anomalie_ae"]),
                "severity": sev,
            }
        )

    con.close()
    return alerts
