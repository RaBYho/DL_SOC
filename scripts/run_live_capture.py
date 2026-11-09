#!/usr/bin/env python3
"""Script de capture de trafic en direct (dumpcap/tcpdump) et analyse NIDS temps réel."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
from typing import Any
import yaml

from nids.adapters.stage1 import CatBoostStage1, XGBoostStage1
from nids.adapters.stage2 import CnnStage2
from nids.kitsune_runner import KitNETAnomalyDetector
from nids.pipeline import CascadedNIDSPipeline
from nids.flow_extractor import convert_pcap_to_flows, get_default_interface
from nids.live_filter import pre_filter_flows, SessionTracker
from nids.live_guard import LiveAlertGuard, ConsolidatedAlert

DEFAULT_BPF_FILTER = (
    "not (udp port 5353 or udp port 1900 or udp port 5355 or udp port 137 or udp port 138 "
    "or net 224.0.0.0/4 or host 239.255.255.250 or host 255.255.255.255)"
)


def parse_args() -> argparse.Namespace:
    """Parse les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Capture temps réel (dumpcap/tcpdump) et analyse via CICFlowMeter + NIDS."
    )
    parser.add_argument("-i", "--interface", type=str, default=None, help="Interface réseau (défaut: auto-détectée).")
    parser.add_argument("-b", "--duration", type=int, default=15, help="Durée de chaque micro-batch en secondes.")
    parser.add_argument("--tool", choices=["dumpcap", "tcpdump"], default="dumpcap", help="Outil de capture.")
    parser.add_argument("--pcap", type=Path, default=None, help="Mode PCAP hors-ligne (sans capture live).")
    parser.add_argument("--work-dir", type=Path, default=Path("/tmp/nids_capture"), help="Dossier temporaire PCAP/CSV.")
    parser.add_argument("--keep-pcaps", action="store_true", help="Conserver les fichiers PCAP après analyse.")
    parser.add_argument("--allow-loopback", action="store_true", help="Autoriser le trafic de boucle locale (127.0.0.1).")
    parser.add_argument("--max-chunks", type=int, default=None, help="Arrêter après N chunks traités.")
    parser.add_argument("--output", type=Path, default=None, help="Fichier JSON de sortie des alertes.")
    parser.add_argument("--config", type=Path, default=Path("configs/live_guard.yaml"), help="Config live_guard.")
    parser.add_argument("--t1", type=float, default=0.01, help="Seuil Étage 1 (défaut: 0.01).")
    parser.add_argument("--t2", type=float, default=0.10, help="Seuil Étage 2 (défaut: 0.10).")
    parser.add_argument("--t3", type=float, default=0.15, help="Seuil Kitsune RMSE (défaut: 0.15).")
    parser.add_argument("--no-kitsune", action="store_true", help="Désactive la branche Kitsune.")
    parser.add_argument("--bpf-filter", type=str, default=DEFAULT_BPF_FILTER, help="Filtre BPF noyau pour capture.")
    return parser.parse_args()


def _check_tool_exists(tool: str) -> str:
    """Vérifie l'existence de l'exécutable de capture sur le système."""
    path = shutil.which(tool)
    if path:
        return path
    for candidate in [f"/usr/bin/{tool}", f"/usr/sbin/{tool}"]:
        if Path(candidate).exists():
            return candidate
    raise FileNotFoundError(f"L'outil de capture '{tool}' n'est pas installé sur le système.")


