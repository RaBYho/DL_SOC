"""Définition canonique des étiquettes et constantes de classification NIDS."""

from typing import Final

# Étiquettes de base
BENIGN: Final[str] = "BENIGN"
ANOMALY_UNKNOWN: Final[str] = "ANOMALY_UNKNOWN"
SUSPECT_UNCERTAIN: Final[str] = "SUSPECT_UNCERTAIN"
UNKNOWN_ATTACK_LIKELY: Final[str] = "UNKNOWN_ATTACK_LIKELY"

# 14 classes d'attaques officielles de CICIDS2017 (Étage 2)
ATTACK_CLASSES: Final[tuple[str, ...]] = (
    "Bot",
    "DDoS",
    "DoS GoldenEye",
    "DoS Hulk",
    "DoS Slowhttptest",
    "DoS slowloris",
    "FTP-Patator",
    "Heartbleed",
    "Infiltration",
    "PortScan",
    "SSH-Patator",
    "Web Attack – Brute Force",
    "Web Attack – Sql Injection",
    "Web Attack – XSS",
)

ALL_LABELS: Final[frozenset[str]] = frozenset(
    {BENIGN, ANOMALY_UNKNOWN, SUSPECT_UNCERTAIN, UNKNOWN_ATTACK_LIKELY, *ATTACK_CLASSES}
)

# Table de normalisation tolérante (minuscules et tirets variés)
_NORMALIZATION_MAP: dict[str, str] = {
    "benign": BENIGN,
    "bot": "Bot",
    "ddos": "DDoS",
    "dos goldeneye": "DoS GoldenEye",
    "dos hulk": "DoS Hulk",
    "dos slowhttptest": "DoS Slowhttptest",
    "dos slowloris": "DoS slowloris",
    "ftp-patator": "FTP-Patator",
    "heartbleed": "Heartbleed",
    "infiltration": "Infiltration",
    "portscan": "PortScan",
    "ssh-patator": "SSH-Patator",
    "web attack – brute force": "Web Attack – Brute Force",
    "web attack - brute force": "Web Attack – Brute Force",
    "web attack – sql injection": "Web Attack – Sql Injection",
    "web attack - sql injection": "Web Attack – Sql Injection",
    "web attack – xss": "Web Attack – XSS",
    "web attack - xss": "Web Attack – XSS",
    "anomaly_unknown": ANOMALY_UNKNOWN,
    "suspect_uncertain": SUSPECT_UNCERTAIN,
    "unknown_attack_likely": UNKNOWN_ATTACK_LIKELY,
}


def normalize_label(raw_label: str) -> str:
    """Normalise une étiquette brute issue des datasets en étiquette canonique."""
    cleaned = raw_label.strip()
    # Si déjà strictement canonique
    if cleaned in ALL_LABELS:
        return cleaned

    lowered = cleaned.lower()
    if lowered in _NORMALIZATION_MAP:
        return _NORMALIZATION_MAP[lowered]

    raise ValueError(f"Étiquette réseau inconnue : '{raw_label}'")
