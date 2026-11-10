"""Tests unitaires pour la calibration dynamique de Kitsune sans empoisonnement."""

import numpy as np
import pytest

from nids.kitsune_runner import compute_live_dynamic_threshold, LiveKitsuneCalibrator


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


def test_compute_live_dynamic_threshold_mu_plus_3sigma():
    """Vérifie le calcul par méthode mu + 3*sigma."""
    rmses = np.array([0.0020, 0.0022, 0.0018, 0.0020, 0.0020])
    s1s = np.zeros(len(rmses))
    expected = float(round(np.mean(rmses) + 3.0 * np.std(rmses), 5))

    threshold = compute_live_dynamic_threshold(
        rmse_scores=rmses,
        s1_scores=s1s,
        method="mu_plus_3sigma",
        fallback_t3=0.0035,
    )
    assert threshold == expected
    assert 0.0023 < threshold < 0.0030


def test_compute_live_dynamic_threshold_empty_fallback():
    """Vérifie le repli sur fallback_t3 lorsqu'aucun flux sain n'est disponible."""
    threshold = compute_live_dynamic_threshold(
        rmse_scores=[],
        s1_scores=[],
        fallback_t3=0.0035,
    )
    assert threshold == 0.0035


def test_live_kitsune_calibrator_sliding_window_and_anti_poisoning():
    """Vérifie le gestionnaire de calibration avec fenêtre glissante et anti-empoisonnement."""
    calibrator = LiveKitsuneCalibrator(
        default_t3=0.0035,
        method="mu_plus_3sigma",
        min_clean_flows=5,
        max_history_flows=10,
        t1=0.5,
    )
    assert calibrator.current_threshold == 0.0035
    assert len(calibrator) == 0

    # Batch 1: 3 flux bénins (< 0.0035) -> min_clean_flows (5) pas encore atteint
    batch1_rmse = [0.0020, 0.0021, 0.0019]
    batch1_s1 = [0.01, 0.02, 0.01]
    t_after_b1 = calibrator.update(batch1_rmse, batch1_s1)
    assert t_after_b1 == 0.0035
    assert len(calibrator) == 3

    # Batch 2: 3 flux bénins + 1 attaque connue (s1=0.99) + 1 anomalie (rmse=0.0080 > t3)
    batch2_rmse = [0.0020, 0.0019, 0.0022, 0.0080, 0.0020]
    batch2_s1 = [0.01, 0.02, 0.01, 0.01, 0.99]
    t_after_b2 = calibrator.update(batch2_rmse, batch2_s1)

    # 3 flux bénins ajoutés -> total = 6 flux sains (l'attaque s1=0.99 et l'anomalie 0.0080 sont rejetées !)
    assert len(calibrator) == 6
    assert t_after_b2 < 0.0035
    assert t_after_b2 > 0.0020
