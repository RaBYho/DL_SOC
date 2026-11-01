import asyncio
import logging
from typing import Any, Dict, Optional
from dashboard.backend.services.notifications.config import get_notifications_config
from dashboard.backend.services.notifications.throttling import AlertThrottler
from dashboard.backend.services.notifications.telegram import TelegramNotifier
from dashboard.backend.services.notifications.email_notifier import EmailNotifier
from dashboard.backend.services.health_service import health_service

logger = logging.getLogger("nids.notifications.dispatcher")


class NotificationDispatcher:
    """Gestionnaire central de distribution des notifications multi-canaux."""

    def __init__(self, debounce_window_sec: float = 60.0):
        self.throttler = AlertThrottler(debounce_window_sec=debounce_window_sec)
        self._digest_task: Optional[asyncio.Task] = None

    def start_digest_worker(self):
        """Lance une tâche de fond pour expédier les rapports de synthèse réguliers."""
        if self._digest_task is None or self._digest_task.done():
            self._digest_task = asyncio.create_task(self._periodic_digest_loop())

    async def _periodic_digest_loop(self):
        """Boucle de vérification des agrégations anti-spam toutes les 15 secondes."""
        while True:
            try:
                await asyncio.sleep(15.0)
                await self.flush_digests()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in notifications digest loop: {e}")

    async def notify_incident(self, flow: Dict[str, Any]):
        """
        Analyse un flux incident, applique le filtrage de niveau et le throttling,
        puis dispatche l'alerte vers les canaux configurés.
        """
        cfg = get_notifications_config()
        if not cfg.telegram_enabled and not cfg.email_enabled:
            return

        is_zd = bool(flow.get("anomalie_ae") == 1 or flow.get("is_zero_day"))
        pred = str(flow.get("pred", "BENIGN")).upper()
        is_attack = pred != "BENIGN"

        # Vérification des critères configurés
        should_process = False
        if is_zd and cfg.notify_zero_day:
            should_process = True
        elif is_attack:
            if not cfg.notify_critical_only:
                should_process = True
            else:
                # Filtrage des attaques considérées critiques (DDoS, Botnet, Infiltration, PortScan...)
                critical_attacks = {
                    "DDOS", "DOS SLOWLORIS", "DOS SLOWHTTPTEST", "DOS HULK",
                    "DOS GOLDENEYE", "HEARTBLEED", "BOTNET", "INFILTRATION",
                    "PORT SCAN", "BRUTE FORCE", "WEB ATTACK"
                }
                if any(crit in pred for crit in critical_attacks) or flow.get("confiance", 0) >= 80:
                    should_process = True

        if not should_process:
            return

        # Application du Throttling anti-spam
        src_ip = str(flow.get("src_ip", "0.0.0.0"))
        dst_port = flow.get("dst_port")
        mse = float(flow.get("mse_ae", 0.0) or 0.0)
        attack_label = "ZERO_DAY" if is_zd else pred

        should_send, _ = self.throttler.process_event(
            attack_type=attack_label,
            src_ip=src_ip,
            dst_port=dst_port,
            mse_ae=mse,
            is_zero_day=is_zd,
        )

        if not should_send:
            # Doublon groupé dans la fenêtre glissante
            return

        # Envoi simultané sur les canaux actifs
        tasks = []
        if cfg.telegram_enabled and cfg.telegram_bot_token and cfg.telegram_chat_id:
            msg_tg = TelegramNotifier.format_incident_message(flow)
            tasks.append(
                TelegramNotifier.send_message(
                    bot_token=cfg.telegram_bot_token,
                    chat_id=cfg.telegram_chat_id,
                    text=msg_tg,
                )
            )

        if cfg.email_enabled and cfg.smtp_host and cfg.email_to:
            tasks.append(EmailNotifier.send_incident_alert(cfg, flow))

        if not tasks:
            return

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, Exception):
                health_service.record_log("notifications", f"Erreur distribution alerte: {res}", "ERROR")
            elif isinstance(res, tuple):
                success, msg = res
                level = "INFO" if success else "WARN"
                health_service.record_log("notifications", f"Alerte envoyée ({level}): {msg}", level)

    async def flush_digests(self):
        """Envoie les digests accumulés après expiration de la fenêtre glissante."""
        cfg = get_notifications_config()
        if not cfg.telegram_enabled and not cfg.email_enabled:
            return

        expired = self.throttler.collect_expired_digests()
        for digest in expired:
            if cfg.telegram_enabled and cfg.telegram_bot_token and cfg.telegram_chat_id:
                msg = TelegramNotifier.format_digest_message(digest)
                await TelegramNotifier.send_message(
                    bot_token=cfg.telegram_bot_token,
                    chat_id=cfg.telegram_chat_id,
                    text=msg,
                )
                health_service.record_log(
                    "notifications",
                    f"Rapport de synthèse Telegram envoyé pour {digest['attack_type']} ({digest['count']} flux)",
                    "INFO",
                )

    async def notify_incident_opened(self, incident: Dict[str, Any]):
        """Expédie une notification instantanée à l'ouverture d'un nouvel incident corrélé."""
        cfg = get_notifications_config()
        if not cfg.telegram_enabled and not cfg.email_enabled:
            return

        tasks = []
        if cfg.telegram_enabled and cfg.telegram_bot_token and cfg.telegram_chat_id:
            msg = TelegramNotifier.format_incident_opened(incident)
            tasks.append(
                TelegramNotifier.send_message(
                    bot_token=cfg.telegram_bot_token,
                    chat_id=cfg.telegram_chat_id,
                    text=msg,
                )
            )

        if cfg.email_enabled and cfg.smtp_host and cfg.email_to:
            tasks.append(EmailNotifier.send_incident_opened(cfg, incident))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    logger.error(f"Error dispatching incident open notification: {res}")
                elif isinstance(res, tuple):
                    success, msg = res
                    level = "INFO" if success else "WARN"
                    health_service.record_log(
                        "notifications",
                        f"Notification Ouverture #{incident.get('incident_code')}: {msg}",
                        level,
                    )

    async def notify_incident_closed(self, incident: Dict[str, Any]):
        """Expédie un rapport de synthèse à la clôture de l'incident (fin d'attaque)."""
        cfg = get_notifications_config()
        if not cfg.telegram_enabled and not cfg.email_enabled:
            return

        tasks = []
        if cfg.telegram_enabled and cfg.telegram_bot_token and cfg.telegram_chat_id:
            msg = TelegramNotifier.format_incident_closed(incident)
            tasks.append(
                TelegramNotifier.send_message(
                    bot_token=cfg.telegram_bot_token,
                    chat_id=cfg.telegram_chat_id,
                    text=msg,
                )
            )

        if cfg.email_enabled and cfg.smtp_host and cfg.email_to:
            tasks.append(EmailNotifier.send_incident_closed(cfg, incident))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    logger.error(f"Error dispatching incident close notification: {res}")
                elif isinstance(res, tuple):
                    success, msg = res
                    level = "INFO" if success else "WARN"
                    health_service.record_log(
                        "notifications",
                        f"Notification Clôture #{incident.get('incident_code')}: {msg}",
                        level,
                    )


# Instance globale
notification_dispatcher = NotificationDispatcher()
