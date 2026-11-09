"""Module d'étalonnage et de calibration rigoureuse des seuils opérationnels sans fuite."""

from pathlib import Path
from typing import Sequence
import numpy as np
import yaml


def check_no_test_leakage(file_path: Path | str) -> None:
    """Empêche formellement toute calibration sur un jeu de données de test.

    Raises:
        PermissionError: Si le nom de fichier suggère un split de test.
    """
    path_str = Path(file_path).stem.lower()
    if "test" in path_str:
        raise PermissionError(
            f"Interdiction absolue de calibrer sur un jeu de test ('{file_path}'). "
            "Les seuils doivent impérativement être ajustés sur le split de validation (val.parquet)."
        )


def calibrate_t1_recall(
    y_true_binary: np.ndarray | Sequence[int],
    scores: np.ndarray | Sequence[float],
    target_recall: float = 0.98,
    step: float = 0.01,
) -> float:
    """Calibre le seuil t1 de l'Étage 1 pour garantir un rappel cible sur les attaques.

    Balaye les seuils pour sélectionner le seuil le plus élevé (minimisant les faux positifs)
    qui satisfait le rappel minimum exigé sur les classes malveillantes.

    Args:
        y_true_binary: Étiquettes binaires réelles (1 = attaque, 0 = bénin).
        scores: Probabilités continues d'attaque prédites par l'Étage 1.
        target_recall: Rappel minimal cible à respecter (ex: 0.98).
        step: Incrément de balayage du seuil.

    Returns:
        float: Seuil t1 optimal retenu.
    """
    y_true = np.asarray(y_true_binary, dtype=int)
    y_scores = np.asarray(scores, dtype=float)

    total_attacks = np.sum(y_true == 1)
    if total_attacks == 0:
        return 0.5

    best_t1 = 0.05
    threshold_candidates = np.arange(0.05, 0.96, step)

    for t in threshold_candidates:
        preds = y_scores >= t
        tp = np.sum((preds == 1) & (y_true == 1))
        recall = tp / total_attacks

        if recall >= target_recall:
            best_t1 = float(t)

    return round(best_t1, 3)


def calibrate_t3_kitsune_percentile(
    benign_scores: np.ndarray | Sequence[float], percentile: float = 99.0
) -> float:
    """Calibre le seuil d'anomalie t3 de Kitsune au percentile désiré sur trafic bénin.

    Args:
        benign_scores: Scores RMSE de Kitsune observés sur le trafic sain de validation.
        percentile: Percentile cible pour la frontière de décision (par défaut 99.0).

    Returns:
        float: Seuil t3 calibré.
    """
    clean_scores = np.asarray(benign_scores, dtype=float)
    clean_scores = clean_scores[~np.isnan(clean_scores)]

    if len(clean_scores) == 0:
        return 0.15

    t3 = float(np.percentile(clean_scores, percentile))
    return round(t3, 4)


def save_thresholds(
    output_path: Path | str,
    t1: float,
    t2: float,
    t3: float,
    time_tolerance_sec: float = 1.0,
) -> None:
    """Enregistre les seuils calibrés dans le fichier de configuration YAML."""
    config_dict = {
        "stage1": {
            "t1": float(t1),
            "aggregation": "max",
        },
        "stage2": {
            "t2": float(t2),
        },
        "kitsune": {
            "t3": float(t3),
            "time_tolerance_sec": float(time_tolerance_sec),
            "aggregation_rule": "max",
        },
        "labels": {
            "default_benign": "BENIGN",
            "anomaly_unknown": "ANOMALY_UNKNOWN",
            "suspect_uncertain": "SUSPECT_UNCERTAIN",
            "unknown_attack_likely": "UNKNOWN_ATTACK_LIKELY",
        },
    }

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as f:
        yaml.safe_dump(config_dict, f, sort_keys=False)
