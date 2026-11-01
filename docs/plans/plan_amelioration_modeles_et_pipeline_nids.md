# 📋 Plan d'Amélioration des Modèles & du Pipeline NIDS (DL_SOC)

## 🎯 Objectif & Contexte

Ce plan vise à clarifier, assainir et perfectionner l'écosystème d'intelligence artificielle du projet **DL_SOC**. Il résout la confusion architecturale actuelle (discordance entre 58 et 59 variables, accumulation d'artéfacts hétéroclites dans `models/`, notebook de recherche monolithique de 84 cellules non factorisées) et introduit des améliorations de pointe pour réduire les fausses alertes en environnement SOC et fiabiliser la détection des menaces 0-day.

---

## 🔍 Diagnostic des Frictions Actuelles

| Friction Identifiée | Impact Technique & Opérationnel | Solution Proposée |
| :--- | :--- | :--- |
| **Discordance dimensionnelle (58 vs 59)** | `feature_cols.json` déclare 58 features, mais le scaler et `dnn_v4.pt` attendent 59 entrées. Contournement par duplication artificielle du protocole dans `nids_core.py`. | Unification stricte sur 58 features canoniques et suppression du hack `np.insert`. |
| **Désordre dans `models/`** | Multiplicité de versions sans registre unifié (`dnn.pt`, `dnn_v3.pt`, `dnn_v4.pt`, multiples scalers). | Mise en place d'un **Model Registry** avec `manifest.json` et archivage des versions antérieures dans `models/archive/`. |
| **Monolithe de recherche `NIDS.ipynb`** | 84 cellules mélangeant extraction PCAP lourde, tests Colab éphémères et modélisation, avec toutes les sorties vidées. | Découpage modulaire et scripté (Extraction, Audit Data Leakage, Entraînement, Évaluation SOC avec graphiques exportés). |
| **Faux positifs & Calibration** | 300 à 600 fausses alertes sur le jeu de test. Probabilités Softmax brutes trop confiantes sur le trafic hors-distribution. | Calibration de probabilités (Temperature Scaling), benchmark tabulaire (LightGBM) et seuillage dynamique. |
| **Découplage DNN / Auto-encodeur** | Les deux modèles s'exécutent en parallèle sans règle de décision formelle d'ensemble ou de gestion d'incertitude. | Logique de décision unifiée à trois niveaux (Attaque connue / 0-day anomalie / Zone d'incertitude vers Active Learning). |

---

## 🔬 Évaluation Critique : Qu'est-ce qui augmente VRAIMENT l'efficacité du modèle ?

Il est primordial d'être rigoureux et scientifiquement honnête : **restructurer des fichiers ne rend pas magiquement un réseau de neurones plus intelligent**. 

Pour évaluer la rentabilité des efforts, nous distinguons formellement ce qui relève de **l'hygiène logicielle** de ce qui apporte des **gains algorithmiques mesurables** sur le taux de faux positifs, le rappel et le $F_1$-score.

### 1. Les Leviers à Fort Impact Algorithmique Mesurable

| Levier d'Amélioration | Mécanisme Scientifique | Gain Réel Attendu en Production |
| :--- | :--- | :--- |
| **Calibration des Probabilités (Temperature Scaling)** | Les DNN profonds avec Softmax souffrent d'une sur-confiance pathologique (*Guo et al., ICML 2017*). Un flux bénin atypique est fréquemment prédit comme attaque avec 99% de certitude. L'ajustement d'un facteur de température $T$ sur la validation réaligne les probabilités prédites sur les fréquences réelles. | 🎯 **Réduction immédiate de 30% à 50% des fausses alertes** (principale cause de saturation des analystes SOC). |
| **Arbitrage Conjoint DNN + Auto-Encodeur** | L'Auto-encodeur mesure la conformité d'un flux par rapport au trafic sain baseline ($\text{MSE} \le 0.6029$). Si le DNN alerte sur une attaque mais que l'Auto-encodeur indique une reconstruction quasi-parfaite ($\text{MSE} \ll 0.1$), le flux est requalifié comme faux positif potentiel du DNN. | 🛡️ **Filtrage des alertes fantômes** et qualification fiable des véritables 0-days (inconnus du DNN mais détectés par l'Auto-encodeur). |
| **Benchmark Tabulaire (LightGBM / CatBoost)** | Sur des métriques réseau statistiques tabulaires (durées, octets, drapeaux TCP, IAT), les modèles à base d'arbres boostés surpassent régulièrement les réseaux denses MLP (*Grinsztajn et al., NeurIPS 2022*). | 🚀 **Gain estimé de +1% à +3% de $F_1$-macro**, vitesse d'inférence CPU accrue et meilleure séparation des classes minoritaires (`WebAttack`, `Bot`). |
| **Suppression du Biais 59d (`protocol` dupliqué)** | Dans le modèle v4, la colonne `protocol` est injectée deux fois pour combler la dimension manquante. Cela biaise l'apprentissage en sur-pondérant artificiellement le protocole au détriment des caractéristiques dynamiques du flux. | 📈 **Régularité accrue des gradients** et élimination d'artefacts décisionnels indésirables. |
| **Boucle Active Learning (`feedback_flows`)** | Le jeu CIC-IDS2017 reflète un réseau de laboratoire unique en 2017. Tout trafic moderne subit un glissement de distribution (*domain shift*). Ré-entraîner avec les qualifications humaines est le seul moyen de progresser dans le temps. | 🔄 **Adaptation continue aux nouveaux patterns d'attaque** et non-obsolescence du modèle. |

