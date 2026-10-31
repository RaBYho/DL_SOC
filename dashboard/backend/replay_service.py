import asyncio
import logging
import time
from typing import Any, Dict, Optional
import numpy as np
import pandas as pd
from dashboard.backend.config import BASE, DB_PATH, PCAP_DIR
from dashboard.backend.database import get_kpis, init_db
from dashboard.backend.ws_manager import ws_manager
from nids_core import Scorer
from nids_sensor import extract

logger = logging.getLogger("dashboard.replay")


class PCAPReplayService:
    """Service de rejeu PCAP en tâche de fond pour animer le Dashboard SOC."""

    def __init__(self):
        self.is_running: bool = False
        self.is_paused: bool = False
        self.current_file: Optional[str] = None
        self.total_flows: int = 0
        self.processed_flows: int = 0
        self.alerts_count: int = 0
        self._task: Optional[asyncio.Task] = None
        self._scorer: Optional[Scorer] = None

    def _get_scorer(self) -> Scorer:
        if self._scorer is None:
            self._scorer = Scorer(BASE)
        return self._scorer

    def get_status(self) -> Dict[str, Any]:
        pct = (
            round(self.processed_flows / self.total_flows * 100.0, 1)
            if self.total_flows > 0
            else 0.0
        )
        return {
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "current_file": self.current_file,
            "total_flows": self.total_flows,
            "processed_flows": self.processed_flows,
            "progress_percent": pct,
            "alerts_count": self.alerts_count,
        }

    async def start_replay(
        self,
        pcap_name: str,
        rate_per_sec: int = 25,
        sensor_id: str = "lab-replay",
    ) -> Dict[str, Any]:
        """Déclenche le rejeu d'une capture réseau en arrière-plan."""
        if self.is_running:
            return {"error": "Un rejeu est déjà en cours."}

        pcap_path = PCAP_DIR / pcap_name
        if not pcap_path.exists():
            return {"error": f"Fichier {pcap_name} introuvable dans {PCAP_DIR}"}

        self.is_running = True
        self.is_paused = False
        self.current_file = pcap_name
        self.processed_flows = 0
        self.alerts_count = 0

        # Lancement en arrière-plan
        self._task = asyncio.create_task(
            self._replay_worker(pcap_path, rate_per_sec, sensor_id)
        )
        return {"status": "started", "file": pcap_name}

    def pause_replay(self) -> Dict[str, Any]:
        self.is_paused = True
        return {"status": "paused"}

    def resume_replay(self) -> Dict[str, Any]:
        self.is_paused = False
        return {"status": "resumed"}

    def stop_replay(self) -> Dict[str, Any]:
        self.is_running = False
        self.is_paused = False
        if self._task and not self._task.done():
            self._task.cancel()
        return {"status": "stopped"}

    async def _replay_worker(
        self, pcap_path, rate_per_sec: int, sensor_id: str
    ) -> None:
        try:
            logger.info(f"Extraction NFStream du fichier {pcap_path.name}...")
            # Extraction non bloquante via threadpool
            df: pd.DataFrame = await asyncio.to_thread(extract, str(pcap_path))
            self.total_flows = len(df)
            logger.info(
                f"{self.total_flows} flux extraits. Démarrage de l'injection..."
            )

            scorer = self._get_scorer()
            init_db(str(DB_PATH))

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

            batch_size = max(1, min(rate_per_sec, 50))
            sleep_interval = batch_size / float(rate_per_sec)

            import sqlite3

            for i in range(0, self.total_flows, batch_size):
                if not self.is_running:
                    break

                while self.is_paused and self.is_running:
                    await asyncio.sleep(0.5)

                sub_df = df.iloc[i : i + batch_size].copy()
                now = time.time()

                # Scoring IA
                res = scorer.predict_df(sub_df)
                has_ae = "anomalie_ae" in res.columns
                mse_vals = (
                    res["mse_ae"].tolist() if has_ae else [None] * len(res)
                )
                anom_vals = (
                    res["anomalie_ae"].tolist() if has_ae else [0] * len(res)
                )

                # Insertion base SQLite
                con = sqlite3.connect(str(DB_PATH))
                rows = []
                alerts_to_send = []

                for idx, (_, r) in enumerate(sub_df.iterrows()):
                    p = res["pred"].iloc[idx]
                    c = float(res["confiance"].iloc[idx])
                    m = (
                        float(mse_vals[idx])
                        if mse_vals[idx] is not None
                        else None
                    )
                    a = int(anom_vals[idx]) if anom_vals[idx] is not None else 0

                    rows.append(
                        (
                            now,
                            sensor_id,
                            r.get("bidirectional_first_seen_ms", now * 1000),
                            r.get("src_ip", "192.168.1.10"),
                            r.get("src_mac", "00:00:00:00:00:00"),
                            int(r.get("src_port", 0)),
                            r.get("dst_ip", "10.0.0.1"),
                            int(r.get("dst_port", 80)),
                            int(r.get("protocol", 6)),
                            p,
                            c,
                            m,
                            a,
                        )
                    )

                    if p != "BENIGN" or a == 1:
                        self.alerts_count += 1
                        alerts_to_send.append(
                            {
                                "timestamp": time.strftime(
                                    "%H:%M:%S", time.localtime(now)
                                ),
                                "sensor": sensor_id,
                                "src_ip": r.get("src_ip", "192.168.1.10"),
                                "src_port": int(r.get("src_port", 0)),
                                "dst_ip": r.get("dst_ip", "10.0.0.1"),
                                "dst_port": int(r.get("dst_port", 80)),
                                "protocol": "TCP"
                                if r.get("protocol") == 6
                                else "UDP",
                                "classification": p,
                                "confidence": round(c * 100.0, 1),
                                "mse_ae": round(m, 3) if m is not None else 0.0,
                                "is_anomaly": bool(a),
                                "severity": severity_map.get(
                                    p, "High" if bool(a) else "Medium"
                                ),
                            }
                        )

                with con:
                    con.executemany(
                        """INSERT INTO flows (received_at, sensor_id, flow_start_ms, src_ip, src_mac,
                        src_port, dst_ip, dst_port, protocol, pred, confiance, mse_ae, anomalie_ae)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        rows,
                    )
                con.close()

                self.processed_flows += len(sub_df)

                # Broadcast WebSocket vers le Dashboard
                await ws_manager.broadcast(
                    {
                        "type": "new_flows",
                        "received": len(sub_df),
                        "alerts_count": len(alerts_to_send),
                        "anomalies_count": sum(
                            1 for a in alerts_to_send if a["is_anomaly"]
                        ),
                        "recent_alerts": alerts_to_send,
                        "kpis": get_kpis(str(DB_PATH)),
                        "replay_status": self.get_status(),
                    }
                )

                await asyncio.sleep(sleep_interval)

            logger.info("Rejeu PCAP terminé avec succès !")
        except asyncio.CancelledError:
            logger.info("Rejeu PCAP interrompu.")
        except Exception as e:
            logger.error(f"Erreur durant le rejeu PCAP: {e}", exc_info=True)
        finally:
            self.is_running = False
            self.is_paused = False
            await ws_manager.broadcast(
                {
                    "type": "replay_finished",
                    "file": pcap_path.name,
                    "kpis": get_kpis(str(DB_PATH)),
                }
            )


replay_service = PCAPReplayService()
