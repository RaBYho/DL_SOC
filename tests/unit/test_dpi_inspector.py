"""Tests unitaires pour le moteur d'inspection approfondie des paquets (DPI)."""

from pathlib import Path
import pandas as pd
import pytest
from scapy.all import IP, TCP, Raw, wrpcap

from nids.dpi_inspector import DPIInspector, fuse_predictions_with_dpi


@pytest.fixture
def dpi_inspector() -> DPIInspector:
    return DPIInspector(config_path="configs/dpi_rules.yaml")


def test_dpi_inspector_init(dpi_inspector: DPIInspector):
    """Vérifie que les règles DPI sont bien chargées et compilées."""
    assert dpi_inspector.enabled is True
    assert len(dpi_inspector.rules) >= 4


def test_inspect_payload_fuzzing(dpi_inspector: DPIInspector):
    """Vérifie la détection d'une tentative de fuzzing /.env ou gobuster."""
    payload = b"GET /.env HTTP/1.1\r\nHost: 127.0.0.1\r\nUser-Agent: gobuster/3.6\r\n\r\n"
    res = dpi_inspector.inspect_payload(payload)
    assert res is not None
    attack_class, conf = res
    assert attack_class == "Web Attack – Brute Force"
    assert conf == 1.0


def test_inspect_payload_sqli(dpi_inspector: DPIInspector):
    """Vérifie la détection d'une injection SQL."""
    payload = b"GET /users?id=1' UNION SELECT 1,password FROM users-- HTTP/1.1\r\n\r\n"
    res = dpi_inspector.inspect_payload(payload)
    assert res is not None
    attack_class, conf = res
    assert attack_class == "Web Attack – Sql Injection"
    assert conf == 1.0


def test_inspect_payload_benign(dpi_inspector: DPIInspector):
    """Vérifie qu'un payload HTTP normal ne déclenche aucune règle DPI."""
    payload = b"GET /index.html HTTP/1.1\r\nHost: example.com\r\nUser-Agent: Mozilla/5.0 Chrome/120\r\n\r\n"
    res = dpi_inspector.inspect_payload(payload)
    assert res is None


def test_fuse_predictions_with_dpi():
    """Vérifie la fusion déterministe entre les prédictions ML et les correspondances DPI."""
    preds_df = pd.DataFrame({
        "verdict": ["BENIGN", "BENIGN"],
        "confidence": [0.0, 0.0],
        "stage1_score": [0.001, 0.002],
    })
    flows_df = pd.DataFrame({
        "Flow ID": ["192.168.1.50-10.0.0.1-54321-80-6", "192.168.1.50-10.0.0.1-54322-80-6"],
    })
    dpi_matches = {
        "192.168.1.50-10.0.0.1-54321-80-6": ("Web Attack – Brute Force", 1.0),
    }

    fused = fuse_predictions_with_dpi(preds_df, flows_df, dpi_matches)
    assert fused.iloc[0]["verdict"] == "Web Attack – Brute Force"
    assert fused.iloc[0]["confidence"] == 1.0
    assert fused.iloc[0]["stage1_score"] == 1.0
    # Le flux 2 reste inchangé
    assert fused.iloc[1]["verdict"] == "BENIGN"
    assert fused.iloc[1]["confidence"] == 0.0


def test_inspect_pcap_end_to_end(dpi_inspector: DPIInspector, tmp_path: Path):
    """Vérifie l'inspection complète d'un PCAP et l'association au Flow ID."""
    pcap_file = tmp_path / "test_dpi.pcap"
    pkt = (
        IP(src="192.168.1.10", dst="10.0.0.5")
        / TCP(sport=55555, dport=80, flags="PA")
        / Raw(load=b"GET /.git/HEAD HTTP/1.1\r\nHost: 10.0.0.5\r\n\r\n")
    )
    wrpcap(str(pcap_file), [pkt])

    matches = dpi_inspector.inspect_pcap(pcap_file)
    expected_key = "192.168.1.10-10.0.0.5-55555-80-6"
    assert expected_key in matches
    assert matches[expected_key][0] == "Web Attack – Brute Force"


def test_inspect_payload_benign_cookies(dpi_inspector: DPIInspector):
    """Vérifie que des cookies standards avec id= ou cat= ne déclenchent pas Infiltration."""
    req = (
        b"GET /search?q=open+nids HTTP/1.1\r\n"
        b"Host: www.google.com\r\n"
        b"Cookie: 1P_JAR=2026-11-10; NID=511; id=220076a9b; cat=tech; session=abc\r\n\r\n"
    )
    assert dpi_inspector.inspect_payload(req) is None


def test_inspect_pcap_ignores_server_responses(dpi_inspector: DPIInspector, tmp_path: Path):
    """Vérifie que les réponses HTTP serveur contenant des balises <script> sont ignorées."""
    pcap_file = tmp_path / "server_resp.pcap"
    resp = (
        IP(src="172.217.114.4", dst="192.168.1.10")
        / TCP(sport=80, dport=55555, flags="PA")
        / Raw(load=b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<script>alert(1)</script>")
    )
    wrpcap(str(pcap_file), [resp])

    matches = dpi_inspector.inspect_pcap(pcap_file)
    assert len(matches) == 0
