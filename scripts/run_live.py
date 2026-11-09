#!/usr/bin/env python3
"""Moteur d'analyse temps réel et de réduction des fausses alertes (Phase 12)."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import time
from typing import Any
import pandas as pd
import yaml

from nids.adapters.stage1 import CatBoostStage1, XGBoostStage1
from nids.adapters.stage2 import CnnStage2
from nids.pipeline import CascadedNIDSPipeline
from nids.flow_alignment import aggregate_scores
from nids.fusion import fuse_decisions
from nids.live_filter import pre_filter_flows
from nids.live_guard import LiveAlertGuard, ConsolidatedAlert


def parse_args() -> argparse.Namespace:
    """Parse les arguments de la ligne de commande pour le moteur live."""
    parser = argparse.ArgumentParser(
        description="Moteur de détection temps réel et consolidation des alertes."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--replay-dir", type=Path, help="Dossier de chunks pour le replay séquentiel.")
    group.add_argument("--watch-dir", type=Path, help="Dossier surveillé en continu pour nouveaux chunks.")

    parser.add_argument("--config", type=Path, default=Path("configs/live_guard.yaml"), help="Config live.")
    parser.add_argument("--delay", type=float, default=0.0, help="Délai en secondes entre chunks rejoués.")
    parser.add_argument("--max-chunks", type=int, default=None, help="Arrêt après N chunks traités.")
    parser.add_argument("--output", type=Path, default=None, help="Chemin JSON de sortie des alertes.")
    parser.add_argument("--t1", type=float, default=0.01, help="Seuil Étage 1 (défaut: 0.01).")
    parser.add_argument("--t2", type=float, default=0.10, help="Seuil Étage 2 (défaut: 0.10).")
    parser.add_argument("--t3", type=float, default=0.15, help="Seuil Kitsune (défaut: 0.15).")
    return parser.parse_args()


def _load_chunk(path: Path) -> pd.DataFrame:
    """Charge un fichier de flux au format Parquet ou CSV."""
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def _score_chunk(
    path: Path, df: pd.DataFrame, pipe: CascadedNIDSPipeline, t2: float, t3: float
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Exécute l'inférence supervisée et la fusion Kitsune si disponible."""
    sup_df = pipe.predict(df)
    pkt_file = path.with_name(f"{path.stem}_packets.parquet")
    if pkt_file.exists():
        pkts = pd.read_parquet(pkt_file)
        k_scores = aggregate_scores(df, pkts, rule="max")
        verdicts = fuse_decisions(sup_df, k_scores, t2=t2, t3=t3)
    else:
        verdicts = sup_df["verdict"]
    return verdicts, sup_df["stage1_score"], sup_df["confidence"]


def _process_chunk(
    path: Path, pipe: CascadedNIDSPipeline, guard: LiveAlertGuard, cfg: dict[str, Any], t2: float, t3: float
) -> list[ConsolidatedAlert]:
    """Traite un chunk unique : pré-filtrage -> inférence ML -> leaky bucket."""
    raw_df = _load_chunk(path)
    if len(raw_df) == 0:
        return []
    df_to_score, _ = pre_filter_flows(raw_df, cfg)
    if len(df_to_score) == 0:
        return []

    verdicts, s1_scores, confs = _score_chunk(path, df_to_score, pipe, t2, t3)
    return guard.process_batch(
        flows_df=df_to_score,
        verdicts=verdicts,
        s1_scores=s1_scores.values,
        s2_confs=confs.values,
    )


def _display_alert(alert: ConsolidatedAlert) -> None:
    """Affiche une alerte consolidée formatée sur la console."""
    print(
        f"🚨 [ALERTE CONSOLIDÉE] {alert.src_ip} -> {alert.dst_ip} | "
        f"Classe: {alert.attack_class} | Score hôte: {alert.host_score:.1f} | "
        f"Flux: {alert.flow_count} | Supprimés (cooldown): {alert.suppressed_count}"
    )


def _run_replay(
    args: argparse.Namespace, pipe: CascadedNIDSPipeline, guard: LiveAlertGuard, cfg: dict[str, Any]
) -> list[ConsolidatedAlert]:
    """Mode Replay : rejoue tous les fichiers chunks du dossier dans l'ordre."""
    chunk_files = sorted(
        [p for p in args.replay_dir.glob("*") if p.suffix in (".csv", ".parquet") and "_packets" not in p.name]
    )
    if args.max_chunks:
        chunk_files = chunk_files[: args.max_chunks]

    all_alerts: list[ConsolidatedAlert] = []
    print(f"▶️  Mode Replay démarré : {len(chunk_files)} chunk(s) à traiter...")
    for idx, chunk_path in enumerate(chunk_files, start=1):
        print(f"   [{idx}/{len(chunk_files)}] Traitement de : {chunk_path.name}")
        alerts = _process_chunk(chunk_path, pipe, guard, cfg, args.t2, args.t3)
        for a in alerts:
            _display_alert(a)
        all_alerts.extend(alerts)
        if args.delay > 0:
            time.sleep(args.delay)
    return all_alerts


def _run_watch(
    args: argparse.Namespace, pipe: CascadedNIDSPipeline, guard: LiveAlertGuard, cfg: dict[str, Any]
) -> list[ConsolidatedAlert]:
    """Mode Surveillance : scrute le dossier cible pour traiter les nouveaux chunks."""
    seen: set[str] = set()
    all_alerts: list[ConsolidatedAlert] = []
    print(f"👀 Mode Surveillance démarré sur : {args.watch_dir} (Ctrl+C pour quitter)")
    while True:
        candidates = sorted(
            [p for p in args.watch_dir.glob("*") if p.suffix in (".csv", ".parquet") and "_packets" not in p.name]
        )
        for chunk_path in candidates:
            if chunk_path.name in seen:
                continue
            seen.add(chunk_path.name)
            alerts = _process_chunk(chunk_path, pipe, guard, cfg, args.t2, args.t3)
            for a in alerts:
                _display_alert(a)
            all_alerts.extend(alerts)
            if args.max_chunks and len(seen) >= args.max_chunks:
                return all_alerts
        time.sleep(1.0)


def main() -> None:
    args = parse_args()
    print("=" * 78)
    print("   🛡️  MOTEUR TEMPS RÉEL NIDS & RÉDUCTION DES FAUSSES ALERTES")
    print("=" * 78)

    with open(args.config) as f:
        config = yaml.safe_load(f)

    pipe = CascadedNIDSPipeline([CatBoostStage1(), XGBoostStage1()], CnnStage2(), args.t1, args.t2)
    guard = LiveAlertGuard(config)

    alerts = _run_replay(args, pipe, guard, config) if args.replay_dir else _run_watch(args, pipe, guard, config)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump([asdict(a) for a in alerts], f, indent=2)
        print(f"\n📁 {len(alerts)} alertes sauvegardées dans : {args.output}")

    print("\n" + "=" * 78)
    print(f"✅ Exécution terminée : {len(alerts)} alerte(s) consolidée(s) générée(s).")
    print("=" * 78 + "\n")


if __name__ == "__main__":
    main()
