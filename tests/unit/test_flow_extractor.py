"""Tests unitaires pour l'extraction de flux CICFlowMeter à partir de fichiers PCAP."""

import json
from pathlib import Path
import pytest
from scapy.all import IP, TCP, wrpcap

from nids.flow_extractor import convert_pcap_to_flows, get_default_interface


@pytest.fixture(scope="module")
def expected_features() -> list[str]:
    """Charge les 78 variables attendues par le modèle CNN-1D."""
    with open("models/cnn_feature_names.json") as f:
        return json.load(f)


def test_get_default_interface():
    """Vérifie que la détection d'interface réseau retourne un nom valide."""
    iface = get_default_interface()
    assert isinstance(iface, str)
    assert len(iface) > 0


def test_convert_pcap_to_flows(tmp_path: Path, expected_features: list[str]):
    """Vérifie la conversion d'un PCAP en DataFrame normalisé CICFlowMeter."""
    pcap_path = tmp_path / "sample.pcap"
    pkts = [
        IP(src="192.168.1.10", dst="1.1.1.1") / TCP(sport=12345, dport=80, flags="S"),
        IP(src="1.1.1.1", dst="192.168.1.10") / TCP(sport=80, dport=12345, flags="SA"),
        IP(src="192.168.1.10", dst="1.1.1.1") / TCP(sport=12345, dport=80, flags="A"),
    ]
    wrpcap(str(pcap_path), pkts)

    df = convert_pcap_to_flows(pcap_path)

    assert len(df) == 1
    assert df["Source IP"].iloc[0] == "192.168.1.10"
    assert df["Destination IP"].iloc[0] == "1.1.1.1"
    assert df["Source Port"].iloc[0] == 12345
    assert df["Destination Port"].iloc[0] == 80
    assert "Flow ID" in df.columns
    assert "Timestamp" in df.columns

    # Vérification que toutes les 78 caractéristiques cibles sont bien présentes
    for feat in expected_features:
        assert feat in df.columns, f"Colonne manquante : {feat}"
        val = df[feat].iloc[0]
        assert not pytest.approx(val) is None


def test_convert_empty_pcap(tmp_path: Path):
    """Vérifie qu'un PCAP sans paquet retourne un DataFrame vide sans crasher."""
    empty_pcap = tmp_path / "empty.pcap"
    wrpcap(str(empty_pcap), [])

    df = convert_pcap_to_flows(empty_pcap)
    assert len(df) == 0
