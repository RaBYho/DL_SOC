#!/usr/bin/env python3
"""Script de capture de trafic en direct (dumpcap/tcpdump) et analyse NIDS temps réel."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any
import numpy as np
import pandas as pd
from rich.console import Console
import yaml

from nids.adapters.stage1 import CatBoostStage1, XGBoostStage1
from nids.adapters.stage2 import CnnStage2
from nids.cli_ui import (
    print_alert_card,
    print_banner,
    print_batch_status,
    print_session_summary,
    suppress_c_stderr,
)
from nids.kitsune_runner import KitNETAnomalyDetector, LiveKitsuneCalibrator
from nids.pipeline import CascadedNIDSPipeline
from nids.flow_extractor import convert_pcap_to_flows, get_default_interface
from nids.live_filter import pre_filter_flows, SessionTracker
from nids.live_guard import LiveAlertGuard, ConsolidatedAlert
from nids.dpi_inspector import DPIInspector, fuse_predictions_with_dpi

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
    parser.add_argument("--t1", type=float, default=None, help="Seuil Étage 1 (défaut: config ou 0.50).")
    parser.add_argument("--t2", type=float, default=None, help="Seuil Étage 2 (défaut: config ou 0.70).")
    parser.add_argument("--t3", type=float, default=None, help="Seuil Kitsune RMSE (défaut: auto-calibré ou config).")
    parser.add_argument("--no-kitsune", action="store_true", help="Désactive la branche Kitsune.")
    parser.add_argument("--no-dpi", action="store_true", help="Désactive l'inspection de contenu (DPI).")
    parser.add_argument("--bpf-filter", type=str, default=DEFAULT_BPF_FILTER, help="Filtre BPF noyau pour capture.")
    parser.add_argument("--cooldown", type=float, default=None, help="Durée de cooldown anti-flood en secondes (écrase la config).")
    parser.add_argument("--dashboard", action="store_true", help="Active l'envoi temps réel des flux et alertes au Dashboard SOC.")
    parser.add_argument("--dashboard-url", type=str, default="http://localhost:8000/api/dashboard", help="URL de l'API Dashboard SOC.")
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


def _build_capture_cmd(
    tool_bin: str, tool: str, iface: str, duration: int, pcap_pattern: Path, bpf_filter: str | None
) -> list[str]:
    """Construit la ligne de commande dumpcap ou tcpdump."""
    if tool == "dumpcap":
        cmd = [tool_bin, "-P", "-i", iface, "-b", f"duration:{duration}"]
        if bpf_filter:
            cmd.extend(["-f", bpf_filter])
        return cmd + ["-w", str(pcap_pattern), "-q"]
    cmd = [tool_bin, "-i", iface, "-G", str(duration), "-w", str(pcap_pattern), "-q"]
    return cmd + ([bpf_filter] if bpf_filter else [])


def _start_capture_process(
    tool: str, iface: str, duration: int, pcap_pattern: Path, bpf_filter: str | None = None
) -> subprocess.Popen:
    """Démarre le processus de capture réseau avec filtrage BPF noyau."""
    tool_bin = _check_tool_exists(tool)
    pcap_pattern.parent.mkdir(parents=True, exist_ok=True)
    try:
        pcap_pattern.parent.chmod(0o777)
    except OSError:
        pass
    cmd = _build_capture_cmd(tool_bin, tool, iface, duration, pcap_pattern, bpf_filter)
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except PermissionError as exc:
        raise PermissionError(
            f"Droit insuffisant pour exécuter {tool}.\n"
            "-> Exécutez : sudo usermod -aG wireshark $USER (puis relancez avec newgrp wireshark)\n"
            f"-> Ou lancez avec sudo : sudo {sys.executable} scripts/run_live_capture.py -i {iface}"
        ) from exc
    time.sleep(0.1)
    if proc.poll() is not None:
        err = proc.stderr.read().decode().strip() if proc.stderr else ""
        raise PermissionError(
            f"Échec de capture sur [{iface}] via {tool} (code {proc.returncode}) : {err}\n"
            "-> Exécutez : sudo usermod -aG wireshark $USER (puis relancez avec newgrp wireshark)\n"
            f"-> Ou lancez avec sudo : sudo {sys.executable} scripts/run_live_capture.py -i {iface}"
        )
    return proc


def _predict_and_fuse(
    pipe: CascadedNIDSPipeline,
    to_score: pd.DataFrame,
    pcap_path: Path,
    dpi: DPIInspector | None,
    calib: LiveKitsuneCalibrator | None,
) -> pd.DataFrame:
    """Exécute l'inférence supervisée, Kitsune et la fusion DPI."""
    sup_df = pipe.predict(to_score)
    if calib is not None and "kitsune_score" in sup_df:
        pipe.t3 = calib.update(sup_df["kitsune_score"].values, sup_df["stage1_score"].values)
    if dpi is not None:
        sup_df = fuse_predictions_with_dpi(sup_df, to_score, dpi.inspect_pcap(pcap_path))
    return sup_df


