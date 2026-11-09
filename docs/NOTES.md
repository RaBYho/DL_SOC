# Notes de Recherche et d'Audit des Modèles (Jalon 1)

Ce document consigne les informations techniques issues de l'audit statique et de l'inspection physique des modèles téléchargés dans `models/`.

---

## 1. Modèle Étage 1 : NIDS-CatBoost (Détecteur principal)
- **Dépôt source** : `pop123ux/pcap-ml-traffic-classifier` (Hugging Face)
- **Fichier local** : `models/cicids_catboost.cbm` (591 Ko)
- **Fichier de métadonnées** : `models/catboost_feature_names.json`
- **Features d'entrée** : **76 colonnes de flux CICIDS2017** (extraites par CICFlowMeter).
- **Format** : Binaire CatBoost natif. Chargement sécurisé sans `pickle` :
  ```python
  from catboost import CatBoostClassifier
  model = CatBoostClassifier()
  model.load_model("models/cicids_catboost.cbm")
  ```

---

## 2. Modèle Étage 1 : NIDS-XGBoost AegisAI (Second avis)
- **Dépôt source** : `csperera/aegis-ai` (GitHub)
- **Fichiers locaux** :
  - `models/xgb_model.json` (1.7 Mo, JSON natif XGBoost)
  - `models/xgb_feature_names.json` (30 features clés)
  - `models/xgb_scaler.pkl` (StandardScaler fitted sur 30 features)
- **Features d'entrée (30 colonnes ordonnées)** :
  `Flow Duration`, `Fwd IAT Total`, `Bwd IAT Total`, `Flow Bytes/s`, `Fwd IAT Max`, `Flow IAT Max`, `Idle Max`, `Idle Mean`, `Idle Min`, `Fwd Header Length.1`, `Fwd Header Length`, `Bwd IAT Max`, `Fwd IAT Std`, `Fwd IAT Mean`, `Bwd IAT Mean`, `Fwd IAT Min`, `Bwd IAT Min`, `Flow IAT Std`, `Bwd IAT Std`, `Idle Std`, `Flow IAT Mean`, `Flow IAT Min`, `Total Length of Bwd Packets`, `Subflow Bwd Bytes`, `Packet Length Variance`, `Bwd Header Length`, `min_seg_size_forward`, `Active Max`, `Active Mean`, `Active Min`.
- **Chargement** :
  ```python
  import xgboost as xgb
  model = xgb.XGBClassifier()
  model.load_model("models/xgb_model.json")
  ```

---

## 3. Modèle Étage 2 : CNN-1D PyTorch (Classification fine - 14 classes)
- **Dépôt source** : `saidimn/ids-cnn-cicids2017` (Hugging Face)
- **Fichiers locaux** :
  - `models/cnn1d_attacks_only.pth` (1.9 Mo, state_dict PyTorch)
  - `models/cnn_scaler.pkl` (StandardScaler fitted sur 78 features)
- **Features d'entrée** : **78 features** (vérifié via `n_features_in_ = 0x4E = 78`).
- **Architecture PyTorch exacte (rétro-ingénierie statique)** :
  ```python
  import torch.nn as nn

  class AttackCNN1D(nn.Module):
      def __init__(self, num_classes=14):
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

      def forward(self, x):
          # x shape: (batch_size, 1, 78)
          x = self.features(x)
          return self.classifier(x)
  ```
- **Sortie** : 14 classes d'attaques CICIDS2017.

---

## 4. Kitsune (Branche Anomalies Non-Supervisée)
- **Dépôt source** : `ymirsky/Kitsune-py` (GitHub)
- **Composants** : `AfterImage` (Scapy L3/L4) + `KitNET` (Autoencodeurs).
- **Statut** : Prêt pour le Jalon 3.
