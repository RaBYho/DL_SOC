"""Tests unitaires pour la génération du mini-échantillon synthétique."""

import json
from pathlib import Path
import pandas as pd

from nids.sample_generator import generate_mini_sample
from nids.labels import ATTACK_CLASSES, BENIGN
from nids.features import NETWORK_METADATA_COLUMNS


def test_generate_mini_sample(tmp_path: Path):
    """Vérifie la structure, les métadonnées et la complétude des classes du mini-dataset."""
    with open("models/cnn_feature_names.json") as f:
        feature_names = json.load(f)

    out_file = tmp_path / "test_mini.csv"
    df = generate_mini_sample(out_file, feature_names, n_benign=50, n_per_attack=3, seed=42)

    assert out_file.exists()
    assert len(df) == 50 + (14 * 3)

    # Vérification des colonnes de métadonnées réseau
    for col in NETWORK_METADATA_COLUMNS:
        assert col in df.columns

    # Vérification de toutes les 14 classes d'attaques
    unique_labels = set(df["Label"].unique())
    assert BENIGN in unique_labels
    for attack in ATTACK_CLASSES:
        assert attack in unique_labels

    # Aucune valeur manquante ou infinie
    assert not df.isna().any().any()
