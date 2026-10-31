# 📋 Plan 4 : Assistant IA & LLM pour l'Analyse d'Incidents

## 🎯 Objectif
Fournir à l'analyste SOC une aide cognitive immédiate lors de l'investigation d'un flux réseau complexe ou inconnu, en combinant :
1. **Un mode universel « Copier-Coller »** : zéro coût, zéro dépendance API, 100% privé, compatible avec n'importe quel LLM (ChatGPT, Claude, Gemini Web, DeepSeek).
2. **Un mode « Analyse Intégrée »** : analyse en un clic directement dans le dashboard SOC via un LLM local (Ollama / `llama.cpp`) ou une API Cloud (Google Gemini API).

---

## 🏗️ Architecture Technique

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INCIDENT SÉLECTIONNÉ                              │
│         (Métadonnées réseau, score MSE, drapeaux TCP, caractéristiques)     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                    CHOIX DU MODE D'ASSISTANCE PAR L'ANALYSTE
                                       │
        ┌──────────────────────────────┴──────────────────────────────┐
        ▼                                                             ▼
┌─────────────────────────────────┐                 ┌─────────────────────────────────┐
│     MODE 1 : COPIER-COLLER      │                 │   MODE 2 : ANALYSE INTÉGRÉE     │
│   (Presse-papiers instantané)   │                 │   (Connecteur API / Ollama)     │
├─────────────────────────────────┤                 ├─────────────────────────────────┤
│ • Génère un prompt Markdown     │                 │ • Envoi au backend FastAPI      │
│ • Structure SOC / Tier-3        │                 │ • Ollama local (100% privé)     │
│ • Prêt à coller sur Web LLM     │                 │   OU Google Gemini API          │
│ • Zéro clé API requise          │                 │ • Rendu streaming dans l'UI     │
└────────────────┬────────────────┘                 └────────────────┬────────────────┘
                 │                                                   │
                 ▼                                                   ▼
┌─────────────────────────────────┐                 ┌─────────────────────────────────┐
│   ChatGPT / Claude / Gemini     │                 │  Onglet "Rapport IA" (Drawer)   │
│   (Analyse externe manuelle)    │                 │  • Synthèse & Gravité           │
│                                 │                 │  • MITRE ATT&CK (ex: T1046)     │
│                                 │                 │  • Règle iptables en 1 clic     │
└─────────────────────────────────┘                 └─────────────────────────────────┘
```

---

## 📦 Composants à Implémenter

### 1. Mode 1 : Générateur de Prompt Forensique (Copier-Coller)

#### Structure du Prompt Généré
En cliquant sur le bouton **« 📋 Copier le Prompt IA »**, le texte suivant est copié dans le presse-papiers avec les vraies données du flux :

```markdown
Tu es un analyste senior en cybersécurité SOC Tier-3.
Analyse le flux réseau suspect suivant détecté par notre NIDS (Deep Learning) :

### 🌐 Métadonnées du flux
- **Horodatage :** 2026-10-31 16:45:12
- **Source :** 192.168.1.150:48212 ➔ **Destination :** 10.0.0.5:445 (SMB)
- **Protocole :** TCP
- **Durée :** 0.08 seconde
- **Volume :** 18 paquets | 2 450 octets
- **Flags TCP :** SYN=1, ACK=0, FIN=1, RST=0, PSH=0

### 🧠 Métriques du Modèle NIDS
- **Score d'anomalie MSE :** 4.75 (Seuil normal d'alerte : 0.35)
- **Classification préliminaire :** SUSPECT_ZERODAY (Confiance : 89%)
- **Caractéristiques les plus divergentes :**
  1. `Packet Rate` : 225 pkts/s (Normal : < 20 pkts/s)
  2. `TCP Flag Combination` : SYN+FIN inhabituel
  3. `Byte Variance` : Faible variance (paquets de taille identique)

### 🎯 Instructions d'analyse attendues :
1. **Hypothèse de menace :** Quelle est la nature probable de ce flux (ex: scan furtif, exploit SMB/EternalBlue, tentative d'évasion) ?
2. **Cartographie MITRE ATT&CK :** Indique la tactique et technique MITRE associée (ID et nom).
3. **Évaluation de sévérité :** Évalue le risque réel (Faible / Moyen / Élevé / Critique) avec justification.
4. **Remédiation immédiate :** Fournis la commande exacte `iptables` pour bloquer cette IP source et une règle de détection Suricata/Snort.
```

---

### 2. Mode 2 : Connecteur d'Analyse Intégrée

#### A. Backend (`services/ai_analyzer.py`)
- Service unifié d'interrogation de LLM :
  - **Option Locale (recommandée pour la confidentialité) :** Requête vers Ollama (`http://localhost:11434/api/generate`) ou `llama.cpp` local.
  - **Option Cloud :** Appel direct à l'API Google Gemini via `google-genai` ou endpoint REST (avec la clé configurée par l'admin).
- Prompt système rigoureusement calibré pour renvoyer une réponse structurée en 3 sections :
  1. *Diagnostic rapide* (2-3 phrases).
  2. *Mapping MITRE ATT&CK*.
  3. *Script de blocage* (`iptables -A INPUT -s ... -j DROP`).

#### B. Endpoints API
- `POST /api/incidents/{incident_id}/ai-analysis` :
  - Déclenche l'analyse en direct du flux et renvoie la réponse au format Markdown.
- `GET /api/settings/ai` / `POST /api/settings/ai` :
  - Configuration du provider (Ollama / Gemini / Désactivé), de l'URL d'écoute, du modèle (ex: `llama3`, `mistral`, `gemini-2.5-flash`), et de la clé API optionnelle.

---

### 3. Frontend (`dashboard/frontend/src/`)

#### A. Tiroir d'Incident (`IncidentDrawer.vue`)
- Deux boutons dédiés dans le panneau supérieur d'actions :
  - **Bouton 1 : « 📋 Copier pour LLM »** (Icône presse-papiers, notification toast de confirmation au clic).
  - **Bouton 2 : « 🤖 Diagnostic IA »** (Icône cerveau/robot).
- Onglet dédié **« 🧠 Rapport d'Assistance IA »** :
  - Si l'analyse a été lancée : affichage en streaming ou avec squelette de chargement.
  - Rendu Markdown soigné avec blocs de code stylisés.
  - Bouton « Copier la commande de blocage » à côté de la règle iptables générée.

#### B. Paramètres de l'IA dans `SettingsView.vue`
- Section « **Assistance IA & LLM** » :
  - Sélecteur de mode : `Désactivé` / `Ollama Local (Hors-ligne)` / `Google Gemini API`.
  - Champ URL Ollama (par défaut : `http://localhost:11434`).
  - Champ Modèle (par défaut : `mistral:latest` ou `gemini-2.5-flash`).
  - Champ Clé API (chiffré/masqué).
  - Bouton « ⚡ Tester la connexion IA ».

---

## 📅 Étapes de Déploiement

1. **Étape 1 :** Création du générateur de prompt forensique côté frontend (Mode 1 - Copier-Coller immédiat).
2. **Étape 2 :** Création du service backend `ai_analyzer.py` avec connecteur Ollama & Gemini.
3. **Étape 3 :** Création de l'endpoint FastAPI `/api/incidents/{id}/ai-analysis`.
4. **Étape 4 :** Intégration de l'onglet IA dans `IncidentDrawer.vue` avec rendu markdown.
5. **Étape 5 :** Ajout de la configuration du provider IA dans `SettingsView.vue`.
