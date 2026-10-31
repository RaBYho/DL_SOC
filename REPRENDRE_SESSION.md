# Reprendre la Session DL_SOC

Ce document consigne l'état d'avancement exact du projet **HDVR Autonomous Defense (DL_SOC)**, les instructions pour reprendre cette session de travail Antigravity (`agy`), ainsi que les commandes essentielles du système.

---

## 1. Reprendre la Session Antigravity CLI

Pour reprendre exactement cette session de travail avec l'historique complet et les contextes actifs :

### Option A : Reprendre directement par son ID unique (Recommandé)
```bash
cd /home/hoby/Documents/Projet-dev/IA/DL_SOC
agy --conversation d1a3c9ac-156f-4867-b4f9-db85fa0d87be
```

### Option B : Reprendre la dernière conversation active
```bash
cd /home/hoby/Documents/Projet-dev/IA/DL_SOC
agy -c
# ou
agy --continue
```

---

## 2. État Actuel du Projet & Dernières Réalisations

- **Branche active :** `main` (synchronisée avec GitHub `origin/main`).
- **Dernier commit :** [`834bc22`](https://github.com/RaBYho/DL_SOC/commit/834bc22) : `feat(model-agility): dynamic non-frozen model classes across backend, prompts & UI`
- **Suite de tests :** **30/30 tests unitaires validés** (`pytest tests/`).
- **Frontend SPA :** Vue 3 + Pinia + Vite compilé avec succès dans `dashboard/dist/`.
- **Serveur de développement :** Uvicorn actif en tâche de fond sur le port 8000.

### Fonctionnalités Majeures Récemment Finalisées :
1. **Architecture Modèle Dynamique & Non-Figée :**
   - Zéro classe codée en dur. Lecture dynamique de `models/classes.json` et agrégation des nouvelles classes issues d'Active Learning (`flows` et `feedback_flows`).
   - Endpoint `GET /api/dashboard/models/classes`, injection dans `GET /init` et le WebSocket.
   - Suppression des références statiques "(12 classes)" dans l'UI, le store Pinia, `ModelsView.vue`, `IncidentTable.vue`, `translations.js` et les prompts IA.
2. **Prompts Forensiques Riches & Détection de Campagne Multi-Flux :**
   - Sélection multiple d'alertes dans le tableau d'incidents avec raccourcis ("Tous les 0-Day", "Tous les filtrés").
   - Modal d'investigation de pattern de campagne (`BatchPatternModal.vue`) avec corrélation spatio-temporelle, plage MSE et exportation de prompt prêt pour LLM externes (Gemini, Claude, ChatGPT, Ollama).
3. **Boucle Active Learning & Human-in-the-Loop :**
   - Table SQLite `feedback_flows` pour stocker les qualifications et corrections des analystes.
   - Export du dataset au format JSON et CSV pour ré-entraînement (`/api/dashboard/feedback/export`).
   - Notebook Google Colab prêt à l'emploi : `retrain_dnn_v5_colab.ipynb`.
4. **Alerting Multi-Canal :**
   - Intégration Telegram Bot et SMTP Email avec rapports HTML forensiques et limitation de cadence.
5. **Surveillance de la Santé Système & Erreurs :**
   - Diagnostics consolidés de l'infrastructure (sonde, moteur IA, SQLite, WebSocket, hôte CPU/RAM/disque).
   - Tiroir dédié avec déclenchement de tests unitaires par composant.

---

## 3. Commandes Utiles du Projet

### A. Environnement Virtuel Python
```bash
cd /home/hoby/Documents/Projet-dev/IA/DL_SOC
source .venv/bin/activate
```

### B. Lancer la Suite de Tests (30/30 tests)
```bash
.venv/bin/pytest -v tests/
```

### C. Démarrer le Serveur Backend (FastAPI + Uvicorn + WebSocket)
```bash
.venv/bin/uvicorn nids_server:app --host 0.0.0.0 --port 8000 --reload
```
- **Documentation OpenAPI (Swagger) :** http://localhost:8000/docs
- **API Dashboard Base :** http://localhost:8000/api/dashboard/init
- **Classes dynamiques :** http://localhost:8000/api/dashboard/models/classes
- **Diagnostic Santé :** http://localhost:8000/api/dashboard/system/health
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

## 4. Prochaine Étape / Roadmap

1. **Page Threat Intelligence & Flux CTI en Direct :**
   - Connecter la vue `ThreatIntelView.vue` à des sources de Threat Intelligence actualisées (MITRE ATT&CK CTI STIX feed, CISA Known Exploited Vulnerabilities catalog, AlienVault OTX ou AbuseIPDB API).
   - Enrichir les IOCs (IPs malveillantes, ports ciblés) détectés lors des sessions de capture avec les données CTI en temps réel.
2. **Ré-entraînement du Modèle DNN v5 :**
   - Exécuter `retrain_dnn_v5_colab.ipynb` avec les nouvelles données exportées de `feedback_flows`.
   - Remplacer le modèle actif par `dnn_v5.pt` et vérifier la détection automatique des nouvelles classes.
