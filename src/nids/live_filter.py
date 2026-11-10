"""Pré-filtrage déterministe en direct pour éliminer le bruit et les faux positifs triviaux."""

import time
from typing import Any
import numpy as np
import pandas as pd

from nids.flow_alignment import compute_canonical_5tuple_key


class SessionTracker:
    """Table d'état des sessions TCP actives avec TTL (120s par défaut)."""

    def __init__(self, ttl_sec: float = 120.0) -> None:
        self.ttl_sec = ttl_sec
        self.sessions: dict[str, float] = {}

    def _extract_time(self, df: pd.DataFrame, current_time: float | None) -> float:
        """Détermine l'horodatage de référence du batch (PCAP ou système)."""
        if current_time is not None:
            return current_time
        if "Timestamp" in df.columns:
            ts = df["Timestamp"]
            if pd.api.types.is_numeric_dtype(ts):
                return float(ts.max())
            dt = pd.to_datetime(ts, errors="coerce").dropna()
            if len(dt) > 0:
                return float(dt.astype("datetime64[ns]").astype(np.int64).max() / 1e9)
        return time.time()

    def update(self, df: pd.DataFrame, current_time: float | None = None) -> None:
        """Enregistre les sessions TCP ayant émis un drapeau SYN."""
        if len(df) == 0:
            return
        now = self._extract_time(df, current_time)
        cutoff = now - self.ttl_sec
        self.sessions = {k: t for k, t in self.sessions.items() if t >= cutoff}

        syn = pd.to_numeric(df.get("SYN Flag Count", 0), errors="coerce").fillna(0)
        syn_mask = syn > 0
        if not syn_mask.any():
            return
        try:
            keys = compute_canonical_5tuple_key(df.loc[syn_mask])
            for k in keys:
                self.sessions[k] = now
        except ValueError:
            pass

    def get_active_mask(self, df: pd.DataFrame, current_time: float | None = None) -> pd.Series:
        """Renvoie un masque booléen indiquant si chaque flux appartient à une session active."""
        if len(df) == 0 or not self.sessions:
            return pd.Series(False, index=df.index)
        now = self._extract_time(df, current_time)
        cutoff = now - self.ttl_sec
        active = {k for k, t in self.sessions.items() if t >= cutoff}
        if not active:
            return pd.Series(False, index=df.index)
        try:
            return compute_canonical_5tuple_key(df).isin(active)
        except ValueError:
            return pd.Series(False, index=df.index)


def _is_multicast_or_broadcast(df: pd.DataFrame, ignored_ports: set[int]) -> pd.Series:
    """Détecte les flux multicast, broadcast ou ports de découverte de service."""
    dst_ip = df.get("Destination IP", pd.Series("", index=df.index)).astype(str)
    src_p = pd.to_numeric(df.get("Source Port", 0), errors="coerce").fillna(0).astype(int)
    dst_p = pd.to_numeric(df.get("Destination Port", 0), errors="coerce").fillna(0).astype(int)

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


def _is_micro_dead_orphan(
    df: pd.DataFrame, min_packets: int, session_tracker: SessionTracker | None = None
) -> pd.Series:
    """Détecte les flux orphelins (<= min_packets sans SYN) hors sessions actives."""
    fwd_pkts = pd.to_numeric(df.get("Total Fwd Packets", 0), errors="coerce").fillna(0)
    bwd_pkts = pd.to_numeric(df.get("Total Backward Packets", 0), errors="coerce").fillna(0)
    syn_flags = pd.to_numeric(df.get("SYN Flag Count", 0), errors="coerce").fillna(0)

    total_pkts = fwd_pkts + bwd_pkts
    is_orphan = (total_pkts < min_packets) & (syn_flags == 0)

    if session_tracker is not None:
        is_active = session_tracker.get_active_mask(df)
        return is_orphan & (~is_active)

    return is_orphan


def _build_ignore_mask(
    df: pd.DataFrame,
    cfg: dict[str, Any],
    allow_loopback: bool = False,
    session_tracker: SessionTracker | None = None,
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
    mask_orphan = _is_micro_dead_orphan(df, min_packets, session_tracker=session_tracker)
    return mask_mcast | _is_whitelisted(df, whitelisted_ips) | mask_orphan


def pre_filter_flows(
    df: pd.DataFrame,
    config: dict[str, Any],
    allow_loopback: bool | None = None,
    session_tracker: SessionTracker | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Sépare les flux à analyser de ceux écartés par pré-filtrage déterministe."""
    if len(df) == 0:
        return df.copy(), df.copy()

    cfg = config.get("pre_filter", {})
    if allow_loopback is None:
        allow_loopback = bool(cfg.get("allow_loopback", False))

    if session_tracker is not None:
        session_tracker.update(df)

    should_ignore = _build_ignore_mask(
        df, cfg, allow_loopback=allow_loopback, session_tracker=session_tracker
    )
    return df.loc[~should_ignore].copy(), df.loc[should_ignore].copy()
