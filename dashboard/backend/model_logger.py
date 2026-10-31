import asyncio
import collections
from datetime import datetime
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional
import pandas as pd

from dashboard.backend.config import PROJECT_ROOT
from dashboard.backend.ws_manager import ws_manager

logger = logging.getLogger("dashboard.model_logger")

LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
MODEL_LOG_FILE = LOGS_DIR / "model_inference.log"

# Mémoire tampon circulaire des N derniers logs pour affichage temps réel
_recent_logs: collections.deque = collections.deque(maxlen=300)
_log_counter: int = 0


def log_inference(
    flows_count: int,
    duration_ms: float,
    predictions: Any,
    confidences: Optional[Any] = None,
    mse_ae: Optional[Any] = None,
    anomalie_ae: Optional[Any] = None,
    device: str = "cpu",
    model_version: str = "v4",
    flows_df: Optional[pd.DataFrame] = None,
) -> None:
    """Enregistre un événement d'inférence dans le fichier .log et dans la mémoire tampon."""
    global _log_counter
    if flows_count <= 0:
        return

    now = datetime.now()
    ts_str = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    _log_counter += 1

    # Résumé des prédictions
    if isinstance(predictions, (pd.Series, list)):
        class_series = pd.Series(predictions)
        class_counts = class_series.value_counts().to_dict()
    else:
        class_counts = {}

    benign_count = class_counts.get("BENIGN", 0)
    attacks_count = sum(v for k, v in class_counts.items() if k != "BENIGN")

    # Statistiques MSE et anomalies de l'Auto-Encodeur
    max_mse = None
    mean_mse = None
    anomalies_count = 0
    if mse_ae is not None:
        try:
            mse_series = pd.Series(mse_ae).dropna()
            if not mse_series.empty:
                max_mse = float(mse_series.max())
                mean_mse = float(mse_series.mean())
        except Exception:
            pass

    if anomalie_ae is not None:
        try:
            anom_series = pd.Series(anomalie_ae)
            anomalies_count = int(anom_series.sum())
        except Exception:
            pass

    # Détermination du niveau de criticité du log
    if attacks_count > 0:
        level = "ALERT"
    elif anomalies_count > 0:
        level = "ANOMALY"
    else:
        level = "INFO"

    # Construction du message texte pour le terminal / fichier .log
    pred_str = ", ".join(f"{k}:{v}" for k, v in class_counts.items())
    mse_summary = f"Max MSE={max_mse:.4f} (Moy={mean_mse:.4f})" if max_mse is not None else "AE=N/A"
    
    log_line = (
        f"[{ts_str}] [{level:<7}] [DNN-{model_version} on {device}] "
        f"Batch={flows_count} | Latency={duration_ms:.2f}ms | "
        f"Preds=[{pred_str}] | {mse_summary} | Anomalies={anomalies_count}\n"
    )

    # Détails supplémentaires si attaques détectées
    attack_detail_lines = []
    if attacks_count > 0 and flows_df is not None:
        try:
            for idx, pred_label in enumerate(predictions):
                if pred_label != "BENIGN":
                    src = flows_df.iloc[idx].get("src_ip", "?")
                    dst = flows_df.iloc[idx].get("dst_ip", "?")
                    dport = flows_df.iloc[idx].get("dst_port", "?")
                    conf = (
                        float(confidences[idx]) * 100.0
                        if confidences is not None
                        else 0.0
                    )
                    attack_detail_lines.append(
                        f"  └─> [DETECTION] {pred_label} (Conf: {conf:.1f}%) from {src} -> {dst}:{dport}\n"
                    )
                    if len(attack_detail_lines) >= 3:  # Limiter à 3 détails max par batch
                        if attacks_count > 3:
                            attack_detail_lines.append(
                                f"  └─> ... et {attacks_count - 3} autre(s) attaque(s)\n"
                            )
                        break
        except Exception:
            pass

    # Écriture dans le fichier .log physique
    try:
        with open(MODEL_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line)
            for d in attack_detail_lines:
                f.write(d)
            f.flush()
    except Exception as e:
        logger.error(f"Erreur d'écriture dans {MODEL_LOG_FILE}: {e}")

    # Enregistrement dans le tampon circulaire en mémoire
    log_entry: Dict[str, Any] = {
        "id": _log_counter,
        "timestamp": ts_str,
        "level": level,
        "device": device,
        "batch_size": flows_count,
        "latency_ms": round(duration_ms, 2),
        "predictions": class_counts,
        "attacks_count": attacks_count,
        "benign_count": benign_count,
        "max_mse": round(max_mse, 4) if max_mse is not None else None,
        "mean_mse": round(mean_mse, 4) if mean_mse is not None else None,
        "anomalies_count": anomalies_count,
        "raw_text": log_line.strip(),
        "details": [d.strip() for d in attack_detail_lines],
    }

    _recent_logs.append(log_entry)

    # Diffusion en direct vers le WebSocket si une boucle asyncio est active
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running() and ws_manager.active_connections:
            loop.create_task(
                ws_manager.broadcast({"type": "model_log", "log": log_entry})
            )
    except RuntimeError:
        # Aucune boucle asyncio en cours (ex: script offline ou test synchrone)
        pass


def get_recent_logs(limit: int = 100) -> List[Dict[str, Any]]:
    """Récupère les derniers logs d'inférence en mémoire."""
    logs_list = list(_recent_logs)
    return logs_list[-limit:] if limit > 0 else logs_list


def clear_logs() -> bool:
    """Vide la mémoire tampon et réinitialise le fichier .log."""
    global _recent_logs
    _recent_logs.clear()
    try:
        with open(MODEL_LOG_FILE, "w", encoding="utf-8") as f:
            f.write(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO   ] Log terminal réinitialisé.\n"
            )
        return True
    except Exception as e:
        logger.error(f"Erreur vidage log: {e}")
        return False
