"""Générateur d'échantillons de flux représentatifs (mini.csv)."""

from pathlib import Path
import numpy as np
import pandas as pd

from nids.labels import ATTACK_CLASSES, BENIGN
from nids.features import NETWORK_METADATA_COLUMNS


def generate_mini_sample(
    output_path: Path | str,
    feature_names: list[str],
    n_benign: int = 100,
    n_per_attack: int = 7,
    seed: int = 42,
) -> pd.DataFrame:
    """Génère un mini-dataset synthétique représentatif avec métadonnées et attaques.

    Args:
        output_path: Chemin du fichier CSV de sortie.
        feature_names: Liste ordonnée des variables numériques de flux.
        n_benign: Nombre de lignes de trafic bénin.
        n_per_attack: Nombre de lignes pour chacune des 14 classes d'attaques.
        seed: Graine aléatoire pour la reproductibilité.

    Returns:
        pd.DataFrame: DataFrame complet généré et sauvegardé.
    """
    rng = np.random.default_rng(seed)
    n_attacks = len(ATTACK_CLASSES) * n_per_attack
    total_rows = n_benign + n_attacks

    # 1. Métadonnées réseau
    protocols = rng.choice([6, 17], size=total_rows)  # TCP ou UDP
    src_ips = [f"192.168.10.{rng.integers(10, 50)}" for _ in range(total_rows)]
    dst_ips = [f"172.16.0.{rng.integers(1, 10)}" for _ in range(total_rows)]
    src_ports = rng.integers(1024, 65535, size=total_rows)
    dst_ports = rng.choice([80, 443, 22, 21, 53, 8080], size=total_rows)
    flow_ids = [
        f"{src_ips[i]}-{dst_ips[i]}-{src_ports[i]}-{dst_ports[i]}-{protocols[i]}"
        for i in range(total_rows)
    ]
    timestamps = [
        f"2017-07-07 {10 + (i // 60):02d}:{i % 60:02d}:00" for i in range(total_rows)
    ]

    metadata_dict = {
        "Flow ID": flow_ids,
        "Source IP": src_ips,
        "Destination IP": dst_ips,
        "Source Port": src_ports,
        "Destination Port": dst_ports,
        "Protocol": protocols,
        "Timestamp": timestamps,
    }

    # 2. Variables numériques : différentiation réaliste bénin vs attaques
    features_dict = {}
    for feat in feature_names:
        if feat == "Destination Port":
            features_dict[feat] = dst_ports
        elif "Duration" in feat or "IAT" in feat:
            benign_vals = rng.exponential(scale=100.0, size=n_benign)
            attack_vals = rng.exponential(scale=50000.0, size=n_attacks)
            features_dict[feat] = np.concatenate([benign_vals, attack_vals])
        elif "Bytes" in feat or "Length" in feat:
            benign_vals = rng.uniform(20.0, 500.0, size=n_benign)
            attack_vals = rng.uniform(2000.0, 50000.0, size=n_attacks)
            features_dict[feat] = np.concatenate([benign_vals, attack_vals])
        elif "Packets" in feat or "Header" in feat:
            benign_vals = rng.integers(1, 10, size=n_benign)
            attack_vals = rng.integers(50, 500, size=n_attacks)
            features_dict[feat] = np.concatenate([benign_vals, attack_vals])
        else:
            benign_vals = rng.uniform(0.0, 10.0, size=n_benign)
            attack_vals = rng.uniform(20.0, 100.0, size=n_attacks)
            features_dict[feat] = np.concatenate([benign_vals, attack_vals])

    # 3. Étiquettes
    labels = [BENIGN] * n_benign
    for attack in ATTACK_CLASSES:
        labels.extend([attack] * n_per_attack)

    all_data = {**metadata_dict, **features_dict, "Label": labels}
    df = pd.DataFrame(all_data)

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_file, index=False)

    return df
