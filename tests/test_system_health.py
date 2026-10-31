import pytest
from fastapi.testclient import TestClient
from nids_server import app
from dashboard.backend.services.health_service import health_service


@pytest.fixture
def client():
    return TestClient(app)


def test_health_service_direct():
    """Vérifie le fonctionnement unitaire du service de santé."""
    # Test enregistrement de latence
    health_service.record_inference_latency(14.5)
    health_service.record_inference_latency(18.2)

    # Test journalisation d'événement système
    health_service.log_system_event(
        level="WARNING",
        source="TestService",
        message="Alerte de test pour la validation unitaire",
        details={"code": 42}
    )

    logs = health_service.get_system_logs(limit=10)
    assert len(logs) > 0
    assert any(l["message"] == "Alerte de test pour la validation unitaire" for l in logs)

    # Test génération du rapport de santé consolidé
    status = health_service.get_health_status()
    assert "status" in status
    assert status["status"] in ("HEALTHY", "DEGRADED", "CRITICAL")
    assert "score" in status
    assert 0 <= status["score"] <= 100
    assert "components" in status
    assert "sensors" in status["components"]
    assert "ai_engine" in status["components"]
    assert "database" in status["components"]
    assert "websocket" in status["components"]
    assert "host" in status["components"]
    assert "issues" in status


def test_system_health_api_endpoints(client):
    """Vérifie les endpoints REST de diagnostic système."""
    # 1. Endpoint direct /api/system/health
    res = client.get("/api/system/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "components" in data

    # 2. Endpoint dashboard /api/dashboard/system/health
    res_dash = client.get("/api/dashboard/system/health")
    assert res_dash.status_code == 200
    assert res_dash.json()["status"] == data["status"]

    # 3. Endpoint logs système
    res_logs = client.get("/api/dashboard/system/logs?limit=5")
    assert res_logs.status_code == 200
    assert isinstance(res_logs.json(), list)

    # 4. Endpoint optimisation SQLite
    res_opt = client.post("/api/dashboard/system/optimize-db")
    assert res_opt.status_code == 200
    assert res_opt.json()["status"] == "success"

    # 5. Endpoint test composant individuel
    res_test = client.post(
        "/api/dashboard/system/test-component",
        json={"component": "database"}
    )
    assert res_test.status_code == 200
    test_data = res_test.json()
    assert test_data["component"] == "database"
    assert "latency_ms" in test_data
