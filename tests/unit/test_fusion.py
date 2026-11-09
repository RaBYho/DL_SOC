"""Tests unitaires pour le moteur de fusion décisionnelle (fusion.py)."""

import numpy as np
import pandas as pd
import pytest

from nids.fusion import fuse_decisions
from nids.labels import (
    ALL_LABELS,
    BENIGN,
    ANOMALY_UNKNOWN,
    SUSPECT_UNCERTAIN,
    UNKNOWN_ATTACK_LIKELY,
)


@pytest.mark.parametrize(
    "is_suspect,stage2_class,confidence,kitsune_score,expected_verdict",
    [
        # Cas 1 : Normal partout -> BENIGN
        (False, None, 0.0, 0.05, BENIGN),
        # Cas 2 : Normal en supervisé mais anormal Kitsune -> ANOMALY_UNKNOWN (0-day)
        (False, None, 0.0, 0.35, ANOMALY_UNKNOWN),
        # Cas 3 : Suspect et Étage 2 confiant (Kitsune indifférent) -> Attaque identifiée
        (True, "DDoS", 0.90, 0.02, "DDoS"),
        (True, "PortScan", 0.85, 0.40, "PortScan"),
        # Cas 4 : Suspect mais incertain + Kitsune normal -> SUSPECT_UNCERTAIN
        (True, "DDoS", 0.45, 0.05, SUSPECT_UNCERTAIN),
        # Cas 5 : Suspect et incertain + Kitsune anormal -> UNKNOWN_ATTACK_LIKELY
        (True, "DDoS", 0.45, 0.35, UNKNOWN_ATTACK_LIKELY),
        # Cas 6 : Kitsune absent (NaN) -> Repli sur décision Étages 1+2
        (False, None, 0.0, np.nan, BENIGN),
        (True, "Bot", 0.95, np.nan, "Bot"),
        (True, "Bot", 0.40, np.nan, SUSPECT_UNCERTAIN),
    ],
)
def test_fusion_matrix_all_cases(
    is_suspect: bool,
    stage2_class: str | None,
    confidence: float,
    kitsune_score: float,
    expected_verdict: str,
):
    """Vérifie l'exactitude de chacun des cas de la matrice d'arbitrage."""
    supervised_df = pd.DataFrame({
        "stage1_score": [0.9 if is_suspect else 0.1],
        "is_suspect": [is_suspect],
        "stage2_class": [stage2_class],
        "confidence": [confidence],
        "verdict": [stage2_class if (is_suspect and confidence >= 0.7) else (SUSPECT_UNCERTAIN if is_suspect else BENIGN)],
    })
    kitsune_series = pd.Series([kitsune_score], name="kitsune_score")

    final_verdicts = fuse_decisions(
        supervised_df=supervised_df,
        kitsune_scores=kitsune_series,
        t2=0.7,
        t3=0.15,
    )

    assert len(final_verdicts) == 1
    assert final_verdicts.iloc[0] == expected_verdict
    assert final_verdicts.iloc[0] in ALL_LABELS


def test_fusion_exact_boundary_threshold():
    """Vérifie le comportement exactement à la frontière du seuil t3."""
    supervised_df = pd.DataFrame({
        "is_suspect": [False],
        "stage2_class": [None],
        "confidence": [0.0],
        "verdict": [BENIGN],
    })
    # kitsune_score exactement égal à t3 -> considéré comme anormal (>= t3)
    kitsune_series = pd.Series([0.15])

    verdicts = fuse_decisions(supervised_df, kitsune_series, t2=0.7, t3=0.15)
    assert verdicts.iloc[0] == ANOMALY_UNKNOWN


def test_fusion_mismatched_lengths_raises():
    """Vérifie qu'une disparité de longueurs lève une ValueError explicite."""
    supervised_df = pd.DataFrame({"is_suspect": [False, True]})
    kitsune_series = pd.Series([0.1])  # Longueur 1 vs 2

    with pytest.raises(ValueError, match="Longueur incohérente"):
        fuse_decisions(supervised_df, kitsune_series)
