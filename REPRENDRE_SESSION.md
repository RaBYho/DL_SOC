# Reprendre la Session DL_SOC

Ce document consigne l'état d'avancement exact du projet **HDVR Autonomous Defense (DL_SOC)**, les instructions pour reprendre cette session de travail Antigravity (`agy`), ainsi que les commandes essentielles du système.

---

## 1. Reprendre la Session Antigravity CLI

Pour reprendre exactement cette session de travail avec l'historique complet et les contextes actifs :

### Option A : Reprendre directement par son ID unique (Recommandé)
```bash
cd /home/hoby/Documents/Projet-dev/IA/DL_SOC
agy --conversation 72f3bc05-00ba-43a1-a7ac-8560a2dd3bfa
```

### Option B : Reprendre la dernière conversation active
```bash
cd /home/hoby/Documents/Projet-dev/IA/DL_SOC
agy -c
# ou
agy --continue
```

---

## 2. État Actuel du Projet & Sprint 12h Finalisé

- **Branche active :** `main`
- **Suite de tests :** **32/32 tests unitaires et d'intégration validés** (`pytest -v tests/`).
- **Modèles Actifs en Production (Sprint 12h Complété) :**
  - **DNN v5** (`models/dnn_v5.pt`, 234 Ko, 58 features strictes, calibré avec $T=1.4982$, macro $F_1 = 0.9555$).
  - **Auto-Encodeur v2** (`models/ae_v2.pt`, 24 Ko, seuil quantile 99.9% = $1.481025$, ratio de séparation $29.4\times$).
  - **Model Registry Déclaratif** (`models/manifest.json`).
  - **Schéma Canonique des Features** (`models/schema_features.json`).
  - **Benchmark Tabulaire LightGBM** (`models/lgb_v5.txt`, $F_1 = 0.9588$, 205 fausses alertes).
  - **Rapport de Benchmark Complet :** `docs/models_metrics/benchmark_v4_v5_lightgbm.md`.
  - **Notebook Officiel de Réentraînement Colab :** `retrain_dnn_v5_colab.ipynb` (28 cellules + 3 suites de tests automatisées).
  - **Cahier R&D Documenté :** `NIDS.ipynb` (en-tête et orientation R&D / Production).
- **Frontend SPA :** Vue 3 + Pinia + Vite compilé dans `dashboard/dist/` servi par FastAPI.
- **Rejeux PCAP Réseau Validés :**
  - `pcap/PortScan.pcap` : 1 024/1 024 flux classifiés PortScan (100% de détection).
  - `pcap/normal.pcap` : 35/35 flux classifiés BENIGN (0 fausse alerte).

---

## 3. Commandes Utiles du Projet

### A. Environnement Virtuel Python
```bash
cd /home/hoby/Documents/Projet-dev/IA/DL_SOC
source .venv/bin/activate
```

### B. Lancer la Suite de Tests (32/32 tests)
```bash
.venv/bin/pytest -v tests/
```

### C. Démarrer le Serveur Backend (FastAPI + Uvicorn + WebSocket)
```bash
.venv/bin/uvicorn nids_server:app --host 0.0.0.0 --port 8000 --reload
```
- **Documentation OpenAPI (Swagger) :** http://localhost:8000/docs
- **API Dashboard Base :** http://localhost:8000/api/dashboard/init
- **Santé de la Sonde & Modèles :** http://localhost:8000/health
- **Diagnostic Santé Système :** http://localhost:8000/api/dashboard/system/health
- **Flux WebSocket Live :** ws://localhost:8000/ws

### D. Développement & Compilation Frontend (Vue 3 / Vite)
```bash
cd dashboard/frontend
npm run build      # Compile vers dashboard/dist/ (servi par FastAPI)
npm run dev        # Mode dev avec hot-reload (Vite port 5173)
```

### E. Contrôle du Rejeu PCAP en Ligne de Commande
```bash
# Lister les PCAP disponibles
curl -s http://localhost:8000/api/dashboard/pcaps | python3 -m json.tool

# Démarrer un rejeu (ex: PortScan.pcap ou DDoS.pcap)
curl -X POST "http://localhost:8000/api/dashboard/replay/start?pcap_name=PortScan.pcap&speed=1.0"

# Vérifier le statut du rejeu
curl -s http://localhost:8000/api/dashboard/replay/status | python3 -m json.tool
```

---

## 4. Documentation Technique & Plans

- [README.md](file:///home/hoby/Documents/Projet-dev/IA/DL_SOC/README.md) : Vue d'ensemble du système et démarrage rapide.
- [docs/models_metrics/benchmark_v4_v5_lightgbm.md](file:///home/hoby/Documents/Projet-dev/IA/DL_SOC/docs/models_metrics/benchmark_v4_v5_lightgbm.md) : Benchmark comparatif v4, v5, LightGBM et Auto-Encodeur v2.
- [docs/plans/feuille_de_route_sprint_12h_24h.md](file:///home/hoby/Documents/Projet-dev/IA/DL_SOC/docs/plans/feuille_de_route_sprint_12h_24h.md) : Suivi des 5 blocs du sprint.
- [docs/plans/plan_amelioration_modeles_et_pipeline_nids.md](file:///home/hoby/Documents/Projet-dev/IA/DL_SOC/docs/plans/plan_amelioration_modeles_et_pipeline_nids.md) : Analyse architecturale et ML critique.
