"""Tests d'intégration pour le script de capture temps réel run_live_capture.py."""

from pathlib import Path
import subprocess
import sys
from scapy.all import IP, TCP, wrpcap


def test_run_live_capture_help():
    """Vérifie que l'aide en ligne de commande de run_live_capture.py fonctionne."""
    cmd = [sys.executable, "scripts/run_live_capture.py", "--help"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "Capture temps réel" in res.stdout
    assert "--interface" in res.stdout


def test_run_live_capture_offline_pcap(tmp_path: Path):
    """Vérifie l'analyse de bout en bout d'un fichier PCAP sans nécessiter de droits root."""
    pcap_file = tmp_path / "traffic_sample.pcap"
    pkts = [
        IP(src="192.168.10.15", dst="172.16.0.2") / TCP(sport=54321, dport=443, flags="S"),
        IP(src="172.16.0.2", dst="192.168.10.15") / TCP(sport=443, dport=54321, flags="SA"),
        IP(src="192.168.10.15", dst="172.16.0.2") / TCP(sport=54321, dport=443, flags="A"),
    ]
    wrpcap(str(pcap_file), pkts)

    cmd = [
        sys.executable,
        "scripts/run_live_capture.py",
        "--pcap",
        str(pcap_file),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "CAPTURE & ANALYSE RÉSEAU TEMPS RÉEL" in res.stdout
    assert "Exécution terminée" in res.stdout
