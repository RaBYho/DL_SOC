"""Couche d'accès SQLite optimisée et thread-safe pour le stockage NIDS."""

from contextlib import contextmanager
import json
from pathlib import Path
import random
import sqlite3
import time
from typing import Any, Dict, Generator, List, Optional, Tuple

from dashboard.backend.config import DB_PATH


@contextmanager
def get_connection(db_path: Path = DB_PATH) -> Generator[sqlite3.Connection, None, None]:
    """Fournit une connexion SQLite configurée en mode WAL avec timeout."""
    conn = sqlite3.connect(str(db_path), timeout=15.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA busy_timeout = 10000;")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Path = DB_PATH) -> None:
    """Initialise le schéma de base de données avec indexation performante et migration douce."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection(db_path) as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS flows (
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
            anomalie_ae INTEGER,
            incident_id INTEGER,
            packet_count INTEGER DEFAULT 1,
            raw_metrics TEXT
        );

        CREATE TABLE IF NOT EXISTS incidents (
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
            packet_count INTEGER DEFAULT 1,
            targeted_ports TEXT,
            ports_summary TEXT,
            max_confidence REAL DEFAULT 0.0,
            max_mse REAL DEFAULT 0.0,
            is_zero_day INTEGER DEFAULT 0,
            notified_open INTEGER DEFAULT 0,
            notified_close INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS sensor_stats (
            sensor_id TEXT PRIMARY KEY,
            interface TEXT,
            status TEXT DEFAULT 'Online',
            last_heartbeat REAL,
            packets_captured INTEGER DEFAULT 0,
            flows_count INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            source TEXT,
            level TEXT,
            message TEXT,
            details TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_flows_received_at ON flows(received_at);
        CREATE INDEX IF NOT EXISTS idx_flows_pred ON flows(pred);
        CREATE INDEX IF NOT EXISTS idx_flows_src_dst ON flows(src_ip, dst_ip);
        CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
        CREATE INDEX IF NOT EXISTS idx_incidents_updated_at ON incidents(updated_at);
        CREATE INDEX IF NOT EXISTS idx_incidents_src_ip ON incidents(src_ip);
        """)

        # Migration automatique
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(flows)")
        flow_cols = {r["name"] for r in cursor.fetchall()}
        if "packet_count" not in flow_cols:
            conn.execute("ALTER TABLE flows ADD COLUMN packet_count INTEGER DEFAULT 1")
        if "incident_id" not in flow_cols:
            conn.execute("ALTER TABLE flows ADD COLUMN incident_id INTEGER")
        if "raw_metrics" not in flow_cols:
            conn.execute("ALTER TABLE flows ADD COLUMN raw_metrics TEXT")

        cursor.execute("PRAGMA table_info(incidents)")
        inc_cols = {r["name"] for r in cursor.fetchall()}
        if "packet_count" not in inc_cols:
            conn.execute("ALTER TABLE incidents ADD COLUMN packet_count INTEGER DEFAULT 1")


def _determine_severity(attack_type: str, is_zero_day: bool) -> str:
    """Attribue un niveau de sévérité SOC standard."""
    if is_zero_day:
        return "HIGH"
    att = str(attack_type).lower()
    if any(k in att for k in ["ddos", "dos", "infiltration", "bot", "heartbleed"]):
        return "CRITICAL"
    if any(k in att for k in ["portscan", "brute", "sql", "xss", "patator"]):
        return "HIGH"
    return "MEDIUM"