def _extract_telemetry_dict(
    orig_row: pd.Series,
    fwd_pkts: int,
    bwd_pkts: int,
    fwd_bytes: float,
    bwd_bytes: float,
    dpi_rule: str = "",
) -> dict[str, Any]:
    """Extrait l'ensemble des métriques réseau et des 78 caractéristiques CICFlowMeter."""
    tot_pkts = max(1, fwd_pkts + bwd_pkts)
    tot_bytes = fwd_bytes + bwd_bytes
    duration = float(orig_row.get("Flow Duration", 0.0) or 0.0)
    bytes_s = float(orig_row.get("Flow Bytes/s", 0.0) or 0.0)
    pkts_s = float(orig_row.get("Flow Packets/s", 0.0) or 0.0)
    fwd_len_mean = float(orig_row.get("Fwd Packet Length Mean", 0.0) or 0.0)
    bwd_len_mean = float(orig_row.get("Bwd Packet Length Mean", 0.0) or 0.0)
    avg_pkt_size = float(orig_row.get("Average Packet Size", 0.0) or 0.0)
    if avg_pkt_size == 0.0 and tot_pkts > 0 and tot_bytes > 0:
        avg_pkt_size = round(tot_bytes / tot_pkts, 2)

    syn_cnt = int(orig_row.get("SYN Flag Count", orig_row.get("syn_flag_cnt", 0)) or 0)
    ack_cnt = int(orig_row.get("ACK Flag Count", orig_row.get("ack_flag_cnt", 0)) or 0)
    psh_cnt = int(orig_row.get("PSH Flag Count", orig_row.get("psh_flag_cnt", 0)) or 0)
    fin_cnt = int(orig_row.get("FIN Flag Count", orig_row.get("fin_flag_cnt", 0)) or 0)
    rst_cnt = int(orig_row.get("RST Flag Count", orig_row.get("rst_flag_cnt", 0)) or 0)
    down_up = float(orig_row.get("Down/Up Ratio", 0.0) or 0.0)
    if down_up == 0.0 and fwd_pkts > 0:
        down_up = round(bwd_pkts / fwd_pkts, 2)

    # 78 caractéristiques CICFlowMeter
    all_features: dict[str, Any] = {}
    ignored_keys = {"Flow ID", "Source IP", "Destination IP", "Timestamp", "Src IP", "Dst IP"}
    for k, v in orig_row.items():
        if k in ignored_keys:
            continue
        try:
            val_float = float(v)
            if pd.isna(val_float) or np.isinf(val_float):
                all_features[str(k)] = 0.0
            elif float(val_float).is_integer():
                all_features[str(k)] = int(val_float)
            else:
                all_features[str(k)] = round(val_float, 4)
        except (ValueError, TypeError):
            continue

    return {
        "flow_duration": duration,
        "flow_bytes_s": bytes_s,
        "flow_packets_s": pkts_s,
        "total_fwd_packets": fwd_pkts,
        "total_bwd_packets": bwd_pkts,
        "fwd_packet_length_mean": fwd_len_mean,
        "bwd_packet_length_mean": bwd_len_mean,
        "avg_packet_size": avg_pkt_size,
        "syn_flag_count": syn_cnt,
        "ack_flag_count": ack_cnt,
        "psh_flag_count": psh_cnt,
        "fin_flag_count": fin_cnt,
        "rst_flag_count": rst_cnt,
        "down_up_ratio": down_up,
        "dpi_rule": dpi_rule,
        "all_features": all_features,
    }


