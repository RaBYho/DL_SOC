import json, joblib, numpy as np, pandas as pd, torch, torch.nn as nn

class Scorer:
    """Rejoue exactement la chaîne d'entraînement : colonnes -> nettoyage -> log1p -> scaler -> DNN."""
    def __init__(self, base, version="v4", device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.feature_cols = json.load(open(f"{base}/models/feature_cols.json"))
        self.classes = json.load(open(f"{base}/models/classes.json") if not isinstance(json.load(open(f"{base}/models/classes.json")), dict) else list(json.load(open(f"{base}/models/classes.json")).keys()))
        if isinstance(self.classes, dict):
            self.classes = list(self.classes.keys())
        self.scaler = joblib.load(f"{base}/models/scaler_{version}.joblib")
        ck = torch.load(f"{base}/models/dnn_{version}.pt", map_location=self.device)
        a = ck["architecture"]
        self.model = nn.Sequential(
            nn.Linear(a["entree"], 256), nn.BatchNorm1d(256), nn.ReLU(), nn.Dropout(a["dropout"]),
            nn.Linear(256, 128), nn.BatchNorm1d(128), nn.ReLU(), nn.Dropout(a["dropout"]),
            nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, a["sortie"])).to(self.device)
        self.model.load_state_dict(ck["state_dict"])
        self.model.eval()

    def predict_df(self, flows: pd.DataFrame) -> pd.DataFrame:
        manquantes = [c for c in self.feature_cols if c not in flows.columns]
        if manquantes:
            raise ValueError(f"Colonnes manquantes : {manquantes}")
        X = flows[self.feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0)
        X_values = X.values
        if X.shape[1] == 58 and self.scaler.n_features_in_ == 59:
            proto_idx = X.columns.get_loc("protocol")
            X_values = np.insert(X_values, proto_idx, X_values[:, proto_idx], axis=1)
        X_prep = np.log1p(np.clip(X_values, a_min=0, a_max=None)).astype("float32")
        X_scaled = self.scaler.transform(X_prep).astype("float32")
        out = []
        with torch.no_grad():
            for i in range(0, len(X_scaled), 50000):
                xb = torch.tensor(X_scaled[i:i + 50000]).to(self.device)
                out.append(torch.softmax(self.model(xb), dim=1).cpu().numpy())
        proba = np.concatenate(out) if out else np.empty((0, len(self.classes)))
        ids = proba.argmax(1)
        return pd.DataFrame({"pred_id": ids,
                             "pred": [self.classes[i] for i in ids],
                             "confiance": proba.max(1) if len(ids) else []},
                            index=flows.index)
