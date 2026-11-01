import json
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from dashboard.backend import database as db_mod
from dashboard.backend.routes import router
from dashboard.backend.services.notifications.telegram import TelegramNotifier
from dashboard.backend.services.notifications.email_notifier import EmailNotifier
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)


@pytest.fixture
def tmp_db(tmp_path):
    db_file = tmp_path / "test_incidents.db"
    db_mod.init_db(str(db_file))
    return str(db_file)


def test_summarize_ports():
    assert db_mod.summarize_ports([]) == "-"
    assert db_mod.summarize_ports([80]) == "80"
    assert db_mod.summarize_ports([80, 443]) == "80, 443"
    assert db_mod.summarize_ports([21, 22, 80, 443]) == "21, 22, 80, 443"
    # Plage contiguë
    assert db_mod.summarize_ports(list(range(20, 1001))) == "20-1000 (981 ports)"
    # Ports discontinus > 4
    assert db_mod.summarize_ports([22, 80, 443, 8080, 8443, 9000]) == "22, 80, 443, 8080 (+2 autres)"


def test_correlate_portscan_massive_flows(tmp_db):
    """Vérifie que 1 000 flux PortScan consécutifs sont regroupés en 1 seul incident."""
    now = time.time()
    flows = [
        {"src_ip": "172.20.10.5", "dst_ip": "172.20.10.1", "src_port": 50000 + i, "dst_port": 20 + i, "protocol": 6}
        for i in range(1000)
    ]
    preds = ["PortScan"] * 1000
    confs = [0.98] * 1000
    mses = [0.05] * 1000
    anoms = [0] * 1000

    res = db_mod.insert_and_correlate_flows(
        flow_records=flows,
        predictions=preds,
        confidences=confs,
        mse_values=mses,
        anomaly_values=anoms,
        sensor_id="probe-lan-01",
        received_at=now,
        inactivity_window=45.0,
        db_path=tmp_db,
    )

    assert res["total_flows"] == 1000
    assert res["alerts_count"] == 1000
    assert len(res["new_incidents"]) == 1

    # Vérification en base
    incidents = db_mod.get_incidents(db_path=tmp_db)
    assert len(incidents) == 1

    inc = incidents[0]
    assert inc["incident_code"] == "INC-0001"
    assert inc["status"] == "OPEN"
    assert inc["attack_type"] == "PortScan"
    assert inc["src_ip"] == "172.20.10.5"
    assert inc["dst_ip"] == "172.20.10.1"
    assert inc["flow_count"] == 1000
    assert inc["ports_summary"] == "20-1019 (1000 ports)"

    # Vérification que chaque flux individuel pointe sur cet incident
    sub_flows = db_mod.get_incident_flows(inc["id"], limit=20, db_path=tmp_db)
    assert len(sub_flows) == 20
    assert all(f["incident_id"] == inc["id"] for f in sub_flows)


def test_inactivity_window_and_incident_closure(tmp_db):
    """Vérifie que l'incident se clôture après 45s d'inactivité."""
    start_time = 1700000000.0
    flows = [{"src_ip": "10.0.0.99", "dst_ip": "10.0.0.1", "src_port": 1234, "dst_port": 80, "protocol": 6}]
    preds = ["DDoS"]
    confs = [0.99]

    # Ingestion initiale
    db_mod.insert_and_correlate_flows(
        flow_records=flows,
        predictions=preds,
        confidences=confs,
        mse_values=[0.1],
        anomaly_values=[0],
        received_at=start_time,
        inactivity_window=45.0,
        db_path=tmp_db,
    )

    # À +10 secondes, l'incident doit rester OUVERT
    closed = db_mod.close_inactive_incidents(inactivity_seconds=45.0, now=start_time + 10.0, db_path=tmp_db)
    assert len(closed) == 0

    # À +50 secondes (> 45s de silence), l'incident doit se CLÔTURER
    closed = db_mod.close_inactive_incidents(inactivity_seconds=45.0, now=start_time + 50.0, db_path=tmp_db)
    assert len(closed) == 1
    assert closed[0]["status"] == "CLOSED"
    assert closed[0]["duration_sec"] >= 1

    # Vérification du statut en base
    inc = db_mod.get_incidents(db_path=tmp_db)[0]
    assert inc["status"] == "CLOSED"


