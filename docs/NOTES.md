# Notes de Recherche et d'Audit des Modèles (Jalon 1)

Ce document consigne les informations techniques issues de l'audit statique des modèles pré-entraînés avant tout chargement ou intégration.

---

## 1. Modèle Étage 1 : NIDS-CatBoost (Détecteur principal)
- **Dépôt source** : `pop123ux/pcap-ml-traffic-classifier` (Hugging Face)
- **Fichiers & Tailles** :
  - `cicids_catboost.cbm` : **604 kB** (Poids du modèle au format binaire CatBoost natif)
  - `cicids_catboost.json` : **2.17 MB** (Export JSON de la structure et métadonnées)
- **Licence** : Open Source (Apache 2.0)
- **Type de sortie** : Binaire (Bénin vs Malveillant / Attaques CICIDS2017)
- **Chargement** : Direct via l'API CatBoost sans passer par `pickle` :
  ```python
  from catboost import CatBoostClassifier
  model = CatBoostClassifier()
  model.load_model("models/cicids_catboost.cbm")
  ```
- **Statut** : ✅ Validé et prêt. Très léger (< 1 Mo de téléchargement).

---

## 2. Modèle Étage 1 : NIDS-XGBoost AegisAI (Second avis sélectionné)
- **Dépôt source** : `csperera/aegis-ai` (GitHub)
- **Fichiers disponibles dans `models/`** :
  - `xgb_model.json` : Modèle XGBoost natif au format JSON standard
  - `feature_names.json` : Liste ordonnée exacte des colonnes attendues
  - `scaler.pkl` : Objet `StandardScaler` fitted
- **Dataset d'entraînement** : CICIDS2017 complet (2,83 millions de flux réseau).
- **Performances documentées** : AUC 0.9992, Rappel attaques 99 %, Précision 95 %.
- **Format sécurisé** : Modèle sérialisé en `.json` standard d'XGBoost (aucun risque d'exécution de code malveillant).
- **Statut** : ✅ Retenu en remplacement du dépôt indisponible de ScriptedLines404.

---

## 3. Modèle Étage 2 : CNN-1D (Classification fine - 14 classes)
- **Dépôt source** : `saidimn/ids-cnn-cicids2017` (Hugging Face)
- **Fichiers & Tailles** :
  - `cnn1d_attacks_only.pth` : **1.97 MB** (Poids PyTorch du réseau 1D-CNN)
  - `scaler.pkl` : **2.46 kB** (Scikit-Learn StandardScaler)
- **Licence** : MIT
- **Type de modèle** : Conv1D pour flux tabulaires. Entraîné spécifiquement sur les flux d'attaques (**14 classes d'attaques**, le trafic bénin étant déjà filtré par l'Étage 1).
- **Format du .pth** : State dictionary (`state_dict`). Doit être chargé de manière sécurisée :
  ```python
  import torch
  state = torch.load("models/cnn1d_attacks_only.pth", weights_only=True)
  ```
- **Classes cibles (14 attaques CICIDS2017)** :
  1. `Bot`
  2. `DDoS`
  3. `DoS GoldenEye`
  4. `DoS Hulk`
  5. `DoS Slowhttptest`
  6. `DoS slowloris`
  7. `FTP-Patator`
  8. `Heartbleed`
  9. `Infiltration`
  10. `PortScan`
  11. `SSH-Patator`
  12. `Web Attack – Brute Force`
  13. `Web Attack – Sql Injection`
  14. `Web Attack – XSS`
- **Statut** : ✅ Validé. Poids ultra-légers (< 2 Mo au total).

---

## 4. Kitsune (Branche Anomalies Non-Supervisée)
- **Dépôt source** : `ymirsky/Kitsune-py` (GitHub)
- **Composants** :
  - `AfterImage` : Extracteur statistique incrémental 1D par paquets (Scapy).
  - `KitNET` : Réseau d'autoencodeurs (détecteur d'anomalies non supervisé calculant un RMSE par paquet).
- **Périodes de grâce** : `FMgrace` et `ADgrace` (généralement 50 000 paquets en production, réduits à 500 pour les tests locaux sur `mini.pcap`).
- **Compatibilité Python** : Dépendances isolées dans `envs/kitsune.txt` (Plan B documenté : `KitNET-py` pur si blocage Scapy sous Python 3.12).
- **Statut** : ✅ Validé.
