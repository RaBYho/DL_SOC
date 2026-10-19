"""Membre 4 : métriques communes à tous les modèles."""
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import (classification_report, confusion_matrix, f1_score,
                             roc_auc_score)

ROOT = Path(__file__).resolve().parents[1]


def evaluate(y_true, y_pred, y_proba=None, benign_id=0) -> dict:
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    rep = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    benign = y_true == benign_id
    fpr = float(((y_pred != benign_id) & benign).sum() / max(benign.sum(), 1))
    out = {
        "f1_macro": float(f1_score(y_true, y_pred, average="macro")),
        "f1_weighted": float(f1_score(y_true, y_pred, average="weighted")),
        "false_positive_rate": fpr,
        "recall_per_class": {k: v["recall"] for k, v in rep.items() if k.isdigit()},
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }
    if y_proba is not None and y_proba.ndim == 2 and y_proba.shape[1] > 2:
        try:
            out["auc_ovr"] = float(roc_auc_score(y_true, y_proba, multi_class="ovr"))
        except ValueError:
            pass
    return out


def save_metrics(name: str, metrics: dict, extra: dict | None = None):
    d = {**metrics, **(extra or {}), "model": name}
    path = ROOT / "results" / "metrics" / f"{name}.json"
    json.dump(d, open(path, "w"), indent=2)
    print(f"[{name}] F1 macro={d['f1_macro']:.4f}  FPR={d['false_positive_rate']:.5f}")
