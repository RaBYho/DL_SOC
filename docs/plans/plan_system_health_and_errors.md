# 📋 Plan 1 : Traitement des Erreurs & Santé Système (System Health)

## 🎯 Objectif
Établir une séparation claire entre **les pannes techniques d'infrastructure** (capteur déconnecté, saturation de buffer, timeout d'inférence, base SQLite verrouillée) et **les incidents de sécurité réseau** (attaques, détections d'intrusions, zero-days), tout en garantissant à l'administrateur une visibilité immédiate et proactive sur la santé opérationnelle de la chaîne NIDS.

---

## 🏗️ Architecture Technique

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             CHAÎNE NIDS COMPLÈTE                            │
└──────┬──────────────────────┬───────────────────────┬────────────────┬──────┘
       │                      │                       │                │
       ▼                      ▼                       ▼                ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────────┐ ┌────────────┐
│   Capteur    │      │   Moteur     │      │   Base Données   │ │ WebSocket  │
│   Sniffer    │      │  Inférence   │      │     SQLite       │ │  Manager   │
│ (PCAP / Live)│      │  (DL/PyTorch)│      │ (WAL / Verrous)  │ │ (Clients)  │
└──────┬───────┘      └──────┬───────┘      └────────┬─────────┘ └─────┬──────┘
       │                      │                       │                │
       └──────────────────────┴───────────┬───────────┴────────────────┘
                                          │ Heartbeats & Métriques
                                          ▼
                      ┌───────────────────────────────────────┐
                      │    Health Monitor Service (Backend)   │
                      │       Endpoint: /api/system/health    │
                      └───────────────────┬───────────────────┘
                                          │ Statut en temps réel
                                          ▼
                      ┌───────────────────────────────────────┐
                      │    Composant UI: SystemHealthBar      │
                      │     (Header SOC + Drawer Détails)     │
                      └───────────────────────────────────────┘
```

---

## 📦 Composants à Implémenter

### 1. Backend (`dashboard/backend/`)

#### A. Service de Monitoring de Santé (`services/health_service.py`)
Collecte périodique (toutes les 5 à 10 secondes) de l'état des sous-systèmes :
- **Capteurs (Sensors) :**
  - Horodatage du dernier paquet ingéré (`last_seen`).
  - Débit actuel de paquets / flux (`flows_per_sec`).
  - Statut : `ONLINE` (< 15s), `DEGRADED` (15s - 60s sans flux), `OFFLINE` (> 60s).
- **Moteur d'Inférence IA (ML Engine) :**
  - Disponibilité des modèles (Auto-Encodeur MSE + Classifieur multi-classes).
  - Temps d'inférence moyen par batch (latence en ms).
  - Statut : `OPERATIONAL` (< 100ms), `SLOW` (100ms - 500ms), `ERROR` (exceptions ou indisponible).
- **Persistance & Stockage (Database SQLite) :**
  - Taille du fichier `flows.db` et du journal WAL.
  - Temps d'exécution de la requête de contrôle (`PRAGMA quick_check;`).
  - Statut : `HEALTHY`, `HIGH_LATENCY` (> 200ms), `LOCKED` (conflit de verrou).
- **Diffusion Temps Réel (WebSocket) :**
  - Nombre de clients connectés, file d'attente des messages non distribués.

#### B. API Endpoints
- `GET /api/system/health` : Retourne un JSON consolidé avec score global (`OK`, `WARNING`, `CRITICAL`), latences et détails par composant.
- `GET /api/system/logs` : 50 dernières entrées de logs techniques (erreurs et avertissements uniquement).

---

### 2. Frontend (`dashboard/frontend/src/`)

#### A. Pastille d'État dans le Header (`App.vue`)
- Une pastille discrète et visible dans la barre supérieure :
  - 🟢 **Système Nominal** (Tous les composants au vert).
  - 🟡 **Attention Requise** (Ex : capteur sans flux depuis 30s ou latence DB élevée).
  - 🔴 **Incident Système** (Capteur hors-ligne ou échec d'inférence).
- Clic sur la pastille ouvre le **Tiroir de Diagnostic Système** (*System Health Drawer*).

#### B. Tiroir de Diagnostic Système (`components/system/SystemHealthDrawer.vue`)
- Vue d'ensemble visuelle des 4 piliers (Capteur, Modèle IA, Base SQLite, WebSocket).
- Jauge de latence d'inférence en direct.
- Console d'erreurs techniques filtrable (erreurs d'infrastructures distinctes des incidents de sécurité).
- Bouton d'action rapide : « Tester la connexion » et « Vider le cache de télémétrie ».

#### C. Gestionnaire Global d'Erreurs UI (*Toasts & Error Boundary*)
- Interception Axios/Fetch des erreurs 500/503 avec affichage d'un toast informatif et non-bloquant.
- En cas de perte de connexion WebSocket : mode dégradé avec tentative de reconnexion automatique exponentielle et indicateur visuel discret.

---

## 📅 Étapes de Déploiement

1. **Étape 1 :** Création de `health_service.py` et de l'endpoint FastAPI `/api/system/health`.
2. **Étape 2 :** Enrichissement du WebSocket broadcast pour transmettre l'état de santé lors des heartbeats.
3. **Étape 3 :** Création du store Pinia `systemStore.js` côté frontend.
4. **Étape 4 :** Intégration de la pastille d'état dans le Header et du composant `SystemHealthDrawer.vue`.
5. **Étape 5 :** Tests unitaires (`tests/test_system_health.py`) validant la détection des pannes simulées.
