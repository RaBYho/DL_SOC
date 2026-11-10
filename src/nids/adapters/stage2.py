"""Adaptateur d'inférence pour le classifieur fine-grained DNN-1D (Étage 2)."""

import json
import warnings
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.exceptions import InconsistentVersionWarning
import torch
import torch.nn as nn

from nids.features import align
from nids.labels import ATTACK_CLASSES


class AttackCNN1D(nn.Module):
    """Architecture PyTorch 1D-DNN pour la classification des 14 types d'attaques."""

    def __init__(self, num_classes: int = 14) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv1d(1, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Conv1d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Dropout(0.2),
            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Conv1d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Dropout(0.2),
            nn.Conv1d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Conv1d(256, 256, kernel_size=3, padding=1),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.4),
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Passe avant du DNN-1D. Shape d'entrée: (batch_size, 1, n_features)."""
        x = self.features(x)
        return self.classifier(x)


class CnnStage2:
    """Adaptateur pour le modèle PyTorch DNN-1D de l'Étage 2."""

    name: str = "DnnStage2"

    def __init__(
        self,
        model_path: Path | str = "models/cnn1d_attacks_only.pth",
        scaler_path: Path | str = "models/cnn_scaler.pkl",
        features_path: Path | str = "models/cnn_feature_names.json",
    ) -> None:
        self.classes: list[str] = list(ATTACK_CLASSES)

        # Chargement de la liste des variables attendues
        with open(features_path) as f:
            self.expected_features: list[str] = json.load(f)

        # Chargement du scaler avec suppression de l'avertissement de version mineure
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
            self.scaler = joblib.load(str(scaler_path))

        # Initialisation et chargement des poids du réseau de neurones
        self.model = AttackCNN1D(num_classes=len(self.classes))
        state_dict = torch.load(
            str(model_path),
            map_location=torch.device("cpu"),
            weights_only=True,
        )
        self.model.load_state_dict(state_dict)
        self.model.eval()

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        """Calcule la distribution de probabilités sur les 14 classes d'attaques."""
        if len(df) == 0:
            return np.empty((0, len(self.classes)), dtype=float)

        aligned = align(df, self.expected_features)
        scaled = self.scaler.transform(aligned.values)

        # Reshape (n_samples, 1, n_features) pour Conv1d
        tensor_in = torch.from_numpy(scaled).float().unsqueeze(1)

        with torch.no_grad():
            logits = self.model(tensor_in)
            probas = torch.softmax(logits, dim=1).cpu().numpy()

        return probas.astype(float)


# Alias pour nommage DNN
DnnStage2 = CnnStage2

