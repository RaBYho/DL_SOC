# Notes de Recherche et d'Audit des Modèles (Jalon 1)

Ce document consigne les informations techniques issues de l'audit statique des modèles pré-entraînés avant tout chargement ou intégration.

---

## 1. Modèle Étage 1 : NIDS-CatBoost
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

## 2. Modèle Étage 1 (Second avis) : XGBoost ScriptedLines404
- **Dépôt source visé** : `ScriptedLines404/Network-Intrusion-Detection-System-using-Deep-Learning` (GitHub)
- **Statut de l'audit** : ⚠️ Dépôt public introuvable / supprimé de GitHub.
- **Décision d'architecture (conforme au plan)** :
  - Ce modèle est **écarté**. L'Étage 1 repose sur le modèle `NIDS-CatBoost` (pop123ux) qui est complet, binaire, très rapide et parfaitement validé.
  - Si un second avis est nécessaire lors des phases ultérieures, nous pourrons entraîner un `XGBoost` léger directement sur le split de train du jeu de données.

---

## 3. Modèle Étage 2 : CNN-1D (14 classes)
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
- **Périodes de grâce** : `FMgrace` et `ADgrace` (généralement 50 000 paquets en production, réduits à 500-1 000 pour les tests locaux sur `mini.pcap`).
- **Compatibilité Python** : Nécessite un environnement dédié (`envs/kitsune.txt`) ou l'utilisation du Plan B (`KitNET-py` pur) si l'extraction Scapy sous Python 3.12 pose des incompatibilités de types NumPy dépréciés (`np.float`).
- **Statut** : ✅ Validé.
