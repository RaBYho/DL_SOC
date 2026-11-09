"""Moteur de fusion décisionnelle multi-niveaux (Étages 1 & 2 + Kitsune)."""

import numpy as np
import pandas as pd

from nids.labels import (
    ALL_LABELS,
    BENIGN,
    ANOMALY_UNKNOWN,
    SUSPECT_UNCERTAIN,
    UNKNOWN_ATTACK_LIKELY,
)


def fuse_decisions(
    supervised_df: pd.DataFrame,
    kitsune_scores: pd.Series,
    t2: float = 0.7,
    t3: float = 0.15,
) -> pd.Series:
    """Arbitre et fusionne les décisions supervisées avec le score d'anomalie Kitsune.

    Table de décision officielle :
    - Étage 1 Normal & Kitsune Normal (< t3)       -> BENIGN
    - Étage 1 Normal & Kitsune Anormal (>= t3)     -> ANOMALY_UNKNOWN (0-day)
    - Étage 1 Suspect & Étage 2 Confiant (>= t2)   -> Classe d'attaque identifiée
    - Étage 1 Suspect & Étage 2 Incertain & Kitsune Normal  -> SUSPECT_UNCERTAIN
    - Étage 1 Suspect & Étage 2 Incertain & Kitsune Anormal -> UNKNOWN_ATTACK_LIKELY
    - Kitsune NaN                                  -> Repli sur décision Étages 1+2

    Args:
        supervised_df: DataFrame issu de CascadedNIDSPipeline (is_suspect, stage2_class, confidence, verdict).
        kitsune_scores: Series des scores RMSE agrégés par flux réseau.
        t2: Seuil de confiance minimale de l'Étage 2.
        t3: Seuil d'anomalie non-supervisée Kitsune.

    Returns:
        pd.Series: Étiquettes finales d'arbitrage (faisant toutes partie de ALL_LABELS).

    Raises:
        ValueError: Si les longueurs des deux entrées ne correspondent pas.
    """
    n_samples = len(supervised_df)
    if n_samples != len(kitsune_scores):
        raise ValueError(
            f"Longueur incohérente : supervised={n_samples} vs kitsune={len(kitsune_scores)}"
        )

    if n_samples == 0:
        return pd.Series(dtype=object, name="final_verdict")

    is_suspect = supervised_df["is_suspect"].values.astype(bool)
    confidence = supervised_df["confidence"].fillna(0.0).values.astype(float)
    stage2_class = supervised_df["stage2_class"].values
    fallback_verdict = supervised_df["verdict"].values

    k_scores = kitsune_scores.values.astype(float)
    k_is_nan = np.isnan(k_scores)
    k_is_anomalous = (~k_is_nan) & (k_scores >= t3)

    verdicts = np.empty(n_samples, dtype=object)

    for i in range(n_samples):
        # Repli si Kitsune est absent
        if k_is_nan[i]:
            verdicts[i] = fallback_verdict[i]
            continue

        if not is_suspect[i]:
            # Filtré comme normal au niveau supervisé
            if k_is_anomalous[i]:
                verdicts[i] = ANOMALY_UNKNOWN  # 0-day intercepté par Kitsune
            else:
                verdicts[i] = BENIGN
        else:
            # Flux suspect à l'Étage 1
            if confidence[i] >= t2 and stage2_class[i] is not None:
                # Étage 2 confiant : priorité à la classe d'attaque connue
                verdicts[i] = stage2_class[i]
            else:
                # Étage 2 incertain : arbitrage par l'anomalie Kitsune
                if k_is_anomalous[i]:
                    verdicts[i] = UNKNOWN_ATTACK_LIKELY
                else:
                    verdicts[i] = SUSPECT_UNCERTAIN

    return pd.Series(verdicts, index=supervised_df.index, name="final_verdict")
