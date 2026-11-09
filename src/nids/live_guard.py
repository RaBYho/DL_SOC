"""Moteur temps réel de corrélation, calcul de menace cumulée (leaky bucket) et déduplication."""

from dataclasses import dataclass
from typing import Any, Sequence
import numpy as np
import pandas as pd

from nids.labels import BENIGN


@dataclass(frozen=True)
class ConsolidatedAlert:
    """Alerte de sécurité consolidée et dédupliquée pour le SIEM ou l'analyste SOC."""

    timestamp: float
    src_ip: str
    dst_ip: str
    attack_class: str
    host_score: float
    flow_count: int
    suppressed_count: int


class LiveAlertGuard:
    """Gardien temps réel : élimine les faux positifs isolés et consolide les incidents."""

    def __init__(self, config: dict[str, Any]) -> None:
        scoring_cfg = config.get("threat_scoring", {})
        self.alert_threshold = float(scoring_cfg.get("alert_threshold", 100.0))
        self.half_life_sec = float(scoring_cfg.get("half_life_sec", 60.0))
        self.weights = scoring_cfg.get("weights", {})

        quorum_cfg = config.get("quorum_rules", {})
        self.volumetric_classes = set(quorum_cfg.get("volumetric_classes", []))
        self.volumetric_min = int(quorum_cfg.get("volumetric_min_flows", 15))
        self.volumetric_window = float(quorum_cfg.get("volumetric_window_sec", 10.0))

        cooldown_cfg = config.get("cooldown", {})
        self.ttl_sec = float(cooldown_cfg.get("ttl_sec", 300.0))

        # États internes
        self.host_scores: dict[str, float] = {}
        self.host_last_time: dict[str, float] = {}
        self.volumetric_history: dict[tuple[str, str], list[float]] = {}
        self.last_alert_time: dict[tuple[str, str], float] = {}
        self.suppressed_counts: dict[tuple[str, str], int] = {}

    def get_host_score(self, src_ip: str, current_time: float) -> float:
        """Calcule le score actuel d'un hôte après décroissance exponentielle."""
        if src_ip not in self.host_scores:
            return 0.0
        dt = max(0.0, current_time - self.host_last_time[src_ip])
        decay_factor = 2.0 ** (-dt / self.half_life_sec)
        return float(self.host_scores[src_ip] * decay_factor)

    def _determine_weight(self, verdict: str, s2_conf: float) -> float:
        """Attribue la sévérité en points selon l'étiquette et la confiance."""
        if verdict == BENIGN:
            return float(self.weights.get("BENIGN", 0.0))
        if verdict in ("SUSPECT_UNCERTAIN", "ANOMALY_UNKNOWN", "UNKNOWN_ATTACK_LIKELY"):
            return float(self.weights.get(verdict, 20.0))
        if s2_conf >= 0.90:
            return float(self.weights.get("KNOWN_ATTACK_HIGH_CONF", 100.0))
        return float(self.weights.get("KNOWN_ATTACK", 40.0))

    def _check_quorum(self, key: tuple[str, str], current_time: float) -> int:
        """Met à jour et vérifie l'historique des flux dans la fenêtre glissante."""
        history = self.volumetric_history.setdefault(key, [])
        history.append(current_time)
        # Élimination des flux hors de la fenêtre
        cutoff = current_time - self.volumetric_window
        valid = [t for t in history if t >= cutoff]
        self.volumetric_history[key] = valid
        return len(valid)

    def _handle_alert_emission(
        self, key: tuple[str, str], t: float, dst: str, score: float, count: int
    ) -> ConsolidatedAlert | None:
        """Gère l'émission d'alerte sous réserve du cooldown anti-flood."""
        last_t = self.last_alert_time.get(key)
        if last_t is not None and (t - last_t) < self.ttl_sec:
            self.suppressed_counts[key] = self.suppressed_counts.get(key, 0) + 1
            return None

        suppressed = self.suppressed_counts.get(key, 0)
        self.suppressed_counts[key] = 0
        self.last_alert_time[key] = t

        return ConsolidatedAlert(
            timestamp=t,
            src_ip=key[0],
            dst_ip=dst,
            attack_class=key[1],
            host_score=round(score, 2),
            flow_count=count,
            suppressed_count=suppressed,
        )

    def _extract_timestamps(
        self, flows_df: pd.DataFrame, timestamps: Sequence[float] | None
    ) -> np.ndarray:
        """Extrait les timestamps en secondes Unix à partir du flux ou du paramètre."""
        if timestamps is not None:
            return np.asarray(timestamps, dtype=float)
        ts_col = flows_df.get("Timestamp", pd.Series(0.0, index=flows_df.index))
        if pd.api.types.is_numeric_dtype(ts_col):
            return ts_col.astype(float).to_numpy()
        return (pd.to_datetime(ts_col).astype(np.int64) / 1e9).to_numpy()

    def _process_single_flow(
        self, src: str, dst: str, verdict: str, conf: float, t: float
    ) -> ConsolidatedAlert | None:
        """Traite un flux unique et retourne une alerte si le seuil et le quorum sont atteints."""
        current_score = self.get_host_score(src, t)
        weight = self._determine_weight(verdict, conf)
        new_score = current_score + weight
        self.host_scores[src] = new_score
        self.host_last_time[src] = t

        if verdict == BENIGN:
            return None

        key = (src, verdict)
        flow_count = 1
        if verdict in self.volumetric_classes:
            flow_count = self._check_quorum(key, t)
            if flow_count < self.volumetric_min:
                return None

        if new_score >= self.alert_threshold:
            return self._handle_alert_emission(key, t, dst, new_score, flow_count)
        return None

    def process_batch(
        self,
        flows_df: pd.DataFrame,
        verdicts: pd.Series,
        s1_scores: np.ndarray,
        s2_confs: np.ndarray,
        timestamps: Sequence[float] | None = None,
    ) -> list[ConsolidatedAlert]:
        """Traite un micro-batch de flux et retourne les alertes consolidées émises."""
        if len(flows_df) == 0:
            return []

        ts = self._extract_timestamps(flows_df, timestamps)
        alerts: list[ConsolidatedAlert] = []

        for i in range(len(flows_df)):
            src = str(flows_df.iloc[i].get("Source IP", "unknown"))
            dst = str(flows_df.iloc[i].get("Destination IP", "unknown"))
            verdict = str(verdicts.iloc[i])
            conf = float(s2_confs[i])

            alert = self._process_single_flow(src, dst, verdict, conf, float(ts[i]))
            if alert is not None:
                alerts.append(alert)

        return alerts
