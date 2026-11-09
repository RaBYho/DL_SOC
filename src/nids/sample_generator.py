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


def _generate_feature_matrix(
    feature_names: list[str], n: int, is_attack: bool, rng: np.random.Generator
) -> dict[str, np.ndarray]:
    """Génère la matrice de caractéristiques numériques pour le trafic synthétique."""
    data = {}
    for feat in feature_names:
        if feat == "Destination Port":
            continue
        if "Duration" in feat or "IAT" in feat:
            data[feat] = rng.exponential(scale=50000.0 if is_attack else 100.0, size=n)
        elif "Bytes" in feat or "Length" in feat:
            low, high = (2000.0, 50000.0) if is_attack else (20.0, 500.0)
            data[feat] = rng.uniform(low, high, size=n)
        elif "Packets" in feat or "Header" in feat:
            low, high = (50, 500) if is_attack else (1, 10)
            data[feat] = rng.integers(low, high, size=n)
        else:
            low, high = (20.0, 100.0) if is_attack else (0.0, 10.0)
            data[feat] = rng.uniform(low, high, size=n)
    return data


def _create_noisy_benign_chunk(feature_names: list[str], base_t: float) -> pd.DataFrame:
    """Génère un chunk de 10s contenant du trafic bénin bruité (mDNS, SSDP, orphelins)."""
    rng = np.random.default_rng(101)
    n = 27
    ts = [f"2017-07-07 10:00:{int(i % 10):02d}" for i in range(n)]
    df = pd.DataFrame({
        "Flow ID": [f"noisy-flow-{i}" for i in range(n)],
        "Source IP": ["192.168.10.15"] * n,
        "Destination IP": ["172.16.0.2"] * n,
        "Source Port": [50000 + i for i in range(n)],
        "Destination Port": [443] * n,
        "Protocol": [6] * n,
        "Timestamp": ts,
        **_generate_feature_matrix(feature_names, n, False, rng),
        "Label": [BENIGN] * n,
    })
    # Injection mDNS (dst 224.0.0.251:5353) et SSDP (dst 239.255.255.250:1900)
    df.loc[0:3, "Destination IP"] = "224.0.0.251"
    df.loc[0:3, "Destination Port"] = 5353
    df.loc[4:7, "Destination IP"] = "239.255.255.250"
    df.loc[4:7, "Destination Port"] = 1900
    df.loc[8:11, "Source IP"] = "127.0.0.1"
    # Injection flux micro-morts (<= 1 paquet, 0 SYN)
    df.loc[12:15, "Total Fwd Packets"] = 1
    df.loc[12:15, "Total Backward Packets"] = 0
    df.loc[12:15, "SYN Flag Count"] = 0
    return df


def _create_attack_burst_chunk(
    feature_names: list[str], base_t: float, src_ip: str = "192.168.10.99"
) -> pd.DataFrame:
    """Génère un chunk de 10s contenant une rafale de 20 flux d'attaque (PortScan)."""
    rng = np.random.default_rng(202)
    n = 25  # 5 bénins + 20 attaques
    ts = [f"2017-07-07 10:00:{int(base_t % 60 + (i % 10)):02d}" for i in range(n)]
    benign_feats = _generate_feature_matrix(feature_names, 5, False, rng)
    attack_feats = _generate_feature_matrix(feature_names, 20, True, rng)
    combined_feats = {
        k: np.concatenate([benign_feats[k], attack_feats[k]]) for k in benign_feats
    }
    src_ips = ["192.168.10.15"] * 5 + [src_ip] * 20
    dst_ips = ["172.16.0.2"] * 5 + ["172.16.0.5"] * 20
    dst_ports = [443] * 5 + [80 + i for i in range(20)]
    labels = [BENIGN] * 5 + ["PortScan"] * 20

    df = pd.DataFrame({
        "Flow ID": [f"burst-flow-{i}" for i in range(n)],
        "Source IP": src_ips,
        "Destination IP": dst_ips,
        "Source Port": [40000 + i for i in range(n)],
        "Destination Port": dst_ports,
        "Protocol": [6] * n,
        "Timestamp": ts,
        **combined_feats,
        "Label": labels,
    })
    df.loc[5:, "SYN Flag Count"] = 1  # Conserve les flux au pré-filtrage
    df.loc[5:, "Total Fwd Packets"] = 10
    return df


def generate_replay_chunks(output_dir: Path | str, feature_names: list[str]) -> list[Path]:
    """Génère 3 micro-batchs temporels (10s chacun) pour tester le replay live."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    c1 = _create_noisy_benign_chunk(feature_names, 0.0)
    c2 = _create_attack_burst_chunk(feature_names, 10.0, "192.168.10.99")
    c3 = _create_attack_burst_chunk(feature_names, 20.0, "192.168.10.99")

    p1, p2, p3 = out_dir / "chunk_001.csv", out_dir / "chunk_002.csv", out_dir / "chunk_003.csv"
    c1.to_csv(p1, index=False)
    c2.to_csv(p2, index=False)
    c3.to_csv(p3, index=False)
    return [p1, p2, p3]
