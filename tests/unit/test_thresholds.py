"""Tests unitaires pour l'étalonnage et la calibration des seuils (thresholds.py)."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from nids.thresholds import (
    calibrate_t1_recall,
    calibrate_t3_kitsune_percentile,
    check_no_test_leakage,
    save_thresholds,
)


def test_leakage_check_raises_on_test_file():
    """Vérifie que toute tentative de calibrer sur un jeu de test est formellement bloquée."""
    with pytest.raises(PermissionError, match="Interdiction absolue"):
        check_no_test_leakage("data/processed/test.parquet")

    with pytest.raises(PermissionError, match="Interdiction absolue"):
        check_no_test_leakage("data/samples/my_test_split.csv")

    # Autorisé pour validation ou train
    check_no_test_leakage("data/processed/val.parquet")
    check_no_test_leakage("data/samples/mini.csv")


def test_calibrate_t1_recall():
    """Vérifie le choix optimal de t1 garantissant le rappel minimal visé."""
    # 5 attaques avec scores [0.9, 0.8, 0.7, 0.6, 0.4]
    # 5 bénins avec scores [0.1, 0.1, 0.2, 0.3, 0.5]
    y_true_binary = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    scores = np.array([0.1, 0.1, 0.2, 0.3, 0.5, 0.9, 0.8, 0.7, 0.6, 0.4])

    # Si on veut un rappel d'au moins 0.80 (4 attaques sur 5 capturées)
    t1_chosen = calibrate_t1_recall(y_true_binary, scores, target_recall=0.80)
    # Pour avoir 4 attaques sur 5 (scores 0.9, 0.8, 0.7, 0.6), le seuil max possible est 0.60
    assert np.isclose(t1_chosen, 0.60, atol=0.05)


def test_calibrate_t3_kitsune_percentile():
    """Vérifie le calcul du seuil t3 au 99e percentile sur trafic bénin."""
    # Distribution de 1000 scores bénins
    rng = np.random.default_rng(42)
    benign_scores = rng.normal(loc=0.05, scale=0.01, size=1000)

    t3 = calibrate_t3_kitsune_percentile(benign_scores, percentile=99.0)
    # Le 99e percentile doit être strictement supérieur à la médiane
    assert t3 > np.median(benign_scores)
    # Environ 1 % des scores bénins doivent dépasser t3
    assert np.mean(benign_scores >= t3) <= 0.015


def test_save_thresholds(tmp_path: Path):
    """Vérifie l'enregistrement et la lecture du fichier de configuration YAML."""
    out_yaml = tmp_path / "thresholds_test.yaml"
    save_thresholds(out_yaml, t1=0.45, t2=0.75, t3=0.18)

    assert out_yaml.exists()
    content = out_yaml.read_text()
    assert "t1: 0.45" in content
    assert "t2: 0.75" in content
    assert "t3: 0.18" in content
