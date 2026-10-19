"""Membre 1 : ingestion, nettoyage, split. Produit data/processed/{train,val,test}.parquet"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
CFG = yaml.safe_load(open(ROOT / "config.yaml"))


def clean_label(s: str) -> str:
    s = str(s).strip()
    return "Web Attack" if s.startswith("Web Attack") else s


def load_raw() -> pd.DataFrame:
    files = sorted((ROOT / CFG["paths"]["raw"]).glob("*.csv"))
    if not files:
        raise FileNotFoundError("Aucun CSV dans data/raw/ (voir README)")
    dfs = [pd.read_csv(f, encoding="latin-1", low_memory=False) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    df.columns = [c.strip() for c in df.columns]
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    n0 = len(df)
    df = df.loc[:, ~df.columns.duplicated()].copy()
    df["Label"] = df["Label"].map(clean_label)
    feats = [c for c in df.columns if c != "Label"]
    df[feats] = df[feats].apply(pd.to_numeric, errors="coerce")
    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    df = df.drop_duplicates()                      # AVANT le split
    const = [c for c in feats if df[c].nunique() <= 1]
    df = df.drop(columns=const)                    # colonnes constantes
    print(f"Nettoyage : {n0} -> {len(df)} lignes, {len(const)} colonnes constantes retirées")
    return df.reset_index(drop=True)


def merge_rare(df: pd.DataFrame) -> pd.DataFrame:
    counts = df["Label"].value_counts()
    rare = counts[(counts < CFG["min_class_count"]) & (counts.index != CFG["benign_label"])].index
    df["Label"] = df["Label"].where(~df["Label"].isin(rare), "Other_Attack")
    print("Classes rares regroupées :", list(rare))
    return df


def main():
    df = merge_rare(clean(load_raw()))
    if CFG["sample_frac"] < 1.0:
        df, _ = train_test_split(df, train_size=CFG["sample_frac"],
                                 stratify=df["Label"], random_state=CFG["seed"])

    classes = sorted(df["Label"].unique(), key=lambda c: (c != CFG["benign_label"], c))
    label_map = {c: i for i, c in enumerate(classes)}      # BENIGN = 0
    df = df.rename(columns={"Label": "label"})
    df["label_id"] = df["label"].map(label_map).astype("int8")
    df["is_attack"] = (df["label"] != CFG["benign_label"]).astype("int8")
    feats = [c for c in df.columns if c not in ("label", "label_id", "is_attack")]
    df[feats] = df[feats].astype("float32")

    s = CFG["split"]
    train, tmp = train_test_split(df, train_size=s["train"], stratify=df["label"],
                                  random_state=CFG["seed"])
    val, test = train_test_split(tmp, train_size=s["val"] / (s["val"] + s["test"]),
                                 stratify=tmp["label"], random_state=CFG["seed"])

    out = ROOT / CFG["paths"]["processed"]
    for name, part in [("train", train), ("val", val), ("test", test)]:
        part.reset_index(drop=True).to_parquet(out / f"{name}.parquet")
        print(name, part.shape)
    json.dump(label_map, open(out / "label_map.json", "w"), indent=2)
    json.dump(feats, open(out / "features.json", "w"), indent=2)

    # Contrôle anti-fuite : lignes identiques entre train et test (doit être 0)
    to_set = lambda d: set(map(tuple, d[feats].values))
    print("Lignes communes train/test :", len(to_set(train) & to_set(test)))
    print(train["label"].value_counts())


if __name__ == "__main__":
    main()
