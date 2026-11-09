"""Protocoles et interfaces des adaptateurs de modèles NIDS."""

from typing import Protocol, runtime_checkable
import numpy as np
import pandas as pd


@runtime_checkable
class Stage1Model(Protocol):
    """Protocole pour les modèles de l'Étage 1 (détection binaire)."""

    name: str

    def score(self, df: pd.DataFrame) -> np.ndarray:
        """Calcule la probabilité d'attaque pour chaque flux.

        Args:
            df: DataFrame contenant les flux réseau à évaluer.

        Returns:
            np.ndarray: Vecteur 1D de probabilités dans [0.0, 1.0], shape (n,).
        """
        ...


@runtime_checkable
class Stage2Model(Protocol):
    """Protocole pour les modèles de l'Étage 2 (classification fine multiclasse)."""

    name: str
    classes: list[str]

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        """Calcule la distribution de probabilités sur les classes d'attaques.

        Args:
            df: DataFrame contenant les flux suspects à catégoriser.

        Returns:
            np.ndarray: Matrice 2D de forme (n, nb_classes), chaque ligne sommant à 1.
        """
        ...


@runtime_checkable
class KitsuneModel(Protocol):
    """Protocole pour le détecteur d'anomalies non-supervisé Kitsune."""

    name: str

    def score(self, df: pd.DataFrame) -> np.ndarray:
        """Calcule le score d'erreur de reconstruction RMSE pour chaque flux.

        Args:
            df: DataFrame contenant les flux réseau à évaluer.

        Returns:
            np.ndarray: Vecteur 1D de scores RMSE positifs, shape (n,).
        """
        ...
