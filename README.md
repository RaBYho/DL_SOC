# DL_SOC - Système de Détection d'Intrusions Réseau (NIDS) par Deep Learning

DL_SOC est une solution de détection d'intrusions réseau (NIDS) combinant l'apprentissage profond (**Deep Learning PyTorch**) et l'analyse de flux réseau (**NFStream**) pour la détection en temps réel et l'aide à la décision en environnement **SOC (Security Operations Center)**.

Le système est entraîné et validé sur le jeu de données **CIC-IDS2017**, en respectant une méthodologie stricte pour éliminer le biais de fuite temporelle (*data leakage*).

---

## 🚀 Fonctionnalités Clés

* **Classification Multi-classes (DNN v4)** : Détection et identification précise parmi 12 classes :
  * Trafic sain : `BENIGN`
  * Attaques DoS / DDoS : `DDoS`, `DoS-GoldenEye`, `DoS-Hulk`, `DoS-Slowhttptest`, `DoS-slowloris`
  * Attaques Brute-force & Bots : `FTP-Patator`, `SSH-Patator`, `Bot`
  * Reconnaissance & Web : `PortScan`, `Scan-Vista`, `WebAttack`
* **Détection d'Anomalies Inconnues (Auto-encodeur)** : Modèle non supervisé entraîné uniquement sur le trafic sain (`BENIGN`) pour isoler les déviations statistiques inconnues (*0-day*).
* **Extraction temps réel / PCAP (NFStream)** : Analyse bidirectionnelle des flux réseau sans dépendre du payload applicatif chiffré (analyse statistique des flux, durées, volumes, paquets, drapeaux TCP).
* **Architecture Microservices / SOC** :
  * **Sonde réseau (`nids_sensor.py`)** : Collecteur passif ou rejeu de traces PCAP envoyant des lots de flux vers l'API.
  * **Moteur d'inférence (`nids_core.py`)** : Pré-traitements normalisés et scoring GPU/CPU par batchs.
  * **Serveur SOC (`nids_server.py`)** : API REST FastAPI sécurisée (clé API), persistance SQLite et métriques de détection.

---

## 📐 Architecture du Système

```
                    ┌────────────────────────┐
                    │      Fichiers PCAP     │
                    │   ou Trafic Réseau     │
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │     nids_sensor.py     │ (Sonde NFStream)
                    └───────────┬────────────┘
                                │ HTTP POST /ingest
                                │ Headers: x-api-key
                                ▼
┌────────────────────────────────────────────────────────────┐
│                       nids_server.py                       │ (Serveur FastAPI)
│                                                            │
│   ┌────────────────────────────────────────────────────┐   │
│   │                   nids_core.py                     │   │
│   │  1. Validation des 58 features NFStream            │   │
│   │  2. Nettoyage inf/nan -> 0                         │   │
│   │  3. log(1 + x) & StandardScaler                    │   │
│   │  4. Inférence DNN PyTorch (Multi-classe)           │   │
│   └────────────────────────────────────────────────────┘   │
└───────────────────────────────┬────────────────────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │     Base SQLite        │
                    │  Table 'flows' (SOC)   │
                    └────────────────────────┘
```

---

## 📂 Structure du Répertoire

```text
DL_SOC/
├── models/                     # Modèles entraînés, scalers et configurations
│   ├── classes.json            # Liste des 12 classes supportées
│   ├── feature_cols.json       # Liste des 58 features NFStream retenues
│   ├── dnn_v4.pt               # Poids et architecture du modèle DNN PyTorch (v4)
│   ├── scaler_v4.joblib        # StandardScaler entraîné
│   ├── meta_v4.json            # Métadonnées, paramètres d'extraction et métriques
│   ├── ae_v1.pt                # Auto-encodeur pour détection d'anomalies
│   └── scaler_ae_v1.joblib     # StandardScaler de l'auto-encodeur
├── pcap/                       # Échantillons de captures PCAP pour tests/rejeu
│   ├── DDoS.pcap
│   ├── DoS.pcap
│   ├── PortScan.pcap
│   ├── BruteForce.pcap
│   ├── Bot.pcap
│   ├── WebAttack.pcap
│   └── normal.pcap
├── tests/                      # Suite de tests unitaires et d'intégration
│   ├── test_nids_core.py       # Tests du moteur d'inférence Scorer
│   ├── test_nids_sensor.py     # Tests de la sonde d'extraction NFStream
│   └── test_nids_server.py     # Tests de l'API FastAPI et de la persistance SQLite
├── nids_core.py                # Moteur d'inférence (Scorer)
├── nids_sensor.py              # Sonde d'extraction de flux et client d'ingestion
├── nids_server.py              # API REST FastAPI et journalisation SQLite
├── NIDS.ipynb                  # Notebook de recherche, entraînement et benchmarks
├── requirements.txt            # Dépendances Python requises
└── README.md                   # Documentation du projet
```

