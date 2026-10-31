# 📋 Plan 3 : Triage Zero-Day & Human-in-the-Loop (Active Learning)

## 🎯 Objectif
Permettre à l'analyste SOC d'inspecter en profondeur n'importe quel flux réseau suspect (notamment les anomalies Zero-Day ou les détections incertaines du modèle), de corriger les erreurs de prédiction (faux positifs ou mauvaise classe), et d'enregistrer ces qualifications humaines dans un jeu de données persistant pour le ré-entraînement du NIDS (*Active Learning*).

---

## 🏗️ Architecture Technique

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       FLUX RÉSEAU DÉTECTÉ OU SUSPECT                        │
│                 (Score MSE Anormal ou Classification Ambiguë)               │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TIROIR D'INSPECTION D'INCIDENT (UI)                      │
│        • Métadonnées réseau (IP, Port, Flags TCP, Octets, Durée)            │
│        • Caractéristiques brutes extraites (Features Vector)                │
│        • Comparaison visuelle avec la baseline normale (Radar / Barres)     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                       QUALIFICATION PAR L'ANALYSTE
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
┌───────────────────┐        ┌───────────────────┐        ┌───────────────────┐
│   Faux Positif    │        │  Attaque Connue   │        │   Nouveau Zero-Day│
│  (Trafic Bénin)   │        │   Reclassifiée    │        │      Confirmé     │
└─────────┬─────────┘        └─────────┬─────────┘        └─────────┬─────────┘
          │                            │                            │
          └────────────────────────────┼────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TABLE SQLITE : feedback_flows                            │
│  (Stockage immuable des caractéristiques + qualification humaine)           │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   PIPELINE DE RÉ-ENTRAÎNEMENT (OFFLINE)                     │
│  • Export CSV / Parquet des feedbacks                                       │
│  • Ajustement des seuils de l'Auto-Encodeur & Fine-tuning du Classifieur   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Composants à Implémenter

### 1. Base de Données (`dashboard/backend/database.py`)

#### Nouvelle Table `feedback_flows`
```sql
CREATE TABLE IF NOT EXISTS feedback_flows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    src_ip TEXT,
    dst_ip TEXT,
    src_port INTEGER,
    dst_port INTEGER,
    protocol TEXT,
    raw_features JSON,               -- 78+ caractéristiques brutes (durée, flags, etc.)
    model_predicted_label TEXT,       -- Label initial de l'IA (ex: BENIGN, DoS, Anomaly)
    model_mse_score REAL,             -- Score d'erreur de reconstruction de l'Auto-Encodeur
    human_verdict TEXT NOT NULL,      -- 'FALSE_POSITIVE', 'KNOWN_ATTACK', 'CONFIRMED_ZERODAY'
    corrected_attack_type TEXT,       -- Si KNOWN_ATTACK ou ZERODAY : nom de la menace
    analyst_notes TEXT,               -- Commentaires libres de l'analyste
    status TEXT DEFAULT 'PENDING'     -- 'PENDING', 'EXPORTED', 'RETRAINED'
);
```

---

### 2. Backend (`dashboard/backend/`)

#### Endpoints API
- `GET /api/incidents/{incident_id}/details` :
  - Retourne l'ensemble des métadonnées du flux, le vecteur de features normalisé et non-normalisé, et l'explication des features ayant le plus contribué au score MSE élevé.
- `POST /api/incidents/{incident_id}/feedback` :
  - Enregistre la décision de l'analyste dans `feedback_flows`.
  - Met à jour le statut de l'incident dans la table principale (badge « Qualifié par Analyste »).
- `GET /api/feedback/summary` :
  - Statistiques sur le taux de faux positifs et nombre de zero-days étiquetés.
- `GET /api/feedback/export` :
  - Téléchargement du jeu de données étiqueté au format JSON ou CSV prêt pour l'entraînement PyTorch / Scikit-Learn.

---

### 3. Frontend (`dashboard/frontend/src/`)

#### A. Tiroir d'Inspection d'Incident (`components/incidents/IncidentDrawer.vue`)
Accessible en cliquant sur n'importe quelle ligne de la table des incidents :
1. **En-tête de l'Incident :**
   - Type détecté, niveau de sévérité, horodatage précis et score d'anomalie MSE.
2. **Métriques Clés du Flux :**
   - Badges pour IP source/destination, ports, protocole, durée de connexion.
   - Drapeaux TCP activés (SYN, ACK, FIN, RST, PSH, URG).
3. **Graphique d'Explicabilité :**
   - Affichage des 5 attributs les plus anormaux qui ont fait réagir l'Auto-Encodeur (ex : débit de paquets/sec x10 par rapport à la normale, ratio octets/paquet inhabituel).
4. **Formulaire de Qualification (Human-in-the-Loop) :**
   - Trois boutons radio stylisés :
     - 🟢 **Faux Positif (Bénin)** : Ce flux est légitime.
     - 🟠 **Attaque Connue Reclassifiée** : Sélection de la vraie catégorie dans une liste déroulante (DDoS, PortScan, BruteForce, Infiltration, Botnet).
     - 🟣 **Nouveau Zero-Day Confirmé** : Saisie d'un identifiant ou tag personnalisé pour cette nouvelle signature.
   - Champ texte optionnel : *Notes d'investigation de l'analyste*.
   - Bouton d'action : `[💾 Enregistrer la Qualification]`.

#### B. Mise à jour de la Table des Incidents
- Ajout d'une colonne ou badge de statut :
  - `Non Qualifié` (par défaut).
  - `✅ Faux Positif` (grisé, retiré des alertes actives).
  - `👾 Zero-Day Qualifié` (badge violet avec nom de la menace).

---

## 📅 Étapes de Déploiement

1. **Étape 1 :** Création de la table `feedback_flows` et des fonctions d'écriture dans `database.py`.
2. **Étape 2 :** Implémentation des endpoints de détails et de feedback dans `routes.py`.
3. **Étape 3 :** Création du composant `IncidentDrawer.vue` avec onglet d'inspection des features.
4. **Étape 4 :** Intégration du formulaire de qualification et synchronisation avec le store Pinia (`socStore.js`).
5. **Étape 5 :** Ajout de la fonction d'export du dataset de feedback pour le ré-entraînement.
