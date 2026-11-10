"""Integration tests for NIDS SOC Dashboard FastAPI Server."""

import time
import pytest
from fastapi.testclient import TestClient

from dashboard.backend.server import app
from dashboard.backend.database import init_db
from dashboard.backend.config import DB_PATH


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Ensure database schema is initialized before tests."""
    init_db(DB_PATH)


@pytest.fixture
def client():
    """Returns a TestClient instance."""
    with TestClient(app) as c:
        yield c


def test_healthz(client):
    """Verifies server health and database connectivity."""
    response = client.get("/api/dashboard/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "timestamp" in data


def test_init_endpoint(client):
    """Verifies comprehensive state initialization payload."""
    response = client.get("/api/dashboard/init")
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert "traffic" in data
    assert "timeline" in data
    assert "engine_distribution" in data
    assert "attack_distribution" in data
    assert "thresholds" in data
    assert data["thresholds"]["t1"] == 0.50
    assert data["thresholds"]["t2"] == 0.70


def test_flow_ingest_and_retrieval(client):
    """Tests flow ingestion, incident correlation, and recent flow query."""
    flow_sample = {
        "timestamp": time.time(),
        "src_ip": "192.168.1.105",
        "dst_ip": "10.0.0.1",
        "src_port": 54321,
        "dst_port": 80,
        "protocol": "TCP",
        "packet_count": 5,
        "verdict": "PortScan",
        "stage1_score": 0.92,
        "confidence": 0.88,
        "kitsune_score": 0.045,
        "decision_path": "STAGE2_PORT_SCAN",
        "dpi_rule": "DPI-ATTACK-TOOLS",
        "dpi_category": "Reconnaissance",
        "is_anomaly": True,
        "raw_metrics": {"duration": 120.0, "tot_bytes": 1024},
    }

    payload = {
        "flows": [flow_sample],
        "sensor_id": "test-sensor-01",
    }

    # Ingest
    ingest_res = client.post("/api/dashboard/flows/ingest", json=payload)
    assert ingest_res.status_code == 200
    ingest_data = ingest_res.json()
    assert ingest_data["status"] == "success"
    assert ingest_data["inserted_flows"] == 1

    # Retrieve recent flows
    recent_res = client.get("/api/dashboard/flows/recent?limit=10")
    assert recent_res.status_code == 200
    recent_flows = recent_res.json()
    assert len(recent_flows) >= 1
    found = any(f["src_ip"] == "192.168.1.105" for f in recent_flows)
    assert found

    # Forensics
    flow_id = recent_flows[0]["id"]
    forensics_res = client.get(f"/api/dashboard/flows/{flow_id}/forensics")
    assert forensics_res.status_code == 200
    f_data = forensics_res.json()
    assert "five_tuple" in f_data
    assert "ml_scores" in f_data
    assert "raw_metrics" in f_data
    assert f_data["raw_metrics"]["flow_duration"] == 120.0
    assert f_data["raw_metrics"]["total_fwd_packets"] >= 1
    assert f_data["five_tuple"]["protocol"] in (6, "6", "TCP")


def test_alerts_and_incident_lifecycle(client):
    """Tests alert listing and status update workflow."""
    # List alerts
    alerts_res = client.get("/api/dashboard/alerts")
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()

    if alerts:
        inc = alerts[0]
        inc_id = inc["id"]

        # Detail
        detail_res = client.get(f"/api/dashboard/alerts/{inc_id}")
        assert detail_res.status_code == 200
        assert detail_res.json()["id"] == inc_id

        # Update status
        update_res = client.post(
            f"/api/dashboard/alerts/{inc_id}/status",
            json={"status": "INVESTIGATING", "comment": "Triage started by SOC analyst"},
        )
        assert update_res.status_code == 200
        assert update_res.json()["new_status"] == "INVESTIGATING"


def test_sensor_heartbeat(client):
    """Tests sensor heartbeat registration and list query."""
    heartbeat_payload = {
        "sensor_id": "sensor-alpha",
        "interface": "eth0",
        "status": "capturing",
        "packets_per_sec": 1250.0,
        "flows_per_sec": 42.0,
        "inference_latency_ms": 11.4,
    }

    res = client.post("/api/dashboard/sensor/heartbeat", json=heartbeat_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "acknowledged"
    assert data["sensor_id"] == "sensor-alpha"

    # Query sensors
    sensors_res = client.get("/api/dashboard/sensors")
    assert sensors_res.status_code == 200
    s_list = sensors_res.json()
    assert any(s["sensor_id"] == "sensor-alpha" for s in s_list)


def test_list_pcaps(client):
    """Verifies that discovered PCAPs in repo are returned."""
    res = client.get("/api/dashboard/pcaps")
    assert res.status_code == 200
    pcaps = res.json()
    assert isinstance(pcaps, list)
    # Check that demo pcaps in pcap/ are found
    filenames = [p["filename"] for p in pcaps]
    assert any("demo_" in f for f in filenames)


def test_system_logs(client):
    """Tests system log event ingestion."""
    log_payload = {
        "level": "INFO",
        "component": "pipeline",
        "message": "Cascaded pipeline initialized successfully",
        "metadata": {"models": 4},
    }
    res = client.post("/api/dashboard/system/log", json=log_payload)
    assert res.status_code == 200
    assert res.json()["status"] == "logged"


def test_websocket_connection(client):
    """Verifies WebSocket connection and ping-pong."""
    with client.websocket_connect("/ws") as ws:
        ws.send_text("ping")
        data = ws.receive_text()
        assert "pong" in data


def test_spa_index_served(client):
    """Verifies that the compiled Vue SPA index.html is served at root /."""
    res = client.get("/")
    assert res.status_code == 200
    assert "NIDS SOC Command Center" in res.text


def test_threat_actors_and_targeted_stats(client):
    """Verifies threat actors list (criminels) and targeted victim/port statistics."""
    # Ingest a loopback attack and an external attack
    now = time.time()
    payload = {
        "flows": [
            {
                "timestamp": now,
                "src_ip": "127.0.0.1",
                "dst_ip": "127.0.0.1",
                "src_port": 40000,
                "dst_port": 8080,
                "protocol": "TCP",
                "verdict": "Web_Attack",
                "confidence": 0.95,
                "is_anomaly": True,
            },
            {
                "timestamp": now + 1,
                "src_ip": "198.51.100.42",
                "dst_ip": "10.0.0.50",
                "src_port": 51234,
                "dst_port": 443,
                "protocol": "TCP",
                "verdict": "DDoS",
                "confidence": 0.99,
                "is_anomaly": True,
            },
        ],
        "sensor_id": "test-sensor-threats",
    }
    client.post("/api/dashboard/flows/ingest", json=payload)

    # 1. Threat Actors with exclude_loopback=True
    res_actors = client.get("/api/dashboard/threat-actors?exclude_loopback=true")
    assert res_actors.status_code == 200
    actors = res_actors.json()
    assert isinstance(actors, list)
    actor_ips = [a["src_ip"] for a in actors]
    assert "198.51.100.42" in actor_ips
    assert "127.0.0.1" not in actor_ips

    # Check actor structure
    actor = next(a for a in actors if a["src_ip"] == "198.51.100.42")
    assert actor["total_attacks"] >= 1
    assert "DDoS" in actor["threat_classes"]
    assert 443 in actor["targeted_ports"]
    assert actor["severity"] in ("CRITICAL", "HIGH")

    # 2. Targeted Stats with exclude_loopback=True
    res_targets = client.get("/api/dashboard/stats/targets?exclude_loopback=true")
    assert res_targets.status_code == 200
    targets = res_targets.json()
    assert "top_targeted_port" in targets
    assert "top_targeted_service" in targets
    assert "top_targeted_ip" in targets
    assert "top_ports" in targets
    assert "top_victims" in targets
    # 127.0.0.1 should not be top victim when exclude_loopback=True
    assert targets["top_targeted_ip"] != "127.0.0.1"

    # 3. Flows and Alerts exclude_loopback toggle
    flows_filtered = client.get("/api/dashboard/flows/recent?exclude_loopback=true").json()
    for f in flows_filtered:
        assert not f["src_ip"].startswith("127.")
        assert not f["dst_ip"].startswith("127.")

    alerts_filtered = client.get("/api/dashboard/alerts?exclude_loopback=true").json()
    for a in alerts_filtered:
        assert not a["src_ip"].startswith("127.")


def test_realtime_chart_endpoints(client: TestClient):
    """Verifies stats timeline and engine distribution endpoints for real-time charts."""
    res_tl = client.get("/api/dashboard/stats/timeline?window_minutes=15&buckets=20&exclude_loopback=true")
    assert res_tl.status_code == 200
    timeline = res_tl.json()
    assert isinstance(timeline, list)
    assert len(timeline) == 20
    assert "timestamp" in timeline[0]
    assert "normal" in timeline[0]
    assert "attacks" in timeline[0]
    assert "anomalies" in timeline[0]

    res_ed = client.get("/api/dashboard/stats/engine-distribution?exclude_loopback=true")
    assert res_ed.status_code == 200
    engines = res_ed.json()
    assert isinstance(engines, list)
    engine_names = [e["engine"] for e in engines]
    assert any("ML" in name for name in engine_names)
    assert any("DPI" in name for name in engine_names)
    assert any("Kitsune" in name for name in engine_names)


