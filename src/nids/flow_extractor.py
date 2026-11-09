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


def convert_pcap_to_flows(
    pcap_path: Path | str,
    output_csv: Path | str | None = None,
    mapping_path: Path | str = "configs/cicflowmeter_mapping.yaml",
) -> pd.DataFrame:
    """Convertit un PCAP en DataFrame normalisé compatible avec le pipeline ML."""
    pcap = Path(pcap_path)
    with open(mapping_path) as f:
        mapping = yaml.safe_load(f)

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        temp_csv = Path(tmp.name)

    try:
        _run_cicflowmeter_on_pcap(pcap, temp_csv)
        if not temp_csv.exists() or temp_csv.stat().st_size == 0:
            return pd.DataFrame()
        raw_df = pd.read_csv(temp_csv)
        if len(raw_df) == 0:
            return pd.DataFrame()
        norm_df = _normalize_flow_df(raw_df, mapping)
        if output_csv:
            out_p = Path(output_csv)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            norm_df.to_csv(out_p, index=False)
        return norm_df
    finally:
        if temp_csv.exists():
            temp_csv.unlink()