def _send_batch_to_dashboard(
    dashboard_url: str | None,
    sensor_id: str,
    iface: str,
    to_score: pd.DataFrame,
    sup_df: pd.DataFrame | None = None,
    ignored_df: pd.DataFrame | None = None,
    consolidated_alerts: list[ConsolidatedAlert] | None = None,
) -> None:
    """Transmet de manière asynchrone / non-bloquante les flux analysés au Dashboard SOC."""
    if not dashboard_url:
        return
    try:
        from datetime import datetime
        import urllib.request
        flow_records = []

        confirmed_ips: set[str] = set()
        confirmed_pairs: set[tuple[str, str]] = set()
        if consolidated_alerts:
            for a in consolidated_alerts:
                confirmed_ips.add(a.src_ip)
                confirmed_pairs.add((a.src_ip, a.attack_class))

        # 1. Traitement des flux analysés par les modèles ML / DPI / Kitsune
        if to_score is not None and len(to_score) > 0 and sup_df is not None:
            for i, row in sup_df.iterrows():
                orig_row = to_score.iloc[i]
                src_ip = str(
                    orig_row.get("Source IP")
                    or orig_row.get("Src IP")
                    or orig_row.get("src_ip")
                    or "127.0.0.1"
                )
                dst_ip = str(
                    orig_row.get("Destination IP")
                    or orig_row.get("Dst IP")
                    or orig_row.get("dst_ip")
                    or "127.0.0.1"
                )
                src_port = int(
                    orig_row.get("Source Port")
                    or orig_row.get("Src Port")
                    or orig_row.get("src_port")
                    or 0
                )
                dst_port = int(
                    orig_row.get("Destination Port")
                    or orig_row.get("Dst Port")
                    or orig_row.get("dst_port")
                    or 0
                )
                raw_proto = (
                    orig_row.get("Protocol")
                    or orig_row.get("protocol")
                    or orig_row.get("Proto")
                    or "TCP"
                )

                raw_ts = orig_row.get("Timestamp") or orig_row.get("timestamp")
                if isinstance(raw_ts, (int, float)):
                    flow_ts = float(raw_ts)
                elif raw_ts:
                    try:
                        flow_ts = datetime.strptime(str(raw_ts).strip(), "%Y-%m-%d %H:%M:%S").timestamp()
                    except Exception:
                        flow_ts = time.time()
                else:
                    flow_ts = time.time()

                fwd_pkts = int(orig_row.get("Total Fwd Packets", orig_row.get("Tot Fwd Pkts", 1)) or 1)
                bwd_pkts = int(orig_row.get("Total Backward Packets", orig_row.get("Tot Bwd Pkts", 0)) or 0)
                fwd_bytes = float(orig_row.get("Total Length of Fwd Packets", orig_row.get("TotLen Fwd Pkts", 0.0)) or 0.0)
                bwd_bytes = float(orig_row.get("Total Length of Bwd Packets", orig_row.get("TotLen Bwd Pkts", 0.0)) or 0.0)
                dpi_rule = str(row.get("dpi_rule", "") or "")

                telemetry = _extract_telemetry_dict(orig_row, fwd_pkts, bwd_pkts, fwd_bytes, bwd_bytes, dpi_rule)

                v_str = str(row.get("verdict", "BENIGN"))
                is_confirmed = (
                    (src_ip in confirmed_ips and v_str != "BENIGN")
                    or (src_ip, v_str) in confirmed_pairs
                )

                flow_records.append({
                    "timestamp": flow_ts,
                    "src_ip": src_ip,
                    "dst_ip": dst_ip,
                    "src_port": src_port,
                    "dst_port": dst_port,
                    "protocol": str(raw_proto),
                    "packet_count": max(1, fwd_pkts + bwd_pkts),
                    "verdict": v_str,
                    "stage1_score": float(row.get("stage1_score", 0.0)),
                    "confidence": float(row.get("confidence", 0.0)),
                    "kitsune_score": float(row.get("kitsune_score", 0.0)),
                    "decision_path": str(row.get("decision_path", "STAGE1_BENIGN")),
                    "dpi_rule": dpi_rule,
                    "dpi_category": str(row.get("dpi_category", "") or ""),
                    "is_anomaly": bool(row.get("is_anomaly", False)),
                    "is_confirmed_alert": bool(is_confirmed),
                    "flow_duration": telemetry["flow_duration"],
                    "flow_bytes_s": telemetry["flow_bytes_s"],
                    "flow_packets_s": telemetry["flow_packets_s"],
                    "total_fwd_packets": fwd_pkts,
                    "total_bwd_packets": bwd_pkts,
                    "avg_packet_size": telemetry["avg_packet_size"],
                    "syn_flag_count": telemetry["syn_flag_count"],
                    "ack_flag_count": telemetry["ack_flag_count"],
                    "psh_flag_count": telemetry["psh_flag_count"],
                    "down_up_ratio": telemetry["down_up_ratio"],
                    "raw_metrics": telemetry,
                })

        # 2. Transmission des flux pré-filtrés bénins pour visibilité complète du trafic
        if ignored_df is not None and len(ignored_df) > 0:
            for _, orig_row in ignored_df.head(50).iterrows():
                src_ip = str(
                    orig_row.get("Source IP")
                    or orig_row.get("Src IP")
                    or orig_row.get("src_ip")
                    or "127.0.0.1"
                )
                dst_ip = str(
                    orig_row.get("Destination IP")
                    or orig_row.get("Dst IP")
                    or orig_row.get("dst_ip")
                    or "127.0.0.1"
                )
                src_port = int(
                    orig_row.get("Source Port")
                    or orig_row.get("Src Port")
                    or orig_row.get("src_port")
                    or 0
                )
                dst_port = int(
                    orig_row.get("Destination Port")
                    or orig_row.get("Dst Port")
                    or orig_row.get("dst_port")
                    or 0
                )
                raw_proto = (
                    orig_row.get("Protocol")
                    or orig_row.get("protocol")
                    or orig_row.get("Proto")
                    or "TCP"
                )

                raw_ts = orig_row.get("Timestamp") or orig_row.get("timestamp")
                if isinstance(raw_ts, (int, float)):
                    flow_ts = float(raw_ts)
                elif raw_ts:
                    try:
                        flow_ts = datetime.strptime(str(raw_ts).strip(), "%Y-%m-%d %H:%M:%S").timestamp()
                    except Exception:
                        flow_ts = time.time()
                else:
                    flow_ts = time.time()

                fwd_pkts = int(orig_row.get("Total Fwd Packets", orig_row.get("Tot Fwd Pkts", 1)) or 1)
                bwd_pkts = int(orig_row.get("Total Backward Packets", orig_row.get("Tot Bwd Pkts", 0)) or 0)
                fwd_bytes = float(orig_row.get("Total Length of Fwd Packets", orig_row.get("TotLen Fwd Pkts", 0.0)) or 0.0)
                bwd_bytes = float(orig_row.get("Total Length of Bwd Packets", orig_row.get("TotLen Bwd Pkts", 0.0)) or 0.0)

                telemetry = _extract_telemetry_dict(orig_row, fwd_pkts, bwd_pkts, fwd_bytes, bwd_bytes, "")

                flow_records.append({
                    "timestamp": flow_ts,
                    "src_ip": src_ip,
                    "dst_ip": dst_ip,
                    "src_port": src_port,
                    "dst_port": dst_port,
                    "protocol": str(raw_proto),
                    "packet_count": max(1, fwd_pkts + bwd_pkts),
                    "verdict": "BENIGN",
                    "stage1_score": 0.0,
                    "confidence": 0.0,
                    "kitsune_score": 0.0,
                    "decision_path": "PRE_FILTER_BENIGN",
                    "dpi_rule": "",
                    "dpi_category": "",
                    "is_anomaly": False,
                    "flow_duration": telemetry["flow_duration"],
                    "flow_bytes_s": telemetry["flow_bytes_s"],
                    "flow_packets_s": telemetry["flow_packets_s"],
                    "total_fwd_packets": fwd_pkts,
                    "total_bwd_packets": bwd_pkts,
                    "avg_packet_size": telemetry["avg_packet_size"],
                    "syn_flag_count": telemetry["syn_flag_count"],
                    "ack_flag_count": telemetry["ack_flag_count"],
                    "psh_flag_count": telemetry["psh_flag_count"],
                    "down_up_ratio": telemetry["down_up_ratio"],
                    "raw_metrics": telemetry,
                })

        if not flow_records:
            return

        payload = {
            "sensor_id": sensor_id,
            "interface": iface,
            "flows": flow_records,
            "consolidated_alerts": [asdict(a) for a in (consolidated_alerts or [])],
        }
        url = f"{dashboard_url.rstrip('/')}/flows/ingest"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=1.0) as _:
            pass
    except Exception:
        pass


