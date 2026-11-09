"""Tests unitaires pour l'alignement et le nettoyage des variables (features.py)."""

import numpy as np
import pandas as pd
import pytest

from nids.features import align, NETWORK_METADATA_COLUMNS


def test_align_reorders_and_filters_extra_columns():
    """Vérifie le réordonnancement strict et l'exclusion des colonnes superflues."""
    df = pd.DataFrame({
        "Flow Duration": [100, 200],
        "Source IP": ["192.168.1.1", "192.168.1.2"],
        "Total Fwd Packets": [5, 10],
        "Extra Column": [999, 888],
    })
    expected = ["Total Fwd Packets", "Flow Duration"]

    aligned = align(df, expected)

    assert list(aligned.columns) == expected
    assert aligned["Total Fwd Packets"].tolist() == [5, 10]
    assert aligned["Flow Duration"].tolist() == [100, 200]
    assert "Source IP" not in aligned.columns
    assert "Extra Column" not in aligned.columns


def test_align_missing_expected_column_raises():
    """Vérifie qu'une colonne attendue absente lève une ValueError explicite."""
    df = pd.DataFrame({"Flow Duration": [100]})
    expected = ["Flow Duration", "NonExistentColumn"]

    with pytest.raises(ValueError, match="Colonne manquante : 'NonExistentColumn'"):
        align(df, expected)


def test_align_handles_whitespace_in_column_names():
    """Vérifie la tolérance aux espaces parasites dans les noms de colonnes."""
    df = pd.DataFrame({
        " Flow Duration ": [150],
        " Total Length of Fwd Packets": [300],
    })
    expected = ["Flow Duration", "Total Length of Fwd Packets"]

    aligned = align(df, expected)
    assert list(aligned.columns) == expected
    assert aligned["Flow Duration"].iloc[0] == 150


def test_align_handles_infinite_and_nan_values():
    """Vérifie le remplacement d'inf et NaN par 0.0 par défaut."""
    df = pd.DataFrame({
        "colA": [1.0, np.inf, -np.inf, np.nan],
        "colB": [np.nan, 2.0, 3.0, 4.0],
    })
    expected = ["colA", "colB"]

    aligned = align(df, expected)

    assert not aligned.isna().any().any()
    assert not np.isinf(aligned.values).any()
    assert aligned["colA"].tolist() == [1.0, 0.0, 0.0, 0.0]
    assert aligned["colB"].tolist() == [0.0, 2.0, 3.0, 4.0]


def test_align_does_not_mutate_input_dataframe():
    """Vérifie l'immutabilité du DataFrame d'entrée."""
    original_data = {"Flow Duration": [100, np.inf], "Extra": ["A", "B"]}
    df = pd.DataFrame(original_data)
    df_copy = df.copy(deep=True)

    expected = ["Flow Duration"]
    _ = align(df, expected)

    pd.testing.assert_frame_equal(df, df_copy)


def test_align_empty_dataframe():
    """Vérifie le bon comportement sur un DataFrame vide."""
    df = pd.DataFrame(columns=["Flow Duration", "Source IP"])
    expected = ["Flow Duration"]

    aligned = align(df, expected)
    assert len(aligned) == 0
    assert list(aligned.columns) == expected
