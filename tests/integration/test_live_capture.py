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
    assert "--bpf-filter" in res.stdout
    assert "--duration" in res.stdout


def test_run_live_capture_bpf_filter_argument(tmp_path: Path):
    """Vérifie que le flag --bpf-filter est accepté en CLI."""
    pcap_file = tmp_path / "traffic_bpf.pcap"
    pkts = [
        IP(src="192.168.10.15", dst="172.16.0.2") / TCP(sport=54321, dport=443, flags="S"),
        IP(src="172.16.0.2", dst="192.168.10.15") / TCP(sport=443, dport=54321, flags="SA"),
    ]
    wrpcap(str(pcap_file), pkts)

    cmd = [
        sys.executable,
        "scripts/run_live_capture.py",
        "--pcap",
        str(pcap_file),
        "--bpf-filter",
        "tcp and not port 5353",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "Exécution terminée" in res.stdout


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


def test_run_live_capture_allow_loopback(tmp_path: Path):
    """Vérifie que le flag --allow-loopback permet le traitement du trafic 127.0.0.1."""
    pcap_file = tmp_path / "loopback_sample.pcap"
    pkts = [
        IP(src="127.0.0.1", dst="127.0.0.1") / TCP(sport=40000, dport=80, flags="S"),
        IP(src="127.0.0.1", dst="127.0.0.1") / TCP(sport=80, dport=40000, flags="SA"),
        IP(src="127.0.0.1", dst="127.0.0.1") / TCP(sport=40000, dport=80, flags="A"),
    ]
    wrpcap(str(pcap_file), pkts)

    cmd = [
        sys.executable,
        "scripts/run_live_capture.py",
        "--pcap",
        str(pcap_file),
        "--allow-loopback",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "Exécution terminée" in res.stdout


def test_drain_and_purge_remaining_pcaps(tmp_path: Path):
    """Vérifie le traitement garanti du reliquat (files[-1]) et sa purge immédiate."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("run_live_capture", "scripts/run_live_capture.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _drain_remaining_pcaps = mod._drain_remaining_pcaps

    import yaml
    from nids.adapters.stage1 import CatBoostStage1, XGBoostStage1
    from nids.adapters.stage2 import CnnStage2
    from nids.pipeline import CascadedNIDSPipeline
    from nids.live_guard import LiveAlertGuard

    work_dir = tmp_path / "work"
    work_dir.mkdir()
    pcap_file = work_dir / "capture_00001.pcap"
    pkts = [
        IP(src="192.168.1.10", dst="172.16.0.2") / TCP(sport=12345, dport=80, flags="S"),
        IP(src="172.16.0.2", dst="192.168.1.10") / TCP(sport=80, dport=12345, flags="SA"),
    ]
    wrpcap(str(pcap_file), pkts)

    with open("configs/live_guard.yaml") as f:
        cfg = yaml.safe_load(f)

    pipe = CascadedNIDSPipeline([CatBoostStage1(), XGBoostStage1()], CnnStage2())
    guard = LiveAlertGuard(cfg)
    processed = set()

    # Le fichier doit être traité et supprimé immédiatement
    _drain_remaining_pcaps(work_dir, processed, pipe, guard, cfg, allow_loopback=False, keep=False)

    assert "capture_00001.pcap" in processed
    assert not pcap_file.exists()  # Purge atomique vérifiée !


def test_run_live_capture_no_kitsune_flag(tmp_path: Path):
    """Vérifie le fonctionnement du flag --no-kitsune en ligne de commande."""
    pcap_file = tmp_path / "traffic.pcap"
    pkts = [
        IP(src="192.168.10.15", dst="172.16.0.2") / TCP(sport=54321, dport=443, flags="S"),
        IP(src="172.16.0.2", dst="192.168.10.15") / TCP(sport=443, dport=54321, flags="SA"),
    ]
    wrpcap(str(pcap_file), pkts)

    cmd = [
        sys.executable,
        "scripts/run_live_capture.py",
        "--pcap",
        str(pcap_file),
        "--no-kitsune",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "Exécution terminée" in res.stdout
