# Pipeline NIDS Hybride à Deux Étages + Détection d'Anomalies (Kitsune)

Système de détection d'intrusions réseau (NIDS) combinant le filtrage supervisé en cascade à base d'arbres de décision et de réseaux de neurones profonds, couplé à une branche non-supervisée d'autoencodeurs en ligne pour l'interception d'attaques inconnues (*0-days*).

---

## 1. Architecture du Système

Le système repose sur un traitement hybride des flux et des paquets réseau :

```
PCAP ─┬─► CICFlowMeter ─► Flux réseau ─► ÉTAGE 1 (CatBoost + XGBoost) ─► ÉTAGE 2 (CNN-1D) ─┐
      │                                                                                  ├─► FUSION ─► Décision
      └─► KITSUNE (Autoencodeurs) ─────► packet_scores.parquet ─► Alignement par flux ───┘
```

### Rôle des composants

1. **Étage 1 — Filtrage binaire rapide (CatBoost + XGBoost)** :
   - Évalue la probabilité globale d'attaque sur 76 et 30 métriques de flux.
   - Écarte instantanément le trafic bénin ($score < t_1$).
2. **Étage 2 — Classification fine (1D-CNN PyTorch)** :
   - Invoqué uniquement sur les flux suspects ($score \ge t_1$).
   - Catégorise le vecteur parmi les **14 familles d'attaques** de référence de CICIDS2017 avec un seuil de confiance $t_2$.
3. **Branche Non-Supervisée — Kitsune (KitNET)** :
   - Extrait les statistiques incrémentales de paquets et calcule une erreur de reconstruction RMSE sans étiquette préalable.
   - Aligne vectoriellement les scores paquets avec les flux réseau selon un quintuplet canonique bidirectionnel.
4. **Moteur de Fusion Multi-Niveaux** :
   - Arbitre entre la confiance supervisée et l'anomalie non supervisée ($t_3$) pour qualifier le trafic en `BENIGN`, attaque spécifique (14 classes), `ANOMALY_UNKNOWN` (0-day) ou `UNKNOWN_ATTACK_LIKELY`.

---

## 2. Modèles Pré-entraînés Utilisés

