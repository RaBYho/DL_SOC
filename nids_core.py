import json
from pathlib import Path
import time
import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn


class Scorer:
    """Rejoue exactement la chaîne d'entraînement : colonnes -> nettoyage -> log1p -> scaler -> DNN + Autoencodeur."""

    def __init__(self, base, version=None, ae_version=None, manifest_path=None, device=None):
        self.base = str(base)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        # 1. Chargement déclaratif depuis le manifest.json si présent
        manifest_file = Path(manifest_path) if manifest_path else (Path(base) / "models" / "manifest.json")
        self.manifest = None
        if manifest_file.exists():
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    self.manifest = json.load(f)
            except Exception:
                self.manifest = None

        if self.manifest:
            active_v = self.manifest.get("active_version", "v4")
            self.version = version or active_v
            self.ae_version = ae_version or self.manifest.get("unsupervised", {}).get("version", "v1")

            features_file = self.manifest.get("feature_cols_file", "feature_cols.json")
            classes_file = self.manifest.get("classes_file", "classes.json")
            dnn_file = self.manifest.get("supervised", {}).get("model_file", f"dnn_{self.version}.pt")
            scaler_file = self.manifest.get("supervised", {}).get("scaler_file", f"scaler_{self.version}.joblib")

            ae_file = self.manifest.get("unsupervised", {}).get("model_file", f"ae_{self.ae_version}.pt")
            ae_meta_file = self.manifest.get("unsupervised", {}).get("meta_file", f"meta_ae_{self.ae_version}.json")
            ae_scaler_file = self.manifest.get("unsupervised", {}).get("scaler_file", f"scaler_ae_{self.ae_version}.joblib")
            ae_threshold = self.manifest.get("unsupervised", {}).get("threshold_mse")
        else:
            self.version = version or "v4"
            self.ae_version = ae_version or "v1"
            features_file = "feature_cols.json"
            classes_file = "classes.json"
            dnn_file = f"dnn_{self.version}.pt"
            scaler_file = f"scaler_{self.version}.joblib"
            ae_file = f"ae_{self.ae_version}.pt"
            ae_meta_file = f"meta_ae_{self.ae_version}.json"
            ae_scaler_file = f"scaler_ae_{self.ae_version}.joblib"
            ae_threshold = None

        with open(f"{base}/models/{features_file}", "r", encoding="utf-8") as f:
            self.feature_cols = json.load(f)

        with open(f"{base}/models/{classes_file}", "r", encoding="utf-8") as f:
            classes_data = json.load(f)
        self.classes = list(classes_data.keys()) if isinstance(classes_data, dict) else classes_data

        # Modèle supervisé DNN
        self.scaler = joblib.load(f"{base}/models/{scaler_file}")
        ck = torch.load(f"{base}/models/{dnn_file}", map_location=self.device, weights_only=False)
        a = ck["architecture"]
        self.model = nn.Sequential(
            nn.Linear(a["entree"], 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(a["dropout"]),
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(a["dropout"]),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, a["sortie"]),
        ).to(self.device)
        self.model.load_state_dict(ck["state_dict"])
        self.model.eval()

        # Calibration des probabilités (Temperature Scaling)
        self.temperature = 1.0
        if self.manifest and "supervised" in self.manifest:
            self.temperature = float(self.manifest["supervised"].get("temperature", 1.0))

        # Modèle non-supervisé Auto-encodeur (si présent)
        self.ae_model = None
        self.scaler_ae = None
        self.ae_seuil = None

        ae_path = Path(base) / "models" / ae_file
        ae_meta_path = Path(base) / "models" / ae_meta_file
        ae_scaler_path = Path(base) / "models" / ae_scaler_file

        if ae_path.exists() and ae_meta_path.exists() and ae_scaler_path.exists():
            with open(ae_meta_path, "r", encoding="utf-8") as f:
                ae_meta = json.load(f)
            self.ae_seuil = float(ae_threshold if ae_threshold is not None else ae_meta.get("seuil_q999", 0.6029))
            archi = ae_meta.get("archi", [59, 32, 16, 8, 16, 32, 59])
            layers = []
            for i in range(len(archi) - 1):
                layers.append(nn.Linear(archi[i], archi[i + 1]))
                if i < len(archi) - 2:
                    layers.append(nn.ReLU())
            self.ae_model = nn.Sequential(*layers).to(self.device)
            self.ae_model.load_state_dict(torch.load(ae_path, map_location=self.device, weights_only=False))
            self.ae_model.eval()
            self.scaler_ae = joblib.load(ae_scaler_path)

    @property
    def has_ae(self) -> bool:
        return self.ae_model is not None

    def predict_df(self, flows: pd.DataFrame) -> pd.DataFrame:
        if len(flows) == 0:
            cols = ["pred_id", "pred", "confiance"]
            if self.has_ae:
                cols += ["mse_ae", "anomalie_ae"]
            return pd.DataFrame(columns=cols, index=flows.index)

        t_start = time.perf_counter()

        manquantes = [c for c in self.feature_cols if c not in flows.columns]
        if manquantes:
            raise ValueError(f"Colonnes manquantes : {manquantes}")

        X = flows[self.feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0)
        X_values = X.values

        # Inférence DNN
        if X.shape[1] == 58 and self.scaler.n_features_in_ == 59:
            proto_idx = X.columns.get_loc("protocol")
            X_values = np.insert(X_values, proto_idx, X_values[:, proto_idx], axis=1)

        X_prep = np.log1p(np.clip(X_values, a_min=0, a_max=None)).astype("float32")
        X_scaled = self.scaler.transform(X_prep).astype("float32")

        out = []
        with torch.no_grad():
            for i in range(0, len(X_scaled), 50000):
                xb = torch.tensor(X_scaled[i : i + 50000]).to(self.device)
                logits = self.model(xb)
                if self.temperature != 1.0:
                    logits = logits / self.temperature
                out.append(torch.softmax(logits, dim=1).cpu().numpy())
        proba = np.concatenate(out) if out else np.empty((0, len(self.classes)))
        ids = proba.argmax(1)

        res_dict = {
            "pred_id": ids,
            "pred": [self.classes[i] for i in ids],
            "confiance": proba.max(1) if len(ids) else [],
        }

        # Inférence Auto-encodeur
        if self.has_ae:
            X_ae_values = X.values
            if X.shape[1] == 58 and self.scaler_ae.n_features_in_ == 59:
                proto_idx = X.columns.get_loc("protocol")
                X_ae_values = np.insert(X_ae_values, proto_idx, X_ae_values[:, proto_idx], axis=1)

            X_ae_prep = np.log1p(np.clip(X_ae_values, a_min=0, a_max=None)).astype("float32")
            X_ae_scaled = self.scaler_ae.transform(X_ae_prep).astype("float32")

            out_ae = []
            with torch.no_grad():
                for i in range(0, len(X_ae_scaled), 50000):
                    xb_ae = torch.tensor(X_ae_scaled[i : i + 50000]).to(self.device)
                    xb_rec = self.ae_model(xb_ae)
                    mse_batch = torch.mean((xb_ae - xb_rec) ** 2, dim=1).cpu().numpy()
                    out_ae.append(mse_batch)

            mse_ae = np.concatenate(out_ae) if out_ae else np.empty((0,))
            res_dict["mse_ae"] = mse_ae
            res_dict["anomalie_ae"] = mse_ae > self.ae_seuil

        duration_ms = (time.perf_counter() - t_start) * 1000.0
        try:
            from dashboard.backend.model_logger import log_inference
            log_inference(
                flows_count=len(flows),
                duration_ms=duration_ms,
                predictions=res_dict["pred"],
                confidences=res_dict.get("confiance"),
                mse_ae=res_dict.get("mse_ae"),
                anomalie_ae=res_dict.get("anomalie_ae"),
                device=str(self.device),
                model_version=getattr(self, "version", "v4"),
                flows_df=flows,
            )
        except Exception:
            pass

        return pd.DataFrame(res_dict, index=flows.index)
