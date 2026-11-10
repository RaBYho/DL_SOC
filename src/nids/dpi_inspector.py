"""Module d'inspection approfondie des paquets (DPI) pour le NIDS hybride."""

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any
from urllib.parse import unquote_to_bytes
import pandas as pd
from scapy.all import IP, IPv6, PcapReader, Raw, TCP, UDP
import yaml


@dataclass(frozen=True)
class DPIRule:
    """Règle DPI compilée pour détection par motif dans la charge utile."""

    rule_id: str
    attack_class: str
    confidence: float
    regexes: tuple[re.Pattern[bytes], ...]


def _compile_rule(raw_rule: dict[str, Any]) -> DPIRule:
    """Compile une règle brute issue du fichier YAML en expressions régulières d'octets."""
    rule_id = str(raw_rule.get("id", "UNKNOWN"))
    attack_class = str(raw_rule.get("attack_class", "Infiltration"))
    confidence = float(raw_rule.get("confidence", 1.0))
    patterns = raw_rule.get("patterns", [])
    compiled = []
    for pat in patterns:
        try:
            compiled.append(re.compile(pat.encode("utf-8"), re.IGNORECASE))
        except re.error:
            continue
    return DPIRule(rule_id, attack_class, confidence, tuple(compiled))


class DPIInspector:
    """Inspecteur de charge utile applicative basé sur des règles légères."""

    def __init__(self, config_path: Path | str = "configs/dpi_rules.yaml") -> None:
        self.config_path = Path(config_path)
        self.enabled: bool = False
        self.rules: list[DPIRule] = []
        if self.config_path.exists():
            with open(self.config_path) as f:
                cfg = yaml.safe_load(f) or {}
            self.enabled = bool(cfg.get("enabled", True))
            raw_rules = cfg.get("rules", [])
            self.rules = [_compile_rule(r) for r in raw_rules]

    def inspect_payload(self, payload: bytes) -> tuple[str, float] | None:
        """Vérifie si la charge utile brute correspond à l'une des règles DPI."""
        if not self.enabled or not payload:
            return None
        decoded = unquote_to_bytes(payload.replace(b"+", b" "))
        for rule in self.rules:
            for pattern in rule.regexes:
                if pattern.search(payload) or pattern.search(decoded):
                    return rule.attack_class, rule.confidence
        return None

    def _extract_packet_keys(self, pkt) -> list[str]:
        """Génère les clés Flow ID 5-tuples bidirectionnelles d'un paquet."""
        if not pkt.haslayer(IP) and not pkt.haslayer(IPv6):
            return []
        proto = 6 if pkt.haslayer(TCP) else (17 if pkt.haslayer(UDP) else 0)
        src = pkt[IP].src if pkt.haslayer(IP) else pkt[IPv6].src
        dst = pkt[IP].dst if pkt.haslayer(IP) else pkt[IPv6].dst
        sport = pkt[TCP].sport if pkt.haslayer(TCP) else (pkt[UDP].sport if pkt.haslayer(UDP) else 0)
        dport = pkt[TCP].dport if pkt.haslayer(TCP) else (pkt[UDP].dport if pkt.haslayer(UDP) else 0)
        k1 = f"{src}-{dst}-{sport}-{dport}-{proto}"
        k2 = f"{dst}-{src}-{dport}-{sport}-{proto}"
        return [k1, k2]

    def inspect_pcap(self, pcap_path: Path | str) -> dict[str, tuple[str, float]]:
        """Scanne un fichier PCAP et associe chaque anomalie DPI à ses clés de flux."""
        pcap_file = Path(pcap_path)
        if not self.enabled or not pcap_file.exists() or pcap_file.stat().st_size <= 24:
            return {}
        matches: dict[str, tuple[str, float]] = {}
        try:
            with PcapReader(str(pcap_file)) as reader:
                for pkt in reader:
                    if pkt.haslayer(Raw):
                        load = bytes(pkt[Raw].load)
                        if load.startswith((b"HTTP/1.", b"HTTP/2", b"HTTP/0.9")):
                            continue
                        hit = self.inspect_payload(load)
                        if hit is not None:
                            for key in self._extract_packet_keys(pkt):
                                matches[key] = hit
        except Exception:
            return matches
        return matches


def fuse_predictions_with_dpi(
    predictions_df: pd.DataFrame,
    flows_df: pd.DataFrame,
    dpi_matches: dict[str, tuple[str, float]],
) -> pd.DataFrame:
    """Fusionne les prédictions du modèle ML avec les correspondances déterministes DPI."""
    if not dpi_matches or len(flows_df) == 0:
        return predictions_df

    fused = predictions_df.copy()
    flow_ids = flows_df.get("Flow ID", pd.Series("", index=flows_df.index)).astype(str)

    for i, fid in enumerate(flow_ids):
        if fid in dpi_matches:
            attack_class, conf = dpi_matches[fid]
            fused.at[i, "verdict"] = attack_class
            fused.at[i, "confidence"] = max(float(fused.at[i, "confidence"]), conf)
            fused.at[i, "stage1_score"] = 1.0

    return fused
