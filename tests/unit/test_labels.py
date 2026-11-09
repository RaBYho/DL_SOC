"""Tests unitaires pour la gestion et normalisation des étiquettes (labels)."""

import pytest

from nids.labels import (
    ALL_LABELS,
    ATTACK_CLASSES,
    BENIGN,
    ANOMALY_UNKNOWN,
    SUSPECT_UNCERTAIN,
    UNKNOWN_ATTACK_LIKELY,
    normalize_label,
)


def test_constants_count_and_types():
    """Vérifie le compte et l'unicité des constantes d'étiquettes."""
    assert BENIGN == "BENIGN"
    assert ANOMALY_UNKNOWN == "ANOMALY_UNKNOWN"
    assert SUSPECT_UNCERTAIN == "SUSPECT_UNCERTAIN"
    assert UNKNOWN_ATTACK_LIKELY == "UNKNOWN_ATTACK_LIKELY"
    assert len(ATTACK_CLASSES) == 14
    assert len(set(ATTACK_CLASSES)) == 14
    assert len(ALL_LABELS) == 14 + 4  # 14 attaques + 4 états système


def test_normalize_label_benign():
    """Vérifie la normalisation des variantes de bénin."""
    assert normalize_label("BENIGN") == BENIGN
    assert normalize_label("benign") == BENIGN
    assert normalize_label("  BENIGN  ") == BENIGN
    assert normalize_label("Benign") == BENIGN


@pytest.mark.parametrize(
    "raw_input,expected",
    [
        ("DDoS", "DDoS"),
        ("ddos", "DDoS"),
        ("PortScan", "PortScan"),
        ("portscan", "PortScan"),
        ("Bot", "Bot"),
        ("FTP-Patator", "FTP-Patator"),
        ("SSH-Patator", "SSH-Patator"),
        ("Web Attack – Brute Force", "Web Attack – Brute Force"),
        ("Web Attack - Brute Force", "Web Attack – Brute Force"),
    ],
)
def test_normalize_attack_labels(raw_input: str, expected: str):
    """Vérifie la normalisation tolérante des noms d'attaques."""
    assert normalize_label(raw_input) == expected


def test_normalize_unknown_label_raises():
    """Vérifie qu'une étiquette invalide lève une ValueError explicite."""
    with pytest.raises(ValueError, match="Étiquette réseau inconnue"):
        normalize_label("AlienAttack_999")
