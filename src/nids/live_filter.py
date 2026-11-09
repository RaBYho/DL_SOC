"""Pré-filtrage déterministe en direct pour éliminer le bruit et les faux positifs triviaux."""

from typing import Any
import pandas as pd


def _is_multicast_or_broadcast(df: pd.DataFrame, ignored_ports: set[int]) -> pd.Series:
    """Détecte les flux multicast, broadcast ou ports de découverte de service."""
    dst_ip = df.get("Destination IP", pd.Series("", index=df.index)).astype(str)
    src_p = pd.to_numeric(df.get("Source Port", 0), errors="coerce").fillna(0).astype(int)
    dst_p = pd.to_numeric(df.get("Destination Port", 0), errors="coerce").fillna(0).astype(int)

    # Plages multicast IPv4 (224.0.0.0/4), broadcast, et IPv6 (ff..)
    is_mcast_ip = (
        dst_ip.str.startswith(("224.", "225.", "239.", "ff", "FF"))
        | (dst_ip == "255.255.255.255")
    )
    is_ignored_port = src_p.isin(ignored_ports) | dst_p.isin(ignored_ports)

    return is_mcast_ip | is_ignored_port


def _is_whitelisted(df: pd.DataFrame, whitelisted_ips: set[str]) -> pd.Series:
    """Détecte les flux impliquant des adresses IP en liste blanche."""
    src_ip = df.get("Source IP", pd.Series("", index=df.index)).astype(str)
    dst_ip = df.get("Destination IP", pd.Series("", index=df.index)).astype(str)

    return src_ip.isin(whitelisted_ips) | dst_ip.isin(whitelisted_ips)


def _is_micro_dead_orphan(df: pd.DataFrame, min_packets: int) -> pd.Series:
    """Détecte les flux orphelins (<= min_packets sans drapeaux d'initiation SYN)."""
    fwd_pkts = pd.to_numeric(df.get("Total Fwd Packets", 0), errors="coerce").fillna(0)
    bwd_pkts = pd.to_numeric(df.get("Total Backward Packets", 0), errors="coerce").fillna(0)
    syn_flags = pd.to_numeric(df.get("SYN Flag Count", 0), errors="coerce").fillna(0)

    total_pkts = fwd_pkts + bwd_pkts
    # Flux micro-mort : peu de paquets et aucun SYN (les SYN scans sont donc conservés)
    return (total_pkts < min_packets) & (syn_flags == 0)


def _build_ignore_mask(
    df: pd.DataFrame, cfg: dict[str, Any], allow_loopback: bool = False
) -> pd.Series:
    """Construit le masque booléen d'exclusion à partir de la configuration."""
    ignored_ports = set(cfg.get("ignored_ports", [5353, 1900, 5355, 137, 138]))
    raw_whitelist = cfg.get("whitelisted_ips", ["127.0.0.1"])
    if allow_loopback:
        whitelisted_ips = set(ip for ip in raw_whitelist if not ip.startswith("127."))
    else:
        whitelisted_ips = set(raw_whitelist)
    min_packets = int(cfg.get("min_total_packets", 2))

    mask_mcast = (
        _is_multicast_or_broadcast(df, ignored_ports)
        if cfg.get("ignore_multicast_broadcast", True)
        else pd.Series(False, index=df.index)
    )
    return mask_mcast | _is_whitelisted(df, whitelisted_ips) | _is_micro_dead_orphan(df, min_packets)


def pre_filter_flows(
    df: pd.DataFrame, config: dict[str, Any], allow_loopback: bool | None = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Sépare les flux à analyser de ceux écartés par pré-filtrage déterministe."""
    if len(df) == 0:
        return df.copy(), df.copy()

    cfg = config.get("pre_filter", {})
    if allow_loopback is None:
        allow_loopback = bool(cfg.get("allow_loopback", False))

    should_ignore = _build_ignore_mask(df, cfg, allow_loopback=allow_loopback)
    return df.loc[~should_ignore].copy(), df.loc[should_ignore].copy()