### 2. Les Leviers de Stabilité & Hygiène Logicielle (N'améliorent pas le $F_1$, mais préviennent les pannes)

* **Le `manifest.json` et le nettoyage de `models/`** n'augmentent pas la précision intrinsèque. Ils éliminent le risque critique d'utiliser le mauvais scaler avec le mauvais checkpoint ou de charger un modèle à 3 classes au lieu de 12.
* **La modularisation de `NIDS.ipynb`** ne change pas les poids du modèle mais permet la reproductibilité, l'auditabilité et le versionnage sain du code d'entraînement.

### 3. Protocole Expérimental « Mesurer Avant / Après »

Aucune modification algorithmique ne sera promue en production sans validation empirique sur le banc de test :
1. **Baseline T0** : Évaluation du modèle v4 actuel sur le jeu de test de référence (nombre exact de faux positifs, faux négatifs, $F_1$-score macro, temps d'inférence par flux).
2. **Évaluation T1 (Calibration & Double Barrière)** : Mesure de la réduction des fausses alertes sans dégradation du rappel des attaques.
3. **Évaluation T2 (Modèle v5 / LightGBM)** : Comparaison stricte sur les mêmes métriques.

---

## 🏗️ Architecture Cible du Registre de Modèles & Inférence

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        REGISTRE DE MODÈLES : models/                            │
│                                                                                 │
│   manifest.json  <── Déclare la version active, classes, scalers et seuils     │
│   ├── classes.json              (Liste des classes supportées)                 │
│   ├── schema_features.json      (58 features canoniques et types)               │
│   ├── active/                                                                   │
│   │   ├── dnn_v4.pt             (Modèle supervisé calibré)                      │
│   │   ├── scaler_v4.joblib      (StandardScaler 58 variables)                   │
│   │   ├── ae_v1.pt              (Auto-encodeur non-supervisé)                   │
│   │   ├── scaler_ae_v1.joblib   (StandardScaler Auto-encodeur)                  │
│   │   └── meta_v4.json          (Hyperparamètres, métriques & reproductibilité) │
│   └── archive/                  (dnn.pt, dnn_v3.pt, scalers historiques)        │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ Initialisation
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        MOTEUR D'INFÉRENCE : nids_core.py                        │
│                                                                                 │
│   1. Validation stricte du vecteur (58 features exactes)                        │
│   2. Nettoyage mathématique : inf -> NaN -> 0, clip(min=0), log1p              │
│   3. Double scoring parallèle :                                                 │
│      ├── DNN Multi-classes  ──> Logits calibrés + Confiance réelle              │
│      └── Auto-Encodeur      ──> Erreur de reconstruction MSE                    │
│   4. Arbitrage SOC unifié :                                                     │
│      • Attaque connue (DNN Confiance > 85%)                                     │
│      • Alerte 0-Day / Anomalie (MSE > seuil quantile 99.9%)                     │
│      • Trafic Bénin certifié (DNN Benign + MSE normal)                          │
│      • Flux ambigu / incertain ──> Ingestion automatique Active Learning        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Plan d'Action en 5 Phases

### Phase 1 : Clarification & Verrouillage du Schéma (58 Features)
- [ ] **Définir le Schéma Canonique** : Créer `models/schema_features.json` documentant explicitement les 58 caractéristiques NFStream (nom, type, borne min, description sémantique).
- [ ] **Supprimer le Contournement 59d** :
  - Créer un scaler propre à 58 features pour la version cible (`v5` ou alignement `v4`).
  - Éliminer le bloc `np.insert(..., proto_idx)` dans `nids_core.py`.
- [ ] **Garantir la Validation Pydantic / Pandas** : Valider les colonnes dès l'entrée d'ingestion avec un message d'erreur explicite en cas d'écart.

### Phase 2 : Restructuration du Dossier `models/` (Model Registry)
- [ ] **Nettoyage et Archivage** :
  - Déplacer `dnn.pt`, `dnn_v3.pt`, `dnn_model_v3.pt`, `scaler.joblib`, `scaler_v2.joblib`, `scaler_v3.joblib` vers `models/archive/`.
- [ ] **Création du `manifest.json`** :
  ```json
  {
    "active_version": "v4",
    "classes_file": "classes.json",
    "schema_file": "schema_features.json",
    "supervised": {
      "model_file": "dnn_v4.pt",
      "scaler_file": "scaler_v4.joblib",
      "features_count": 58,
      "calibration": "temperature_scaling"
    },
    "unsupervised": {
      "model_file": "ae_v1.pt",
      "scaler_file": "scaler_ae_v1.joblib",
      "threshold_mse": 0.6029
    }
  }
  ```
- [ ] **Mise à Jour de `nids_core.py`** : Permettre l'instanciation de `Scorer(manifest_path="models/manifest.json")` tout en maintenant la rétrocompatibilité des arguments.

### Phase 3 : Modularisation & Modernisation de `NIDS.ipynb`
- [ ] **Scinder le Monolithe en Modules Clairs** :
  1. `01_extraction_pcap_nfstream.py` / section : Extraction reproductible hors-Colab.
  2. `02_data_leakage_audit.ipynb` : Vérification rigoureuse de non-chevauchement temporel et analyse des distributions.
  3. `03_model_benchmarks.ipynb` : Entraînement comparatif rigoureux (MLP PyTorch vs LightGBM vs Auto-encodeur).
  4. `04_soc_evaluation.ipynb` : Métriques opérationnelles orientées SOC (matrices de confusion normalisées, taux de faux positifs par heure de trafic, courbes de précision/rappel).
- [ ] **Persistance des Graphiques d'Évaluation** : Exporter automatiquement les courbes d'apprentissage, matrices de confusion et histogrammes MSE dans `docs/models_metrics/`.

### Phase 4 : Améliorations Algorithmiques & Réduction des Faux Positifs
- [ ] **Calibration des Probabilités (Temperature Scaling)** :
  - Ajuster un paramètre de température $T$ sur le jeu de validation pour calibrer les probabilités Softmax.
  - Empêcher la sur-confiance sur les flux atypiques mais bénins.
- [ ] **Benchmark Tabulaire Gradient Boosting (LightGBM)** :
  - Évaluer un modèle LightGBM sur les 58 features tabulaires comme référence de comparaison face au DNN PyTorch.
- [ ] **Logique d'Ensemble & Fusion Raisonnée** :
  - Formaliser le moteur d'arbitrage dans `nids_core.py` : corréler la certitude du DNN avec la reconstruction de l'Auto-encodeur pour qualifier précisément le niveau de sévérité de l'alerte.

### Phase 5 : MLOps & Boucle Active Learning Continue
- [ ] **Industrialiser `retrain_dnn_v5_colab.ipynb`** :
  - Automatiser la fusion du jeu de base CIC-IDS2017 avec les qualifications issues de `feedback_flows` (table SQLite).
  - Validation automatique : rejet du nouveau modèle si les faux positifs augmentent de plus de 5% par rapport au modèle en production.
- [ ] **Génération du Rapport Comparatif v4 vs v5** :
  - Rapport Markdown synthétique généré à l'issue de chaque réentraînement comparant F1-macro, faux positifs et taux de détection 0-day.

---

## ✅ Critères de Succès & Validation

1. **Intégrité Dimensionnelle** : 0 duplication artificielle de features dans le code d'inférence. Schéma strict à 58 colonnes.
2. **Non-Régression Fonctionnelle** : 100% des tests unitaires validés (`pytest -v tests/`, 30/30 tests réussis).
3. **Réduction Documentée des Faux Positifs** : Baisse mesurée de 30% à 50% des fausses alertes sur le jeu de test de référence par rapport à la v4 non calibrée.
4. **Temps d'Inférence Préservé** : Inférence par lot inférieure à 15 ms pour 1 000 flux sur CPU standard.
5. **Clarté Opérationnelle** : Dossier `models/` épuré, lisible en moins de 2 minutes par un nouvel ingénieur ou analyste SOC.

---

## ⚡ Feuille de Route d'Exécution Rapide

Pour une mise en œuvre en mode commando, consultez la [Feuille de Route Sprint 12h / 24h](file:///home/hoby/Documents/Projet-dev/IA/DL_SOC/docs/plans/feuille_de_route_sprint_12h_24h.md).

