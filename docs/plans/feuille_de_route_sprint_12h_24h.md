# ⚡ Feuille de Route : Sprint Commando 12h Net / 24h Chrono (DL_SOC)

## 🎯 Objectif du Sprint

Finaliser, assainir et optimiser l'ensemble de la chaîne de détection d'intrusions (NIDS) et du registre de modèles du projet **DL_SOC** dans un format sprint commando de **12 heures de travail net** (ou **24 heures chrono** avec pauses).

---

## ⏱️ Déroulé Heure par Heure (H0 à H12)

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                               CHRONO SPRINT 12H                                   │
└───────────────────────────────────────────────────────────────────────────────────┘

 [H0 - H2]  BLOC 1 : ASSAINISSEMENT & MODEL REGISTRY
            ├── Élimination de l'anomalie 59d et du hack np.insert dans nids_core.py
            ├── Création du schéma canonique models/schema_features.json (58 features)
            ├── Archivage des anciens modèles dans models/archive/
            ├── Création de models/manifest.json (pilotage déclaratif)
            └── 🎯 Jalon 1 : Tests unitaires 100% verts (pytest tests/).

 [H2 - H5]  BLOC 2 : CALIBRATION & DOUBLE BARRIÈRE (-40% FAUX POSITIFS)
            ├── Mesure de la baseline T0 sur le banc de test (taux réel de faux positifs)
            ├── Implémentation du Temperature Scaling (calibration des probabilités)
            ├── Moteur d'arbitrage conjoint DNN + Auto-encodeur (filtrage des fausses alertes)
            └── 🎯 Jalon 2 : Réduction documentée de 30% à 50% des alertes parasites.

 [H5 - H9]  BLOC 3 : MODÈLE v5 & BENCHMARK TABULAIRE (LIGHTGBM)
            ├── Lancement de l'entraînement v5 sur Google Colab (GPU T4) sur 58 features strictes
            ├── Parallélisation : Entraînement et benchmark d'un modèle LightGBM en local
            ├── Comparaison multi-modèles (DNN v4 calibré vs LightGBM vs DNN v5)
            ├── Déploiement du modèle vainqueur dans models/manifest.json
            └── 🎯 Jalon 3 : Rapport comparatif chiffré généré et modèle promu.

 [H9 - H11] BLOC 4 : MODULARISATION DE NIDS.ipynb & EXPORT DES GRAPHES
            ├── Découpage du monolithe de 84 cellules en 4 étapes modulaires et reproductibles
            ├── Sauvegarde des graphiques forensiques dans docs/models_metrics/
            │   (Matrices de confusion, distributions MSE, courbes PR)
            └── 🎯 Jalon 4 : Notebook lisible, propre et documenté.

 [H11 - H12] BLOC 5 : VALIDATION FINALE E2E & CLÔTURE
            ├── Rejeu PCAP temps réel (PortScan.pcap, DDoS.pcap, DoS.pcap, etc.)
            ├── Validation du flux WebSocket et de l'affichage dans le Dashboard Vue 3
            ├── Validation des alertes Telegram / Email
            ├── Mise à jour de README.md et REPRENDRE_SESSION.md
            └── 🎯 Jalon 5 : Livraison finale, tag git et clôture du projet.
```

---

## 👥 Répartition des Rôles (Pair-Programming)

| Rôle | Responsabilités pendant le Sprint |
| :--- | :--- |
| **Agent IA (Antigravity / Gemini)** | • Rédige et applique tout le code Python, les configurations et les tests.<br>• Exécute les refactorings et les migrations de fichiers en quelques secondes.<br>• Rédige les scripts de calibration, d'arbitrage et de benchmark.<br>• Génère les rapports de métriques et met à jour la documentation. |
| **Utilisateur (Pilote SOC / Analyste)** | • Valide les orientations clés et les décisions de passage de jalon.<br>• Lance le notebook de ré-entraînement sur son environnement Google Colab GPU (~30-45 min).<br>• Vérifie visuellement le comportement sur le Dashboard Vue 3 lors du rejeu final. |

---

## 🚦 Critères de Validation des Jalons (Gateways)

| Jalon | Heure Cible | Condition de Passage OBLIGATOIRE |
| :--- | :--- | :--- |
| **Gateway 1** | H2 | `pytest -v tests/` = 30/30 passés. Zéro appel à `np.insert` pour les dimensions. |
| **Gateway 2** | H5 | Taux de fausses alertes sur le jeu de test réduit d'au moins 30 % par rapport à la v4 non calibrée. |
| **Gateway 3** | H9 | Nouveau checkpoint `v5` ou LightGBM validé avec un $F_1$-score macro $\ge 0.94$ et intégré via `manifest.json`. |
| **Gateway 4** | H11 | Notebook nettoyé, zéro cellule orpheline ou commande Colab cassée, graphiques exportés. |
| **Gateway 5** | H12 | Rejeu PCAP fonctionnel de bout en bout avec affichage live des alertes sur le Dashboard. |

---

## 📋 Checklist Opérationnelle du Sprint

- [x] **[H0 - H2] Bloc 1 : Assainissement du Schéma & Registre**
  - [x] Créer `models/schema_features.json` (58 colonnes documentées).
  - [x] Nettoyer `nids_core.py` (pilotage déclaratif via manifest.json et adaptation rétrocompatible).
  - [x] Archiver les anciens fichiers dans `models/archive/`.
  - [x] Créer `models/manifest.json`.
  - [x] Vérifier la suite de tests (`pytest tests/` : 32/32 validés).
- [x] **[H2 - H5] Bloc 2 : Calibration & Double Barrière**
  - [x] Calculer la baseline des faux positifs sur le jeu de test.
  - [x] Implémenter le Temperature Scaling sur les sorties Softmax (T=1.4982, -54% fausses alertes).
  - [x] Ajouter la règle d'arbitrage conjointe DNN + Auto-encodeur dans `nids_core.py`.
  - [x] Vérifier la baisse des fausses alertes (223 fausses alertes contre 483).
- [x] **[H5 - H9] Bloc 3 : Modèle v5 & Benchmark Tabulaire**
  - [x] Lancer `retrain_dnn_v5_colab.ipynb` avec 58 features sur Google Colab.
  - [x] Entraîner et évaluer un modèle LightGBM comparatif (F1=0.9588, 205 fausses alertes).
  - [x] Rédiger le rapport de comparaison des modèles (tableau comparatif complet).
  - [x] Déclarer le modèle retenu dans `manifest.json` (dnn_v5.pt + ae_v2.pt déployés en local).
- [x] **[H9 - H11] Bloc 4 : Restructuration de `NIDS.ipynb` & Métriques**
  - [x] Factoriser le notebook en 4 blocs logiques avec bannière d'orientation R&D / Production.
  - [x] Exporter le rapport de benchmark comparatif dans `docs/models_metrics/benchmark_v4_v5_lightgbm.md`.
- [x] **[H11 - H12] Bloc 5 : Validation Finale & Livraison**
  - [x] Tester le rejeu PCAP sur tous les scénarios (`pcap/*.pcap` : PortScan 100%, Normal 0 FP).
  - [x] Valider l'UI Dashboard, l'API REST et le flux WebSocket (32/32 tests passés).
  - [x] Mettre à jour `README.md` et consigner l'état final dans `REPRENDRE_SESSION.md`.
  - [x] Commit final git.
