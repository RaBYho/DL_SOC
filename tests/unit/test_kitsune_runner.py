"""Tests unitaires pour le module Kitsune / KitNET (kitsune_runner.py)."""

from pathlib import Path
import numpy as np
import pandas as pd

from nids.kitsune_runner import KitNETAnomalyDetector, generate_aligned_packet_scores


def test_kitnet_grace_period_logic():
    """Vérifie que la période de grâce est bien respectée et signalée."""
    detector = KitNETAnomalyDetector(n_features=5, fm_grace=3, ad_grace=2)
    # Total grace = 5 paquets
    dummy_x = np.ones(5)

    for i in range(5):
        score, is_grace = detector.process_vector(dummy_x)
        assert is_grace is True
        assert score == 0.0

    # 6e paquet : post-période de grâce
    score, is_grace = detector.process_vector(dummy_x)
    assert is_grace is False
    assert score >= 0.0


def test_generate_aligned_packet_scores(tmp_path: Path):
    """Vérifie la génération de scores paquets synchronisés au format Parquet."""
    flows = pd.DataFrame({
        "Flow ID": ["F1", "F2"],
        "Source IP": ["192.168.1.1", "10.0.0.1"],
        "Destination IP": ["10.0.0.2", "192.168.1.2"],
        "Source Port": [1000, 2000],
        "Destination Port": [80, 443],
        "Protocol": [6, 6],
        "Timestamp": ["2017-07-07 10:00:00", "2017-07-07 10:00:05"],
        "Flow Duration": [1_000_000, 2_000_000],
        "Label": ["BENIGN", "DDoS"],
    })

    out_file = tmp_path / "packet_scores.parquet"
    pkts = generate_aligned_packet_scores(flows, out_file, packets_per_flow=4, seed=42)

    assert out_file.exists()
    assert len(pkts) == 8
    expected_cols = {
        "timestamp",
        "src_ip",
        "dst_ip",
        "src_port",
        "dst_port",
        "protocol",
        "rmse_score",
        "is_grace_period",
    }
    assert expected_cols.issubset(set(pkts.columns))

    # Vérification que le score moyen des paquets de DDoS est plus élevé que le bénin
    benign_ip = flows.loc[0, "Source IP"]
    benign_pkts = pkts[(pkts["src_ip"] == benign_ip) | (pkts["dst_ip"] == benign_ip)]
    attack_pkts = pkts[~pkts.index.isin(benign_pkts.index)]

    assert attack_pkts["rmse_score"].mean() > benign_pkts["rmse_score"].mean()


def test_kitnet_score_dataframe():
    """Vérifie le calcul vectorisé des scores RMSE pour un DataFrame de flux."""
    detector = KitNETAnomalyDetector(n_features=4, fm_grace=0, ad_grace=0, seed=123)
    df = pd.DataFrame({
        "Flow ID": ["F1", "F2"],
        "Source IP": ["10.0.0.1", "10.0.0.2"],
        "f1": [1.0, 2.0],
        "f2": [0.5, 1.5],
        "f3": [0.2, 0.8],
        "f4": [1.1, 0.9],
    })

    scores = detector.score(df)
    assert isinstance(scores, np.ndarray)
    assert len(scores) == 2
    assert np.all(scores >= 0.0)
    assert detector.score(pd.DataFrame()).size == 0
