"""Tests d'intégration pour le pipeline temps réel et le script run_live.py."""

import json
from pathlib import Path
import subprocess
import sys
import yaml
import pytest
import pandas as pd

from nids.adapters.stage1 import CatBoostStage1, XGBoostStage1
from nids.adapters.stage2 import CnnStage2
from nids.pipeline import CascadedNIDSPipeline
from nids.live_filter import pre_filter_flows
from nids.live_guard import LiveAlertGuard, ConsolidatedAlert
from nids.sample_generator import generate_replay_chunks


@pytest.fixture(scope="module")
def feature_names() -> list[str]:
    """Charge les noms des variables standard pour les flux."""
    with open("models/cnn_feature_names.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def live_config() -> dict:
    """Charge la configuration du gardien temps réel."""
    with open("configs/live_guard.yaml") as f:
        return yaml.safe_load(f)


def test_generate_replay_chunks(tmp_path: Path, feature_names: list[str]):
    """Vérifie la génération des chunks temporels pour le mode replay."""
    chunk_paths = generate_replay_chunks(tmp_path, feature_names)
    assert len(chunk_paths) == 3
    for p in chunk_paths:
        assert p.exists()
        df = pd.read_csv(p)
        assert len(df) > 0
        assert "Timestamp" in df.columns
        assert "Source IP" in df.columns


def test_live_pipeline_flow(tmp_path: Path, feature_names: list[str], live_config: dict):
    """Vérifie l'enchaînement filtrage -> ML -> leaky bucket sur les 3 chunks."""
    chunk_paths = generate_replay_chunks(tmp_path, feature_names)

    # 1. Modèles et Pipeline
    catboost = CatBoostStage1()
    xgboost = XGBoostStage1()
    cnn = CnnStage2()
    pipeline = CascadedNIDSPipeline([catboost, xgboost], cnn, t1=0.01, t2=0.10)
    guard = LiveAlertGuard(live_config)

    # Chunk 1 : trafic bénin bruyant (mDNS, SSDP, orphelins) -> 0 alerte
    df1 = pd.read_csv(chunk_paths[0])
    to_score1, _ = pre_filter_flows(df1, live_config)
    sup1 = pipeline.predict(to_score1)
    alerts1 = guard.process_batch(
        to_score1, sup1["verdict"], sup1["stage1_score"].values, sup1["confidence"].values
    )
    assert len(alerts1) == 0

    # Chunk 2 : rafale d'attaque (20 flux) -> exactement 1 alerte consolidée
    df2 = pd.read_csv(chunk_paths[1])
    to_score2, _ = pre_filter_flows(df2, live_config)
    sup2 = pipeline.predict(to_score2)
    alerts2 = guard.process_batch(
        to_score2, sup2["verdict"], sup2["stage1_score"].values, sup2["confidence"].values
    )
    assert len(alerts2) == 1
    assert alerts2[0].src_ip == "192.168.10.99"
    assert alerts2[0].flow_count >= 1
    assert alerts2[0].host_score >= 100.0

    # Chunk 3 : poursuite de l'attaque sous cooldown (< 300s) -> 0 nouvelle alerte
    df3 = pd.read_csv(chunk_paths[2])
    to_score3, _ = pre_filter_flows(df3, live_config)
    sup3 = pipeline.predict(to_score3)
    alerts3 = guard.process_batch(
        to_score3, sup3["verdict"], sup3["stage1_score"].values, sup3["confidence"].values
    )
    assert len(alerts3) == 0
    # Vérification que les flux ont bien été comptabilisés en suppression
    assert guard.suppressed_counts[("192.168.10.99", alerts2[0].attack_class)] > 0


def test_run_live_cli_replay(tmp_path: Path, feature_names: list[str]):
    """Vérifie l'exécution CLI de scripts/run_live.py en mode --replay-dir."""
    chunks_dir = tmp_path / "chunks"
    generate_replay_chunks(chunks_dir, feature_names)

    cmd = [
        sys.executable,
        "scripts/run_live.py",
        "--replay-dir",
        str(chunks_dir),
        "--delay",
        "0.0",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "MOTEUR TEMPS RÉEL NIDS" in res.stdout
    assert "ALERTE CONSOLIDÉE" in res.stdout
    assert "192.168.10.99" in res.stdout
