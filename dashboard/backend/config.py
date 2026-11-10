"""Configuration centralisée pour le serveur Backend du Dashboard SOC."""

import os
from pathlib import Path

ROOT_DIR: Path = Path(__file__).resolve().parent.parent.parent
REPO_ROOT: Path = ROOT_DIR

HOST: str = os.getenv("NIDS_DASHBOARD_HOST", "0.0.0.0")
PORT: int = int(os.getenv("NIDS_DASHBOARD_PORT", "8000"))

DB_PATH: Path = Path(os.getenv("NIDS_DB_PATH", str(ROOT_DIR / "nids.db")))
DIST_DIR: Path = ROOT_DIR / "dashboard" / "frontend" / "dist"
FRONTEND_DIST: Path = DIST_DIR
STATIC_DIR: Path = ROOT_DIR / "dashboard" / "static"
PCAP_DIR: Path = ROOT_DIR / "pcap"
SAMPLES_DIR: Path = ROOT_DIR / "data" / "samples"
CONFIGS_DIR: Path = ROOT_DIR / "configs"

CORS_ORIGINS: list[str] = ["*"]
