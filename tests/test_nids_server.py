import json
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    # Configuration des variables d'environnement avant l'import de nids_server
    test_db = tmp_path_factory.mktemp("db") / "test_nids.db"
    os.environ["NIDS_BASE"] = str(BASE_DIR)
    os.environ["NIDS_DB"] = str(test_db)
    os.environ["NIDS_API_KEY"] = "test-secret-key"

    import nids_server

    # Forcer la réassignation au cas où le module avait déjà été importé
    nids_server.BASE = str(BASE_DIR)
    nids_server.DB = str(test_db)
    nids_server.API_KEY = "test-secret-key"
    nids_server.scorer = nids_server.Scorer(str(BASE_DIR))

    return TestClient(nids_server.app)


@pytest.fixture(scope="module")
def feature_cols():
    with open(BASE_DIR / "models" / "feature_cols.json") as f:
        return json.load(f)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert isinstance(data["classes"], list)
    assert len(data["classes"]) == 12
    assert data["ae_enabled"] is True
    assert data["ae_threshold"] is not None


def test_ingest_unauthorized(client):
    payload = {"sensor_id": "sensor-01", "flows": []}
    # Sans clé
    res1 = client.post("/ingest", json=payload)
    assert res1.status_code == 401

    # Avec clé invalide
    res2 = client.post("/ingest", json=payload, headers={"x-api-key": "mauvaise-cle"})
    assert res2.status_code == 401


def test_ingest_empty_batch(client):
    payload = {"sensor_id": "sensor-01", "flows": []}
    response = client.post(
        "/ingest", json=payload, headers={"x-api-key": "test-secret-key"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["received"] == 0
    assert data["alerts"] == 0
    assert data["anomalies"] == 0
    assert data["preds"] == []


def test_ingest_valid_flows_and_stats(client, feature_cols):
    # Création d'un flux valide
    flow_1 = {col: 10.0 for col in feature_cols}
    flow_1.update({
        "bidirectional_first_seen_ms": 1600000000000,
        "src_ip": "192.168.1.50",
        "src_mac": "00:aa:bb:cc:dd:ee",
        "src_port": 45678,
        "dst_ip": "10.0.0.1",
        "dst_port": 80,
        "protocol": 6,
    })

    flow_2 = {col: 20.0 for col in feature_cols}
    flow_2.update({
        "bidirectional_first_seen_ms": 1600000001000,
        "src_ip": "192.168.1.51",
        "src_mac": "00:aa:bb:cc:dd:ef",
        "src_port": 45679,
        "dst_ip": "10.0.0.1",
        "dst_port": 443,
        "protocol": 6,
    })

    payload = {"sensor_id": "sensor-test", "flows": [flow_1, flow_2]}

    response = client.post(
        "/ingest", json=payload, headers={"x-api-key": "test-secret-key"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["received"] == 2
    assert "alerts" in data
    assert "anomalies" in data
    assert len(data["preds"]) == 2

    # Vérification du endpoint /stats
    stats_resp = client.get("/stats", headers={"x-api-key": "test-secret-key"})
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert isinstance(stats, dict)
    assert sum(stats.values()) == 2

    # Vérification du endpoint /stats/anomalies
    anom_resp = client.get("/stats/anomalies", headers={"x-api-key": "test-secret-key"})
    assert anom_resp.status_code == 200
    anom_data = anom_resp.json()
    assert "total_flows" in anom_data
    assert "anomalies" in anom_data
    assert anom_data["total_flows"] == 2


def test_spa_dashboard_serving(client):
    # Test index.html à la racine
    resp = client.get("/")
    assert resp.status_code == 200
    assert "DL_SOC" in resp.text
    assert 'id="app"' in resp.text

    # Test route SPA (HTML5 history fallback)
    route_resp = client.get("/alerts")
    assert route_resp.status_code == 200
    assert 'id="app"' in route_resp.text