def _process_pcap_chunk(
    pcap_path: Path,
    pipe: CascadedNIDSPipeline,
    guard: LiveAlertGuard,
    cfg: dict[str, Any],
    allow_loopback: bool = False,
    session_tracker: SessionTracker | None = None,
    dpi_inspector: DPIInspector | None = None,
    calibrator: LiveKitsuneCalibrator | None = None,
    dashboard_url: str | None = None,
    sensor_id: str = "sensor-live",
    iface: str = "live",
) -> tuple[list[ConsolidatedAlert], int]:
    """Convertit un PCAP en flux CICFlowMeter et l'analyse via le pipeline live."""
    with suppress_c_stderr():
        flows_df = convert_pcap_to_flows(pcap_path)
    if len(flows_df) == 0:
        return [], 0
    to_score, ignored_df = pre_filter_flows(
        flows_df, cfg, allow_loopback=allow_loopback, session_tracker=session_tracker
    )
    if len(to_score) == 0:
        if dashboard_url and len(ignored_df) > 0:
            _send_batch_to_dashboard(dashboard_url, sensor_id, iface, to_score, None, ignored_df=ignored_df)
        return [], len(flows_df)
    sup_df = _predict_and_fuse(pipe, to_score, pcap_path, dpi_inspector, calibrator)
    alerts = guard.process_batch(
        flows_df=to_score,
        verdicts=sup_df["verdict"],
        s1_scores=sup_df["stage1_score"].values,
        s2_confs=sup_df["confidence"].values,
    )
    if dashboard_url:
        _send_batch_to_dashboard(
            dashboard_url, sensor_id, iface, to_score, sup_df, ignored_df=ignored_df, consolidated_alerts=alerts
        )
    return alerts, len(flows_df)


