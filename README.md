# DL_SOC
Great beginning
=======
# NIDS par ML/DL sur CIC-IDS2017 : évaluation rigoureuse et explicabilité

**Question** : quelles performances réelles obtiennent des modèles ML/DL sur CIC-IDS2017
avec une évaluation rigoureuse (nettoyage, pas de fuite de données), et quelles features
expliquent leurs décisions ?

## Démarrage
```bash
python -m venv .venv && source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements.txt
# Placer les CSV CIC-IDS2017 (MachineLearningCVE) dans data/raw/
python src/data_prep.py            # produit data/processed/{train,val,test}.parquet
python src/models_classic.py       # RF + XGBoost -> results/metrics/*.json
```

## Contrats
- Données : `train/val/test.parquet`, colonnes `label` (str), `label_id` (int), `is_attack` (0/1)
- Mapping des classes : `data/processed/label_map.json`
- Modèles : `train(X_train, y_train, X_val, y_val, config)` et `predict(model, X) -> (y_pred, y_proba)`
- Résultats : un JSON par modèle dans `results/metrics/` (écrit via `evaluation.save_metrics`)
- Seed = 42 partout. Aucun changement de données/split après le jour 5.

## Équipe
1 Données | 2 Modèles classiques | 3 Deep learning | 4 Évaluation + SHAP | 5 Rapport + slides