---

## 🛠️ Installation

### 1. Prérequis
* Python 3.10 ou supérieur (testé sous Python 3.12 / 3.13)
* Système Linux / macOS / WSL (avec `libpcap` installé pour NFStream)

```bash
# Sur Debian/Ubuntu :
sudo apt-get update && sudo apt-get install -y libpcap-dev
```

### 2. Cloner le dépôt et initialiser l'environnement

```bash
git clone https://github.com/RaBYho/DL_SOC.git
cd DL_SOC

# Création du venv
python3 -m venv .venv
source .venv/bin/activate

# Installation des dépendances
pip install -r requirements.txt
pip install pytest httpx
```

*(Optionnel)* Si vous utilisez `uv` pour des installations ultra-rapides :
```bash
uv pip install -r requirements.txt pytest httpx
```

---

## ⚙️ Configuration

Le serveur s'appuie sur des variables d'environnement pour sa configuration :

| Variable | Description | Valeur par défaut / Exemple |
| :--- | :--- | :--- |
| `NIDS_BASE` | Chemin absolu ou relatif de la racine du projet | `.` |
| `NIDS_DB` | Chemin vers la base de données SQLite | `./nids.db` |
| `NIDS_API_KEY` | Clé secrète d'authentification pour l'ingestion | `secret-soc-key-123` |

---

## 🚦 Guide d'Utilisation

### 1. Démarrer le Serveur SOC

```bash
export NIDS_BASE="."
export NIDS_DB="./nids.db"
export NIDS_API_KEY="secret-soc-key-123"

uvicorn nids_server:app --host 0.0.0.0 --port 8000
```

Vérifier la santé du service :
```bash
curl http://localhost:8000/health
```
Réponse attendue :
```json
{
  "ok": true,
  "classes": ["BENIGN", "Bot", "DDoS", "DoS-GoldenEye", "DoS-Hulk", "DoS-Slowhttptest", "DoS-slowloris", "FTP-Patator", "PortScan", "SSH-Patator", "Scan-Vista", "WebAttack"]
}
```

### 2. Lancer la Sonde / Rejouer une capture PCAP

Pour extraire les flux d'un fichier `.pcap` et les envoyer au serveur :

```python
import json
from nids_sensor import extract, send

# 1. Charger la liste des features attendues
with open("models/feature_cols.json") as f:
    feature_cols = json.load(f)

# 2. Extraire les flux du PCAP
df_flows = extract("pcap/PortScan.pcap")

# 3. Envoyer au serveur NIDS
preds = send(
    df=df_flows,
    feature_cols=feature_cols,
    url="http://localhost:8000",
    key="secret-soc-key-123",
    sensor_id="sonde-reseau-01",
    batch=500
)

print(f"Prédictions reçues : {len(preds)} flux analysés")
```

### 3. Consulter les alertes et statistiques

```bash
curl -H "x-api-key: secret-soc-key-123" http://localhost:8000/stats
```
Exemple de réponse :
```json
{
  "BENIGN": 1420,
  "PortScan": 312,
  "DDoS": 45
}
```

---

## 🧪 Tests Unitaires

Le projet inclut une suite complète de tests unitaires couvrant l'ensemble des modules :

```bash
pytest -v tests/
```

Les tests valident :
* **`tests/test_nids_core.py`** : Chargement du modèle PyTorch, pipeline de normalisation, gestion des colonnes manquantes et valeurs NaN/Inf.
* **`tests/test_nids_sensor.py`** : Transformation des DataFrames NFStream en records JSON et découpage par lots pour l'envoi HTTP.
* **`tests/test_nids_server.py`** : Sécurité de l'API (validation de la clé `x-api-key`), ingestion des lots, détection des alertes et stockage SQLite.

---

## 📊 Performances du Modèle (v4)

Évaluation sur le jeu de test chronologique (avec 3 graines aléatoires) :
* **F1-Score Macro** : ~**94.4 %**
* **Détection précoce** : DoS, DDoS, PortScan, BruteForce détectés avec une sensibilité > 98 %.
* **Limites documentées** : Faux positifs légers sur le trafic SSH/HTTPS standard et couverture des flux Botnets concentrée sur les balises (*beacons*).

---

## 📄 Licence

Projet développé dans le cadre de recherches et d'applications en Détection d'Intrusions IA / SOC.
