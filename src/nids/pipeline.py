"""Orchestrateur du pipeline NIDS en cascade et parallèle (Étage 1 + Étage 2 + Kitsune)."""

from typing import Sequence
import numpy as np
import pandas as pd

from nids.adapters.base import Stage1Model, Stage2Model, KitsuneModel
from nids.labels import BENIGN, SUSPECT_UNCERTAIN, ANOMALY_UNKNOWN


class CascadedNIDSPipeline:
    """Pipeline hybride : filtrage binaire (Étage 1), classification fine (Étage 2) et Kitsune."""

    def __init__(
        self,
        stage1_models: Sequence[Stage1Model],
        stage2_model: Stage2Model,
        t1: float = 0.5,
        t2: float = 0.7,
        kitsune_detector: KitsuneModel | None = None,
        t3: float = 0.15,
    ) -> None:
        """Initialise le pipeline hybride en cascade et parallèle.

        Args:
            stage1_models: Liste des modèles de l'Étage 1 (au moins un modèle requis).
            stage2_model: Modèle de l'Étage 2 pour la catégorisation fine.
            t1: Seuil de suspicion de l'Étage 1 (orienté rappel).
            t2: Seuil de confiance minimale de l'Étage 2.
            kitsune_detector: Détecteur d'anomalies non-supervisé Kitsune (optionnel).
            t3: Seuil d'anomalie Kitsune RMSE.
        """
        if not stage1_models:
            raise ValueError("Au moins un modèle d'Étage 1 doit être configuré.")

        self.stage1_models = list(stage1_models)
        self.stage2_model = stage2_model
        self.t1 = t1
        self.t2 = t2
        self.kitsune_detector = kitsune_detector
        self.t3 = t3

    def _evaluate_stage1(self, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        """Évalue les flux avec les modèles d'Étage 1 et renvoie (scores, masque_suspect)."""
        scores_list = [model.score(df) for model in self.stage1_models]
        stage1_scores = np.max(np.column_stack(scores_list), axis=1)
        return stage1_scores, (stage1_scores >= self.t1)

    def _evaluate_stage2(
        self,
        df: pd.DataFrame,
        suspect_indices: np.ndarray,
        verdicts: np.ndarray,
        confidences: np.ndarray,
        classes: np.ndarray,
    ) -> None:
        """Exécute l'Étage 2 sur les flux suspects et met à jour les résultats in-place."""
        if len(suspect_indices) == 0:
            return
        probas = self.stage2_model.predict_proba(df.iloc[suspect_indices])
        max_p = np.max(probas, axis=1)
        pred_idx = np.argmax(probas, axis=1)
        names = [self.stage2_model.classes[i] for i in pred_idx]

        for i, idx in enumerate(suspect_indices):
            conf = float(max_p[i])
            confidences[idx] = conf
            classes[idx] = names[i]
            verdicts[idx] = names[i] if conf >= self.t2 else SUSPECT_UNCERTAIN

    def _evaluate_kitsune(
        self,
        df: pd.DataFrame,
        benign_indices: np.ndarray,
        verdicts: np.ndarray,
        confidences: np.ndarray,
        classes: np.ndarray,
        k_scores_out: np.ndarray,
    ) -> None:
        """Évalue les flux bénins avec Kitsune pour intercepter les anomalies Zero-Day."""
        if self.kitsune_detector is None or len(benign_indices) == 0:
            return
        k_scores = np.asarray(self.kitsune_detector.score(df.iloc[benign_indices]), dtype=float)
        k_scores_out[benign_indices] = k_scores
        for j, idx in enumerate(benign_indices):
            rmse = float(k_scores[j])
            if rmse >= self.t3:
                verdicts[idx] = ANOMALY_UNKNOWN
                confidences[idx] = float(min(1.0, rmse / (2.0 * self.t3)))
                classes[idx] = ANOMALY_UNKNOWN

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """Exécute l'inférence hybride (Étage 1 + Étage 2 + branche parallèle Kitsune)."""
        n_samples = len(df)
        has_kitsune = self.kitsune_detector is not None
        cols = ["stage1_score", "is_suspect", "stage2_class", "confidence", "verdict"]
        if has_kitsune:
            cols.append("kitsune_score")
        if n_samples == 0:
            return pd.DataFrame(columns=cols)

        s1_scores, is_suspect = self._evaluate_stage1(df)
        verdicts = np.full(n_samples, BENIGN, dtype=object)
        stage2_classes = np.full(n_samples, None, dtype=object)
        confidences = np.zeros(n_samples, dtype=float)
        k_scores = np.full(n_samples, np.nan, dtype=float) if has_kitsune else None

        self._evaluate_stage2(df, np.where(is_suspect)[0], verdicts, confidences, stage2_classes)
        if has_kitsune:
            self._evaluate_kitsune(
                df, np.where(~is_suspect)[0], verdicts, confidences, stage2_classes, k_scores
            )

        res = {
            "stage1_score": s1_scores,
            "is_suspect": is_suspect,
            "stage2_class": stage2_classes,
            "confidence": confidences,
            "verdict": verdicts,
        }
        if has_kitsune:
            res["kitsune_score"] = k_scores

        return pd.DataFrame(res, index=df.index)
