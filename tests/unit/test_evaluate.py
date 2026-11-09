"""Tests unitaires pour le module d'évaluation et de métriques (evaluate.py)."""

import numpy as np
import pandas as pd
import pytest

from nids.evaluate import (
    compute_stage1_metrics,
    compute_multiclass_metrics,
    compute_kitsune_contribution,
    compare_nids_configurations,
)
from nids.labels import BENIGN, ANOMALY_UNKNOWN


def test_compute_stage1_metrics():
    """Vérifie le calcul du rappel, précision, F1 et FPR pour l'Étage 1."""
    # 4 attaques, 4 bénins
    y_true_binary = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    # Modèle détecte 3 attaques (1 faux négatif) et 1 faux positif
    y_pred_binary = np.array([1, 1, 1, 0, 1, 0, 0, 0])

    metrics = compute_stage1_metrics(y_true_binary, y_pred_binary)

    assert np.isclose(metrics["recall"], 0.75)  # 3 TP / 4 attaques
    assert np.isclose(metrics["precision"], 0.75)  # 3 TP / 4 prédictions positives
    assert np.isclose(metrics["fpr"], 0.25)  # 1 FP / 4 bénins
    assert "f1_score" in metrics


def test_compute_multiclass_metrics():
    """Vérifie le calcul des métriques multiclasses (F1 macro et pondéré)."""
    y_true = ["DDoS", "DDoS", "PortScan", "BENIGN"]
    y_pred = ["DDoS", "PortScan", "PortScan", "BENIGN"]

    metrics = compute_multiclass_metrics(y_true, y_pred)

    assert "f1_macro" in metrics
    assert "f1_weighted" in metrics
    assert "confusion_matrix" in metrics
    assert metrics["f1_macro"] > 0.0


def test_compute_kitsune_contribution():
    """Vérifie le calcul de l'apport net de Kitsune (rattrapage d'attaques ratées)."""
    y_true = np.array(["DDoS", "PortScan", "BENIGN", "BENIGN"])
    supervised_verdicts = np.array([BENIGN, "PortScan", BENIGN, BENIGN])  # DDoS a été raté
    final_hybrid_verdicts = np.array([ANOMALY_UNKNOWN, "PortScan", BENIGN, BENIGN])  # Rattrapé par Kitsune

    contrib = compute_kitsune_contribution(y_true, supervised_verdicts, final_hybrid_verdicts)

    assert contrib["missed_by_supervised"] == 1
    assert contrib["recovered_by_kitsune"] == 1
    assert np.isclose(contrib["recovery_rate"], 1.0)
