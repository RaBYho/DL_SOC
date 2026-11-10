"""Tests unitaires pour l'interface en ligne de commande Rich (cli_ui)."""

import os
from pathlib import Path
from rich.console import Console

from nids.cli_ui import (
    get_severity_style,
    print_banner,
    print_batch_status,
    print_alert_card,
    print_session_summary,
    suppress_c_stderr,
)
from nids.live_guard import ConsolidatedAlert


def test_get_severity_style():
    """Vérifie l'association correcte des couleurs et niveaux de sévérité."""
    style_crit, label_crit = get_severity_style("Web Attack – Sql Injection")
    assert "red" in style_crit
    assert "CRITIQUE" in label_crit

    style_warn, label_warn = get_severity_style("PortScan")
    assert "yellow" in style_warn

    style_anom, label_anom = get_severity_style("ANOMALY_UNKNOWN")
    assert "magenta" in style_anom


def test_print_banner():
    """Vérifie le rendu de la bannière Sentinel SOC."""
    console = Console(record=True, width=100)
    print_banner(
        console=console,
        iface="eth0",
        duration=15,
        t1=0.50,
        t2=0.70,
        t3=0.0100,
        tool="dumpcap",
        is_pcap=False,
    )
    output = console.export_text()
    assert "CAPTURE & ANALYSE RÉSEAU TEMPS RÉEL" in output
    assert "eth0" in output
    assert "0.50" in output
    assert "0.70" in output


def test_print_batch_status():
    """Vérifie l'affichage de l'état d'un micro-batch."""
    console = Console(record=True, width=100)
    print_batch_status(console, batch_num=1, pcap_name="test.pcap", n_flows=25, n_alerts=0)
    output = console.export_text()
    assert "Batch #1" in output
    assert "test.pcap" in output
    assert "25 flux" in output
    assert "0 alerte" in output


def test_print_alert_card():
    """Vérifie la mise en forme de la carte d'alerte et la présence du pattern pour regex."""
    console = Console(record=True, width=100)
    alert = ConsolidatedAlert(
        timestamp=1000.0,
        src_ip="192.168.1.50",
        dst_ip="10.0.0.1",
        attack_class="Web Attack – Sql Injection",
        flow_count=3,
        host_score=95.5,
        suppressed_count=1,
    )
    print_alert_card(console, alert)
    output = console.export_text()
    assert "192.168.1.50" in output
    assert "10.0.0.1" in output
    assert "Classe: Web Attack – Sql Injection" in output
    assert "Score hôte: 95.5" in output


def test_print_session_summary():
    """Vérifie la synthèse finale avec le tableau de statistiques."""
    console = Console(record=True, width=100)
    alerts = [
        ConsolidatedAlert(
            timestamp=1000.0,
            src_ip="192.168.1.50",
            dst_ip="10.0.0.1",
            attack_class="PortScan",
            flow_count=10,
            host_score=80.0,
            suppressed_count=2,
        )
    ]
    print_session_summary(console, alerts=alerts, total_batches=5, output_path=Path("/tmp/alerts.json"))
    output = console.export_text()
    assert "Exécution terminée" in output
    assert "1 alerte(s) consolidée(s)" in output
    assert "PortScan" in output


def test_suppress_c_stderr():
    """Vérifie que suppress_c_stderr intercepte les écritures directes sur fd 2."""
    with suppress_c_stderr():
        os.write(2, b"Should be suppressed\n")
