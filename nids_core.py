import json
from pathlib import Path
import time
import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn


class Scorer:
    """Rejoue exactement la chaîne d'entraînement : colonnes -> nettoyage -> log1p -> scaler -> DNN + LightGBM + Autoencodeur."""

    def __init__(self, base=".", version=None, ae_version=None, manifest_path=None, device=None):
        self.base = str(base)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        models_dir = Path(base) / "models"

        # 1. Résolution intelligente du manifest.json ou manifest_v5.json
        manifest_file = None
        if manifest_path:
            manifest_file = Path(manifest_path)
        else:
            candidates = [
                models_dir / "manifest.json",
                models_dir / "manifest_v5.json",
            ]
            for cand in candidates:
                if cand.exists():
                    manifest_file = cand
                    break

        self.manifest = None
        if manifest_file and manifest_file.exists():
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    self.manifest = json.load(f)
            except Exception:
                self.manifest = None

        if self.manifest:
            active_v = self.manifest.get("active_version", "v5")
            self.version = version or active_v
            self.ae_version = ae_version or self.manifest.get("unsupervised", {}).get("version", "v2")

            features_file = self.manifest.get("feature_cols_file", "feature_cols.json")
            classes_file = self.manifest.get("classes_file", "classes.json")
            dnn_file = self.manifest.get("supervised", {}).get("model_file", f"dnn_{self.version}.pt")
            scaler_file = self.manifest.get("supervised", {}).get("scaler_file", f"scaler_{self.version}.joblib")

            ae_file = self.manifest.get("unsupervised", {}).get("model_file", f"ae_{self.ae_version}.pt")
            ae_meta_file = self.manifest.get("unsupervised", {}).get("meta_file", f"meta_ae_{self.ae_version}.json")
            ae_scaler_file = self.manifest.get("unsupervised", {}).get("scaler_file", f"scaler_ae_{self.ae_version}.joblib")
            ae_threshold = self.manifest.get("unsupervised", {}).get("threshold_mse")
        else:
            # Détection automatique de v5 et v2 si dnn_v5.pt et ae_v2.pt existent
            if (models_dir / "dnn_v5.pt").exists() and (models_dir / "ae_v2.pt").exists():
                default_v = "v5"
                default_ae_v = "v2"
            else:
                default_v = "v4"
                default_ae_v = "v1"

            self.version = version or default_v
            self.ae_version = ae_version or default_ae_v
            features_file = "feature_cols.json"
            classes_file = "classes.json"
            dnn_file = f"dnn_{self.version}.pt"
            scaler_file = f"scaler_{self.version}.joblib"
            ae_file = f"ae_{self.ae_version}.pt"
            ae_meta_file = f"meta_ae_{self.ae_version}.json"
            ae_scaler_file = f"scaler_ae_{self.ae_version}.joblib"
            ae_threshold = None

        with open(models_dir / features_file, "r", encoding="utf-8") as f:
            self.feature_cols = json.load(f)

        with open(models_dir / classes_file, "r", encoding="utf-8") as f:
            classes_data = json.load(f)
        self.classes = list(classes_data.keys()) if isinstance(classes_data, dict) else list(classes_data)
        self.benign_id = self.classes.index("BENIGN") if "BENIGN" in self.classes else 0

        # Modèle supervisé DNN
        self.scaler = joblib.load(models_dir / scaler_file)
        ck = torch.load(models_dir / dnn_file, map_location=self.device, weights_only=False)
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
        if self.manifest and "supervised" in self.manifest and "temperature" in self.manifest["supervised"]:
            self.temperature = float(self.manifest["supervised"]["temperature"])
        elif isinstance(ck, dict) and "temperature_calibree" in ck:
            self.temperature = float(ck["temperature_calibree"])

        # Chargement optionnel et résilient de LightGBM
        self.lgb_model = None
        try:
            import lightgbm as lgb
            lgb_filename = f"lgb_{self.version}.txt"
            if self.manifest and "supervised" in self.manifest and "lgb_file" in self.manifest["supervised"]:
                lgb_filename = self.manifest["supervised"]["lgb_file"]
            lgb_path = models_dir / lgb_filename
            if lgb_path.exists():
                self.lgb_model = lgb.Booster(model_file=str(lgb_path))
        except Exception:
            self.lgb_model = None

        # Modèle non-supervisé Auto-encodeur (si présent)
        self.ae_model = None
        self.scaler_ae = None
        self.ae_seuil = None
        self.ae_seuil_sain = None

        ae_path = models_dir / ae_file
        ae_meta_path = models_dir / ae_meta_file
        ae_scaler_path = models_dir / ae_scaler_file

        if ae_path.exists() and ae_meta_path.exists() and ae_scaler_path.exists():
            with open(ae_meta_path, "r", encoding="utf-8") as f:
                ae_meta = json.load(f)
            self.ae_seuil = float(ae_threshold if ae_threshold is not None else ae_meta.get("seuil_q999", 1.4810))
            self.ae_seuil_sain = float(ae_meta.get("seuil_sain_q90", min(0.10, self.ae_seuil * 0.25)))
            archi = ae_meta.get("archi", [58, 32, 16, 8, 16, 32, 58])
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

        # Niveau 1 — Inférence Supervisée & Fusion (Soft Voting DNN + LightGBM)
        out_dnn = []
        with torch.no_grad():
            for i in range(0, len(X_scaled), 50000):
                xb = torch.tensor(X_scaled[i : i + 50000]).to(self.device)
                logits = self.model(xb)
                if self.temperature != 1.0:
                    logits = logits / self.temperature
                out_dnn.append(torch.softmax(logits, dim=1).cpu().numpy())
        proba_dnn = np.concatenate(out_dnn, axis=0) if out_dnn else np.empty((0, len(self.classes)))

        if self.lgb_model is not None and X_scaled.shape[1] == self.lgb_model.num_feature():
            proba_lgb = self.lgb_model.predict(X_scaled)
            proba = (0.60 * proba_lgb) + (0.40 * proba_dnn)
        else:
            proba = proba_dnn

        ids = proba.argmax(axis=1)
        confs = proba.max(axis=1).astype(np.float32)
        preds_str = [self.classes[i] for i in ids]

        # Niveau 2 — Double Barrière Auto-Encodeur (si self.has_ae)
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

            mse_ae = np.concatenate(out_ae) if out_ae else np.empty((0,), dtype=np.float32)
            anomalie_ae = (mse_ae > self.ae_seuil).astype(bool)

            # Règle Anti-Faux Positifs (Réduction du bruit SOC)
            fp_mask = (ids != self.benign_id) & (confs < 0.75) & (mse_ae < self.ae_seuil_sain)
            if np.any(fp_mask):
                ids[fp_mask] = self.benign_id
                confs[fp_mask] = proba[fp_mask, self.benign_id]
                for idx in np.where(fp_mask)[0]:
                    preds_str[idx] = "BENIGN"

            # Règle Détection Zero-Day / Attaque Inconnue (Droit de veto de l'AE)
            zero_day_mask = (ids == self.benign_id) & anomalie_ae
            if np.any(zero_day_mask):
                proba_no_benign = proba.copy()
                proba_no_benign[:, self.benign_id] = -1.0
                fallback_ids = proba_no_benign.argmax(axis=1)

                ids[zero_day_mask] = fallback_ids[zero_day_mask]
                for idx in np.where(zero_day_mask)[0]:
                    preds_str[idx] = "Zero-Day / Unknown Attack"

                zd_mse = mse_ae[zero_day_mask]
                confs[zero_day_mask] = np.clip(
                    0.75 + 0.10 * np.log1p(zd_mse / max(self.ae_seuil, 1e-6)),
                    0.75,
                    0.99
                )

        res_dict = {
            "pred_id": ids.astype(int),
            "pred": preds_str,
            "confiance": confs.astype(np.float32),
        }
        if self.has_ae:
            res_dict["mse_ae"] = mse_ae.astype(np.float32)
            res_dict["anomalie_ae"] = anomalie_ae.astype(bool)

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
                model_version=getattr(self, "version", "v5"),
                flows_df=flows,
            )
        except Exception:
            pass

        return pd.DataFrame(res_dict, index=flows.index)
