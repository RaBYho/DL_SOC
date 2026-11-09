"""Module d'évaluation rigoureuse, calcul des métriques et benchmarks comparatifs."""

from typing import Any, Sequence
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score

from nids.labels import BENIGN, ANOMALY_UNKNOWN


def compute_stage1_metrics(
    y_true_binary: Sequence[int], y_pred_binary: Sequence[int]
) -> dict[str, float]:
    """Calcule les métriques de détection binaire de l'Étage 1."""
    yt = np.asarray(y_true_binary, dtype=int)
    yp = np.asarray(y_pred_binary, dtype=int)

    tp = int(np.sum((yp == 1) & (yt == 1)))
    fp = int(np.sum((yp == 1) & (yt == 0)))
    tn = int(np.sum((yp == 0) & (yt == 0)))
    fn = int(np.sum((yp == 0) & (yt == 1)))

    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    f1 = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "recall": float(round(recall, 4)),
        "precision": float(round(precision, 4)),
        "fpr": float(round(fpr, 4)),
        "f1_score": float(round(f1, 4)),
    }


def compute_multiclass_metrics(
    y_true: Sequence[str], y_pred: Sequence[str]
) -> dict[str, Any]:
    """Calcule les scores F1 (macro et pondéré) et la matrice de confusion."""
    labels_order = sorted(list(set(y_true).union(set(y_pred))))

    f1_mac = float(
        f1_score(y_true, y_pred, average="macro", zero_division=0, labels=labels_order)
    )
    f1_w = float(
        f1_score(
            y_true, y_pred, average="weighted", zero_division=0, labels=labels_order
        )
    )
    cm = confusion_matrix(y_true, y_pred, labels=labels_order)

    return {
        "f1_macro": round(f1_mac, 4),
        "f1_weighted": round(f1_w, 4),
        "classes": labels_order,
        "confusion_matrix": cm.tolist(),
    }


def compute_kitsune_contribution(
    y_true: Sequence[str],
    supervised_verdicts: Sequence[str],
    hybrid_verdicts: Sequence[str],
) -> dict[str, Any]:
    """Mesure la valeur ajoutée nette de Kitsune (attaques ratées rattrapées)."""
    yt = np.asarray(y_true, dtype=object)
    ys = np.asarray(supervised_verdicts, dtype=object)
    yh = np.asarray(hybrid_verdicts, dtype=object)

    is_true_attack = yt != BENIGN
    is_true_benign = yt == BENIGN

    # Attaques non détectées par le superviseur
    missed_by_sup = is_true_attack & (ys == BENIGN)
    nb_missed = int(np.sum(missed_by_sup))

    # Attaques rattrapées par l'hybride
    recovered = missed_by_sup & (yh != BENIGN)
    nb_recovered = int(np.sum(recovered))

    # Faux positifs supplémentaires ajoutés par Kitsune
    extra_fp = is_true_benign & (ys == BENIGN) & (yh != BENIGN)
    nb_extra_fp = int(np.sum(extra_fp))

    recovery_rate = (nb_recovered / nb_missed) if nb_missed > 0 else 0.0

    return {
        "missed_by_supervised": nb_missed,
        "recovered_by_kitsune": nb_recovered,
        "recovery_rate": float(round(recovery_rate, 4)),
        "additional_false_positives": nb_extra_fp,
    }


def compare_nids_configurations(
    y_true: Sequence[str],
    supervised_verdicts: Sequence[str],
    kitsune_verdicts: Sequence[str],
    hybrid_verdicts: Sequence[str],
) -> pd.DataFrame:
    """Compare 3 architectures sur le même jeu de données (Supervisé seul, Kitsune seul, Hybride)."""
    yt_binary = (np.asarray(y_true) != BENIGN).astype(int)

    configs = {
        "Supervisé seul (Étages 1 + 2)": (np.asarray(supervised_verdicts) != BENIGN).astype(int),
        "Kitsune seul (Non-supervisé)": (np.asarray(kitsune_verdicts) != BENIGN).astype(int),
        "Pipeline Hybride Complet": (np.asarray(hybrid_verdicts) != BENIGN).astype(int),
    }

    rows = []
    for name, y_pred_bin in configs.items():
        m = compute_stage1_metrics(yt_binary, y_pred_bin)
        rows.append({
            "Configuration": name,
            "Rappel Attaques": m["recall"],
            "Précision": m["precision"],
            "F1-Score": m["f1_score"],
            "Faux Positifs (FPR)": m["fpr"],
        })

    return pd.DataFrame(rows)
