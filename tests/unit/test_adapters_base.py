"""Tests unitaires pour les protocoles d'adaptateurs de base."""

import numpy as np
import pandas as pd

from nids.adapters.base import Stage1Model, Stage2Model, KitsuneModel


class DummyStage1:
    name: str = "DummyStage1"

    def score(self, df: pd.DataFrame) -> np.ndarray:
        return np.ones(len(df), dtype=float) * 0.9


class DummyStage2:
    name: str = "DummyStage2"
    classes: list[str] = ["DDoS", "PortScan"]

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        return np.tile([0.8, 0.2], (len(df), 1))


class DummyKitsune:
    name: str = "DummyKitsune"

    def score(self, df: pd.DataFrame) -> np.ndarray:
        return np.ones(len(df), dtype=float) * 0.25


class IncompleteModel:
    name: str = "Incomplete"
    # Ne définit pas la méthode score


def test_stage1_protocol_compliance():
    """Vérifie la conformité au protocole Stage1Model."""
    model = DummyStage1()
    assert isinstance(model, Stage1Model)
    assert not isinstance(IncompleteModel(), Stage1Model)

    df = pd.DataFrame({"col1": [1, 2, 3]})
    scores = model.score(df)
    assert isinstance(scores, np.ndarray)
    assert scores.shape == (3,)
    assert np.all((scores >= 0.0) & (scores <= 1.0))


def test_stage2_protocol_compliance():
    """Vérifie la conformité au protocole Stage2Model."""
    model = DummyStage2()
    assert isinstance(model, Stage2Model)
    assert not isinstance(IncompleteModel(), Stage2Model)

    df = pd.DataFrame({"col1": [1, 2]})
    probas = model.predict_proba(df)
    assert isinstance(probas, np.ndarray)
    assert probas.shape == (2, 2)
    assert np.allclose(probas.sum(axis=1), 1.0)


def test_kitsune_protocol_compliance():
    """Vérifie la conformité au protocole KitsuneModel."""
    model = DummyKitsune()
    assert isinstance(model, KitsuneModel)
    assert not isinstance(IncompleteModel(), KitsuneModel)

    df = pd.DataFrame({"col1": [1, 2, 3]})
    scores = model.score(df)
    assert isinstance(scores, np.ndarray)
    assert scores.shape == (3,)
    assert np.all(scores >= 0.0)
