"""Test End-to-End complet du pipeline hybride : Superviseur (CatBoost + XGBoost + CNN-1D) + Kitsune + Fusion."""

import pandas as pd
import pytest

from nids.adapters.stage1 import CatBoostStage1, XGBoostStage1
from nids.adapters.stage2 import CnnStage2
from nids.pipeline import CascadedNIDSPipeline
from nids.flow_alignment import aggregate_scores
from nids.fusion import fuse_decisions
from nids.labels import ALL_LABELS, BENIGN


@pytest.mark.e2e
@pytest.mark.requires_models
def test_full_hybrid_nids_pipeline():
    """Valide l'exécution complète du système NIDS de bout en bout avec fusion multimodale."""
    # 1. Chargement des flux et des paquets scorés
    flows = pd.read_csv("data/samples/mini.csv")
    packets = pd.read_parquet("data/samples/packet_scores.parquet")

    # 2. Instanciation des vrais modèles
    catboost = CatBoostStage1()
    xgboost = XGBoostStage1()
    cnn = CnnStage2()

    # 3. Exécution de la cascade supervisée (Étage 1 + 2)
    pipeline = CascadedNIDSPipeline(
        stage1_models=[catboost, xgboost],
        stage2_model=cnn,
        t1=0.01,
        t2=0.10,
    )
    supervised_df = pipeline.predict(flows)

    # 4. Alignement vectorisé des paquets Kitsune par flux
    kitsune_scores = aggregate_scores(flows, packets, rule="max", time_tolerance_sec=1.0)

    # 5. Fusion décisionnelle finale
    final_verdicts = fuse_decisions(
        supervised_df=supervised_df,
        kitsune_scores=kitsune_scores,
        t2=0.10,
        t3=0.15,
    )

    # Vérifications de conformité
    assert len(final_verdicts) == len(flows)
    assert set(final_verdicts.unique()).issubset(ALL_LABELS)
    assert BENIGN in final_verdicts.values

    print("\n--- Synthèse finale des décisions du NIDS hybride sur mini.csv ---")
    summary = final_verdicts.value_counts()
    print(summary.to_string())
