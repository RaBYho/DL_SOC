"""Module d'extraction et normalisation des flux réseau (PCAP -> CICFlowMeter -> CICIDS2017)."""

from pathlib import Path
import tempfile
from typing import Any
from cicflowmeter.sniffer import create_sniffer
import numpy as np
import pandas as pd
import yaml


def get_default_interface() -> str:
    """Détecte l'interface réseau active par défaut via /sys/class/net."""
    net_dir = Path("/sys/class/net")
    if not net_dir.exists():
        return "lo"

    for iface_path in sorted(net_dir.iterdir()):
        oper_file = iface_path / "operstate"
        if iface_path.name != "lo" and oper_file.exists():
            if oper_file.read_text().strip().lower() == "up":
                return iface_path.name

    return "lo"


def _run_cicflowmeter_on_pcap(pcap_path: Path, temp_csv: Path) -> None:
    """Exécute CICFlowMeter en sous-tâche Scapy sur le fichier PCAP."""
    sniffer, session = create_sniffer(
        input_file=str(pcap_path),
        input_interface=None,
        output_mode="csv",
        output=str(temp_csv),
        fields=None,
        verbose=False,
    )
    sniffer.start()
    sniffer.join()
    if hasattr(session, "_gc_stop"):
        session._gc_stop.set()
        session._gc_thread.join(timeout=1.0)
    session.flush_flows()


def _normalize_flow_df(raw_df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    """Normalise les colonnes du CSV cicflowmeter vers le standard CICIDS2017."""
    df = raw_df.rename(columns=mapping).copy()
    if "Fwd Header Length" in df.columns:
        df["Fwd Header Length.1"] = df["Fwd Header Length"]

    src = df.get("Source IP", pd.Series("", index=df.index)).astype(str)
    dst = df.get("Destination IP", pd.Series("", index=df.index)).astype(str)
    sp = df.get("Source Port", pd.Series(0, index=df.index)).astype(str)
    dp = df.get("Destination Port", pd.Series(0, index=df.index)).astype(str)
    proto = df.get("Protocol", pd.Series(0, index=df.index)).astype(str)
    df["Flow ID"] = src + "-" + dst + "-" + sp + "-" + dp + "-" + proto

    return df.replace([np.inf, -np.inf], 0.0).fillna(0.0)


def _extract_and_load_flows(pcap: Path, temp_csv: Path, mapping: dict[str, str]) -> pd.DataFrame:
    """Exécute CICFlowMeter en isolation et charge le DataFrame normalisé."""
    try:
        _run_cicflowmeter_on_pcap(pcap, temp_csv)
    except Exception:
        return pd.DataFrame()

    if not temp_csv.exists() or temp_csv.stat().st_size == 0:
        return pd.DataFrame()
    raw_df = pd.read_csv(temp_csv)
    return _normalize_flow_df(raw_df, mapping) if len(raw_df) > 0 else pd.DataFrame()


def _clamp_direction_tso(res: pd.DataFrame, prefix: str, mtu: float, mss: float) -> None:
    """Borne les métriques de paquets TSO/GSO pour une direction (Fwd ou Bwd)."""
    max_col = f"{prefix} Packet Length Max"
    tot_col = f"Total Length of {prefix} Packets"
    pkt_col = "Total Fwd Packets" if prefix == "Fwd" else "Total Backward Packets"
    mean_col = f"{prefix} Packet Length Mean"
    std_col = f"{prefix} Packet Length Std"
    if max_col not in res.columns or tot_col not in res.columns or pkt_col not in res.columns:
        return
    mask = res[max_col] > mtu
    if not mask.any():
        return
    tot = res.loc[mask, tot_col].astype(float)
    virt = np.maximum(res.loc[mask, pkt_col].astype(float), np.ceil(tot / mss))
    res.loc[mask, max_col] = mtu
    res.loc[mask, pkt_col] = virt
    res.loc[mask, mean_col] = np.where(virt > 0, tot / virt, 0.0)
    res.loc[mask, std_col] = 0.0


def _clamp_global_tso(res: pd.DataFrame, mtu: float) -> None:
    """Borne les métriques globales de taille de paquets et ajuste moyenne et variance."""
    if "Max Packet Length" not in res.columns:
        return
    mask = res["Max Packet Length"] > mtu
    if not mask.any():
        return
    res.loc[mask, "Max Packet Length"] = mtu
    fwd_len = res.loc[mask, "Total Length of Fwd Packets"].astype(float)
    bwd_len = res.loc[mask, "Total Length of Bwd Packets"].astype(float)
    tot_pkts = (
        res.loc[mask, "Total Fwd Packets"].astype(float)
        + res.loc[mask, "Total Backward Packets"].astype(float)
    )
    res.loc[mask, "Packet Length Mean"] = np.where(tot_pkts > 0, (fwd_len + bwd_len) / tot_pkts, 0.0)
    if "Packet Length Std" in res.columns:
        res.loc[mask, "Packet Length Std"] = np.minimum(res.loc[mask, "Packet Length Std"], 500.0)
        res.loc[mask, "Packet Length Variance"] = res.loc[mask, "Packet Length Std"] ** 2


def normalize_tso_mtu(
    df: pd.DataFrame, mtu: float = 1514.0, mss: float = 1460.0
) -> pd.DataFrame:
    """Normalise les flux issus de cartes TSO/GSO ou de loopback vers le standard Ethernet MTU 1514."""
    if len(df) == 0:
        return df
    res = df.copy()
    _clamp_direction_tso(res, "Fwd", mtu, mss)
    _clamp_direction_tso(res, "Bwd", mtu, mss)
    _clamp_global_tso(res, mtu)
    return res


def convert_pcap_to_flows(
    pcap_path: Path | str,
    output_csv: Path | str | None = None,
    mapping_path: Path | str = "configs/cicflowmeter_mapping.yaml",
    mtu_norm: bool = True,
    mtu: float = 1514.0,
    mss: float = 1460.0,
) -> pd.DataFrame:
    """Convertit un PCAP en DataFrame normalisé compatible avec le pipeline ML."""
    pcap = Path(pcap_path)
    if not pcap.exists() or pcap.stat().st_size <= 24:
        return pd.DataFrame()

    with open(mapping_path) as f:
        mapping = yaml.safe_load(f)

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        temp_csv = Path(tmp.name)

    try:
        df = _extract_and_load_flows(pcap, temp_csv, mapping)
        if len(df) > 0 and mtu_norm:
            df = normalize_tso_mtu(df, mtu, mss)
        if output_csv and len(df) > 0:
            Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_csv, index=False)
        return df
    finally:
        if temp_csv.exists():
            temp_csv.unlink()