def _display_alert(a: ConsolidatedAlert, console: Console | None = None) -> None:
    """Affiche une alerte consolidée via la console Rich."""
    c = console or Console()
    print_alert_card(c, a)


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
    dpi: DPIInspector | None = None,
    calibrator: LiveKitsuneCalibrator | None = None,
    console: Console | None = None,
) -> tuple[list[ConsolidatedAlert], int]:
    """Traite un fichier PCAP unique hors-ligne sans capture active."""
    c = console or Console()
    c.print(f"[bold cyan]📦 [Offline PCAP][/bold cyan] Extraction des flux depuis : [bold]{args.pcap}[/bold]")
    d_url = args.dashboard_url if getattr(args, "dashboard", False) else None
    alerts, n_flows = _process_pcap_chunk(
        args.pcap,
        pipe,
        guard,
        cfg,
        allow_loopback,
        session_tracker,
        dpi,
        calibrator,
        dashboard_url=d_url,
        sensor_id="sensor-offline",
        iface="pcap",
    )
    print_batch_status(c, 1, args.pcap.name, n_flows, len(alerts))
    for a in alerts:
        _display_alert(a, c)
    return alerts, 1


def _drain_remaining_pcaps(
    work_dir: Path,
    processed: set[str],
    pipe: CascadedNIDSPipeline,
    guard: LiveAlertGuard,
    cfg: dict[str, Any],
    allow_loopback: bool,
    keep: bool,
    session_tracker: SessionTracker | None = None,
    dpi: DPIInspector | None = None,
    calibrator: LiveKitsuneCalibrator | None = None,
    console: Console | None = None,
    dashboard_url: str | None = None,
    sensor_id: str = "sensor-live",
    iface: str = "live",
) -> list[ConsolidatedAlert]:
    """Traite et purge tous les fichiers PCAP restants après l'arrêt de la capture."""
    c = console or Console()
    remaining = sorted(work_dir.glob("capture*.pcap"))
    drain_alerts: list[ConsolidatedAlert] = []
    for pf in remaining:
        if pf.name not in processed and pf.exists() and pf.stat().st_size > 24:
            processed.add(pf.name)
            chunk_alerts, n_flows = _process_pcap_chunk(
                pf,
                pipe,
                guard,
                cfg,
                allow_loopback,
                session_tracker,
                dpi,
                calibrator,
                dashboard_url=dashboard_url,
                sensor_id=sensor_id,
                iface=iface,
            )
            print_batch_status(c, len(processed), pf.name, n_flows, len(chunk_alerts), is_final=True)
            for a in chunk_alerts:
                _display_alert(a, c)
            drain_alerts.extend(chunk_alerts)
        _cleanup_pcap(pf, keep)
    return drain_alerts


