import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from nids_core import Scorer

BASE_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def scorer():
    return Scorer(base=str(BASE_DIR), version="v4", device="cpu")


@pytest.fixture(scope="module")
def feature_cols():
    with open(BASE_DIR / "models" / "feature_cols.json") as f:
        return json.load(f)


def test_scorer_initialization(scorer):
    assert len(scorer.classes) == 12
    assert "BENIGN" in scorer.classes
    assert len(scorer.feature_cols) == 58
    assert scorer.scaler is not None
    assert scorer.model is not None


def test_predict_df_valid(scorer, feature_cols):
    n_samples = 5
    data = {col: np.random.uniform(0, 100, size=n_samples) for col in feature_cols}
    # Ensure protocol is integer-like
    data["protocol"] = np.random.choice([6, 17], size=n_samples)
    df = pd.DataFrame(data)

    res = scorer.predict_df(df)

    assert len(res) == n_samples
    assert list(res.columns) == ["pred_id", "pred", "confiance"]
    assert res["pred_id"].dtype in [np.int32, np.int64, int]
    assert all(pred in scorer.classes for pred in res["pred"])
    assert (res["confiance"] >= 0.0).all() and (res["confiance"] <= 1.0).all()


def test_predict_df_with_inf_and_nan(scorer, feature_cols):
    n_samples = 4
    data = {col: [10.0, np.inf, -np.inf, np.nan] for col in feature_cols}
    data["protocol"] = [6, 6, 17, 6]
    df = pd.DataFrame(data)

    res = scorer.predict_df(df)

    assert len(res) == n_samples
    assert not res["confiance"].isna().any()
    assert all(pred in scorer.classes for pred in res["pred"])


def test_predict_df_missing_columns(scorer):
    df_incomplete = pd.DataFrame({
        "protocol": [6],
        "bidirectional_duration_ms": [1000]
    })
    with pytest.raises(ValueError, match="Colonnes manquantes"):
        scorer.predict_df(df_incomplete)


def test_predict_df_empty(scorer, feature_cols):
    df_empty = pd.DataFrame(columns=feature_cols)
    res = scorer.predict_df(df_empty)

    assert len(res) == 0
    assert list(res.columns) == ["pred_id", "pred", "confiance"]