def _start_capture_process(
    tool: str, iface: str, duration: int, pcap_pattern: Path, bpf_filter: str | None = None
) -> subprocess.Popen:
    """Démarre le processus de capture réseau avec filtrage BPF noyau."""
    tool_bin = _check_tool_exists(tool)
    if tool == "dumpcap":
        cmd = [tool_bin, "-P", "-i", iface, "-b", f"duration:{duration}"]
        if bpf_filter:
            cmd.extend(["-f", bpf_filter])
        cmd.extend(["-w", str(pcap_pattern), "-q"])
    else:
        cmd = [tool_bin, "-i", iface, "-G", str(duration), "-w", str(pcap_pattern), "-q"]
        if bpf_filter:
            cmd.extend([bpf_filter])

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except PermissionError as exc:
        raise PermissionError(
            f"Droit insuffisant pour exécuter {tool}.\n"
            "-> Exécutez : sudo usermod -aG wireshark $USER\n"
            f"-> Ou lancez avec sudo : sudo {sys.executable} scripts/run_live_capture.py -i {iface}"
        ) from exc

    time.sleep(0.1)
    if proc.poll() is not None:
        err = proc.stderr.read().decode().strip() if proc.stderr else ""
        raise PermissionError(
            f"Échec de capture sur [{iface}] via {tool} (code {proc.returncode}) : {err}\n"
            "-> Exécutez : sudo usermod -aG wireshark $USER (puis reconnectez-vous)\n"
            f"-> Ou lancez avec sudo : sudo {sys.executable} scripts/run_live_capture.py -i {iface}"
        )
    return proc


def _process_pcap_chunk(
    pcap_path: Path,
    pipe: CascadedNIDSPipeline,
    guard: LiveAlertGuard,
    cfg: dict[str, Any],
    allow_loopback: bool = False,
    session_tracker: SessionTracker | None = None,
) -> list[ConsolidatedAlert]:
    """Convertit un PCAP en flux CICFlowMeter et l'analyse via le pipeline live."""
    flows_df = convert_pcap_to_flows(pcap_path)
    if len(flows_df) == 0:
        return []

    to_score, _ = pre_filter_flows(
        flows_df, cfg, allow_loopback=allow_loopback, session_tracker=session_tracker
    )
    if len(to_score) == 0:
        return []

    sup_df = pipe.predict(to_score)
    return guard.process_batch(
        flows_df=to_score,
        verdicts=sup_df["verdict"],
        s1_scores=sup_df["stage1_score"].values,
        s2_confs=sup_df["confidence"].values,
    )


def _display_alert(a: ConsolidatedAlert) -> None:
    """Affiche une alerte consolidée sur la sortie standard."""
    print(
        f"🚨 [ALERTE CONSOLIDÉE] {a.src_ip} -> {a.dst_ip} | "
        f"Classe: {a.attack_class} | Score hôte: {a.host_score:.1f} | "
        f"Flux: {a.flow_count} | Supprimés: {a.suppressed_count}"
    )


def _cleanup_pcap(path: Path, keep: bool) -> None:
    """Supprime le fichier PCAP traité si la conservation n'est pas demandée."""
    if not keep and path.exists():
        try:
            path.unlink()
        except OSError:
            pass


def _run_offline_pcap(
    args: argparse.Namespace,
    pipe: CascadedNIDSPipeline,
    guard: LiveAlertGuard,
    cfg: dict[str, Any],
    allow_loopback: bool = False,
    session_tracker: SessionTracker | None = None,
) -> list[ConsolidatedAlert]:
    """Traite un fichier PCAP unique hors-ligne sans capture active."""
    print(f"📦 [Offline PCAP] Extraction des flux depuis : {args.pcap}")
    alerts = _process_pcap_chunk(args.pcap, pipe, guard, cfg, allow_loopback, session_tracker)
    for a in alerts:
        _display_alert(a)
    return alerts


def _drain_remaining_pcaps(
    work_dir: Path,
    processed: set[str],
    pipe: CascadedNIDSPipeline,
    guard: LiveAlertGuard,
    cfg: dict[str, Any],
    allow_loopback: bool,
    keep: bool,
    session_tracker: SessionTracker | None = None,
) -> list[ConsolidatedAlert]:
    """Traite et purge tous les fichiers PCAP restants après l'arrêt de la capture."""
    remaining = sorted(work_dir.glob("capture*.pcap"))
    drain_alerts: list[ConsolidatedAlert] = []
    for pf in remaining:
        if pf.name not in processed and pf.exists() and pf.stat().st_size > 24:
            processed.add(pf.name)
            print(f"⚡ [Batch Final #{len(processed)}] Traitement de {pf.name}...")
            chunk_alerts = _process_pcap_chunk(pf, pipe, guard, cfg, allow_loopback, session_tracker)
            for a in chunk_alerts:
                _display_alert(a)
            drain_alerts.extend(chunk_alerts)
        _cleanup_pcap(pf, keep)
    return drain_alerts


