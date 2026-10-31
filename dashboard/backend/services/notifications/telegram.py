import logging
import httpx
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("nids.notifications.telegram")


class TelegramNotifier:
    """Notificateur Telegram asynchrone utilisant l'API Bot officielle."""

    TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/{method}"

    @staticmethod
    async def send_message(
        bot_token: str,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
        dashboard_url: Optional[str] = "http://localhost:8000",
    ) -> Tuple[bool, str]:
        """Envoie un message via l'API Telegram avec gestion des erreurs et boutons optionnels."""
        if not bot_token or not chat_id:
            return False, "Bot token ou Chat ID manquant"

        url = TelegramNotifier.TELEGRAM_API_URL.format(token=bot_token, method="sendMessage")

        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }

        if dashboard_url:
            payload["reply_markup"] = {
                "inline_keyboard": [
                    [
                        {
                            "text": "🔍 Ouvrir le SOC Dashboard",
                            "url": dashboard_url,
                        }
                    ]
                ]
            }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                data = resp.json()

                if resp.status_code == 200 and data.get("ok"):
                    return True, "Message Telegram envoyé avec succès"
                else:
                    err_desc = data.get("description", resp.text)
                    logger.warning(f"Telegram API error ({resp.status_code}): {err_desc}")
                    return False, f"Erreur Telegram: {err_desc}"
        except httpx.RequestError as e:
            logger.error(f"Telegram connection exception: {e}")
            return False, f"Impossible de contacter Telegram: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram message: {e}")
            return False, f"Erreur inattendue: {str(e)}"

    @classmethod
    def format_incident_message(cls, flow: Dict[str, Any]) -> str:
        """Formate une alerte d'incident unitaire pour Telegram."""
        is_zd = bool(flow.get("anomalie_ae") or flow.get("is_zero_day"))
        pred = flow.get("pred", "SUSPICIOUS")
        src_ip = flow.get("src_ip", "Inconnu")
        dst_ip = flow.get("dst_ip", "10.0.0.1")
        dst_port = flow.get("dst_port", 0)
        conf = round(float(flow.get("confiance", 0.0)), 1)
        mse = round(float(flow.get("mse_ae", 0.0)), 4)
        sensor_id = flow.get("sensor_id", "probe-lan-01")

        if is_zd:
            badge = "⚡ <b>ALERTE ZERO-DAY DÉTECTÉE</b>"
            category = "Anomalie Réseau Inconnue (Autoencodeur)"
        else:
            badge = f"🚨 <b>INCIDENT DE SÉCURITÉ : {pred}</b>"
            category = f"Signature connue détectée ({conf}% conf.)"

        msg = (
            f"{badge}\n\n"
            f"<b>Type :</b> <code>{category}</code>\n"
            f"<b>Source IP :</b> <code>{src_ip}</code>\n"
            f"<b>Cible :</b> <code>{dst_ip}:{dst_port}</code>\n"
            f"<b>Sonde active :</b> <code>{sensor_id}</code>\n"
            f"<b>MSE Reconstruction :</b> <code>{mse}</code>\n"
            f"<i>Statut : Flux intercepté et analysé par le NIDS.</i>"
        )
        return msg

    @classmethod
    def format_digest_message(cls, digest: Dict[str, Any]) -> str:
        """Formate un rapport de regroupement d'alertes massives (Anti-Spam)."""
        attack = digest.get("attack_type", "Attaque")
        src_ip = digest.get("src_ip", "Inconnu")
        count = digest.get("count", 0)
        dur = digest.get("duration_sec", 60)
        ports = ", ".join(str(p) for p in digest.get("ports", [])) or "Multiples"
        max_mse = digest.get("max_mse", 0.0)

        msg = (
            f"🛡️ <b>RAPPORT DE MITIGATION ANTI-SPAM (DIGEST)</b>\n\n"
            f"<b>Attaque :</b> <code>{attack}</code>\n"
            f"<b>Volume intercepté :</b> <b>{count:,} flux</b> en {dur}s\n"
            f"<b>Source offensive :</b> <code>{src_ip}</code>\n"
            f"<b>Ports visés :</b> <code>{ports}</code>\n"
            f"<b>Erreur MSE Max :</b> <code>{max_mse}</code>\n\n"
            f"<i>Alerte agrégée automatiquement par le SOC pour éviter la fatigue d'alerte.</i>"
        )
        return msg

    @classmethod
    async def send_test(cls, bot_token: str, chat_id: str) -> Tuple[bool, str]:
        """Envoie un message de test pour valider les tokens Telegram."""
        test_msg = (
            "🚀 <b>NIDS AI SOC - Test de Notification Telegram</b>\n\n"
            "Ce message confirme que l'intégration Telegram du centre des opérations de sécurité est opérationnelle.\n\n"
            "• Chiffrement de flux : Actif\n"
            "• Throttling anti-spam : Prêt\n"
            "• Surveillance Zero-Day : En écoute\n"
        )
        return await cls.send_message(bot_token, chat_id, test_msg)
