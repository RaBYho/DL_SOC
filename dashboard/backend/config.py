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

# Paramètres des modèles d'IA
DEFAULT_AE_THRESHOLD = 0.6029
AE_THRESHOLD = DEFAULT_AE_THRESHOLD
DEFAULT_CONF_THRESHOLD = 70.0
ACTIVE_DNN_VERSION = "v4"
ACTIVE_AE_VERSION = "v1"

# Paramètres du serveur
HOST = os.environ.get("NIDS_HOST", "0.0.0.0")
PORT = int(os.environ.get("NIDS_PORT", 8000))
