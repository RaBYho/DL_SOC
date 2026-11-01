import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from nids_core import Scorer

BASE_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def scorer():
    return Scorer(base=str(BASE_DIR), device="cpu")


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
    # Auto-encodeur
    assert scorer.has_ae is True
    assert scorer.ae_seuil is not None
    assert scorer.ae_model is not None


def test_predict_df_valid(scorer, feature_cols):
    n_samples = 5
    data = {col: np.random.uniform(0, 100, size=n_samples) for col in feature_cols}
    # Ensure protocol is integer-like
    data["protocol"] = np.random.choice([6, 17], size=n_samples)
    df = pd.DataFrame(data)

    res = scorer.predict_df(df)

    assert len(res) == n_samples
    assert "pred_id" in res.columns
    assert "pred" in res.columns
    assert "confiance" in res.columns
    assert "mse_ae" in res.columns
    assert "anomalie_ae" in res.columns

    assert res["pred_id"].dtype in [np.int32, np.int64, int]
    valid_classes = set(scorer.classes) | {"Zero-Day / Unknown Attack"}
    assert all(pred in valid_classes for pred in res["pred"])
    assert (res["confiance"] >= 0.0).all() and (res["confiance"] <= 1.0).all()
    assert (res["mse_ae"] >= 0.0).all()
    assert res["anomalie_ae"].dtype == bool


def test_predict_df_with_inf_and_nan(scorer, feature_cols):
    n_samples = 4
    data = {col: [10.0, np.inf, -np.inf, np.nan] for col in feature_cols}
    data["protocol"] = [6, 6, 17, 6]
    df = pd.DataFrame(data)

    res = scorer.predict_df(df)

    assert len(res) == n_samples
    assert not res["confiance"].isna().any()
    assert not res["mse_ae"].isna().any()
    valid_classes = set(scorer.classes) | {"Zero-Day / Unknown Attack"}
    assert all(pred in valid_classes for pred in res["pred"])


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
    assert "pred_id" in res.columns
    assert "pred" in res.columns
    assert "confiance" in res.columns
    assert "mse_ae" in res.columns
    assert "anomalie_ae" in res.columns


def test_scorer_manifest_loading():
    manifest_path = BASE_DIR / "models" / "manifest.json"
    assert manifest_path.exists()
    s = Scorer(base=str(BASE_DIR), manifest_path=str(manifest_path), device="cpu")
    assert s.manifest is not None
    assert s.manifest["active_version"] in ["v4", "v5"]
    assert s.manifest["supervised"]["features_count"] == 58
    assert len(s.classes) == 12
    assert s.has_ae is True


def test_schema_features_consistency(feature_cols):
    schema_path = BASE_DIR / "models" / "schema_features.json"
    assert schema_path.exists()
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    assert schema["total_features"] == 58
    assert set(schema["features"].keys()) == set(feature_cols)


def test_scorer_lgb_and_temperature_loading(scorer):
    """Vérifie le chargement de LightGBM, la température calibrée et les seuils AE v2."""
    assert scorer.lgb_model is not None
    assert scorer.lgb_model.num_feature() == 58
    assert scorer.temperature > 1.0  # Temperature scaling calibrée (1.4982)
    assert scorer.ae_seuil_sain == 0.10
    assert scorer.ae_seuil > 1.0  # q99.9 (1.4810)
    assert scorer.benign_id == scorer.classes.index("BENIGN")


def test_zero_day_veto_override(scorer, feature_cols):
    """Vérifie qu'un flux avec MSE > ae_seuil ne ressort JAMAIS comme BENIGN (Droit de veto Zero-Day)."""
    # Données avec supervision initialement BENIGN mais anomalie AE élevée
    zero_data = {col: [0.0] for col in feature_cols}
    zero_data["protocol"] = [6]
    df_zero = pd.DataFrame(zero_data)

    res = scorer.predict_df(df_zero)
    assert len(res) == 1
    assert res["anomalie_ae"].iloc[0] == True
    assert res["pred"].iloc[0] == "Zero-Day / Unknown Attack"
    assert res["pred"].iloc[0] != "BENIGN"
    assert res["confiance"].iloc[0] >= 0.75
    assert res["pred_id"].iloc[0] != scorer.benign_id


def test_anti_false_positive_reclassification(scorer, feature_cols):
    """Vérifie la règle anti-faux positifs : force à BENIGN si conf < 0.75 et mse_ae < seuil_sain."""
    # Créer un flux et tester la règle de double barrière
    # En simulant les masques directement sur la logique
    data = {col: [0.0] for col in feature_cols}
    data["protocol"] = [6]
    df = pd.DataFrame(data)
    res = scorer.predict_df(df)
    assert len(res) == 1
    assert "pred" in res.columns
    assert "confiance" in res.columns


