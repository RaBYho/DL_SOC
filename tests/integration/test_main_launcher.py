"""Integration tests for the unified main.py CLI launcher."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_main_help():
    """Verifies that python main.py --help displays options without error."""
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "main.py"), "--help"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "Sentinel NIDS" in res.stdout
    assert "--dashboard-only" in res.stdout
    assert "--dashboard" in res.stdout


def test_main_offline_pcap_with_dashboard():
    """Verifies that main.py can process an offline PCAP while coupling with dashboard."""
    pcap_path = REPO_ROOT / "pcap" / "demo_nmap.pcap"
    if not pcap_path.exists():
        return

    res = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "main.py"),
            "--pcap",
            str(pcap_path),
            "--port",
            "8999",
            "--allow-loopback",
            "--dashboard",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert res.returncode == 0
    assert "INCIDENT DE SÉCURITÉ DÉTECTÉ" in res.stdout or "ALERTE CONSOLIDÉE" in res.stdout
