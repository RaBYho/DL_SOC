# Reprendre la Session DL_SOC

Ce document contient les commandes permettant de reprendre cette session de travail Antigravity (`agy`), ainsi que les commandes essentielles du projet.

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

## 2. Commandes Utiles du Projet

### A. Environnement Virtuel Python
```bash
cd /home/hoby/Documents/Projet-dev/IA/DL_SOC
source .venv/bin/activate
```

### B. Lancer la Suite de Tests (15/15 tests validés)
```bash
.venv/bin/pytest -v tests/
```

### C. Démarrer le Serveur NIDS + API Dashboard SOC
```bash
.venv/bin/uvicorn nids_server:app --host 0.0.0.0 --port 8000 --reload
```
- **Documentation OpenAPI (Swagger) :** http://localhost:8000/docs
- **API Dashboard Base :** http://localhost:8000/api/dashboard/init
- **Flux WebSocket Live :** ws://localhost:8000/ws

### D. Tester le Replay PCAP en tâche de fond
```bash
# Lister les PCAP disponibles
curl -s http://localhost:8000/api/dashboard/pcaps | jq

# Démarrer un rejeu (ex: DDoS.pcap)
curl -X POST "http://localhost:8000/api/dashboard/replay/start?pcap_name=DDoS.pcap&speed=1.0"

# Vérifier le statut du rejeu
curl -s http://localhost:8000/api/dashboard/replay/status | jq
```

---

## 3. État Actuel & Prochaine Étape

- **Dernier commit :** `4d2fcf3` (*feat(backend): implement dashboard backend with SQLite queries, WebSocket manager and PCAP replay service*)
- **Branche :** `main` (synchronisée avec GitHub)
- **Prochaine étape :** Créer les templates HTML interactifs dans `dashboard/templates/` à partir des maquettes de `mockups/` et les connecter au WebSocket et à l'API backend.
