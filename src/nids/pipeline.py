"""Orchestrateur du pipeline NIDS en cascade (Étage 1 + Étage 2)."""

from typing import Sequence
import numpy as np
import pandas as pd

from nids.adapters.base import Stage1Model, Stage2Model
from nids.labels import BENIGN, SUSPECT_UNCERTAIN


class CascadedNIDSPipeline:
    """Pipeline en cascade : filtrage binaire rapide (Étage 1) puis classification fine (Étage 2)."""

    def __init__(
        self,
        stage1_models: Sequence[Stage1Model],
        stage2_model: Stage2Model,
        t1: float = 0.5,
        t2: float = 0.7,
    ) -> None:
        """Initialise le pipeline en cascade.

        Args:
            stage1_models: Liste des modèles de l'Étage 1 (au moins un modèle requis).
            stage2_model: Modèle de l'Étage 2 pour la catégorisation fine.
            t1: Seuil de suspicion de l'Étage 1 (orienté rappel).
            t2: Seuil de confiance minimale de l'Étage 2.
        """
        if not stage1_models:
            raise ValueError("Au moins un modèle d'Étage 1 doit être configuré.")

        self.stage1_models = list(stage1_models)
        self.stage2_model = stage2_model
        self.t1 = t1
        self.t2 = t2

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """Exécute l'inférence en cascade sur un lot de flux réseau.

        Args:
            df: DataFrame contenant les flux réseau à analyser.

        Returns:
            pd.DataFrame: Résultats enrichis (score_stage1, is_suspect, stage2_class, confidence, verdict).
        """
        n_samples = len(df)
        if n_samples == 0:
            return pd.DataFrame(
                columns=["stage1_score", "is_suspect", "stage2_class", "confidence", "verdict"]
            )

        # 1. Étage 1 : Évaluation binaire (score maximum des modèles actifs)
        stage1_scores_list = [model.score(df) for model in self.stage1_models]
        stage1_scores = np.max(np.column_stack(stage1_scores_list), axis=1)

        is_suspect = stage1_scores >= self.t1

        # Initialisation des résultats
        verdicts = np.full(n_samples, BENIGN, dtype=object)
        stage2_classes = np.full(n_samples, None, dtype=object)
        confidences = np.zeros(n_samples, dtype=float)

        # 2. Étage 2 : Invoqué UNIQUEMENT sur les flux suspects
        suspect_indices = np.where(is_suspect)[0]
        if len(suspect_indices) > 0:
            suspect_df = df.iloc[suspect_indices]
            probas = self.stage2_model.predict_proba(suspect_df)

            max_probas = np.max(probas, axis=1)
            pred_class_indices = np.argmax(probas, axis=1)
            class_names = [self.stage2_model.classes[idx] for idx in pred_class_indices]

            for i, idx in enumerate(suspect_indices):
                conf = float(max_probas[i])
                confidences[idx] = conf
                stage2_classes[idx] = class_names[i]

                # Arbitrage avec le seuil de confiance t2
                if conf >= self.t2:
                    verdicts[idx] = class_names[i]
                else:
                    verdicts[idx] = SUSPECT_UNCERTAIN

        return pd.DataFrame(
            {
                "stage1_score": stage1_scores,
                "is_suspect": is_suspect,
                "stage2_class": stage2_classes,
                "confidence": confidences,
                "verdict": verdicts,
            },
            index=df.index,
        )