def test_zero_day_incident_creation(tmp_db):
    """Vérifie qu'une anomalie AE sans classe d'attaque crée un incident Zero-Day."""
    flows = [{"src_ip": "192.168.1.50", "dst_ip": "192.168.1.1", "src_port": 4444, "dst_port": 8888, "protocol": 6}]
    preds = ["BENIGN"]
    confs = [0.60]
    mses = [2.85]
    anoms = [1]  # Anomalie AE détectée

    res = db_mod.insert_and_correlate_flows(
        flow_records=flows,
        predictions=preds,
        confidences=confs,
        mse_values=mses,
        anomaly_values=anoms,
        db_path=tmp_db,
    )

    assert len(res["new_incidents"]) == 1
    inc = res["new_incidents"][0]
    assert inc["attack_type"] == "Zero-Day"
    assert inc["is_zero_day"] == 1
    assert inc["severity"] == "High"


def test_incident_api_endpoints(tmp_db, monkeypatch):
    """Vérifie les endpoints REST /incidents, /summary, /flows."""
    monkeypatch.setattr(db_mod, "DB_PATH", Path(tmp_db))

    # Ingestion d'un flux malveillant
    db_mod.insert_and_correlate_flows(
        flow_records=[{"src_ip": "1.2.3.4", "dst_ip": "5.6.7.8", "src_port": 100, "dst_port": 22, "protocol": 6}],
        predictions=["SSH-Patator"],
        confidences=[0.95],
        mse_values=[0.2],
        anomaly_values=[0],
        db_path=tmp_db,
    )

    client = TestClient(app)

    # 1. GET /incidents
    resp = client.get("/api/dashboard/incidents")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["attack_type"] == "SSH-Patator"
    assert data[0]["src_ip"] == "1.2.3.4"
    assert "X-Total-Count" in resp.headers

    # 2. GET /incidents/summary
    resp_sum = client.get("/api/dashboard/incidents/summary")
    assert resp_sum.status_code == 200
    summary = resp_sum.json()
    assert summary["total"] == 1
    assert summary["open"] == 1

    # 3. GET /incidents/{id}/flows
    inc_id = data[0]["id"]
    resp_flows = client.get(f"/api/dashboard/incidents/{inc_id}/flows")
    assert resp_flows.status_code == 200
    flows_data = resp_flows.json()
    assert len(flows_data) == 1
    assert flows_data[0]["src_ip"] == "1.2.3.4"


def test_telegram_and_email_incident_formatters():
    """Vérifie le formatage des messages d'ouverture et de clôture d'incident."""
    incident = {
        "id": 42,
        "incident_code": "INC-0042",
        "attack_type": "PortScan",
        "severity": "High",
        "src_ip": "172.20.10.5",
        "dst_ip": "172.20.10.1",
        "ports_summary": "20-1000 (981 ports)",
        "flow_count": 981,
        "max_confidence": 0.985,
        "duration_sec": 18,
        "is_zero_day": False,
    }

    # Telegram Open & Close
    tg_open = TelegramNotifier.format_incident_opened(incident)
    assert "[INCIDENT OUVERT #INC-0042]" in tg_open
    assert "172.20.10.5" in tg_open
    assert "20-1000 (981 ports)" in tg_open

    tg_close = TelegramNotifier.format_incident_closed(incident)
    assert "[INCIDENT CLOS #INC-0042]" in tg_close
    assert "981 flux / paquets" in tg_close
    assert "18s" in tg_close

    # Email Open & Close template generation
    from dashboard.backend.services.notifications.config import NotificationsConfig
    cfg = NotificationsConfig(smtp_host="localhost", smtp_port=25, email_to="admin@soc.lab")
    # Verify method callable without throwing template errors
    html_open = EmailNotifier._create_html_template(
        title="Ouverture d'Incident",
        subtitle="Test",
        badge_text="High",
        badge_color="#ef4444",
        metrics=[("Attaque", "PortScan")],
        recommendation="Action requise",
    )
    assert "Ouverture d'Incident" in html_open
