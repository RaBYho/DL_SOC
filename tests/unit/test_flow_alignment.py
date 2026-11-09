"""Tests unitaires pour l'alignement vectorisé paquets <-> flux (flow_alignment.py)."""

import numpy as np
import pandas as pd
import pytest

from nids.flow_alignment import aggregate_scores, compute_canonical_5tuple_key


def test_compute_canonical_5tuple_key_bidirectional():
    """Vérifie que la clé est strictement identique dans le sens Aller et Retour."""
    # Aller : A -> B
    df_fwd = pd.DataFrame({
        "src_ip": ["192.168.1.10"],
        "dst_ip": ["10.0.0.1"],
        "src_port": [54321],
        "dst_port": [80],
        "protocol": [6],
    })
    # Retour : B -> A
    df_bwd = pd.DataFrame({
        "src_ip": ["10.0.0.1"],
        "dst_ip": ["192.168.1.10"],
        "src_port": [80],
        "dst_port": [54321],
        "protocol": [6],
    })

    key_fwd = compute_canonical_5tuple_key(df_fwd)
    key_bwd = compute_canonical_5tuple_key(df_bwd)

    assert key_fwd.iloc[0] == key_bwd.iloc[0]


def test_aggregate_scores_max_rule():
    """Vérifie l'agrégation par la règle 'max' pour 3 paquets du même flux."""
    flows = pd.DataFrame({
        "Flow ID": ["F1"],
        "Source IP": ["192.168.1.10"],
        "Destination IP": ["10.0.0.1"],
        "Source Port": [5000],
        "Destination Port": [80],
        "Protocol": [6],
        "Timestamp": ["2017-07-07 10:00:00"],
        "Flow Duration": [10_000_000],  # 10 secondes (en microsecondes)
    })

    # 3 paquets appartenant à ce flux : 0.1, 0.9, 0.3
    packets = pd.DataFrame({
        "timestamp": [
            "2017-07-07 10:00:01",
            "2017-07-07 10:00:05",
            "2017-07-07 10:00:09",
        ],
        "src_ip": ["192.168.1.10", "10.0.0.1", "192.168.1.10"],
        "dst_ip": ["10.0.0.1", "192.168.1.10", "10.0.0.1"],
        "src_port": [5000, 80, 5000],
        "dst_port": [80, 5000, 80],
        "protocol": [6, 6, 6],
        "rmse_score": [0.1, 0.9, 0.3],
    })

    scores = aggregate_scores(flows, packets, rule="max")

    assert len(scores) == 1
    assert np.isclose(scores.iloc[0], 0.9)


def test_aggregate_scores_packet_outside_time_window_is_ignored():
    """Vérifie qu'un paquet hors de la fenêtre temporelle est ignoré."""
    flows = pd.DataFrame({
        "Flow ID": ["F1"],
        "Source IP": ["192.168.1.10"],
        "Destination IP": ["10.0.0.1"],
        "Source Port": [5000],
        "Destination Port": [80],
        "Protocol": [6],
        "Timestamp": ["2017-07-07 10:00:00"],
        "Flow Duration": [2_000_000],  # 2 secondes -> fin à 10:00:02
    })

    packets = pd.DataFrame({
        "timestamp": [
            "2017-07-07 10:00:01",  # Dans la fenêtre -> score 0.2
            "2017-07-07 10:00:30",  # Hors fenêtre (+30s) -> score 0.99
        ],
        "src_ip": ["192.168.1.10", "192.168.1.10"],
        "dst_ip": ["10.0.0.1", "10.0.0.1"],
        "src_port": [5000, 5000],
        "dst_port": [80, 80],
        "protocol": [6, 6],
        "rmse_score": [0.2, 0.99],
    })

    scores = aggregate_scores(flows, packets, rule="max", time_tolerance_sec=1.0)
    assert np.isclose(scores.iloc[0], 0.2)


def test_aggregate_scores_flow_without_packets_returns_nan():
    """Vérifie qu'un flux sans paquet correspondant renvoie explicitement NaN (et jamais 0.0)."""
    flows = pd.DataFrame({
        "Flow ID": ["F_Orphan"],
        "Source IP": ["1.1.1.1"],
        "Destination IP": ["2.2.2.2"],
        "Source Port": [1111],
        "Destination Port": [2222],
        "Protocol": [6],
        "Timestamp": ["2017-07-07 10:00:00"],
        "Flow Duration": [1_000_000],
    })

    packets = pd.DataFrame({
        "timestamp": ["2017-07-07 10:00:00"],
        "src_ip": ["9.9.9.9"],
        "dst_ip": ["8.8.8.8"],
        "src_port": [9999],
        "dst_port": [8888],
        "protocol": [6],
        "rmse_score": [0.8],
    })

    scores = aggregate_scores(flows, packets)
    assert len(scores) == 1
    assert np.isnan(scores.iloc[0])


def test_aggregate_scores_empty_inputs():
    """Vérifie la robustesse face à des DataFrames vides."""
    empty_flows = pd.DataFrame(
        columns=[
            "Flow ID",
            "Source IP",
            "Destination IP",
            "Source Port",
            "Destination Port",
            "Protocol",
            "Timestamp",
            "Flow Duration",
        ]
    )
    empty_packets = pd.DataFrame(
        columns=[
            "timestamp",
            "src_ip",
            "dst_ip",
            "src_port",
            "dst_port",
            "protocol",
            "rmse_score",
        ]
    )

    scores = aggregate_scores(empty_flows, empty_packets)
    assert len(scores) == 0
