"""Tests unitaires pour l'orchestrateur du pipeline en cascade (pipeline.py)."""

import numpy as np
import pandas as pd
import pytest

from nids.pipeline import CascadedNIDSPipeline
from nids.labels import BENIGN, SUSPECT_UNCERTAIN


class MockStage1:
    def __init__(self, scores: list[float]) -> None:
        self.name = "MockStage1"
        self._scores = np.array(scores, dtype=float)

    def score(self, df: pd.DataFrame) -> np.ndarray:
        return self._scores[: len(df)]


class MockStage2:
    def __init__(self, probas: list[list[float]], classes: list[str]) -> None:
        self.name = "MockStage2"
        self.classes = classes
        self._probas = np.array(probas, dtype=float)

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        return self._probas[: len(df)]


class ExplodingStage2:
    name = "ExplodingStage2"
    classes = ["DDoS"]

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        raise AssertionError("L'Étage 2 ne devait JAMAIS être appelé !")


def test_pipeline_all_benign_never_calls_stage2():
    """Prouve que l'Étage 2 n'est jamais exécuté si tous les flux sont bénins."""
    df = pd.DataFrame({"dummy": [1, 2, 3]})
    s1 = MockStage1(scores=[0.1, 0.2, 0.4])  # Tous < t1=0.5
    s2 = ExplodingStage2()

    pipeline = CascadedNIDSPipeline(stage1_models=[s1], stage2_model=s2, t1=0.5, t2=0.7)
    res = pipeline.predict(df)

    assert len(res) == 3
    assert (res["verdict"] == BENIGN).all()
    assert (res["is_suspect"] == False).all()


def test_pipeline_decision_matrix():
    """Vérifie la décision selon les seuils t1 et t2."""
    df = pd.DataFrame({"dummy": [1, 2, 3]})
    # Flux 0: Bénin (0.1 < 0.5)
    # Flux 1: Suspect (0.95 >= 0.5) et confiant (0.85 >= 0.7 -> DDoS)
    # Flux 2: Suspect (0.80 >= 0.5) mais incertain (0.55 < 0.7 -> SUSPECT_UNCERTAIN)
    s1 = MockStage1(scores=[0.1, 0.95, 0.80])
    s2 = MockStage2(
        probas=[
            [0.85, 0.15],  # Flux 1
            [0.55, 0.45],  # Flux 2
        ],
        classes=["DDoS", "PortScan"],
    )

    pipeline = CascadedNIDSPipeline(stage1_models=[s1], stage2_model=s2, t1=0.5, t2=0.7)
    res = pipeline.predict(df)

    assert res.loc[0, "verdict"] == BENIGN
    assert res.loc[1, "verdict"] == "DDoS"
    assert res.loc[2, "verdict"] == SUSPECT_UNCERTAIN


def test_pipeline_empty_dataframe():
    """Vérifie le traitement d'un lot vide."""
    df = pd.DataFrame()
    s1 = MockStage1(scores=[])
    s2 = MockStage2(probas=[], classes=["DDoS"])

    pipeline = CascadedNIDSPipeline(stage1_models=[s1], stage2_model=s2)
    res = pipeline.predict(df)

    assert len(res) == 0
    assert "verdict" in res.columns


def test_pipeline_requires_at_least_one_stage1_model():
    """Vérifie qu'une liste vide de modèles Étage 1 lève une ValueError."""
    s2 = MockStage2(probas=[], classes=["DDoS"])
    with pytest.raises(ValueError, match="Au moins un modèle"):
        CascadedNIDSPipeline(stage1_models=[], stage2_model=s2)
