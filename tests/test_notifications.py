import pytest
import time
from fastapi.testclient import TestClient
from nids_server import app
from dashboard.backend.services.notifications.config import (
    NotificationsConfig,
    mask_secret,
    get_masked_config,
    save_notifications_config,
)
from dashboard.backend.services.notifications.throttling import AlertThrottler
from dashboard.backend.services.notifications.telegram import TelegramNotifier
from dashboard.backend.services.notifications.email_notifier import EmailNotifier


def test_notifications_config_and_masking():
    cfg = NotificationsConfig(
        telegram_enabled=True,
        telegram_bot_token="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ",
        telegram_chat_id="-100987654321",
        email_enabled=True,
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_user="soc@example.com",
        smtp_password="MySecretPassword123",
        smtp_use_tls=True,
        email_from="soc@example.com",
        email_to="analyst@example.com",
    )
    d = cfg.to_dict()
    assert d["telegram_enabled"] is True
    assert d["smtp_port"] == 587

    # Test masking
    masked = mask_secret("123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ")
    assert masked.startswith("123••••")
    assert masked.endswith("xyZ")
    assert "ABCdef" not in masked


def test_alert_throttler_debounce_and_digest():
    throttler = AlertThrottler(debounce_window_sec=1.0)

    # 1st event: should be sent immediately
    should_send, data = throttler.process_event(
        attack_type="DDoS",
        src_ip="192.168.1.100",
        dst_port=80,
        mse_ae=0.85,
    )
    assert should_send is True
    assert data is not None
    assert data["attack_type"] == "DDoS"

    # Immediate 2nd event with same key: should be suppressed/throttled
    should_send_2, data_2 = throttler.process_event(
        attack_type="DDoS",
        src_ip="192.168.1.100",
        dst_port=80,
        mse_ae=0.90,
    )
    assert should_send_2 is False
    assert data_2 is None

    # Event from another IP: should be immediate
    should_send_3, _ = throttler.process_event(
        attack_type="DDoS",
        src_ip="192.168.1.101",
        dst_port=80,
    )
    assert should_send_3 is True

    # After waiting for debounce window to expire: digest collection
    time.sleep(1.1)
    digests = throttler.collect_expired_digests()
    assert len(digests) >= 1
    # Check that 192.168.1.100 was aggregated
    aggregated = next((d for d in digests if d["src_ip"] == "192.168.1.100"), None)
    assert aggregated is not None
    assert aggregated["count"] == 2
    assert aggregated["max_mse"] == 0.90


def test_telegram_message_formatting():
    flow = {
        "pred": "PortScan",
        "confiance": 98.5,
        "mse_ae": 0.1234,
        "src_ip": "10.0.0.42",
        "dst_ip": "10.0.0.1",
        "dst_port": 443,
        "sensor_id": "probe-test",
        "anomalie_ae": 0,
    }
    msg = TelegramNotifier.format_incident_message(flow)
    assert "INCIDENT DE SÉCURITÉ : PortScan" in msg
    assert "10.0.0.42" in msg
    assert "10.0.0.1:443" in msg

    # Zero-Day message
    flow_zd = {
        "pred": "BENIGN",
        "confiance": 50.0,
        "mse_ae": 1.45,
        "src_ip": "172.16.0.5",
        "dst_ip": "10.0.0.2",
        "dst_port": 8080,
        "anomalie_ae": 1,
    }
    msg_zd = TelegramNotifier.format_incident_message(flow_zd)
    assert "ZERO-DAY" in msg_zd
    assert "172.16.0.5" in msg_zd


def test_email_template_generation():
    html = EmailNotifier._create_html_template(
        title="ALERTE SÉCURITÉ",
        subtitle="Test subtitle",
        badge_text="Critique",
        badge_color="#ef4444",
        metrics=[("IP Source", "1.2.3.4"), ("Port Cible", "443")],
        recommendation="Bloquer l'IP",
    )
    assert "ALERTE SÉCURITÉ" in html
    assert "1.2.3.4" in html
    assert "#ef4444" in html
    assert "Bloquer l&#39;IP" in html or "Bloquer l'IP" in html


def test_notification_api_endpoints():
    client = TestClient(app)

    # 1. GET settings/notifications
    res = client.get("/api/dashboard/settings/notifications")
    assert res.status_code == 200
    data = res.json()
    assert "telegram_enabled" in data
    assert "email_enabled" in data

    # 2. POST settings/notifications
    update_payload = {
        "telegram_enabled": True,
        "telegram_chat_id": "-100111222333",
        "notify_critical_only": True,
    }
    res_post = client.post("/api/dashboard/settings/notifications", json=update_payload)
    assert res_post.status_code == 200
    res_data = res_post.json()
    assert res_data["status"] == "success"
    assert res_data["config"]["telegram_chat_id"] == "-100111222333"

    # 3. Test Telegram endpoint without valid token (should gracefully fail)
    res_tg = client.post("/api/dashboard/notifications/test-telegram", json={"bot_token": "fake", "chat_id": "123"})
    assert res_tg.status_code == 200
    assert "success" in res_tg.json()

    # 4. Test Email endpoint without host (should fail validation gracefully)
    res_email = client.post("/api/dashboard/notifications/test-email", json={})
    assert res_email.status_code == 200
    assert res_email.json()["success"] is False
