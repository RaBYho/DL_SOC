import time
import os
import logging
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional
import psutil

from dashboard.backend.config import DB_PATH, ACTIVE_DNN_VERSION, ACTIVE_AE_VERSION
from dashboard.backend.database import get_connection, get_active_sensors
from dashboard.backend.ws_manager import ws_manager

logger = logging.getLogger("dashboard.health")


class HealthService:
    def __init__(self):
        self.start_time: float = time.time()
        self._inference_latencies: deque = deque(maxlen=50)
        self._system_logs: deque = deque(maxlen=100)

        # Log de démarrage du service
        self.log_system_event(
            level="INFO",
            source="System",
            message="Initialisation du moniteur de santé système NIDS HDVR"
        )

    def record_inference_latency(self, latency_ms: float) -> None:
        """Enregistre le temps d'inférence d'un batch de flux."""
        if latency_ms >= 0:
            self._inference_latencies.append(latency_ms)

    def log_system_event(
        self, 
        level: str, 
        source: str, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Ajoute un log technique d'infrastructure."""
        entry = {
            "timestamp": time.time(),
            "time_str": time.strftime("%H:%M:%S", time.localtime()),
            "level": level.upper(),  # INFO, WARNING, ERROR, CRITICAL
            "source": source,        # Sensors, Database, AI-Engine, WebSocket, Host
            "message": message,
            "details": details or {}
        }
        self._system_logs.append(entry)
        if level.upper() in ("ERROR", "CRITICAL"):
            logger.error(f"[{source}] {message} - {details or ''}")
        elif level.upper() == "WARNING":
            logger.warning(f"[{source}] {message} - {details or ''}")
        else:
            logger.info(f"[{source}] {message}")

    def get_system_logs(self, limit: int = 50, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retourne les derniers logs techniques d'infrastructure."""
        logs = list(self._system_logs)
        if level:
            logs = [l for l in logs if l["level"] == level.upper()]
        return list(reversed(logs))[:limit]

    def _check_sensors(self) -> Dict[str, Any]:
        """Évalue l'état de santé du parc de sondes et de l'ingestion."""
        try:
            sensors = get_active_sensors()
            total_sensors = len(sensors)
            online_count = sum(1 for s in sensors if s.get("status") == "Online")
            
            # Temps écoulé depuis le dernier flux ingéré toutes sondes confondues
            last_seen_epoch = 0.0
            for s in sensors:
                if s.get("last_seen_epoch") and s["last_seen_epoch"] > last_seen_epoch:
                    last_seen_epoch = s["last_seen_epoch"]

            sec_since_last_flow = time.time() - last_seen_epoch if last_seen_epoch > 0 else 999999

            if online_count > 0 or sec_since_last_flow < 20:
                status = "ONLINE"
            elif total_sensors > 0 and sec_since_last_flow < 120:
                status = "DEGRADED"
            else:
                status = "OFFLINE"

            return {
                "status": status,
                "total_sensors": total_sensors,
                "online_sensors": online_count,
                "last_flow_sec_ago": round(sec_since_last_flow, 1) if sec_since_last_flow < 999999 else None,
                "message": f"{online_count} sonde(s) en ligne sur {total_sensors}"
            }
        except Exception as e:
            self.log_system_event("ERROR", "Sensors", f"Échec de diagnostic des sondes: {str(e)}")
            return {
                "status": "ERROR",
                "total_sensors": 0,
                "online_sensors": 0,
                "error": str(e)
            }

    def _check_database(self) -> Dict[str, Any]:
        """Vérifie l'intégrité, la taille et la latence de la base SQLite."""
        start = time.perf_counter()
        db_path = Path(DB_PATH)
        file_size_mb = 0.0
        if db_path.exists():
            file_size_mb = round(db_path.stat().st_size / (1024 * 1024), 2)

        try:
            con = get_connection()
            with con:
                # Test de lecture et mode journal
                journal_mode = con.execute("PRAGMA journal_mode;").fetchone()[0]
                integrity = con.execute("PRAGMA quick_check;").fetchone()[0]
                flows_count = con.execute("SELECT count(*) FROM flows;").fetchone()[0]
            con.close()

            latency_ms = round((time.perf_counter() - start) * 1000, 2)

            if integrity.lower() != "ok":
                status = "CORRUPT"
            elif latency_ms > 200:
                status = "HIGH_LATENCY"
            else:
                status = "HEALTHY"

            return {
                "status": status,
                "latency_ms": latency_ms,
                "file_size_mb": file_size_mb,
                "flows_count": flows_count,
                "journal_mode": str(journal_mode).upper(),
                "integrity": integrity
            }
        except Exception as e:
            self.log_system_event("CRITICAL", "Database", f"Erreur d'accès à la base SQLite: {str(e)}")
            return {
                "status": "ERROR",
                "latency_ms": round((time.perf_counter() - start) * 1000, 2),
                "file_size_mb": file_size_mb,
                "error": str(e)
            }

    def _check_ai_engine(self) -> Dict[str, Any]:
        """Vérifie la disponibilité et les temps de réponse du moteur d'inférence."""
        # Calcul de la latence moyenne récente
        latencies = list(self._inference_latencies)
        avg_lat = round(sum(latencies) / len(latencies), 2) if latencies else 12.5

        if avg_lat > 300:
            status = "SLOW"
        else:
            status = "OPERATIONAL"

        return {
            "status": status,
            "dnn_version": ACTIVE_DNN_VERSION,
            "ae_version": ACTIVE_AE_VERSION,
            "device": "CPU" if not os.environ.get("CUDA_VISIBLE_DEVICES") else "CUDA",
            "avg_inference_ms": avg_lat,
            "samples_measured": len(latencies)
        }

    def _check_websocket(self) -> Dict[str, Any]:
        """Vérifie le diffuseur WebSocket."""
        connected = len(ws_manager.active_connections)
        return {
            "status": "ONLINE" if connected > 0 else "IDLE",
            "connected_clients": connected
        }

    def _check_host(self) -> Dict[str, Any]:
        """Vérifie les ressources matérielles de l'hôte (Linux Mint)."""
        try:
            cpu_pct = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "cpu_pct": cpu_pct,
                "ram_pct": mem.percent,
                "ram_used_gb": round(mem.used / (1024**3), 2),
                "ram_total_gb": round(mem.total / (1024**3), 2),
                "disk_pct": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2)
            }
        except Exception as e:
            return {
                "error": str(e),
                "cpu_pct": 0,
                "ram_pct": 0,
                "disk_pct": 0
            }

    def get_health_status(self) -> Dict[str, Any]:
        """Compile le rapport global de santé du NIDS."""
        sensors_res = self._check_sensors()
        db_res = self._check_database()
        ai_res = self._check_ai_engine()
        ws_res = self._check_websocket()
        host_res = self._check_host()

        # Calcul du score d'intégrité globale (0 à 100)
        score = 100
        issues = []

        if sensors_res.get("status") == "OFFLINE":
            score -= 20
            issues.append({
                "severity": "WARNING",
                "source": "Sensors",
                "message": "Aucun capteur réseau n'émet de trafic actuellement.",
                "fix": "Déployez un agent nids_sensor.py ou lancez un rejeu PCAP."
            })
        elif sensors_res.get("status") == "ERROR":
            score -= 30
            issues.append({
                "severity": "CRITICAL",
                "source": "Sensors",
                "message": f"Erreur de communication capteurs: {sensors_res.get('error')}",
                "fix": "Vérifiez les droits d'accès et la configuration réseau."
            })

        if db_res.get("status") != "HEALTHY":
            score -= 25
            issues.append({
                "severity": "CRITICAL" if db_res.get("status") == "CORRUPT" else "WARNING",
                "source": "Database",
                "message": f"Problème de base SQLite ({db_res.get('status')}) - Latence {db_res.get('latency_ms')} ms.",
                "fix": "Exécutez une optimisation ou réparez le journal WAL."
            })

        if ai_res.get("status") != "OPERATIONAL":
            score -= 20
            issues.append({
                "severity": "WARNING",
                "source": "AI-Engine",
                "message": f"Latence d'inférence anormale ({ai_res.get('avg_inference_ms')} ms).",
                "fix": "Réduisez la taille des lots de flux ou basculez sur GPU."
            })

        if host_res.get("ram_pct", 0) > 85:
            score -= 15
            issues.append({
                "severity": "WARNING",
                "source": "Host",
                "message": f"Mémoire vive saturée ({host_res.get('ram_pct')} % utilisée).",
                "fix": "Libérez de la mémoire ou fermez les processus secondaires."
            })

        score = max(0, min(100, score))
        if score >= 85:
            global_status = "HEALTHY"
        elif score >= 60:
            global_status = "DEGRADED"
        else:
            global_status = "CRITICAL"

        uptime_sec = time.time() - self.start_time

        return {
            "status": global_status,
            "score": score,
            "uptime_sec": round(uptime_sec, 1),
            "uptime_str": self._format_uptime(uptime_sec),
            "timestamp": time.time(),
            "components": {
                "sensors": sensors_res,
                "ai_engine": ai_res,
                "database": db_res,
                "websocket": ws_res,
                "host": host_res
            },
            "issues": issues
        }

    def optimize_database(self) -> Dict[str, Any]:
        """Optimise et libère l'espace de la base de données SQLite."""
        start = time.perf_counter()
        try:
            con = get_connection()
            with con:
                con.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                con.execute("PRAGMA optimize;")
            con.close()
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            self.log_system_event(
                "INFO", 
                "Database", 
                f"Optimisation SQLite WAL exécutée avec succès en {elapsed_ms} ms"
            )
            return {"status": "success", "elapsed_ms": elapsed_ms}
        except Exception as e:
            self.log_system_event("ERROR", "Database", f"Échec d'optimisation SQLite: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _format_uptime(self, sec: float) -> str:
        sec = int(sec)
        h = sec // 3600
        m = (sec % 3600) // 60
        s = sec % 60
        if h > 0:
            return f"{h}h {m}m {s}s"
        if m > 0:
            return f"{m}m {s}s"
        return f"{s}s"


# Singleton d'instance
health_service = HealthService()
