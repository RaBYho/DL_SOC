"""Module d'alignement vectorisé des scores d'anomalies (paquets) avec les flux réseau."""

from typing import Literal
import numpy as np
import pandas as pd


def compute_canonical_5tuple_key(df: pd.DataFrame) -> pd.Series:
    """Calcule une clé canonique de quintuplet bidirectionnelle 100 % vectorisée.

    Garantit que les paquets aller (A -> B) et retour (B -> A) partagent
    strictement la même clé sans aucune boucle for.

    Args:
        df: DataFrame contenant les colonnes d'adresses, ports et protocole.

    Returns:
        pd.Series: Clé canonique formatée min(epA, epB)<->max(epA, epB)/proto.
    """
    col_map = {c.strip().lower(): c for c in df.columns}

    # Détection tolérante des colonnes (format flux ou format paquets)
    src_ip_col = col_map.get("source ip", col_map.get("src_ip"))
    dst_ip_col = col_map.get("destination ip", col_map.get("dst_ip"))
    src_port_col = col_map.get("source port", col_map.get("src_port"))
    dst_port_col = col_map.get("destination port", col_map.get("dst_port"))
    proto_col = col_map.get("protocol", col_map.get("proto"))

    if not all([src_ip_col, dst_ip_col, src_port_col, dst_port_col, proto_col]):
        raise ValueError("Colonnes du quintuplet réseau incomplètes pour le calcul de la clé.")

    # Concaténation vectorisée des points de terminaison IP:Port
    ep_a = df[src_ip_col].astype(str) + ":" + df[src_port_col].astype(str)
    ep_b = df[dst_ip_col].astype(str) + ":" + df[dst_port_col].astype(str)
    proto = df[proto_col].astype(str)

    # Ordonnancement lexicographique bidirectionnel min / max
    is_a_le_b = ep_a <= ep_b
    ep_min = np.where(is_a_le_b, ep_a, ep_b)
    ep_max = np.where(is_a_le_b, ep_b, ep_a)

    return pd.Series(ep_min + "<->" + ep_max + "/" + proto, index=df.index, name="canonical_key")


def _prepare_flow_intervals(flows: pd.DataFrame, time_tolerance_sec: float) -> pd.DataFrame:
    """Prépare les fenêtres temporelles des flux [début, fin]."""
    flows_meta = pd.DataFrame(index=flows.index)
    flows_meta["flow_idx"] = flows.index
    flows_meta["canonical_key"] = compute_canonical_5tuple_key(flows)

    start_time = pd.to_datetime(flows["Timestamp"])
    duration_sec = pd.to_numeric(flows["Flow Duration"], errors="coerce").fillna(0.0) / 1e6
    end_time = start_time + pd.to_timedelta(duration_sec, unit="s")

    tol = pd.to_timedelta(time_tolerance_sec, unit="s")
    flows_meta["win_start"] = start_time - tol
    flows_meta["win_end"] = end_time + tol

    return flows_meta


def aggregate_scores(
    flows: pd.DataFrame,
    packets: pd.DataFrame,
    rule: Literal["max", "mean"] = "max",
    time_tolerance_sec: float = 1.0,
) -> pd.Series:
    """Agrège vectoriellement les scores de paquets par flux réseau sans boucle Python.

    Args:
        flows: DataFrame des flux réseau (avec Timestamp, Flow Duration et quintuplet).
        packets: DataFrame des paquets scorés (avec timestamp, quintuplet, rmse_score).
        rule: Règle d'agrégation mathématique ("max" ou "mean").
        time_tolerance_sec: Marge de tolérance temporelle aux bornes en secondes.

    Returns:
        pd.Series: Score d'anomalie agrégé pour chaque flux (NaN si aucun paquet associé).
    """
    if len(flows) == 0:
        return pd.Series(dtype=float, name="kitsune_score")

    if len(packets) == 0:
        return pd.Series(np.nan, index=flows.index, name="kitsune_score")

    flows_meta = _prepare_flow_intervals(flows, time_tolerance_sec)

    # Filtrage des paquets en période d'apprentissage
    if "is_grace_period" in packets.columns:
        valid_pkts = packets[~packets["is_grace_period"].astype(bool)].copy()
    else:
        valid_pkts = packets.copy()

    valid_pkts["canonical_key"] = compute_canonical_5tuple_key(valid_pkts)
    valid_pkts["pkt_time"] = pd.to_datetime(valid_pkts["timestamp"])

    # Jointure vectorisée sur le quintuplet canonique
    merged = pd.merge(
        flows_meta,
        valid_pkts[["canonical_key", "pkt_time", "rmse_score"]],
        on="canonical_key",
        how="inner",
    )

    if len(merged) == 0:
        return pd.Series(np.nan, index=flows.index, name="kitsune_score")

    # Filtrage temporel vectorisé
    in_window = (merged["pkt_time"] >= merged["win_start"]) & (
        merged["pkt_time"] <= merged["win_end"]
    )
    matched = merged[in_window]

    if len(matched) == 0:
        return pd.Series(np.nan, index=flows.index, name="kitsune_score")

    # Agrégation par identifiant de flux
    if rule == "mean":
        agg_scores = matched.groupby("flow_idx")["rmse_score"].mean()
    else:
        agg_scores = matched.groupby("flow_idx")["rmse_score"].max()

    return agg_scores.reindex(flows.index).rename("kitsune_score")
