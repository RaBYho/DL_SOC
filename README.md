# DL_SOC - Système de Détection d'Intrusions Réseau (NIDS) par Deep Learning & SOC Hybride

DL_SOC est une plateforme intégrée de détection d'intrusions réseau (NIDS) combinant l'apprentissage profond (**Deep Learning PyTorch v5**), l'analyse comportementale non supervisée (**Auto-Encodeur v2**), des modèles de référence tabulaires (**LightGBM**) et l'extraction de flux temps réel (**NFStream**) pour la supervision et l'aide à la décision en environnement **SOC (Security Operations Center)**.

Le système est entraîné et validé sur le jeu de données **CIC-IDS-2017** avec split temporel strict afin de garantir une étanchéité absolue vis-à-vis des fuites de données (*data leakage*).

---

## 🚀 Fonctionnalités Clés

* **Moteur Deep Learning v5 (58 dimensions strictes)** :
  * Élimination complète de l'anomalie historique de duplication de colonne (58 features natives).
  * 12 classes reconnues : `BENIGN`, `Bot`, `DDoS`, `DoS-GoldenEye`, `DoS-Hulk`, `DoS-Slowhttptest`, `DoS-slowloris`, `FTP-Patator`, `PortScan`, `SSH-Patator`, `Scan-Vista`, `WebAttack`.
  * Macro $F_1$-score atteignant **0.9555** et **réduction de 27% des attaques ratées** vs la baseline v4.
* **Calibration de Probabilité (Temperature Scaling $T = 1.4982$)** :
  * Lissage dynamique des logits Softmax éliminant la sur-confiance intrinsèque des réseaux profonds.
  * **Division par deux des fausses alertes (-53.8%)** pour les analystes du SOC.
* **Double Barrière Conjointe & Auto-Encodeur v2** :
  * Auto-encodeur ($58 \to 32 \to 16 \to 8 \to 16 \to 32 \to 58$) entraîné exclusivement sur le trafic bénin.
  * Ratio de séparation médiane de **29.4x** entre attaques et trafic sain.
  * Seuil d'anomalie quantile 99.9% calibré à **`1.4810`** (arbitrage conjoint éliminant 57 fausses alertes supplémentaires).
* **Benchmark Tabulaire LightGBM** :
  * Modèle challenger déployé avec $F_1$-score macro de **0.9588** et seulement 205 fausses alertes.
* **Architecture SOC & Dashboard Temps Réel** :
  * **Sonde réseau (`nids_sensor.py`)** : Capture passive live ou rejeu PCAP avec transmission par lots.
  * **Serveur API FastAPI (`nids_server.py`)** : Authentification par clé API, streaming WebSocket, intégration base SQLite.
  * **Dashboard Moderne Vue 3 (SPA)** : Visualisation cartographique, distribution des menaces, chronologie d'alertes.
  * **Boucle Active Learning & Assistant IA** : Qualification des flux ambigus par les analystes et rétroaction immédiate.

---

## 📐 Architecture du Pipeline NIDS

```
                             ┌────────────────────────┐
                             │      Fichiers PCAP     │
                             │   ou Trafic Réseau     │
                             └───────────┬────────────┘
                                         │
                                         ▼
                             ┌────────────────────────┐
                             │     nids_sensor.py     │ (Sonde NFStream - 58 Features)
                             └───────────┬────────────┘
                                         │ HTTP POST /ingest
                                         │ Headers: x-api-key: secret
                                         ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │                                     nids_server.py                                     │
 │                                                                                        │
 │  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
 │  │                      nids_core.py (Piloté par manifest.json)                     │  │
 │  │                                                                                  │  │
 │  │  1. Validation du Schéma Canonique (schema_features.json - 58 features)          │  │
 │  │  2. Prétraitement : Nettoyage inf/nan -> 0, log1p & StandardScaler v5            │  │
 │  │  3. Inférence DNN PyTorch v5 + Calibration (T = 1.4982)                          │  │
 │  │  4. Évaluation Auto-Encodeur v2 (Seuil Anomalie q99.9 = 1.4810)                  │  │
 │  │  5. Arbitrage Double Barrière (Filtre anti-fausses alertes conjoint)             │  │
 │  └──────────────────────────────────────────────────────────────────────────────────┘  │
 └───────────────────────────────┬────────────────────────────┬───────────────────────────┘
                                 │                            │
                                 ▼                            ▼
                     ┌────────────────────────┐   ┌────────────────────────┐
                     │    Base SQLite (SOC)   │   │  WebSockets & Dashboard│
                     │  Table 'flows', alerts │   │  Vue 3 SPA (Temps Réel)│
                     └────────────────────────┘   └────────────────────────┘
```

---

## 📂 Organisation du Répertoire

