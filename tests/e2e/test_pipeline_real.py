"""Test End-to-End du pipeline en cascade avec les vrais modèles sur mini.csv."""

import pandas as pd
import pytest

from nids.adapters.stage1 import CatBoostStage1, XGBoostStage1
from nids.adapters.stage2 import CnnStage2
from nids.pipeline import CascadedNIDSPipeline
from nids.labels import ALL_LABELS, BENIGN


@pytest.mark.e2e
@pytest.mark.requires_models
def test_cascaded_pipeline_real_e2e():
    """Vérifie l'exécution complète du pipeline supervisé avec les 3 vrais modèles."""
    df = pd.read_csv("data/samples/mini.csv")

    catboost = CatBoostStage1()
    xgboost = XGBoostStage1()
    cnn = CnnStage2()

    # t1=0.01 pour capturer les suspects sur mini.csv, t2=0.1 pour la confiance
    pipeline = CascadedNIDSPipeline(
        stage1_models=[catboost, xgboost],
        stage2_model=cnn,
        t1=0.01,
        t2=0.1,
    )

    results = pipeline.predict(df)

    assert len(results) == len(df)
    assert set(results.columns) == {
        "stage1_score",
        "is_suspect",
        "stage2_class",
        "confidence",
        "verdict",
    }

    # Toutes les étiquettes produites sont canoniques
    unique_verdicts = set(results["verdict"].unique())
    assert unique_verdicts.issubset(ALL_LABELS)

    # On a bien des flux bénins et des attaques détectées
    assert BENIGN in unique_verdicts
    assert len(unique_verdicts) > 1

    print("\nRépartition des verdicts du pipeline sur mini.csv :")
    print(results["verdict"].value_counts().to_string())