| Composant | Modèle | Format | Source | Licence |
|---|---|---|---|---|
| **Étage 1 (Principal)** | NIDS-CatBoost | Binaire `.cbm` (604 Ko) | [pop123ux/pcap-ml-traffic-classifier](https://huggingface.co/pop123ux/pcap-ml-traffic-classifier) | Apache 2.0 |
| **Étage 1 (Second avis)** | NIDS-XGBoost | JSON natif `.json` (1.7 Mo) | [csperera/aegis-ai](https://github.com/csperera/aegis-ai) | MIT |
| **Étage 2 (14 classes)** | 1D-CNN PyTorch | Poids `.pth` (1.9 Mo) | [saidimn/ids-cnn-cicids2017](https://huggingface.co/saidimn/ids-cnn-cicids2017) | MIT |
| **Anomalies** | Kitsune / KitNET | Autoencodeurs | [ymirsky/Kitsune-py](https://github.com/ymirsky/Kitsune-py) | Apache 2.0 |

---

## 3. Installation et Démarrage Rapide

### Pré-requis
- Python 3.10+ (testé sous Python 3.12)
- Système Linux / macOS / Windows

### Installation locale (CPU optimisé, ~300 Mo)
```bash
# 1. Cloner le dépôt et créer l'environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# 2. Installer les dépendances CPU
pip install -r envs/main.txt
pip install -e .
```

### Lancement de la démonstration CLI
Pour tester immédiatement le pipeline complet sur l'échantillon fourni :
```bash
python scripts/run_demo.py data/samples/mini.csv --packets data/samples/packet_scores.parquet
```

### Moteur Temps Réel & Réduction des Fausses Alertes (Phase 12)
Pour rejouer des micro-batchs de 10 secondes avec pré-filtrage déterministe, corrélation par hôte (*leaky bucket*), quorum volumétrique et déduplication *cooldown* :
```bash
# Mode Replay déterministe (testable en local) :
python scripts/run_live.py --replay-dir data/samples/chunks/

# Mode Surveillance temps réel (watcher de dossier) :
python scripts/run_live.py --watch-dir /tmp/nids_chunks/ --output alerts.json
```

### Capture Réseau en Direct sur Carte Réseau (Live Sniffing)
Pour capturer directement les paquets sur votre interface réseau active (ex: `enx3ecd36af7cdb` ou `eth0`), les convertir en flux via `cicflowmeter` et les scorer en temps réel :
```bash
# Capture en direct par tranches de 5 secondes (avec dumpcap ou tcpdump) :
sudo python scripts/run_live_capture.py -i enx3ecd36af7cdb -b 5

# Ou sans sudo si votre utilisateur appartient au groupe wireshark :
python scripts/run_live_capture.py -i enx3ecd36af7cdb

# Test sur un fichier PCAP hors-ligne (sans droits root) :
python scripts/run_live_capture.py --pcap mon_trafic.pcap --output alerts.json
```

---

## 4. Stratégie de Test et Assurance Qualité

Le projet suit une méthodologie rigoureuse de **Test-Driven Development (TDD)** :

```bash
# Lancer les tests unitaires rapides (sans vrais modèles) :
make test

# Lancer la totalité des tests (unitaires, intégration modèles réels et end-to-end) :
make test-all
```

**Couverture des tests :**
- `tests/unit/` : Alignement vectorisé, étiquettes, adaptateurs, seuils anti-fuite, fusion à 6 cas, pré-filtrage déterministe (`live_filter.py`), score de menace cumulé par hôte avec décroissance exponentielle, quorum volumétrique, cooldown anti-flood (`live_guard.py`) et calibration dynamique Kitsune anti-empoisonnement.
- `tests/integration/` : Inférence sur vrais modèles CatBoost, XGBoost, CNN-1D, synchronisation paquets-flux, pipeline temps réel complet et script CLI `run_live.py`.
- `tests/e2e/` : Exécution du pipeline complet avec rapport décisionnel.

---

## 5. Exécution Déportée sur Google Colab (Calcul Lourd)

Les traitements volumineux (PCAPs complets de 10 à 30 Go, conversion des 2,8 millions de flux en `.parquet`, calibration finale et test de généralisation sur CSE-CIC-IDS2018) sont déportés dans `notebooks/` :

* [`colab_phase7_kitsune_run.ipynb`](notebooks/colab_phase7_kitsune_run.ipynb) : Exécution massive de Kitsune sur PCAPs.
* [`colab_phase10_11_eval.ipynb`](notebooks/colab_phase10_11_eval.ipynb) : Calibration des seuils et benchmark comparatif.

---

## 6. Table de Décision de Fusion

| Étage 1 ($t_1$) | Étage 2 ($t_2$) | Kitsune ($t_3$) | Étiquette Finale | Signification métier |
|---|---|---|---|---|
| **Normal** (< $t_1$) | *Non exécuté* | **Normal** (< $t_3$) | `BENIGN` | Trafic régulier validé |
| **Normal** (< $t_1$) | *Non exécuté* | **Anormal** ($\ge t_3$) | `ANOMALY_UNKNOWN` | Attaque potentielle inconnue / 0-day |
| **Suspect** ($\ge t_1$) | **Confiant** ($\ge t_2$) | *Indifférent* | **Nom de l'attaque** | Attaque connue identifiée (14 classes) |
| **Suspect** ($\ge t_1$) | **Incertain** (< $t_2$) | **Normal** (< $t_3$) | `SUSPECT_UNCERTAIN` | Anomalie légère non confirmée |
| **Suspect** ($\ge t_1$) | **Incertain** (< $t_2$) | **Anormal** ($\ge t_3$) | `UNKNOWN_ATTACK_LIKELY` | Forte suspicion d'attaque non répertoriée |
| *Indifférent* | *Indifférent* | `NaN` (absent) | Décision Étages 1+2 | Repli automatique (fallback flux seul) |
