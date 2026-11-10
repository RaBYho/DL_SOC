"""Module d'exécution et de simulation de Kitsune (KitNET / AfterImage)."""

from pathlib import Path
from typing import Sequence
import numpy as np
import pandas as pd


class KitNETAnomalyDetector:
    """Détecteur d'anomalies non-supervisé inspiré de KitNET (ensemble d'autoencodeurs)."""

    def __init__(
        self,
        n_features: int = 78,
        max_autoencoders: int = 10,
        fm_grace: int = 500,
        ad_grace: int = 500,
        learning_rate: float = 0.01,
        seed: int = 42,
    ) -> None:
        self.name = "KitNET"
        self.n_features = n_features
        self.max_autoencoders = max_autoencoders
        self.fm_grace = fm_grace
        self.ad_grace = ad_grace
        self.total_grace = fm_grace + ad_grace
        self.learning_rate = learning_rate

        self.packet_count = 0
        rng = np.random.default_rng(seed)
        # Poids synthétiques normalisés pour l'erreur de reconstruction
        self.weights = rng.normal(1.0, 0.05, size=n_features)

    def process_vector(self, x: np.ndarray) -> tuple[float, bool]:
        """Traite un vecteur d'attributs de paquet et renvoie (score_rmse, is_grace_period)."""
        self.packet_count += 1
        is_grace = self.packet_count <= self.total_grace

        if is_grace:
            return 0.0, True

        # Calcul de l'erreur de reconstruction RMSE
        reconstruction = x * self.weights
        rmse = float(np.sqrt(np.mean((x - reconstruction) ** 2)))
        return rmse, False

    def _prepare_array(self, data: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Prépare et adapte la matrice de caractéristiques à n_features."""
        if isinstance(data, pd.DataFrame):
            num_df = data.select_dtypes(include=[np.number])
            arr = num_df.fillna(0.0).to_numpy(dtype=float)
            if arr.shape[1] > self.n_features:
                return arr[:, : self.n_features]
            if arr.shape[1] < self.n_features:
                pad = np.zeros((len(arr), self.n_features - arr.shape[1]))
                return np.hstack([arr, pad])
            return arr
        arr = np.asarray(data, dtype=float)
        return arr.reshape(1, -1) if arr.ndim == 1 else arr

    def score(self, data: pd.DataFrame | np.ndarray, normalize: bool = True) -> np.ndarray:
        """Calcule les scores RMSE d'anomalie pour un lot de flux ou de paquets."""
        if len(data) == 0:
            return np.empty(0, dtype=float)

        arr = self._prepare_array(data)
        if self.packet_count + len(arr) <= self.total_grace:
            self.packet_count += len(arr)
            return np.zeros(len(arr), dtype=float)

        self.packet_count += len(arr)
        if normalize:
            norms = np.linalg.norm(arr, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            arr = arr / norms

        reconstruction = arr * self.weights
        return np.sqrt(np.mean((arr - reconstruction) ** 2, axis=1))


def compute_live_dynamic_threshold(
    rmse_scores: Sequence[float], s1_scores: Sequence[float], t1: float = 0.5,
    percentile: float = 99.9, multiplier: float = 1.5, filter_poisoning: bool = True,
    method: str = "percentile", fallback_t3: float = 0.0035,
) -> float:
    """Calcule le seuil dynamique t3 en protégeant la baseline contre l'empoisonnement."""
    rmses, s1s = np.asarray(rmse_scores, dtype=float), np.asarray(s1_scores, dtype=float)
    if filter_poisoning:
        valid_rmses = rmses[(s1s < t1) & (~np.isnan(rmses))]
    else:
        valid_rmses = rmses[~np.isnan(rmses)]
    if len(valid_rmses) == 0:
        return fallback_t3
    if method == "mu_plus_3sigma":
        return float(round(float(np.mean(valid_rmses)) + 3.0 * float(np.std(valid_rmses)), 5))
    base_p = float(np.percentile(valid_rmses, percentile))
    return float(round(base_p * multiplier, 4))


class LiveKitsuneCalibrator:
    """Gestionnaire de calibration dynamique du seuil Kitsune (t3) sur trafic sain."""

    def __init__(
        self,
        default_t3: float = 0.0035,
        method: str = "mu_plus_3sigma",
        percentile: float = 99.9,
        multiplier: float = 1.5,
        filter_poisoning: bool = True,
        min_clean_flows: int = 10,
        max_history_flows: int = 2000,
        t1: float = 0.5,
    ) -> None:
        self.default_t3 = default_t3
        self.method = method
        self.percentile = percentile
        self.multiplier = multiplier
        self.filter_poisoning = filter_poisoning
        self.min_clean_flows = min_clean_flows
        self.max_history_flows = max_history_flows
        self.t1 = t1
        self.current_threshold = default_t3
        self._clean_scores: list[float] = []

    def update(self, rmse_scores: Sequence[float], s1_scores: Sequence[float]) -> float:
        """Met à jour l'historique bénin et recalibre t3 si min_clean_flows est atteint."""
        rmses = np.asarray(rmse_scores, dtype=float)
        s1s = np.asarray(s1_scores, dtype=float)

        mask = (~np.isnan(rmses)) & (rmses < self.current_threshold)
        if self.filter_poisoning:
            mask = mask & (s1s < self.t1)

        clean_add = rmses[mask]
        if len(clean_add) > 0:
            self._clean_scores.extend(clean_add.tolist())
            if len(self._clean_scores) > self.max_history_flows:
                self._clean_scores = self._clean_scores[-self.max_history_flows :]

        if len(self._clean_scores) >= self.min_clean_flows:
            self.current_threshold = compute_live_dynamic_threshold(
                rmse_scores=self._clean_scores,
                s1_scores=np.zeros(len(self._clean_scores)),
                t1=self.t1,
                percentile=self.percentile,
                multiplier=self.multiplier,
                filter_poisoning=False,
                method=self.method,
                fallback_t3=self.default_t3,
            )
        return self.current_threshold

    def __len__(self) -> int:
        """Retourne le nombre de flux sains enregistrés dans la fenêtre."""
        return len(self._clean_scores)


def generate_aligned_packet_scores(
    flows_df: pd.DataFrame,
    output_path: Path | str,
    packets_per_flow: int = 3,
    anomaly_threshold: float = 0.15,
    seed: int = 42,
) -> pd.DataFrame:
    """Génère un fichier packet_scores.parquet parfaitement synchronisé avec les flux de test.

    Utile pour tester l'alignement local et les tests E2E sans charger un PCAP de plusieurs Go.

    Args:
        flows_df: DataFrame des flux source (ex: mini.csv).
        output_path: Chemin du fichier .parquet généré.
        packets_per_flow: Nombre moyen de paquets générés par flux.
        anomaly_threshold: Seuil d'anomalie de référence pour les attaques.
        seed: Graine aléatoire.

    Returns:
        pd.DataFrame: DataFrame des paquets générés et sauvegardés en Parquet.
    """
    rng = np.random.default_rng(seed)
    records = []

    for _, flow in flows_df.iterrows():
        start_time = pd.to_datetime(flow["Timestamp"])
        duration_sec = float(flow.get("Flow Duration", 1000.0)) / 1e6

        # Les attaques ont une médiane d'erreur RMSE supérieure
        is_attack = str(flow.get("Label", "BENIGN")).upper() != "BENIGN"

        for p in range(packets_per_flow):
            # Répartition des paquets dans la fenêtre [début, fin] du flux
            delta = rng.uniform(0.0, max(duration_sec, 0.001))
            pkt_time = start_time + pd.to_timedelta(delta, unit="s")

            # Score RMSE : faible sur trafic bénin, élevé sur attaque
            if is_attack:
                rmse = float(rng.uniform(anomaly_threshold * 1.2, anomaly_threshold * 3.0))
            else:
                rmse = float(rng.uniform(0.01, anomaly_threshold * 0.7))

            # Aléatoirement dans la direction Aller ou Retour (test bidirectionnel)
            is_fwd = rng.choice([True, False])
            src_ip = flow["Source IP"] if is_fwd else flow["Destination IP"]
            dst_ip = flow["Destination IP"] if is_fwd else flow["Source IP"]
            src_port = flow["Source Port"] if is_fwd else flow["Destination Port"]
            dst_port = flow["Destination Port"] if is_fwd else flow["Source Port"]

            records.append({
                "timestamp": str(pkt_time),
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "src_port": int(src_port),
                "dst_port": int(dst_port),
                "protocol": int(flow["Protocol"]),
                "rmse_score": rmse,
                "is_grace_period": False,
            })

    packets_df = pd.DataFrame(records)
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    packets_df.to_parquet(out_file, index=False)

    return packets_df
