"""Tests d'intégration des adaptateurs avec les vrais modèles téléchargés sur mini.csv."""

import numpy as np
import pandas as pd
import pytest

from nids.adapters.stage1 import CatBoostStage1, XGBoostStage1
from nids.adapters.stage2 import CnnStage2
from nids.labels import BENIGN


@pytest.fixture
def mini_df() -> pd.DataFrame:
    """Charge le mini-dataset représentatif."""
    return pd.read_csv("data/samples/mini.csv")


@pytest.mark.requires_models
def test_catboost_stage1_real_inference(mini_df: pd.DataFrame):
    """Vérifie le chargement et l'inférence du vrai modèle CatBoost sur mini.csv."""
    adapter = CatBoostStage1()
    scores = adapter.score(mini_df)

    assert isinstance(scores, np.ndarray)
    assert len(scores) == len(mini_df)
    assert np.all((scores >= 0.0) & (scores <= 1.0))

    # Test de bon sens : score moyen des attaques supérieur à celui des flux bénins
    benign_mask = mini_df["Label"] == BENIGN
    mean_benign = np.mean(scores[benign_mask])
    mean_attack = np.mean(scores[~benign_mask])

    print(f"CatBoost - Score moyen bénin: {mean_benign:.4f}, attaques: {mean_attack:.4f}")
    assert mean_attack > mean_benign


@pytest.mark.requires_models
def test_xgboost_stage1_real_inference(mini_df: pd.DataFrame):
    """Vérifie le chargement et l'inférence du vrai modèle XGBoost (AegisAI) sur mini.csv."""
    adapter = XGBoostStage1()
    scores = adapter.score(mini_df)

    assert isinstance(scores, np.ndarray)
    assert len(scores) == len(mini_df)
    assert np.all((scores >= 0.0) & (scores <= 1.0))

    benign_mask = mini_df["Label"] == BENIGN
    mean_benign = np.mean(scores[benign_mask])
    mean_attack = np.mean(scores[~benign_mask])

    print(f"XGBoost - Score moyen bénin: {mean_benign:.4f}, attaques: {mean_attack:.4f}")
    assert mean_attack > mean_benign


@pytest.mark.requires_models
def test_cnn_stage2_real_inference(mini_df: pd.DataFrame):
    """Vérifie le chargement et l'inférence du vrai modèle PyTorch DNN-1D sur mini.csv."""
    adapter = CnnStage2()
    probas = adapter.predict_proba(mini_df)

    assert isinstance(probas, np.ndarray)
    assert probas.shape == (len(mini_df), 14)
    assert np.all((probas >= 0.0) & (probas <= 1.0))
    # Chaque ligne doit sommer à 1.0
    assert np.allclose(probas.sum(axis=1), 1.0, atol=1e-5)