def _process_ready_files(
    ready_files: list[Path],
    processed: set[str],
    pipe: CascadedNIDSPipeline,
    guard: LiveAlertGuard,
    cfg: dict[str, Any],
    allow_loopback: bool,
    keep_pcaps: bool,
    session_tracker: SessionTracker | None = None,
    dpi: DPIInspector | None = None,
    calibrator: LiveKitsuneCalibrator | None = None,
    console: Console | None = None,
    dashboard_url: str | None = None,
    sensor_id: str = "sensor-live",
    iface: str = "live",
) -> list[ConsolidatedAlert]:
    """Traite les fichiers PCAP prêts et retourne les alertes émises."""
    c = console or Console()
    batch_alerts: list[ConsolidatedAlert] = []
    for pf in ready_files:
        if pf.name not in processed:
            processed.add(pf.name)
            if not pf.exists() or pf.stat().st_size <= 24:
                _cleanup_pcap(pf, keep_pcaps)
                continue
            chunk_alerts, n_flows = _process_pcap_chunk(
                pf,
                pipe,
                guard,
                cfg,
                allow_loopback,
                session_tracker,
                dpi,
                calibrator,
                dashboard_url=dashboard_url,
                sensor_id=sensor_id,
                iface=iface,
            )
            print_batch_status(c, len(processed), pf.name, n_flows, len(chunk_alerts))
            for a in chunk_alerts:
                _display_alert(a, c)
            batch_alerts.extend(chunk_alerts)
            _cleanup_pcap(pf, keep_pcaps)
    return batch_alerts


