"""Module de normalisation et d'alignement des variables réseau (features)."""

from typing import Final, Sequence
import numpy as np
import pandas as pd

# Colonnes de métadonnées réseau à préserver pour l'alignement avec Kitsune
NETWORK_METADATA_COLUMNS: Final[tuple[str, ...]] = (
    "Flow ID",
    "Source IP",
    "Destination IP",
    "Source Port",
    "Destination Port",
    "Protocol",
    "Timestamp",
)


def align(
    df: pd.DataFrame, expected: Sequence[str], fill_na: float = 0.0
) -> pd.DataFrame:
    """Nettoie, filtre et réordonne un DataFrame selon les variables attendues.

    Écarte automatiquement les colonnes non sollicitées (dont les métadonnées réseau),
    gère les valeurs infinies/NaN et garantit l'immutabilité du DataFrame d'entrée.

    Args:
        df: DataFrame contenant les flux réseau bruts ou traités.
        expected: Séquence ordonnée des noms de colonnes requis par le modèle.
        fill_na: Valeur d'imputation pour les données manquantes ou infinies.

    Returns:
        pd.DataFrame: Nouveau DataFrame strictement aligné sur les variables attendues.

    Raises:
        ValueError: Si une colonne attendue est absente du DataFrame source.
    """
    # Copie locale pour garantir l'immutabilité
    working_df = df.copy()

    # Normalisation des noms de colonnes (suppression des espaces parasites)
    working_df.columns = working_df.columns.str.strip()

    # Vérification de l'exhaustivité des colonnes attendues
    available_cols = set(working_df.columns)
    for col in expected:
        if col not in available_cols:
            raise ValueError(f"Colonne manquante : '{col}'")

    # Sélection stricte dans l'ordre attendu
    aligned_df = working_df.loc[:, list(expected)]

    # Remplacement des valeurs infinies par NaN puis imputation
    aligned_df = aligned_df.replace([np.inf, -np.inf], np.nan)
    aligned_df = aligned_df.fillna(fill_na)

    return aligned_df
