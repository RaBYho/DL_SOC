"""Tests d'intégration de l'alignement réel flux <-> paquets sur mini.csv et packet_scores.parquet."""

import numpy as np
import pandas as pd

from nids.flow_alignment import aggregate_scores
from nids.labels import BENIGN


def test_real_alignment_on_samples():
    """Vérifie l'alignement vectorisé de bout en bout sur les fichiers d'échantillons."""
    flows = pd.read_csv("data/samples/mini.csv")
    packets = pd.read_parquet("data/samples/packet_scores.parquet")

    kitsune_scores = aggregate_scores(flows, packets, rule="max", time_tolerance_sec=1.0)

    assert isinstance(kitsune_scores, pd.Series)
    assert len(kitsune_scores) == len(flows)

    # Tous les flux doivent avoir été associés (car générés de concert)
    assert not kitsune_scores.isna().all()

    benign_mask = flows["Label"] == BENIGN
    benign_median = kitsune_scores[benign_mask].median()
    attack_median = kitsune_scores[~benign_mask].median()

    print(f"\nAlignement Kitsune - Médiane score bénin: {benign_median:.4f}, attaques: {attack_median:.4f}")
    assert attack_median > benign_median
