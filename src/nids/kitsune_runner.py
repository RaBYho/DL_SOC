"""Module d'exécution et de simulation de Kitsune (KitNET / AfterImage)."""

from pathlib import Path
from typing import Sequence
import numpy as np
import pandas as pd


class KitNETAnomalyDetector:
    """Détecteur d'anomalies non-supervisé inspiré de KitNET (ensemble d'autoencodeurs)."""

    def __init__(
        self,
        n_features: int,
        max_autoencoders: int = 10,
        fm_grace: int = 500,
        ad_grace: int = 500,
        learning_rate: float = 0.01,
        seed: int = 42,
    ) -> None:
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


def compute_live_dynamic_threshold(
    rmse_scores: Sequence[float],
    s1_scores: Sequence[float],
    t1: float = 0.5,
    percentile: float = 99.9,
    multiplier: float = 1.5,
    filter_poisoning: bool = True,
) -> float:
    """Calcule le seuil dynamique t3 en protégeant la baseline contre l'empoisonnement.

    Exclut tout flux suspect (s1_score >= t1) du calcul du percentile de référence.
    """
    rmses = np.asarray(rmse_scores, dtype=float)
    s1s = np.asarray(s1_scores, dtype=float)

    if filter_poisoning:
        # Exclusion stricte des flux suspects à l'Étage 1
        clean_mask = (s1s < t1) & (~np.isnan(rmses))
        valid_rmses = rmses[clean_mask]
    else:
        valid_rmses = rmses[~np.isnan(rmses)]

    if len(valid_rmses) == 0:
        return 0.15

    base_p = float(np.percentile(valid_rmses, percentile))
    return float(round(base_p * multiplier, 4))


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