def _stop_capture_proc(proc: subprocess.Popen) -> None:
    """Arrête proprement le sous-processus de capture avec timeout de secours."""
    proc.terminate()
    try:
        proc.wait(timeout=2.0)
    except subprocess.TimeoutExpired:
        proc.kill()


def _poll_and_process_chunks(
    args: argparse.Namespace,
    proc: subprocess.Popen,
    pipe: CascadedNIDSPipeline,
    guard: LiveAlertGuard,
    cfg: dict[str, Any],
    allow_loopback: bool,
    tracker: SessionTracker | None,
    dpi: DPIInspector | None,
    calibrator: LiveKitsuneCalibrator | None,
    console: Console | None = None,
    iface: str = "live",
) -> tuple[list[ConsolidatedAlert], set[str]]:
    """Scrute périodiquement les chunks PCAP et traite ceux qui sont prêts."""
    processed, alerts = set(), []
    d_url = args.dashboard_url if getattr(args, "dashboard", False) else None
    sensor_id = f"sensor-{iface}"
    while proc.poll() is None:
        files = sorted(args.work_dir.glob("capture*.pcap"))
        ready = files[:-1] if len(files) > 1 else []
        alerts.extend(
            _process_ready_files(
                ready,
                processed,
                pipe,
                guard,
                cfg,
                allow_loopback,
                args.keep_pcaps,
                tracker,
                dpi,
                calibrator,
                console,
                dashboard_url=d_url,
                sensor_id=sensor_id,
                iface=iface,
            )
        )
        if args.max_chunks and len(processed) >= args.max_chunks:
            break
        time.sleep(1.0)
    return alerts, processed


def _run_live_loop(
    args: argparse.Namespace,
    iface: str,
    pipe: CascadedNIDSPipeline,
    guard: LiveAlertGuard,
    cfg: dict[str, Any],
    allow_loopback: bool = False,
    session_tracker: SessionTracker | None = None,
    dpi: DPIInspector | None = None,
    calibrator: LiveKitsuneCalibrator | None = None,
    console: Console | None = None,
) -> tuple[list[ConsolidatedAlert], int]:
    """Boucle de surveillance et d'analyse des chunks PCAP générés en temps réel."""
    c = console or Console()
    args.work_dir.mkdir(parents=True, exist_ok=True)
    pcap_pattern = args.work_dir / "capture.pcap"
    proc = _start_capture_process(args.tool, iface, args.duration, pcap_pattern, args.bpf_filter)
    c.print(f"[bold cyan]📡 Capture active sur [{iface}] via {args.tool}[/bold cyan] [dim](Ctrl+C pour arrêter)...[/dim]\n")
    d_url = args.dashboard_url if getattr(args, "dashboard", False) else None
    sensor_id = f"sensor-{iface}"
    try:
        alerts, processed = _poll_and_process_chunks(
            args, proc, pipe, guard, cfg, allow_loopback, session_tracker, dpi, calibrator, c, iface=iface
        )
    finally:
        _stop_capture_proc(proc)
        alerts.extend(
            _drain_remaining_pcaps(
                args.work_dir,
                processed,
                pipe,
                guard,
                cfg,
                allow_loopback,
                args.keep_pcaps,
                session_tracker,
                dpi,
                calibrator,
                c,
                dashboard_url=d_url,
                sensor_id=sensor_id,
                iface=iface,
            )
        )
    return alerts, len(processed)


def _resolve_thresholds(args: argparse.Namespace, cfg: dict[str, Any] | None) -> tuple[float, float, float]:
    """Résout les seuils de décision t1, t2 et t3 depuis les arguments ou la configuration."""
    th_cfg = (cfg or {}).get("thresholds", {})
    t1 = args.t1 if args.t1 is not None else float(th_cfg.get("t1", 0.50))
    t2 = args.t2 if args.t2 is not None else float(th_cfg.get("t2", 0.70))
    k_cfg = (cfg or {}).get("kitsune_live", {})
    t3 = args.t3 if args.t3 is not None else float(k_cfg.get("default_t3", 0.0100))
    return t1, t2, t3


