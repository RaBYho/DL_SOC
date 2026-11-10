#!/usr/bin/env python3
"""Script de démonstration CLI du pipeline NIDS hybride (Étages 1 & 2 + Kitsune)."""

import argparse
from pathlib import Path
import pandas as pd

from nids.adapters.stage1 import CatBoostStage1, XGBoostStage1
from nids.adapters.stage2 import CnnStage2
from nids.pipeline import CascadedNIDSPipeline
from nids.flow_alignment import aggregate_scores
from nids.fusion import fuse_decisions


def parse_args() -> argparse.Namespace:
    """Parse les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Démonstrateur CLI du NIDS hybride à deux étages + Kitsune."
    )
    parser.add_argument(
        "flows_file",
        type=Path,
        help="Chemin vers le fichier de flux réseau (.csv ou .parquet).",
    )
    parser.add_argument(
        "--packets",
        type=Path,
        default=None,
        help="Chemin optionnel vers packet_scores.parquet pour la fusion avec Kitsune.",
    )
    parser.add_argument(
        "--t1",
        type=float,
        default=0.01,
        help="Seuil de suspicion Étage 1 (défaut: 0.01 pour démo sur mini.csv).",
    )
    parser.add_argument(
        "--t2",
        type=float,
        default=0.10,
        help="Seuil de confiance Étage 2 (défaut: 0.10 pour démo).",
    )
    parser.add_argument(
        "--t3",
        type=float,
        default=0.15,
        help="Seuil d'anomalie Kitsune (défaut: 0.15).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Nombre de flux détaillés à afficher dans le tableau (défaut: 10).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("=" * 80)
    print("   🛡️  DÉMONSTRATION DU PIPELINE NIDS HYBRIDE (Étages 1 & 2 + Kitsune)")
    print("=" * 80)

    # 1. Chargement des flux
    print(f"\n[1/4] Chargement des flux réseau depuis : {args.flows_file}")
    if args.flows_file.suffix.lower() == ".parquet":
        flows_df = pd.read_parquet(args.flows_file)
    else:
        flows_df = pd.read_csv(args.flows_file)
    print(f"      -> {len(flows_df)} flux chargés ({len(flows_df.columns)} colonnes).")

    # 2. Instanciation des modèles
    print("\n[2/4] Chargement des modèles pré-entraînés...")
    catboost = CatBoostStage1()
    xgboost = XGBoostStage1()
    cnn = CnnStage2()
    print("      -> CatBoost (Étage 1), XGBoost (Étage 1) et DNN-1D (Étage 2) prêts.")

    # 3. Exécution de la cascade supervisée
    print(f"\n[3/4] Inférence supervisée (Cascade avec t1={args.t1}, t2={args.t2})...")
    pipeline = CascadedNIDSPipeline(
        stage1_models=[catboost, xgboost],
        stage2_model=cnn,
        t1=args.t1,
        t2=args.t2,
    )
    supervised_df = pipeline.predict(flows_df)

    # 4. Branche Kitsune et Fusion
    if args.packets and args.packets.exists():
        print(f"\n[4/4] Alignement et Fusion avec Kitsune ({args.packets}, t3={args.t3})...")
        packets_df = pd.read_parquet(args.packets)
        kitsune_scores = aggregate_scores(flows_df, packets_df, rule="max")
        final_verdicts = fuse_decisions(
            supervised_df=supervised_df,
            kitsune_scores=kitsune_scores,
            t2=args.t2,
            t3=args.t3,
        )
        has_kitsune = True
    else:
        print("\n[4/4] Inférence sans paquet Kitsune (décision supervisée pure)...")
        final_verdicts = supervised_df["verdict"]
        kitsune_scores = pd.Series([None] * len(flows_df), index=flows_df.index)
        has_kitsune = False

    # Affichage du tableau de bord de résultats
    print("\n" + "=" * 80)
    print("📊 RÉSULTATS DÉTAILLÉS DE L'ANALYSE (Échantillon)")
    print("=" * 80)

    display_df = pd.DataFrame({
        "Flow ID": flows_df.get("Flow ID", flows_df.index).astype(str).str[:24],
        "Score Étage 1": supervised_df["stage1_score"].map(lambda x: f"{x:.4f}"),
        "Suspect ?": supervised_df["is_suspect"].map(lambda x: "OUI" if x else "non"),
        "Classe Étage 2": supervised_df["stage2_class"].fillna("-"),
        "Confiance": supervised_df["confidence"].map(lambda x: f"{x:.2%}" if x > 0 else "-"),
        "Kitsune RMSE": kitsune_scores.map(lambda x: f"{x:.4f}" if pd.notna(x) else "-"),
        "VERDICT FINAL": final_verdicts,
    })

    print(display_df.head(args.limit).to_string(index=False))

    print("\n" + "=" * 80)
    print("📈 SYNTHÈSE DES DÉCISIONS")
    print("=" * 80)
    summary = final_verdicts.value_counts()
    for label, count in summary.items():
        pct = (count / len(final_verdicts)) * 100
        print(f"  • {label:<25} : {count:>4} flux ({pct:>5.1f} %)")

    print("=" * 80)
    print("✅ Analyse terminée avec succès.\n")


if __name__ == "__main__":
    main()
