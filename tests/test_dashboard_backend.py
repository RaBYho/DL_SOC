import os
from pathlib import Path
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from dashboard.backend import database as db_mod
from dashboard.backend.routes import router, websocket_endpoint
from dashboard.backend.ws_manager import ConnectionManager

BASE_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test_dash.db"
    db_mod.init_db(str(db_file))

    # Insertion de quelques flux de test
    con = db_mod.get_connection(str(db_file))
    with con:
        con.execute(
            """INSERT INTO flows (received_at, sensor_id, src_ip, src_port, dst_ip, dst_port, protocol, pred, confiance, mse_ae, anomalie_ae)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                1600000000.0,
                "sensor-01",
                "192.168.1.100",
                4444,
                "10.0.0.1",
                80,
                6,
                "DDoS",
                0.99,
                0.85,
                1,
            ),
        )
        con.execute(
            """INSERT INTO flows (received_at, sensor_id, src_ip, src_port, dst_ip, dst_port, protocol, pred, confiance, mse_ae, anomalie_ae)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                1600000010.0,
                "sensor-01",
                "192.168.1.101",
                5555,
                "10.0.0.2",
                22,
                6,
                "SSH-Patator",
                0.95,
                0.32,
                0,
            ),
        )
        con.execute(
            """INSERT INTO flows (received_at, sensor_id, src_ip, src_port, dst_ip, dst_port, protocol, pred, confiance, mse_ae, anomalie_ae)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                1600000020.0,
                "sensor-02",
                "192.168.1.50",
                6666,
                "10.0.0.3",
                443,
                6,
                "BENIGN",
                0.98,
                0.20,
                0,
            ),
        )
    con.close()
    return str(db_file)


def test_database_queries(test_db):
    kpis = db_mod.get_kpis(test_db)
    assert kpis["total_flows"] == 3
    assert kpis["confirmed_attacks"] == 2
    assert kpis["zero_day_anomalies"] == 1

    dist = db_mod.get_attack_distribution(test_db)
    assert len(dist) == 2
    labels = [d["label"] for d in dist]
    assert "DDoS" in labels
    assert "SSH-Patator" in labels

    threats = db_mod.get_threat_vectors(limit=5, db_path=test_db)
    assert len(threats["top_ips"]) >= 1
    assert len(threats["top_ports"]) >= 1

    alerts = db_mod.get_recent_alerts(limit=10, db_path=test_db)
    assert len(alerts) == 2  # Seules les alertes non-BENIGN ou anomalies


def test_ws_manager():
    mgr = ConnectionManager()
    assert len(mgr.active_connections) == 0


def test_dashboard_api_endpoints(test_db, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_PATH", Path(test_db))

    app = FastAPI()
    app.include_router(router)
    app.add_api_websocket_route("/ws", websocket_endpoint)

    client = TestClient(app)

    # Test /api/dashboard/init
    res = client.get("/api/dashboard/init")
    assert res.status_code == 200
    data = res.json()
    assert "kpis" in data
    assert "distribution" in data
    assert "timeline" in data
    assert "threat_vectors" in data
    assert "recent_alerts" in data

    # Test /api/dashboard/stats
    res_stats = client.get("/api/dashboard/stats")
    assert res_stats.status_code == 200
    assert "kpis" in res_stats.json()

    # Test /api/dashboard/alerts avec filtre
    res_alerts = client.get("/api/dashboard/alerts?category=DDoS")
    assert res_alerts.status_code == 200
    alerts = res_alerts.json()
    assert len(alerts) == 1
    assert alerts[0]["classification"] == "DDoS"

    # Test /api/dashboard/pcaps
    res_pcap = client.get("/api/dashboard/pcaps")
    assert res_pcap.status_code == 200
    assert "pcaps" in res_pcap.json()

    # Test WebSocket connection
    with client.websocket_connect("/ws") as websocket:
        init_event = websocket.receive_json()
        assert init_event["type"] == "init"
        assert "kpis" in init_event

        # Test ping/pong
        websocket.send_text("ping")
        pong = websocket.receive_json()
        assert pong["type"] == "pong"

    # Test Replay Controls
    status_res = client.get("/api/dashboard/replay/status")
    assert status_res.status_code == 200
    assert status_res.json()["is_running"] is False

    pause_res = client.post("/api/dashboard/replay/pause")
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == "paused"

    resume_res = client.post("/api/dashboard/replay/resume")
    assert resume_res.status_code == 200
    assert resume_res.json()["status"] == "resumed"

    stop_res = client.post("/api/dashboard/replay/stop")
    assert stop_res.status_code == 200
    assert stop_res.json()["status"] == "stopped"