def _run_live_loop(
    args: argparse.Namespace,
    iface: str,
    pipe: CascadedNIDSPipeline,
    guard: LiveAlertGuard,
    cfg: dict[str, Any],
    allow_loopback: bool = False,
    session_tracker: SessionTracker | None = None,
) -> list[ConsolidatedAlert]:
    """Boucle de surveillance et d'analyse des chunks PCAP générés en temps réel."""
    args.work_dir.mkdir(parents=True, exist_ok=True)
    pcap_pattern = args.work_dir / "capture.pcap"
    proc = _start_capture_process(args.tool, iface, args.duration, pcap_pattern, args.bpf_filter)
    processed: set[str] = set()
    alerts: list[ConsolidatedAlert] = []

    print(f"📡 Capture active sur [{iface}] via {args.tool} (Ctrl+C pour arrêter)...")
    try:
        while proc.poll() is None:
            files = sorted(args.work_dir.glob("capture*.pcap"))
            ready_files = files[:-1] if len(files) > 1 else []
            for pf in ready_files:
                if pf.name not in processed:
                    processed.add(pf.name)
                    if not pf.exists() or pf.stat().st_size <= 24:
                        _cleanup_pcap(pf, args.keep_pcaps)
                        continue
                    print(f"⚡ [Batch #{len(processed)}] Traitement de {pf.name}...")
                    chunk_alerts = _process_pcap_chunk(pf, pipe, guard, cfg, allow_loopback, session_tracker)
                    for a in chunk_alerts:
                        _display_alert(a)
                    alerts.extend(chunk_alerts)
                    _cleanup_pcap(pf, args.keep_pcaps)
                    if args.max_chunks and len(processed) >= args.max_chunks:
                        return alerts
            time.sleep(1.0)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            proc.kill()
        drain_alerts = _drain_remaining_pcaps(
            args.work_dir, processed, pipe, guard, cfg, allow_loopback, args.keep_pcaps, session_tracker
        )
        alerts.extend(drain_alerts)
    return alerts


def _build_pipeline(args: argparse.Namespace) -> CascadedNIDSPipeline:
    """Instancie le pipeline hybride avec modèles supervisés et Kitsune."""
    kitsune = None if args.no_kitsune else KitNETAnomalyDetector(n_features=78, fm_grace=0, ad_grace=0)
    return CascadedNIDSPipeline(
        [CatBoostStage1(), XGBoostStage1()],
        CnnStage2(),
        t1=args.t1,
        t2=args.t2,
        kitsune_detector=kitsune,
        t3=args.t3,
    )


def main() -> None:
    args = parse_args()
    print("=" * 78 + "\n   🛡️  CAPTURE & ANALYSE RÉSEAU TEMPS RÉEL (CICFlowMeter + NIDS)\n" + "=" * 78)

    with open(args.config) as f:
        config = yaml.safe_load(f)

    pipe = _build_pipeline(args)
    guard = LiveAlertGuard(config)
    session_ttl = float(config.get("pre_filter", {}).get("session_ttl_sec", 120.0))
    session_tracker = SessionTracker(ttl_sec=session_ttl)
    iface = args.interface or get_default_interface()
    allow_loopback = args.allow_loopback or (iface == "lo")

    try:
        if args.pcap:
            alerts = _run_offline_pcap(args, pipe, guard, config, allow_loopback, session_tracker)
        else:
            alerts = _run_live_loop(args, iface, pipe, guard, config, allow_loopback, session_tracker)
    except (PermissionError, FileNotFoundError) as err:
        print(f"\n❌ ERREUR DE CAPTURE RÉSEAU :\n{err}\n")
        sys.exit(1)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump([asdict(a) for a in alerts], f, indent=2)

    print(f"\n✅ Exécution terminée : {len(alerts)} alerte(s) consolidée(s).\n" + "=" * 78)


if __name__ == "__main__":
    main()
