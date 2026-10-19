"""Membre 2 : baselines Random Forest / XGBoost (contrat train/predict)."""
import time
from pathlib import Path

import pandas as pd
import yaml
from sklearn.ensemble import RandomForestClassifier
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

from evaluation import evaluate, save_metrics

ROOT = Path(__file__).resolve().parents[1]
CFG = yaml.safe_load(open(ROOT / "config.yaml"))


def load():
    p = ROOT / CFG["paths"]["processed"]
    tr, va, te = (pd.read_parquet(p / f"{n}.parquet") for n in ("train", "val", "test"))
    feats = [c for c in tr.columns if c not in ("label", "label_id", "is_attack")]
    return (tr[feats], tr["label_id"]), (va[feats], va["label_id"]), (te[feats], te["label_id"])


def train_rf(X, y, Xv, yv, cfg):
    m = RandomForestClassifier(n_estimators=200, n_jobs=-1, class_weight="balanced",
                               random_state=cfg["seed"])
    return m.fit(X, y)


def train_xgb(X, y, Xv, yv, cfg):
    m = XGBClassifier(n_estimators=300, max_depth=8, learning_rate=0.1, tree_method="hist",
                      n_jobs=-1, random_state=cfg["seed"])
    return m.fit(X, y, sample_weight=compute_sample_weight("balanced", y))


def predict(model, X):
    proba = model.predict_proba(X)
    return proba.argmax(axis=1), proba


if __name__ == "__main__":
    (Xtr, ytr), (Xva, yva), (Xte, yte) = load()
    for name, fn in [("random_forest", train_rf), ("xgboost", train_xgb)]:
        t0 = time.time(); model = fn(Xtr, ytr, Xva, yva, CFG); t_train = time.time() - t0
        t0 = time.time(); y_pred, y_proba = predict(model, Xte); t_inf = time.time() - t0
        save_metrics(name, evaluate(yte, y_pred, y_proba),
                     {"train_time_s": t_train, "inference_time_s": t_inf})
