# 📋 Plan 2 : Système de Notifications Multi-Canal (Telegram & Mail)

## 🎯 Objectif
Alerter les administrateurs et analystes SOC en temps réel hors du tableau de bord (via Telegram et/ou Email) dès qu'un incident critique ou une anomalie Zero-Day survient, tout en évitant la fatigue d'alerte grâce à un moteur de throttling et d'agrégation d'événements.

---

## 🏗️ Architecture Technique

```
                              ┌──────────────────────────┐
                              │  Événement NIDS Détecté  │
                              └─────────────┬────────────┘
                                            │
                                            ▼
                              ┌──────────────────────────┐
                              │  Moteur de Filtrage      │
                              │  (Seuil : CRITICAL / ZD) │
                              └─────────────┬────────────┘
                                            │
                                            ▼
                              ┌──────────────────────────┐
                              │  Moteur Anti-Spam        │
                              │  (Throttling & Batching) │
                              └─────────────┬────────────┘
                                            │
                     ┌──────────────────────┴──────────────────────┐
                     │                                             │
                     ▼                                             ▼
       ┌──────────────────────────┐                  ┌──────────────────────────┐
       │   Telegram Notifier      │                  │   Email / SMTP Notifier  │
       │ (Bot API Asynchrone)     │                  │  (aiosmtplib + HTML dark)│
       └─────────────┬────────────┘                  └─────────────┬────────────┘
                     │                                             │
                     ▼                                             ▼
       ┌──────────────────────────┐                  ┌──────────────────────────┐
       │   Canal / Groupe Admin   │                  │   Boîte Réception SOC    │
       │ (Markdown + Liens direct)│                  │  (Rapport détaillé HTML) │
       └──────────────────────────┘                  └──────────────────────────┘
```

---

## 📦 Composants à Implémenter

### 1. Backend (`dashboard/backend/`)

#### A. Moteur Anti-Spam & Throttling (`services/notifications/throttling.py`)
- **Problème résolu :** Éviter l'envoi de 500 messages lors d'un scan SYN ou d'une attaque DDoS massive.
- **Règles :**
  - **Fenêtre glissante (Debounce) :** Si une alerte du même type et de la même IP source survient dans les 60 secondes, elle est cumulée.
  - **Rapport Groupé (Digest) :** Après 60 secondes, envoi d'un message synthétique :  
    *« 🚨 Attaque SYN Flood : 1 240 paquets bloqués depuis 192.168.1.50 entre 16:42:00 et 16:43:00 »*.
  - **Alerte Immédiate unitaire :** Réservée aux nouveaux types d'attaques ou aux Zero-Days avérés.

#### B. Notificateur Telegram (`services/notifications/telegram.py`)
- Utilise l'API officielle Bot Telegram (requêtes HTTPS asynchrones via `httpx`).
- Format du message : MarkdownV2 soigné avec émojis d'alerte, IP source, port ciblé, score d'anomalie MSE, et bouton inline : `[🔍 Voir sur le SOC Dashboard]`.
- Pas de dépendance lourde : un client `httpx` async suffit.

#### C. Notificateur Email (`services/notifications/email.py`)
- Utilise `aiosmtplib` pour un envoi non-bloquant en arrière-plan.
- Template HTML responsive en Dark Theme (cohérent avec l'identité du SOC).
- Résumé technique : tableau des caractéristiques du flux, recommandations d'action.

#### D. Endpoints de Configuration & Tests
- `GET /api/settings/notifications` : Récupère la configuration chiffrée/masquée.
- `POST /api/settings/notifications` : Enregistre la configuration (token, chat_id, smtp).
- `POST /api/notifications/test-telegram` : Envoie un message de test immédiat pour valider les identifiants Telegram.
- `POST /api/notifications/test-email` : Envoie un email de test immédiat pour valider la configuration SMTP.

---

### 2. Frontend (`dashboard/frontend/src/`)

#### A. Onglet Notifications dans `SettingsView.vue`
Ajout d'une section claire et modulaire dans les paramètres :
1. **Carte Telegram :**
   - Toggle Activation (Oui / Non).
   - Champ `Bot Token` (masqué avec bouton afficher/masquer).
   - Champ `Chat ID` ou `Channel ID`.
   - Bouton « 🚀 Tester l'envoi Telegram » avec indicateur de succès/erreur.
2. **Carte Email (SMTP) :**
   - Toggle Activation (Oui / Non).
   - Serveur SMTP, Port, Sécurité (TLS / SSL / StartTLS).
   - Nom d'utilisateur & Mot de passe SMTP.
   - Adresse expéditeur et Adresses destinataires (séparées par des virgules).
   - Bouton « ✉️ Tester l'envoi Email ».
3. **Seuils de Déclenchement :**
   - Checkbox : `Alertes Critiques uniquement`.
   - Checkbox : `Anomalies Zero-Day`.
   - Checkbox : `Rapports de pic de trafic (> 5 000 paquets/sec)`.

---

## 📅 Étapes de Déploiement

1. **Étape 1 :** Création du module `services/notifications/` avec gestionnaire de file asynchrone (`asyncio.Queue` ou `BackgroundTasks`).
2. **Étape 2 :** Implémentation du client Telegram async + test unitaire.
3. **Étape 3 :** Implémentation du client Email SMTP + test unitaire.
4. **Étape 4 :** Ajout des endpoints de test et de configuration dans `routes.py`.
5. **Étape 5 :** Intégration de l'interface de paramétrage dans `SettingsView.vue`.
6. **Étape 6 :** Branchement sur le pipeline d'ingestion des alertes dans `nids_server.py`.