def _build_pipeline(args: argparse.Namespace, cfg: dict[str, Any] | None = None) -> CascadedNIDSPipeline:
    """Instancie le pipeline hybride avec modèles supervisés et Kitsune."""
    t1, t2, t3 = _resolve_thresholds(args, cfg)
    kitsune = None if args.no_kitsune else KitNETAnomalyDetector(n_features=78, fm_grace=0, ad_grace=0)
    return CascadedNIDSPipeline(
        [CatBoostStage1(), XGBoostStage1()],
        CnnStage2(),
        t1=t1,
        t2=t2,
        kitsune_detector=kitsune,
        t3=t3,
    )


def _build_kitsune_calibrator(
    args: argparse.Namespace, cfg: dict[str, Any]
) -> LiveKitsuneCalibrator | None:
    """Instancie le gestionnaire de calibration dynamique si activé."""
    if args.no_kitsune or args.t3 is not None:
        return None
    k_cfg = cfg.get("kitsune_live", {})
    if not k_cfg.get("dynamic_calibration", True):
        return None
    t1, _, _ = _resolve_thresholds(args, cfg)
    return LiveKitsuneCalibrator(
        default_t3=float(k_cfg.get("default_t3", 0.0100)),
        method=str(k_cfg.get("calibration_method", "mu_plus_3sigma")),
        percentile=float(k_cfg.get("dynamic_threshold_percentile", 99.9)),
        multiplier=float(k_cfg.get("dynamic_threshold_multiplier", 1.5)),
        filter_poisoning=bool(k_cfg.get("filter_poisoning_with_stage1", True)),
        min_clean_flows=int(k_cfg.get("min_clean_flows", 10)),
        max_history_flows=int(k_cfg.get("max_history_flows", 2000)),
        t1=t1,
    )


def _save_and_report_alerts(
    alerts: list[ConsolidatedAlert], output: Path | None, total_batches: int = 1, console: Console | None = None
) -> None:
    """Sauvegarde les alertes au format JSON et affiche la synthèse finale SOC."""
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w") as f:
            json.dump([asdict(a) for a in alerts], f, indent=2)
    c = console or Console()
    print_session_summary(c, alerts, total_batches, output)


def main() -> None:
    """Point d'entrée principal pour la capture et analyse NIDS temps réel."""
    args = parse_args()
    console = Console()
    with open(args.config) as f:
        config = yaml.safe_load(f)
    if args.cooldown is not None:
        config.setdefault("cooldown", {})["ttl_sec"] = args.cooldown

    t1, t2, t3 = _resolve_thresholds(args, config)
    iface = args.interface or get_default_interface()
    pcap_name = args.pcap.name if args.pcap else None
    print_banner(console, iface, args.duration, t1, t2, t3, args.tool, bool(args.pcap), pcap_name)

    pipe = _build_pipeline(args, config)
    guard, dpi = LiveAlertGuard(config), None if args.no_dpi else DPIInspector()
    calibrator = _build_kitsune_calibrator(args, config)
    tracker = SessionTracker(ttl_sec=float(config.get("pre_filter", {}).get("session_ttl_sec", 120.0)))
    allow_loop = args.allow_loopback or (iface == "lo")

    try:
        if args.pcap:
            alerts, batches = _run_offline_pcap(args, pipe, guard, config, allow_loop, tracker, dpi, calibrator, console)
        else:
            alerts, batches = _run_live_loop(args, iface, pipe, guard, config, allow_loop, tracker, dpi, calibrator, console)
    except (PermissionError, FileNotFoundError) as err:
        console.print(f"\n[bold red]❌ ERREUR DE CAPTURE RÉSEAU :[/bold red]\n{err}\n")
        sys.exit(1)

    _save_and_report_alerts(alerts, args.output, total_batches=batches, console=console)


if __name__ == "__main__":
    main()
