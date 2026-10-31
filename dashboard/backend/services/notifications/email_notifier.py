import logging
from email.message import EmailMessage
from typing import Any, Dict, List, Optional, Tuple
import aiosmtplib

logger = logging.getLogger("nids.notifications.email")


class EmailNotifier:
    """Notificateur Email / SMTP asynchrone avec templates HTML Dark-theme."""

    @staticmethod
    def _create_html_template(
        title: str,
        subtitle: str,
        badge_text: str,
        badge_color: str,
        metrics: List[Tuple[str, str]],
        recommendation: str,
    ) -> str:
        """Génère un email HTML moderne conforme à la charte graphique SOC."""
        rows_html = "".join(
            f"""
            <tr>
              <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #94a3b8; font-size: 13px;">{k}</td>
              <td style="padding: 10px 14px; border-bottom: 1px solid #1e293b; color: #f1f5f9; font-family: monospace; font-size: 13px; font-weight: 600;">{v}</td>
            </tr>
            """
            for k, v in metrics
        )

        return f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>{title}</title>
        </head>
        <body style="margin: 0; padding: 24px; background-color: #0b0f19; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #e2e8f0;">
          <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 620px; background-color: #0f172a; border-radius: 12px; border: 1px solid #1e293b; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
            <!-- En-tête -->
            <tr>
              <td style="padding: 24px 30px; background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); border-bottom: 1px solid #312e81;">
                <table width="100%" border="0" cellpadding="0" cellspacing="0">
                  <tr>
                    <td>
                      <div style="font-size: 11px; letter-spacing: 0.1em; color: #38bdf8; text-transform: uppercase; font-weight: 700; margin-bottom: 6px;">NIDS DL_SOC • Système de Détection Intrusion</div>
                      <h1 style="margin: 0; font-size: 20px; color: #ffffff; font-weight: 700;">{title}</h1>
                      <div style="font-size: 13px; color: #94a3b8; margin-top: 4px;">{subtitle}</div>
                    </td>
                    <td align="right" valign="top">
                      <span style="display: inline-block; padding: 6px 12px; border-radius: 20px; background-color: {badge_color}22; color: {badge_color}; border: 1px solid {badge_color}55; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">
                        {badge_text}
                      </span>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>

            <!-- Données techniques -->
            <tr>
              <td style="padding: 24px 30px;">
                <h3 style="margin: 0 0 14px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b;">Détails Télémétriques du Flux</h3>
                <table width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color: #090d16; border-radius: 8px; border: 1px solid #1e293b; border-collapse: collapse;">
                  {rows_html}
                </table>
              </td>
            </tr>

            <!-- Recommandation SOC -->
            <tr>
              <td style="padding: 0 30px 24px 30px;">
                <div style="background-color: #1e1b4b33; border: 1px solid #4338ca55; border-radius: 8px; padding: 16px;">
                  <div style="font-size: 12px; font-weight: 700; color: #818cf8; text-transform: uppercase; margin-bottom: 6px;">🛡️ Recommandation de Réponse à Incident</div>
                  <div style="font-size: 13px; color: #cbd5e1; line-height: 1.5;">{recommendation}</div>
                </div>
              </td>
            </tr>

            <!-- Pied de page -->
            <tr>
              <td style="padding: 18px 30px; background-color: #090d16; border-top: 1px solid #1e293b; text-align: center; font-size: 12px; color: #64748b;">
                Alerte générée automatiquement par le NIDS AI SOC Engine • Ne pas répondre directement à cet email.
              </td>
            </tr>
          </table>
        </body>
        </html>
        """

    @classmethod
    async def send_email(
        cls,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        email_from: str,
        email_to: str,
        subject: str,
        html_body: str,
        text_body: str,
        use_tls: bool = True,
    ) -> Tuple[bool, str]:
        """Envoie un email de manière asynchrone via aiosmtplib."""
        if not smtp_host or not email_from or not email_to:
            return False, "Configuration SMTP incomplète (hôte ou adresses manquantes)"

        # Nettoyage de la liste des destinataires
        recipients = [addr.strip() for addr in email_to.replace(";", ",").split(",") if addr.strip()]
        if not recipients:
            return False, "Aucun destinataire spécifié"

        msg = EmailMessage()
        msg["From"] = email_from
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")

        try:
            # Gestion TLS / SSL selon le port
            use_ssl_direct = smtp_port == 465
            start_tls = use_tls and smtp_port != 465

            smtp_kwargs = {
                "hostname": smtp_host,
                "port": smtp_port,
                "use_tls": use_ssl_direct,
                "start_tls": start_tls,
                "timeout": 15,
            }
            if smtp_user and smtp_password:
                smtp_kwargs["username"] = smtp_user
                smtp_kwargs["password"] = smtp_password

            await aiosmtplib.send(msg, **smtp_kwargs)
            return True, f"Email envoyé avec succès à {len(recipients)} destinataire(s)"

        except aiosmtplib.SMTPException as e:
            logger.error(f"SMTP error sending email: {e}")
            return False, f"Erreur SMTP: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            return False, f"Erreur inattendue d'envoi: {str(e)}"

    @classmethod
    async def send_incident_alert(cls, cfg: Any, flow: Dict[str, Any]) -> Tuple[bool, str]:
        """Formate et expédie une alerte d'incident par email."""
        is_zd = bool(flow.get("anomalie_ae") or flow.get("is_zero_day"))
        pred = flow.get("pred", "SUSPICIOUS")
        src_ip = flow.get("src_ip", "Inconnu")
        dst_ip = flow.get("dst_ip", "10.0.0.1")
        dst_port = str(flow.get("dst_port", 0))
        conf = f"{round(float(flow.get('confiance', 0.0)), 1)}%"
        mse = str(round(float(flow.get("mse_ae", 0.0)), 4))
        sensor = flow.get("sensor_id", "probe-lan-01")

        if is_zd:
            title = f"ALERTE ZERO-DAY : Anomalie Réseau Non Répertoriée"
            subtitle = f"Détection comportementale avancée par l'Autoencodeur sur la sonde {sensor}"
            badge_text = "Zero-Day Critique"
            badge_color = "#f43f5e"
            recom = "Vérifier la connectivité de l'IP source, isoler l'hôte si inconnu et qualifier le comportement dans l'onglet Incident Triage du dashboard."
        else:
            title = f"ALERTE SÉCURITÉ : {pred} Détecté"
            subtitle = f"Signature d'attaque identifiée par le réseau de neurones profond (DNN)"
            badge_text = "Attaque Confirmée"
            badge_color = "#ef4444"
            recom = f"Bloquer l'IP source {src_ip} sur le pare-feu de périmètre et analyser les ports de destination affectés."

        metrics = [
            ("Vecteur d'Attaque / Prédiction", pred if not is_zd else "Zero-Day Anomaly"),
            ("Adresse Source", src_ip),
            ("Adresse Destination", f"{dst_ip}:{dst_port}"),
            ("Niveau de Confiance IA", conf),
            ("Erreur Reconstruction (MSE)", mse),
            ("Identifiant de la Sonde", sensor),
        ]

        text_body = (
            f"=== {title} ===\n"
            f"Statut : {badge_text}\n"
            f"Source : {src_ip}\n"
            f"Cible : {dst_ip}:{dst_port}\n"
            f"Confiance : {conf} | MSE : {mse}\n"
            f"Recommandation : {recom}\n"
        )

        html_body = cls._create_html_template(
            title=title,
            subtitle=subtitle,
            badge_text=badge_text,
            badge_color=badge_color,
            metrics=metrics,
            recommendation=recom,
        )

        subject = f"[NIDS SOC] {'⚡ ZERO-DAY' if is_zd else '🚨 ' + pred} - Source {src_ip}"

        return await cls.send_email(
            smtp_host=cfg.smtp_host,
            smtp_port=cfg.smtp_port,
            smtp_user=cfg.smtp_user,
            smtp_password=cfg.smtp_password,
            email_from=cfg.email_from,
            email_to=cfg.email_to,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            use_tls=cfg.smtp_use_tls,
        )

    @classmethod
    async def send_test(cls, cfg: Any) -> Tuple[bool, str]:
        """Envoie un email de test pour valider la chaîne SMTP."""
        subject = "[NIDS SOC] Test de Notification SMTP"
        title = "Test de Connectivité SMTP NIDS SOC"
        subtitle = "Validation réussie du canal d'alerte par email"
        badge_text = "Test Réussi"
        badge_color = "#10b981"
        metrics = [
            ("Serveur SMTP", f"{cfg.smtp_host}:{cfg.smtp_port}"),
            ("Chiffrement TLS", "Activé" if cfg.smtp_use_tls else "Désactivé"),
            ("Expéditeur", cfg.email_from),
            ("Destinataire(s)", cfg.email_to),
            ("Statut Télémétrie", "Canal Opérationnel"),
        ]
        recom = "Votre canal d'alerte Email est maintenant configuré. Les alertes critiques et Zero-Days vous parviendront sur cette adresse."

        text_body = "NIDS SOC - Test de notification réussi. Canal d'alerte opérationnel."
        html_body = cls._create_html_template(
            title=title,
            subtitle=subtitle,
            badge_text=badge_text,
            badge_color=badge_color,
            metrics=metrics,
            recommendation=recom,
        )

        return await cls.send_email(
            smtp_host=cfg.smtp_host,
            smtp_port=cfg.smtp_port,
            smtp_user=cfg.smtp_user,
            smtp_password=cfg.smtp_password,
            email_from=cfg.email_from,
            email_to=cfg.email_to,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            use_tls=cfg.smtp_use_tls,
        )
