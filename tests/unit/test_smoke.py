"""Test de fumée (smoke test) pour valider l'importation du package nids."""

import nids


def test_package_import():
    """Vérifie que le package nids est correctement importable et versionné."""
    assert nids.__version__ == "0.1.0"
