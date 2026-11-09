"""Tests unitaires pour la calibration dynamique de Kitsune sans empoisonnement."""

import numpy as np
import pytest

from nids.kitsune_runner import compute_live_dynamic_threshold


def test_anti_poisoning_filters_out_malicious_flows():
    """Vérifie que les flux suspects (s1 >= t1) sont exclus du calcul du seuil dynamique."""
    # 900 paquets bénins avec RMSE faible (autour de 0.05)
    # 100 paquets d'attaques injectés avec fort RMSE (autour de 1.5)
    rmse_benign = np.full(900, 0.05)
    rmse_attack = np.full(100, 1.5)
    all_rmse = np.concatenate([rmse_benign, rmse_attack])

    # Scores Étage 1 : 0.01 pour les bénins, 0.95 pour les attaques (t1 = 0.5)
    s1_benign = np.full(900, 0.01)
    s1_attack = np.full(100, 0.95)
    all_s1 = np.concatenate([s1_benign, s1_attack])

    # Avec protection anti-empoisonnement : le seuil doit être calculé UNIQUEMENT sur le bénin
    threshold_clean = compute_live_dynamic_threshold(
        rmse_scores=all_rmse,
        s1_scores=all_s1,
        t1=0.5,
        percentile=99.9,
        multiplier=1.5,
        filter_poisoning=True,
    )

    # Sans protection anti-empoisonnement : le seuil exploserait à cause des attaques injectées
    threshold_poisoned = compute_live_dynamic_threshold(
        rmse_scores=all_rmse,
        s1_scores=all_s1,
        t1=0.5,
        percentile=99.9,
        multiplier=1.5,
        filter_poisoning=False,
    )

    # Le seuil propre est bas (~0.05 * 1.5 = 0.075), le seuil empoisonné est > 1.0
    assert threshold_clean < 0.15
    assert threshold_poisoned > 1.0
