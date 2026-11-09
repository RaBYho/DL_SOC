"""Test d'intégration pour le script de démonstration CLI run_demo.py."""

import subprocess
import sys


def test_run_demo_cli_execution():
    """Vérifie que le script run_demo.py s'exécute de bout en bout sans lever d'erreur."""
    cmd = [
        sys.executable,
        "scripts/run_demo.py",
        "data/samples/mini.csv",
        "--packets",
        "data/samples/packet_scores.parquet",
        "--limit",
        "5",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    assert result.returncode == 0
    assert "DÉMONSTRATION DU PIPELINE NIDS HYBRIDE" in result.stdout
    assert "SYNTHÈSE DES DÉCISIONS" in result.stdout
    assert "Analyse terminée avec succès" in result.stdout
