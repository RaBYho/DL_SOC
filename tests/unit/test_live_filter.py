"""Tests unitaires pour le pré-filtrage déterministe en direct (live_filter.py)."""

import pandas as pd
import pytest

from nids.live_filter import pre_filter_flows


@pytest.fixture
def base_config() -> dict:
    """Configuration de test représentative de live_guard.yaml."""
    return {
        "pre_filter": {
            "ignore_multicast_broadcast": True,
            "ignored_ports": [5353, 1900, 5355, 137, 138],
            "min_total_packets": 2,
            "whitelisted_ips": ["127.0.0.1", "10.0.0.99"],
            "whitelisted_udp_443_cdns": True,
        }
    }


def test_filter_multicast_and_broadcast_ports(base_config: dict):
    """Vérifie que les paquets multicast (224.0.0.251) et ports mDNS/SSDP sont écartés."""
    df = pd.DataFrame({
        "Flow ID": ["F1", "F2", "F3"],
        "Source IP": ["192.168.1.10", "192.168.1.11", "192.168.1.12"],
        "Destination IP": ["224.0.0.251", "192.168.1.1", "172.16.0.1"],
        "Source Port": [5353, 50000, 54321],
        "Destination Port": [5353, 1900, 80],
        "Protocol": [17, 17, 6],
        "Total Fwd Packets": [5, 5, 5],
        "Total Backward Packets": [5, 5, 5],
        "SYN Flag Count": [0, 0, 1],
    })

    to_score, ignored = pre_filter_flows(df, base_config)

    assert len(to_score) == 1
    assert to_score["Flow ID"].iloc[0] == "F3"
    assert len(ignored) == 2
    assert set(ignored["Flow ID"]) == {"F1", "F2"}


def test_filter_whitelisted_ips(base_config: dict):
    """Vérifie que les IPs dans la liste blanche sont ignorées."""
    df = pd.DataFrame({
        "Flow ID": ["F_Local", "F_Whitelisted", "F_Target"],
        "Source IP": ["127.0.0.1", "192.168.1.10", "192.168.1.10"],
        "Destination IP": ["127.0.0.1", "10.0.0.99", "172.16.0.2"],
        "Source Port": [8080, 5000, 5000],
        "Destination Port": [80, 80, 80],
        "Protocol": [6, 6, 6],
        "Total Fwd Packets": [5, 5, 5],
        "Total Backward Packets": [5, 5, 5],
        "SYN Flag Count": [1, 1, 1],
    })

    to_score, ignored = pre_filter_flows(df, base_config)

    assert len(to_score) == 1
    assert to_score["Flow ID"].iloc[0] == "F_Target"
    assert len(ignored) == 2


def test_filter_orphan_vs_syn_scan(base_config: dict):
    """Vérifie qu'un flux micro-mort (1 paquet sans SYN) est ignoré mais un SYN Scan conservé."""
    df = pd.DataFrame({
        "Flow ID": ["F_Orphan", "F_SynScan", "F_Normal"],
        "Source IP": ["192.168.1.10", "192.168.1.11", "192.168.1.12"],
        "Destination IP": ["172.16.0.1", "172.16.0.2", "172.16.0.3"],
        "Source Port": [1234, 1235, 1236],
        "Destination Port": [80, 80, 80],
        "Protocol": [6, 6, 6],
        "Total Fwd Packets": [1, 1, 10],
        "Total Backward Packets": [0, 0, 10],
        "SYN Flag Count": [0, 1, 1],  # F_SynScan a un SYN !
    })

    to_score, ignored = pre_filter_flows(df, base_config)

    assert "F_Orphan" in ignored["Flow ID"].values
    assert "F_SynScan" in to_score["Flow ID"].values
    assert "F_Normal" in to_score["Flow ID"].values


def test_pre_filter_does_not_mutate_input(base_config: dict):
    """Garantit l'immutabilité du DataFrame d'entrée."""
    df = pd.DataFrame({
        "Flow ID": ["F1"],
        "Source IP": ["127.0.0.1"],
        "Destination IP": ["127.0.0.1"],
        "Source Port": [80],
        "Destination Port": [80],
        "Protocol": [6],
        "Total Fwd Packets": [1],
        "Total Backward Packets": [0],
        "SYN Flag Count": [0],
    })
    df_copy = df.copy(deep=True)

    _ = pre_filter_flows(df, base_config)
    pd.testing.assert_frame_equal(df, df_copy)