def insert_and_correlate_flows(
    flow_records: List[Dict[str, Any]],
    predictions: Optional[List[str]] = None,
    confidences: Optional[List[float]] = None,
    mse_values: Optional[List[float]] = None,
    anomaly_values: Optional[List[int]] = None,
    sensor_id: str = "sensor-live",
    received_at: Optional[float] = None,
    db_path: Path = DB_PATH,
) -> Tuple[int, int]:
    """Insère un lot de flux, stocke les métriques brutes et consolide les alertes."""
    if not flow_records:
        return 0, 0

    now = received_at or time.time()
    alerts_count = 0
    init_db(db_path)

    # Auto-extraction des scores si non fournis en liste séparée
    if predictions is None:
        predictions = [r.get("verdict", r.get("pred", "BENIGN")) for r in flow_records]
    if confidences is None:
        confidences = [float(r.get("confidence", r.get("confiance", 0.0))) for r in flow_records]
    if mse_values is None:
        mse_values = [float(r.get("kitsune_score", r.get("mse_ae", 0.0))) for r in flow_records]
    if anomaly_values is None:
        anomaly_values = [1 if (r.get("is_anomaly") or r.get("anomalie_ae") == 1) else 0 for r in flow_records]

    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Récupération des incidents ouverts récents (< 120s) pour corrélation
        cutoff_time = now - 120.0
        cursor.execute(
            """
            SELECT id, incident_code, src_ip, dst_ip, attack_type, targeted_ports, flow_count, packet_count, max_confidence, max_mse
            FROM incidents
            WHERE status = 'OPEN' AND updated_at >= ?
            """,
            (cutoff_time,),
        )
        open_incidents: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
        for row in cursor.fetchall():
            key = (row["src_ip"], row["dst_ip"], row["attack_type"])
            open_incidents[key] = dict(row)

        flows_to_insert = []
        updated_incidents: Dict[int, Dict[str, Any]] = {}

        for i, raw_rec in enumerate(flow_records):
            pred = predictions[i] if i < len(predictions) else "BENIGN"
            conf = float(confidences[i]) if i < len(confidences) else 0.0
            mse = float(mse_values[i]) if i < len(mse_values) else 0.0
            anom = int(anomaly_values[i]) if i < len(anomaly_values) else 0

            src_ip = str(raw_rec.get("Source IP", raw_rec.get("src_ip", "127.0.0.1")))
            dst_ip = str(raw_rec.get("Destination IP", raw_rec.get("dst_ip", "127.0.0.1")))
            src_port = int(raw_rec.get("Source Port", raw_rec.get("src_port", 0)))
            dst_port = int(raw_rec.get("Destination Port", raw_rec.get("dst_port", 80)))
            raw_proto = raw_rec.get("Protocol", raw_rec.get("protocol", 6))
            if isinstance(raw_proto, str):
                proto_map = {"tcp": 6, "udp": 17, "icmp": 1}
                proto = proto_map.get(raw_proto.lower(), 6)
            else:
                try:
                    proto = int(raw_proto)
                except (ValueError, TypeError):
                    proto = 6
            src_mac = str(raw_rec.get("src_mac", "00:00:00:00:00:00"))
            flow_start = float(raw_rec.get("flow_start_ms", now * 1000))

            # Extraction robuste des métriques (support top-level et nested raw_metrics)
            rm = raw_rec.get("raw_metrics") if isinstance(raw_rec.get("raw_metrics"), dict) else {}

            fwd_pkts = int(
                rm.get("total_fwd_packets")
                or rm.get("fwd_pkts")
                or raw_rec.get("Total Fwd Packets")
                or raw_rec.get("total_fwd_packets")
                or 1
            )
            bwd_pkts = int(
                rm.get("total_bwd_packets")
                or rm.get("bwd_pkts")
                or raw_rec.get("Total Backward Packets")
                or raw_rec.get("total_bwd_packets")
                or 0
            )
            pkt_count = max(1, fwd_pkts + bwd_pkts)

            flow_duration = float(
                rm.get("flow_duration")
                or rm.get("duration")
                or raw_rec.get("Flow Duration")
                or raw_rec.get("flow_duration")
                or 0.0
            )
            flow_bytes_s = float(
                rm.get("flow_bytes_s")
                or raw_rec.get("Flow Bytes/s")
                or raw_rec.get("flow_bytes_s")
                or 0.0
            )
            flow_packets_s = float(
                rm.get("flow_packets_s")
                or raw_rec.get("Flow Packets/s")
                or raw_rec.get("flow_packets_s")
                or 0.0
            )
            fwd_len_mean = float(
                rm.get("fwd_packet_length_mean")
                or raw_rec.get("Fwd Packet Length Mean")
                or raw_rec.get("fwd_packet_length_mean")
                or 0.0
            )
            bwd_len_mean = float(
                rm.get("bwd_packet_length_mean")
                or raw_rec.get("Bwd Packet Length Mean")
                or raw_rec.get("bwd_packet_length_mean")
                or 0.0
            )
            syn_flags = int(
                rm.get("syn_flag_count")
                or raw_rec.get("SYN Flag Count")
                or raw_rec.get("syn_flag_count")
                or 0
            )
            ack_flags = int(
                rm.get("ack_flag_count")
                or raw_rec.get("ACK Flag Count")
                or raw_rec.get("ack_flag_count")
                or 0
            )
            psh_flags = int(
                rm.get("psh_flag_count")
                or raw_rec.get("PSH Flag Count")
                or raw_rec.get("psh_flag_count")
                or 0
            )
            fin_flags = int(
                rm.get("fin_flag_count")
                or raw_rec.get("FIN Flag Count")
                or raw_rec.get("fin_flag_count")
                or 0
            )
            rst_flags = int(
                rm.get("rst_flag_count")
                or raw_rec.get("RST Flag Count")
                or raw_rec.get("rst_flag_count")
                or 0
            )
            down_up = float(
                rm.get("down_up_ratio")
                or raw_rec.get("Down/Up Ratio")
                or raw_rec.get("down_up_ratio")
                or 0.0
            )
            avg_size = float(
                rm.get("avg_packet_size")
                or raw_rec.get("Average Packet Size")
                or raw_rec.get("avg_packet_size")
                or 0.0
            )
            dpi_rule = str(
                rm.get("dpi_rule")
                or raw_rec.get("dpi_rule")
                or ""
            )
            all_feats = rm.get("all_features") or raw_rec.get("all_features") or {}

            forensics_metrics = {
                "flow_duration": flow_duration,
                "flow_bytes_s": flow_bytes_s,
                "flow_packets_s": flow_packets_s,
                "total_fwd_packets": fwd_pkts,
                "total_bwd_packets": bwd_pkts,
                "fwd_packet_length_mean": fwd_len_mean,
                "bwd_packet_length_mean": bwd_len_mean,
                "syn_flag_count": syn_flags,
                "ack_flag_count": ack_flags,
                "psh_flag_count": psh_flags,
                "fin_flag_count": fin_flags,
                "rst_flag_count": rst_flags,
                "down_up_ratio": down_up,
                "avg_packet_size": avg_size,
                "dpi_rule": dpi_rule,
                "all_features": all_feats,
            }
            metrics_json = json.dumps(forensics_metrics)

            incident_id = None
            is_loopback = (
                src_ip.startswith("127.")
                or dst_ip.startswith("127.")
                or src_ip in ("localhost", "::1")
                or dst_ip in ("localhost", "::1")
            )

            is_zero_day = (pred == "BENIGN" and anom == 1)
            attack_type = "ANOMALY_UNKNOWN" if is_zero_day else pred
            corr_key = (src_ip, dst_ip, attack_type)

            if is_loopback:
                is_malicious = False
            else:
                is_confirmed_alert = bool(raw_rec.get("is_confirmed_alert", False))
                has_dpi_signature = bool(dpi_rule and str(dpi_rule).strip() != "")
                is_high_conf_attack = (pred != "BENIGN" and conf >= 0.85)
                is_ongoing_incident = (corr_key in open_incidents)

                is_malicious = (
                    is_confirmed_alert
                    or has_dpi_signature
                    or is_high_conf_attack
                    or is_ongoing_incident
                )

            if is_malicious:
                alerts_count += 1

                if corr_key in open_incidents:
                    inc = open_incidents[corr_key]
                    inc_id = inc["id"]
                    ports = set(str(inc["targeted_ports"] or "").split(",")) if inc["targeted_ports"] else set()
                    ports.add(str(dst_port))
                    ports.discard("")
                    ports_str = ",".join(sorted(ports)[:10])

                    inc["flow_count"] += 1
                    inc["packet_count"] = inc.get("packet_count", 1) + pkt_count
                    inc["max_confidence"] = max(inc["max_confidence"], conf)
                    inc["max_mse"] = max(inc["max_mse"], mse)
                    inc["targeted_ports"] = ports_str
                    inc["ports_summary"] = f"{len(ports)} port(s)"
                    inc["updated_at"] = now
                    updated_incidents[inc_id] = inc
                    incident_id = inc_id
                else:
                    code = f"INC-{int(now)}-{random.randint(100, 999)}"
                    severity = _determine_severity(attack_type, is_zero_day)
                    new_inc = {
                        "incident_code": code,
                        "created_at": now,
                        "updated_at": now,
                        "status": "OPEN",
                        "attack_type": attack_type,
                        "severity": severity,
                        "src_ip": src_ip,
                        "dst_ip": dst_ip,
                        "sensor_id": sensor_id,
                        "flow_count": 1,
                        "packet_count": pkt_count,
                        "targeted_ports": str(dst_port),
                        "ports_summary": "1 port",
                        "max_confidence": conf,
                        "max_mse": mse,
                        "is_zero_day": 1 if is_zero_day else 0,
                    }
                    cursor.execute(
                        """
                        INSERT INTO incidents (
                            incident_code, created_at, updated_at, status, attack_type, severity,
                            src_ip, dst_ip, sensor_id, flow_count, packet_count, targeted_ports,
                            ports_summary, max_confidence, max_mse, is_zero_day
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            new_inc["incident_code"], new_inc["created_at"], new_inc["updated_at"],
                            new_inc["status"], new_inc["attack_type"], new_inc["severity"],
                            new_inc["src_ip"], new_inc["dst_ip"], new_inc["sensor_id"],
                            new_inc["flow_count"], new_inc["packet_count"], new_inc["targeted_ports"],
                            new_inc["ports_summary"], new_inc["max_confidence"], new_inc["max_mse"],
                            new_inc["is_zero_day"]
                        ),
                    )
                    incident_id = cursor.lastrowid
                    new_inc["id"] = incident_id
                    open_incidents[corr_key] = new_inc

            flows_to_insert.append((
                now, sensor_id, flow_start, src_ip, src_mac, src_port, dst_ip, dst_port,
                proto, pred, conf, mse, anom, incident_id, pkt_count, metrics_json
            ))

        # Mise à jour des incidents existants
        for inc_id, inc_data in updated_incidents.items():
            cursor.execute(
                """
                UPDATE incidents SET
                    updated_at = ?,
                    flow_count = ?,
                    packet_count = ?,
                    targeted_ports = ?,
                    ports_summary = ?,
                    max_confidence = ?,
                    max_mse = ?
                WHERE id = ?
                """,
                (
                    inc_data["updated_at"], inc_data["flow_count"], inc_data["packet_count"],
                    inc_data["targeted_ports"], inc_data["ports_summary"], inc_data["max_confidence"],
                    inc_data["max_mse"], inc_id
                ),
            )

        # Insertion en masse des flux
        cursor.executemany(
            """
            INSERT INTO flows (
                received_at, sensor_id, flow_start_ms, src_ip, src_mac, src_port,
                dst_ip, dst_port, protocol, pred, confiance, mse_ae, anomalie_ae,
                incident_id, packet_count, raw_metrics
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            flows_to_insert,
        )

        # Mise à jour de la télémétrie sonde
        total_batch_packets = sum(f[14] for f in flows_to_insert)
        cursor.execute(
            """
            INSERT INTO sensor_stats (sensor_id, interface, status, last_heartbeat, packets_captured, flows_count)
            VALUES (?, 'live', 'Online', ?, ?, ?)
            ON CONFLICT(sensor_id) DO UPDATE SET
                last_heartbeat = excluded.last_heartbeat,
                packets_captured = sensor_stats.packets_captured + excluded.packets_captured,
                flows_count = sensor_stats.flows_count + excluded.flows_count
            """,
            (sensor_id, now, total_batch_packets, len(flows_to_insert)),
        )

    return len(flow_records), alerts_count


def record_sensor_heartbeat(
    sensor_id: str,
    interface: str,
    status: str = "Online",
    packets_captured: int = 0,
    flows_count: int = 0,
    db_path: Path = DB_PATH,
) -> None:
    """Enregistre le battement de cœur d'une sonde avec ses compteurs."""
    init_db(db_path)
    now = time.time()
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO sensor_stats (sensor_id, interface, status, last_heartbeat, packets_captured, flows_count)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(sensor_id) DO UPDATE SET
                interface = excluded.interface,
                status = excluded.status,
                last_heartbeat = excluded.last_heartbeat,
                packets_captured = CASE WHEN excluded.packets_captured > 0 THEN excluded.packets_captured ELSE sensor_stats.packets_captured END,
                flows_count = CASE WHEN excluded.flows_count > 0 THEN excluded.flows_count ELSE sensor_stats.flows_count END
            """,
            (sensor_id, interface, status, now, packets_captured, flows_count),
        )


def log_system_event(
    source: str,
    message: str,
    level: str = "INFO",
    details: Optional[Dict[str, Any]] = None,
    db_path: Path = DB_PATH,
) -> None:
    """Consigne un log système technique dans SQLite."""
    init_db(db_path)
    details_str = json.dumps(details) if details else None
    with get_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO system_logs (timestamp, source, level, message, details) VALUES (?, ?, ?, ?, ?)",
            (time.time(), source, level, message, details_str),
        )


PORT_SERVICE_MAP = {
    80: "HTTP",
    443: "HTTPS",
    22: "SSH",
    21: "FTP",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    3389: "RDP",
    8080: "HTTP-Alt",
    8443: "HTTPS-Alt",
    445: "SMB",
    1433: "MSSQL",
    3306: "MySQL",
    5432: "PostgreSQL",
    6379: "Redis",
    27017: "MongoDB",
}


def get_targeted_stats(exclude_loopback: bool = False, db_path: Path = DB_PATH) -> Dict[str, Any]:
    """Extrait les statistiques sur le port et l'adresse IP la plus ciblée par les flux d'attaque."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        p_query = """
            SELECT dst_port, COUNT(*) as attack_count
            FROM flows
            WHERE (pred != 'BENIGN' OR anomalie_ae = 1)
              AND (? = 0 OR (src_ip NOT LIKE '127.%' AND dst_ip NOT LIKE '127.%' AND src_ip != '::1' AND dst_ip != '::1'))
            GROUP BY dst_port
            ORDER BY attack_count DESC
            LIMIT 5
        """
        rows_ports = conn.execute(p_query, (1 if exclude_loopback else 0,)).fetchall()

        ports_list = []
        for r in rows_ports:
            p_num = int(r["dst_port"])
            ports_list.append({
                "port": p_num,
                "service": PORT_SERVICE_MAP.get(p_num, f"PORT-{p_num}"),
                "attack_count": int(r["attack_count"]),
            })

        top_port_info = ports_list[0] if ports_list else {"port": "-", "service": "-", "attack_count": 0}

        v_query = """
            SELECT dst_ip, COUNT(*) as attack_count, COUNT(DISTINCT src_ip) as attacker_count
            FROM flows
            WHERE (pred != 'BENIGN' OR anomalie_ae = 1)
              AND (? = 0 OR (src_ip NOT LIKE '127.%' AND dst_ip NOT LIKE '127.%' AND src_ip != '::1' AND dst_ip != '::1'))
            GROUP BY dst_ip
            ORDER BY attack_count DESC
            LIMIT 5
        """
        rows_victims = conn.execute(v_query, (1 if exclude_loopback else 0,)).fetchall()

        victims_list = []
        for r in rows_victims:
            victims_list.append({
                "ip": str(r["dst_ip"]),
                "attack_count": int(r["attack_count"]),
                "attacker_count": int(r["attacker_count"]),
            })

        top_victim_info = victims_list[0] if victims_list else {"ip": "-", "attack_count": 0}

        return {
            "top_targeted_port": top_port_info["port"],
            "top_targeted_service": top_port_info["service"],
            "top_targeted_port_service": top_port_info["service"],
            "top_targeted_port_count": top_port_info["attack_count"],
            "top_targeted_ip": top_victim_info["ip"],
            "top_targeted_ip_count": top_victim_info["attack_count"],
            "targeted_ports": ports_list,
            "top_ports": ports_list,
            "targeted_victims": victims_list,
            "top_victims": victims_list,
        }


def get_threat_actors(limit: int = 50, exclude_loopback: bool = False, db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    """Génère la liste d'investigation des attaquants / criminels les plus prolifiques (Criminal List)."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        query = """
            SELECT 
                src_ip,
                COUNT(*) as attack_count,
                COUNT(DISTINCT dst_ip) as victim_count,
                COUNT(DISTINCT dst_port) as targeted_ports_count,
                GROUP_CONCAT(DISTINCT pred) as threat_classes,
                GROUP_CONCAT(DISTINCT dst_port) as targeted_ports,
                MAX(confiance) as max_confidence,
                MAX(mse_ae) as max_mse,
                MAX(received_at) as last_seen,
                MIN(received_at) as first_seen,
                MAX(CASE WHEN pred IN ('DDoS', 'Bot', 'Infiltration', 'Heartbleed') THEN 'CRITICAL'
                         WHEN pred != 'BENIGN' OR anomalie_ae = 1 THEN 'HIGH'
                         ELSE 'MEDIUM' END) as severity
            FROM flows
            WHERE (pred != 'BENIGN' OR anomalie_ae = 1)
              AND (? = 0 OR (src_ip NOT LIKE '127.%' AND src_ip != '::1'))
            GROUP BY src_ip
            ORDER BY attack_count DESC
            LIMIT ?
        """
        rows = conn.execute(query, (1 if exclude_loopback else 0, limit)).fetchall()

        actors = []
        for i, r in enumerate(rows):
            src_ip = str(r["src_ip"])
            threat_str = str(r["threat_classes"] or "ANOMALY_UNKNOWN")
            threats = [t.strip() for t in threat_str.split(",") if t.strip()]
            top_threat = threats[0] if threats else "Malicious"

            ports_raw = str(r["targeted_ports"] or "")
            ports = [p.strip() for p in ports_raw.split(",") if p.strip()]
            ports_display = ", ".join(ports[:4]) + ("..." if len(ports) > 4 else "")

            actors.append({
                "rank": i + 1,
                "src_ip": src_ip,
                "is_loopback": src_ip.startswith("127."),
                "total_attacks": int(r["attack_count"]),
                "victim_count": int(r["victim_count"]),
                "targeted_ports_count": int(r["targeted_ports_count"]),
                "targeted_ports": [int(p) for p in ports if p.isdigit()],
                "targeted_ports_summary": ports_display,
                "threat_classes": threats,
                "top_attack_type": top_threat,
                "max_confidence": float(r["max_confidence"] or 0.0),
                "max_mse": float(r["max_mse"] or 0.0),
                "severity": str(r["severity"] or "HIGH"),
                "first_seen": float(r["first_seen"] or 0.0),
                "last_seen": float(r["last_seen"] or 0.0),
                "status": "FLAGGED",
            })
        return actors


def get_kpis(exclude_loopback: bool = False, db_path: Path = DB_PATH) -> Dict[str, Any]:
    """Calcule les KPI opérationnels incluant le port et l'IP la plus ciblée."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        loop_cond = "AND (? = 0 OR (src_ip != '127.0.0.1' AND dst_ip != '127.0.0.1'))"
        l_flag = 1 if exclude_loopback else 0

        r_flows = conn.execute("SELECT COUNT(*) as c FROM flows WHERE 1=1 " + loop_cond, (l_flag,)).fetchone()
        r_pkts = conn.execute("SELECT COALESCE(SUM(packet_count), 0) as c FROM flows WHERE 1=1 " + loop_cond, (l_flag,)).fetchone()
        r_crit = conn.execute("SELECT COUNT(*) as c FROM incidents WHERE severity = 'CRITICAL' AND (? = 0 OR (src_ip != '127.0.0.1' AND dst_ip != '127.0.0.1'))", (l_flag,)).fetchone()
        r_anom = conn.execute("SELECT COUNT(*) as c FROM flows WHERE anomalie_ae = 1 " + loop_cond, (l_flag,)).fetchone()
        r_benign = conn.execute("SELECT COUNT(*) as c FROM flows WHERE pred = 'BENIGN' AND anomalie_ae = 0 " + loop_cond, (l_flag,)).fetchone()
        r_inc = conn.execute("SELECT COUNT(*) as c FROM incidents WHERE status = 'OPEN' AND (? = 0 OR (src_ip != '127.0.0.1' AND dst_ip != '127.0.0.1'))", (l_flag,)).fetchone()
        r_sensors = conn.execute("SELECT COUNT(*) as c FROM sensor_stats WHERE status = 'Online'").fetchone()

        total_flows = int(r_flows["c"] or 0)
        benign_flows = int(r_benign["c"] or 0)
        filtering_rate_pct = round((benign_flows / total_flows * 100.0), 1) if total_flows > 0 else 100.0

        # Stats cibles & Criminels
        target_stats = get_targeted_stats(exclude_loopback=exclude_loopback, db_path=db_path)
        top_criminals = get_threat_actors(limit=1, exclude_loopback=exclude_loopback, db_path=db_path)
        top_criminal = top_criminals[0]["src_ip"] if top_criminals else "-"
        top_criminal_attacks = top_criminals[0]["total_attacks"] if top_criminals else 0
        top_criminal_threat = top_criminals[0]["top_attack_type"] if top_criminals else "-"

        # Vecteur d'attaque dominant
        r_top_vec = conn.execute(
            """
            SELECT pred, COUNT(*) as c
            FROM flows
            WHERE pred != 'BENIGN' AND (? = 0 OR (src_ip != '127.0.0.1' AND dst_ip != '127.0.0.1'))
            GROUP BY pred
            ORDER BY c DESC LIMIT 1
            """,
            (l_flag,),
        ).fetchone()
        top_vector = r_top_vec["pred"] if r_top_vec else "BENIGN"

        r_dpi_cnt = conn.execute(
            """
            SELECT COUNT(*) as c
            FROM flows
            WHERE (pred LIKE 'Web Attack%' OR pred = 'Infiltration')
              AND (? = 0 OR (src_ip != '127.0.0.1' AND dst_ip != '127.0.0.1'))
            """,
            (l_flag,),
        ).fetchone()

        return {
            "total_packets": int(r_pkts["c"] or 0),
            "total_flows": total_flows,
            "critical_attacks": int(r_crit["c"] or 0),
            "critical_alerts": int(r_crit["c"] or 0),
            "anomalies": int(r_anom["c"] or 0),
            "zero_days": int(r_anom["c"] or 0),
            "open_incidents": int(r_inc["c"] or 0),
            "filtering_rate_pct": filtering_rate_pct,
            "inspection_rate_pct": round(100.0 - filtering_rate_pct, 1) if total_flows > 0 else 0.0,
            "top_vector": top_vector,
            "dpi_triggered": int(r_dpi_cnt["c"] or 0) if r_dpi_cnt else 0,
            "top_attacker_ip": top_criminal,
            "top_attacker_attacks": top_criminal_attacks,
            "top_attacker_threat": top_criminal_threat,
            "top_targeted_ip": target_stats.get("top_targeted_ip", "-"),
            "top_targeted_port": target_stats.get("top_targeted_port", "-"),
            "top_targeted_service": target_stats.get("top_targeted_port_service", "-"),
            "active_sensors": max(1, int(r_sensors["c"] or 0)),
        }


def get_traffic_summary(db_path: Path = DB_PATH) -> Dict[str, Any]:
    """Synthétise l'état global du trafic réseau pour la top status bar."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        row_totals = conn.execute(
            """
            SELECT 
                COUNT(*) as total_flows,
                COALESCE(SUM(packet_count), 0) as total_packets,
                SUM(CASE WHEN (pred != 'BENIGN' OR anomalie_ae = 1) AND (src_ip != '127.0.0.1' AND dst_ip != '127.0.0.1') THEN 1 ELSE 0 END) as total_attacks,
                SUM(CASE WHEN (pred = 'BENIGN' AND anomalie_ae = 1) AND (src_ip != '127.0.0.1' AND dst_ip != '127.0.0.1') THEN 1 ELSE 0 END) as total_zero_days
            FROM flows
            """
        ).fetchone()

        total_flows = int(row_totals["total_flows"] or 0)
        total_packets = int(row_totals["total_packets"] or 0)
        total_attacks = int(row_totals["total_attacks"] or 0)
        total_zero_days = int(row_totals["total_zero_days"] or 0)

        now = time.time()
        row_recent = conn.execute(
            """
            SELECT COUNT(*) as recent_flows,
                   SUM(CASE WHEN (pred != 'BENIGN' OR anomalie_ae = 1) AND (src_ip != '127.0.0.1' AND dst_ip != '127.0.0.1') THEN 1 ELSE 0 END) as recent_attacks
            FROM flows
            WHERE received_at >= ?
            """,
            (now - 60.0,),
        ).fetchone()

        recent_flows = int(row_recent["recent_flows"] or 0)
        recent_attacks = int(row_recent["recent_attacks"] or 0)
        attack_ratio = (total_attacks / total_flows * 100.0) if total_flows > 0 else 0.0

        if recent_attacks >= 5 or (total_attacks > 0 and attack_ratio > 15.0):
            status = "CRITICAL"
        elif recent_attacks > 0 or total_zero_days > 0 or (total_attacks > 0 and attack_ratio > 3.0):
            status = "ELEVATED"
        else:
            status = "NORMAL"

        return {
            "status": status,
            "total_packets": total_packets,
            "total_flows": total_flows,
            "total_attacks": total_attacks,
            "total_zero_days": total_zero_days,
            "attack_ratio_pct": round(attack_ratio, 2),
            "throughput_flows_sec": round(recent_flows / 60.0, 2),
        }


def get_timeline(
    window_minutes: int = 15,
    buckets: int = 20,
    exclude_loopback: bool = False,
    db_path: Path = DB_PATH,
) -> List[Dict[str, Any]]:
    """Génère la série temporelle : flux normaux (zinc) vs pics d'attaques (rouge/ambre).

    Les buckets sont ancrés sur des multiples entiers de bucket_duration pour
    garantir la stabilité absolue des labels et éliminer tout clignotement Chart.js.
    """
    init_db(db_path)
    now = time.time()
    bucket_duration = max(5.0, (window_minutes * 60.0) / max(1, buckets))

    # Ancrage des tranches sur des frontières temporelles fixes (ex: multiples de 30s ou 45s)
    current_bucket_start = (int(now) // int(bucket_duration)) * int(bucket_duration)
    start_time = current_bucket_start - ((buckets - 1) * bucket_duration)

    query = """
        SELECT received_at, pred, anomalie_ae, packet_count, src_ip, dst_ip
        FROM flows
        WHERE received_at >= ?
    """
    params: List[Any] = [start_time]
    if exclude_loopback:
        query += " AND src_ip != '127.0.0.1' AND dst_ip != '127.0.0.1'"
    query += " ORDER BY received_at ASC"

    with get_connection(db_path) as conn:
        rows = conn.execute(query, params).fetchall()

    timeline = []
    for b in range(buckets):
        b_start = start_time + (b * bucket_duration)
        b_end = b_start + bucket_duration
        is_last = (b == buckets - 1)
        flows_in_b = [
            r for r in rows
            if (b_start <= r["received_at"] <= (now + 1.0) if is_last else b_start <= r["received_at"] < b_end)
        ]
        normal_cnt = sum(1 for r in flows_in_b if r["pred"] == "BENIGN" and r["anomalie_ae"] == 0)
        attack_cnt = sum(1 for r in flows_in_b if r["pred"] != "BENIGN")
        anom_cnt = sum(1 for r in flows_in_b if r["pred"] == "BENIGN" and r["anomalie_ae"] == 1)
        packets_cnt = sum(r["packet_count"] for r in flows_in_b)

        time_label = time.strftime("%H:%M:%S", time.localtime(b_start))
        timeline.append({
            "timestamp": b_start,
            "label": time_label,
            "normal": normal_cnt,
            "attacks": attack_cnt,
            "anomalies": anom_cnt,
            "packets": packets_cnt,
            "total": normal_cnt + attack_cnt + anom_cnt,
        })
    return timeline


def get_engine_distribution(exclude_loopback: bool = False, db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    """Ventile la détection par moteur : Signature DPI vs ML Supervisé vs Kitsune Anomaly."""
    init_db(db_path)
    loopback_clause = " AND src_ip != '127.0.0.1' AND dst_ip != '127.0.0.1'" if exclude_loopback else ""
    with get_connection(db_path) as conn:
        r_dpi = conn.execute(
            f"SELECT COUNT(*) as c FROM flows WHERE (pred LIKE 'Web Attack%' OR pred = 'Infiltration'){loopback_clause}"
        ).fetchone()
        r_ml = conn.execute(
            f"SELECT COUNT(*) as c FROM flows WHERE pred IN ('DDoS', 'PortScan', 'Bot', 'FTP-Patator', 'SSH-Patator'){loopback_clause}"
        ).fetchone()
        r_kit = conn.execute(
            f"SELECT COUNT(*) as c FROM flows WHERE anomalie_ae = 1{loopback_clause}"
        ).fetchone()
        r_benign = conn.execute(
            f"SELECT COUNT(*) as c FROM flows WHERE pred = 'BENIGN' AND anomalie_ae = 0{loopback_clause}"
        ).fetchone()

        c_dpi = int(r_dpi["c"] or 0)
        c_ml = int(r_ml["c"] or 0)
        c_kit = int(r_kit["c"] or 0)
        c_ben = int(r_benign["c"] or 0)

        return [
            {"engine": "DPI Signature", "count": c_dpi, "color": "#f97316"},
            {"engine": "ML Supervised (1D-DNN)", "count": c_ml, "color": "#ef4444"},
            {"engine": "Kitsune KitNET (0-Day)", "count": c_kit, "color": "#eab308"},
            {"engine": "Benign Traffic", "count": c_ben, "color": "#10b981"},
        ]


def get_attack_distribution(db_path: Path = DB_PATH) -> Dict[str, int]:
    """Retourne la répartition des attaques par classe détectée."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT pred, COUNT(*) as count
            FROM flows
            WHERE pred != 'BENIGN'
            GROUP BY pred
            ORDER BY count DESC
            """
        ).fetchall()
        dist = {row["pred"]: int(row["count"]) for row in rows}
        if not dist:
            dist["BENIGN"] = 1
        return dist


def get_consolidated_alerts(
    limit: int = 50,
    offset: int = 0,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    exclude_loopback: bool = False,
    db_path: Path = DB_PATH,
) -> List[Dict[str, Any]]:
    """Récupère les alertes et incidents consolidés paginés avec filtres."""
    init_db(db_path)
    query = "SELECT * FROM incidents WHERE 1=1"
    params: List[Any] = []

    if exclude_loopback:
        query += " AND src_ip != '127.0.0.1' AND dst_ip != '127.0.0.1'"
    if severity:
        query += " AND severity = ?"
        params.append(severity.upper())
    if status:
        query += " AND status = ?"
        params.append(status.upper())
    if search:
        query += " AND (src_ip LIKE ? OR dst_ip LIKE ? OR attack_type LIKE ? OR incident_code LIKE ?)"
        s_pat = f"%{search}%"
        params.extend([s_pat, s_pat, s_pat, s_pat])

    query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_connection(db_path) as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_recent_flows(
    limit: int = 100,
    exclude_loopback: bool = False,
    db_path: Path = DB_PATH,
) -> List[Dict[str, Any]]:
    """Récupère les flux récents avec leurs métriques et niveaux de sévérité."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        query = "SELECT * FROM flows WHERE 1=1"
        params: List[Any] = []
        if exclude_loopback:
            count_non_loop = conn.execute(
                "SELECT COUNT(*) FROM flows WHERE src_ip != '127.0.0.1' AND dst_ip != '127.0.0.1'"
            ).fetchone()[0]
            if count_non_loop > 0:
                query += " AND src_ip != '127.0.0.1' AND dst_ip != '127.0.0.1'"
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            pred = d.get("pred", "BENIGN")
            anom = d.get("anomalie_ae", 0)
            is_zero_day = (pred == "BENIGN" and anom == 1)
            attack_type = "ANOMALY_UNKNOWN" if is_zero_day else pred

            # Calcul du niveau de sévérité sémantique
            if attack_type == "BENIGN":
                severity = "BENIGN"
            else:
                severity = _determine_severity(attack_type, is_zero_day)

            d["severity"] = severity
            d["threat_class"] = attack_type

            # Détermination du moteur responsable
            if "Web Attack" in attack_type or attack_type == "Infiltration":
                d["engine"] = "DPI Regex"
            elif is_zero_day:
                d["engine"] = "Kitsune (0-Day)"
            elif pred != "BENIGN":
                d["engine"] = "DNN-1D (Supervisé)"
            else:
                d["engine"] = "Filtrage Rapide"

            # Parse des métriques brutes
            if d.get("raw_metrics"):
                try:
                    d["metrics"] = json.loads(d["raw_metrics"])
                except Exception:
                    d["metrics"] = {}
            else:
                d["metrics"] = {}

            result.append(d)
        return result


def get_flow_forensics(flow_id: int, db_path: Path = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retourne l'ensemble des données d'investigation médico-légale (Forensics Drawer)."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM flows WHERE id = ?", (flow_id,)).fetchone()
        if not row:
            return None
        flow = dict(row)
        metrics = json.loads(flow.get("raw_metrics") or "{}")

        # Calcul sémantique de la sévérité et du moteur responsable
        pred = flow.get("pred", "BENIGN")
        anom = flow.get("anomalie_ae", 0)
        is_zero_day = (pred == "BENIGN" and anom == 1)
        attack_type = "ANOMALY_UNKNOWN" if is_zero_day else pred

        if attack_type == "BENIGN":
            flow["severity"] = "BENIGN"
        else:
            flow["severity"] = _determine_severity(attack_type, is_zero_day)

        if "Web Attack" in attack_type or attack_type == "Infiltration":
            flow["engine"] = "DPI Regex"
        elif is_zero_day:
            flow["engine"] = "Kitsune (0-Day)"
        elif pred != "BENIGN":
            flow["engine"] = "DNN-1D (Supervisé)"
        else:
            flow["engine"] = "Filtrage Rapide"

        # Récupération de l'incident associé s'il existe
        incident = None
        if flow.get("incident_id"):
            inc_row = conn.execute("SELECT * FROM incidents WHERE id = ?", (flow["incident_id"],)).fetchone()
            if inc_row:
                incident = dict(inc_row)

        # Historique des flux récents pour cette IP source (détection de récurrence)
        src_ip = flow.get("src_ip", "")
        ip_history = conn.execute(
            "SELECT id, received_at, dst_port, pred, confiance, mse_ae FROM flows WHERE src_ip = ? ORDER BY id DESC LIMIT 10",
            (src_ip,)
        ).fetchall()

        return {
            "flow": flow,
            "metrics": metrics,
            "incident": incident,
            "ip_history": [dict(r) for r in ip_history],
        }


def get_incident_by_id(incident_id: Any, db_path: Path = DB_PATH) -> Optional[Dict[str, Any]]:
    """Récupère le détail complet d'un incident et ses flux associés (par ID numérique ou code INC-...)."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM incidents WHERE id = ? OR incident_code = ?",
            (str(incident_id), str(incident_id)),
        ).fetchone()
        if not row:
            return None
        inc = dict(row)
        flows = conn.execute(
            "SELECT * FROM flows WHERE incident_id = ? ORDER BY received_at DESC LIMIT 20",
            (inc["id"],)
        ).fetchall()
        inc["associated_flows"] = [dict(f) for f in flows]
        return inc


def update_incident_status(incident_id: Any, status: str, db_path: Path = DB_PATH) -> bool:
    """Met à jour le statut d'un incident (par ID numérique ou code INC-...)."""
    init_db(db_path)
    now = time.time()
    closed_at = now if status in ["RESOLVED", "FALSE_POSITIVE"] else None
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            "UPDATE incidents SET status = ?, updated_at = ?, closed_at = ? WHERE id = ? OR incident_code = ?",
            (status, now, closed_at, str(incident_id), str(incident_id)),
        )
        return cursor.rowcount > 0


def get_sensors_list(db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    """Retourne la liste des sondes réseau enregistrées."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM sensor_stats ORDER BY last_heartbeat DESC").fetchall()
        return [dict(r) for r in rows]


def reset_database(db_path: Path = DB_PATH) -> None:
    """Réinitialise les tables pour les scénarios de test."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        conn.executescript("""
        DELETE FROM flows;
        DELETE FROM incidents;
        DELETE FROM sensor_stats;
        DELETE FROM system_logs;
        DELETE FROM sqlite_sequence;
        """)
