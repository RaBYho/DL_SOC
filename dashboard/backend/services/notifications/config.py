import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional
from dashboard.backend.config import PROJECT_ROOT

logger = logging.getLogger("nids.notifications.config")

CONFIG_FILE = PROJECT_ROOT / "config" / "notifications_config.json"


@dataclass
class NotificationsConfig:
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    email_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    email_from: str = ""
    email_to: str = ""
    notify_critical_only: bool = True
    notify_zero_day: bool = True
    notify_traffic_burst: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NotificationsConfig":
        valid_keys = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


_current_config: Optional[NotificationsConfig] = None


def get_notifications_config() -> NotificationsConfig:
    global _current_config
    if _current_config is not None:
        return _current_config

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                _current_config = NotificationsConfig.from_dict(data)
                return _current_config
        except Exception as e:
            logger.error(f"Failed to load notifications config from {CONFIG_FILE}: {e}")

    _current_config = NotificationsConfig()
    return _current_config


def save_notifications_config(new_data: Dict[str, Any]) -> NotificationsConfig:
    global _current_config
    current = get_notifications_config()
    current_dict = current.to_dict()

    for k, v in new_data.items():
        if k not in current_dict:
            continue
        # If masked password/token received, keep current
        if k in ("telegram_bot_token", "smtp_password") and isinstance(v, str):
            if v.startswith("••••") or v == "******":
                continue
        current_dict[k] = v

    _current_config = NotificationsConfig.from_dict(current_dict)

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(_current_config.to_dict(), f, indent=2)
    except Exception as e:
        logger.error(f"Failed to persist notifications config: {e}")

    return _current_config


def mask_secret(secret: str) -> str:
    if not secret:
        return ""
    if len(secret) <= 6:
        return "••••••••"
    return f"{secret[:3]}••••{secret[-3:]}"


def get_masked_config() -> Dict[str, Any]:
    cfg = get_notifications_config()
    d = cfg.to_dict()
    if d["telegram_bot_token"]:
        d["telegram_bot_token"] = mask_secret(d["telegram_bot_token"])
    if d["smtp_password"]:
        d["smtp_password"] = "••••••••"
    return d