```text
DL_SOC/
├── models/                         # Registre de modèles et métadonnées de production
│   ├── manifest.json               # Registre déclaratif actif (dnn_v5, scaler_v5, ae_v2, T=1.4982)
│   ├── schema_features.json        # Schéma canonique documenté des 58 features
│   ├── classes.json                # Liste officielle des 12 classes de trafic
│   ├── feature_cols.json           # Liste ordonnée des 58 features NFStream
│   ├── dnn_v5.pt                   # Réseau profond PyTorch v5 (234 Ko)
│   ├── scaler_v5.joblib            # StandardScaler v5 (58 dimensions)
│   ├── meta_v5.json                # Métadonnées d'entraînement et température
│   ├── ae_v2.pt                    # Auto-encodeur de détection d'anomalies (24 Ko)
│   ├── scaler_ae_v2.joblib         # StandardScaler de l'auto-encodeur v2
│   ├── meta_ae_v2.json             # Seuil d'anomalie q99.9 (1.481025)
│   ├── lgb_v5.txt                  # Modèle benchmark LightGBM
│   └── archive/                    # Historique des anciens modèles (v1, v2, v3)
├── docs/
│   ├── models_metrics/             # Rapports de benchmark et analyses d'évaluation
│   │   └── benchmark_v4_v5_lightgbm.md
│   └── plans/                      # Plans d'architecture et feuilles de route
│       ├── plan_amelioration_modeles_et_pipeline_nids.md
│       └── feuille_de_route_sprint_12h_24h.md
├── pcap/                           # Échantillons de captures PCAP pour tests et rejeux
│   ├── normal.pcap
│   ├── PortScan.pcap
│   ├── DoS.pcap
│   ├── DDoS.pcap
│   ├── BruteForce.pcap
│   ├── Bot.pcap
│   └── WebAttack.pcap
├── tests/                          # Suite complète de 32 tests unitaires et d'intégration
│   ├── test_nids_core.py           # Inférence, calibration, registre et robustesse aux entrées
│   ├── test_nids_sensor.py         # Extraction NFStream et packaging par lots
│   ├── test_nids_server.py         # API REST FastAPI, ingestion et persistance
│   ├── test_active_learning.py     # Boucle de feedback d'analyste SOC
│   ├── test_ai_assistant.py        # Règles expertes et génération de prompt forensique
│   ├── test_dashboard_backend.py   # Requêtes de métriques SOC et flux WebSockets
│   ├── test_notifications.py       # Alerting Telegram / Email avec déduplication
│   └── test_system_health.py       # Monitoring de latence et santé de la sonde
├── nids_core.py                    # Moteur de scoring, calibration et registre déclaratif
├── nids_sensor.py                  # Sonde d'extraction de flux réseau (NFStream)
├── nids_server.py                  # API REST FastAPI, ingestion et persistance SOC
├── retrain_dnn_v5_colab.ipynb      # Pipeline automatisé de réentraînement Colab (v5, AE v2, LGB)
├── NIDS.ipynb                      # Cahier de recherche et reverse-engineering R&D
├── requirements.txt                # Dépendances Python du projet
└── README.md                       # Documentation technique
```

---

## 🛠️ Installation & Démarrage Rapide

### 1. Prérequis Système
* Python 3.10 ou supérieur (testé avec Python 3.12 et 3.13)
* `libpcap` pour l'analyse des trames réseau :
  ```bash
  sudo apt-get update && sudo apt-get install -y libpcap-dev
  ```

### 2. Environnement Virtuel
```bash
git clone https://github.com/RaBYho/DL_SOC.git
cd DL_SOC

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install pytest httpx
```

### 3. Démarrer le Serveur NIDS / SOC
```bash
export NIDS_BASE="."
export NIDS_DB="./nids.db"
export NIDS_API_KEY="dev-secret-key"

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
  "classes": ["BENIGN", "Bot", "DDoS", "DoS-GoldenEye", "DoS-Hulk", "DoS-Slowhttptest", "DoS-slowloris", "FTP-Patator", "PortScan", "SSH-Patator", "Scan-Vista", "WebAttack"],
  "ae_enabled": true,
  "ae_threshold": 1.481024980545044
}
```

---

## 🚦 Rejouer des Captures PCAP

Pour extraire et classifier des captures réseau réelles :

```python
import json
from nids_sensor import extract, send

# 1. Charger la liste des 58 features canoniques
with open("models/feature_cols.json") as f:
    feature_cols = json.load(f)

# 2. Extraire les flux du PCAP via NFStream
df_flows = extract("pcap/PortScan.pcap")

# 3. Envoyer les flux vers l'API de détection
preds = send(
    df=df_flows,
    feature_cols=feature_cols,
    url="http://localhost:8000",
    key="dev-secret-key",
    sensor_id="sonde-reseau-01",
    batch=500
)

print(f"Prédictions reçues : {len(preds)} flux analysés avec succès.")
```

---

## 📊 Performances Comparatives

| Modèle / Configuration | $F_1$-Score Macro | Attaques Ratées (FN) | Fausses Alertes (FP) | Statut Opérationnel |
| :--- | :---: | :---: | :---: | :--- |
| **v4 Baseline (59d)** | 0.9465 | 364 | 366 | Modèle historique avec colonne dupliquée |
| **LightGBM Benchmark** | **0.9588** | 483 | **205** | Modèle tabulaire challenger de référence |
| **DNN v5 (58d)** | **0.9555** | **266** | 464 | Modèle actif - gain de 27% sur les cyberattaques |
| **DNN v5 Calibré ($T=1.50$)** | 0.9517 | 462 | **223** | **-53.8% de fausses alertes** pour le SOC |
| **Double Barrière (v5 + AE v2)** | 0.9496 | 368 | **426** | **57 fausses alertes éliminées** par l'AE |

Pour le rapport complet, consultez [docs/models_metrics/benchmark_v4_v5_lightgbm.md](file:///home/hoby/Documents/Projet-dev/IA/DL_SOC/docs/models_metrics/benchmark_v4_v5_lightgbm.md).

---

## 🧪 Validation & Tests

Exécuter la suite complète de 32 tests unitaires et d'intégration :

```bash
pytest -v tests/
```

Tous les tests couvrent le moteur d'inférence, la sonde réseau, l'API FastAPI, le WebSocket, l'Active Learning, l'Assistant IA forensique et le système d'alerte.

---

## 📄 Licence & Crédits

Projet développé dans le cadre de recherches et d'applications en Détection d'Intrusions IA / SOC Hybride.
Dataset de référence : **CIC-IDS-2017** (Canadian Institute for Cybersecurity).
