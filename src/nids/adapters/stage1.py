"""Adaptateurs d'inférence pour les modèles de l'Étage 1 (CatBoost et XGBoost)."""

import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

from nids.features import align


class CatBoostStage1:
    """Adaptateur pour le classifieur binaire NIDS-CatBoost."""

    name: str = "CatBoostStage1"

    def __init__(
        self,
        model_path: Path | str = "models/cicids_catboost.cbm",
        features_path: Path | str = "models/catboost_feature_names.json",
    ) -> None:
        from catboost import CatBoostClassifier

        self.model = CatBoostClassifier()
        self.model.load_model(str(model_path))

        with open(features_path) as f:
            self.expected_features: list[str] = json.load(f)

    def score(self, df: pd.DataFrame) -> np.ndarray:
        """Calcule la probabilité d'attaque [0.0, 1.0] pour chaque flux."""
        if len(df) == 0:
            return np.empty(0, dtype=float)

        aligned = align(df, self.expected_features)
        # Inférence de probabilités binaires (colonne 1 = probabilité d'attaque)
        probas = self.model.predict_proba(aligned)
        return probas[:, 1].astype(float)


class XGBoostStage1:
    """Adaptateur pour le classifieur binaire NIDS-XGBoost (AegisAI)."""

    name: str = "XGBoostStage1"

    def __init__(
        self,
        model_path: Path | str = "models/xgb_model.json",
        features_path: Path | str = "models/xgb_feature_names.json",
        scaler_path: Path | str = "models/xgb_scaler.pkl",
    ) -> None:
        import xgboost as xgb

        self.model = xgb.XGBClassifier()
        self.model.load_model(str(model_path))

        with open(features_path) as f:
            self.expected_features: list[str] = json.load(f)

        loaded_scaler = joblib.load(str(scaler_path))
        if isinstance(loaded_scaler, tuple):
            self.scaler = loaded_scaler[0]
        else:
            self.scaler = loaded_scaler

    def score(self, df: pd.DataFrame) -> np.ndarray:
        """Calcule la probabilité d'attaque [0.0, 1.0] pour chaque flux."""
        if len(df) == 0:
            return np.empty(0, dtype=float)

        aligned = align(df, self.expected_features)
        scaled = self.scaler.transform(aligned)
        probas = self.model.predict_proba(scaled)
        return probas[:, 1].astype(float)
