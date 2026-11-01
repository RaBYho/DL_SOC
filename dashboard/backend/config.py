import os
from pathlib import Path

# Résolution des chemins de base du projet
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
PCAP_DIR = PROJECT_ROOT / "pcap"
DEFAULT_DB_PATH = PROJECT_ROOT / "nids.db"

# Variables de configuration
BASE = os.environ.get("NIDS_BASE", str(PROJECT_ROOT))
DB_PATH = Path(os.environ.get("NIDS_DB", str(DEFAULT_DB_PATH)))
API_KEY = os.environ.get("NIDS_API_KEY", "dev-secret-key")

# Charger les paramètres depuis manifest.json si présent
manifest_path = MODELS_DIR / "manifest.json"
manifest_data = {}
if manifest_path.exists():
    try:
        import json
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
    except Exception:
        pass

# Paramètres des modèles d'IA (v5 natif et Auto-Encodeur v2)
DEFAULT_AE_THRESHOLD = float(manifest_data.get("ae_threshold", 1.481025))
AE_THRESHOLD = DEFAULT_AE_THRESHOLD
DEFAULT_CONF_THRESHOLD = 70.0
ACTIVE_DNN_VERSION = str(manifest_data.get("active_version", "v5"))
ACTIVE_AE_VERSION = str(manifest_data.get("active_ae_version", "v2"))

# Paramètres du serveur
HOST = os.environ.get("NIDS_HOST", "0.0.0.0")
PORT = int(os.environ.get("NIDS_PORT", 8000))
