# Notes de Recherche et d'Audit des Modèles (Jalon 1)

Ce document consigne les informations techniques issues de l'audit statique des modèles pré-entraînés avant tout chargement ou intégration.

---

## 1. Modèle Étage 1 : NIDS-CatBoost
- **Dépôt source** : `pop123ux/pcap-ml-traffic-classifier` (Hugging Face)
- **Fichiers** : `À VÉRIFIER`
- **Licence** : `À VÉRIFIER`
- **Type de sortie** : Binaire (Bénin vs Attaque)
- **Features d'entrée (ordre exact)** : `À VÉRIFIER`

---

## 2. Modèle Étage 1 : XGBoost (+ Autoencodeur)
- **Dépôt source** : `ScriptedLines404/Network-Intrusion-Detection-System-using-Deep-Learning` (GitHub)
- **Fichiers** : `À VÉRIFIER`
- **Licence** : `À VÉRIFIER`
- **Dépendance Autoencodeur** : `À VÉRIFIER` (Prend-il les features brutes ou les représentations latentes de l'autoencodeur ?)
- **Features d'entrée** : `À VÉRIFIER`

---

## 3. Modèle Étage 2 : CNN-1D
- **Dépôt source** : `saidimn/ids-cnn-cicids2017` (Hugging Face)
- **Fichiers** : `cnn1d_attacks_only.pth`, `scaler.pkl`
- **Licence** : `À VÉRIFIER`
- **Type de fichier .pth** : `À VÉRIFIER` (State dict ou `nn.Module` complet ?)
- **Nombre et ordre exact des 14 classes** : `À VÉRIFIER`
- **Scaler** : MinMax ou StandardScaler ? (Inspection avec `pickletools` sans exécution non vérifiée)

---

## 4. Kitsune (Branche Anomalies)
- **Dépôt source** : `ymirsky/Kitsune-py` (GitHub)
- **Fichiers** : AfterImage (extraction Scapy/C) + KitNET (autoencodeurs)
- **Compatibilité Python** : Conçu pour Python 3.6, adaptation nécessaire pour Python moderne ou bascule sur Plan B (`KitNET-py` pur).
