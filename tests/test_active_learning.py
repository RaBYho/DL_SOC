import pytest
from fastapi.testclient import TestClient
from nids_server import app
from dashboard.backend.database import (
    record_feedback,
    get_feedback,
    get_feedback_summary,
    export_feedback_dataset,
)


def test_active_learning_db_lifecycle():
    incident_id = "test-inc-1001"
    flow_data = {
        "src_ip": "192.168.1.55",
        "dst_ip": "10.0.0.1",
        "src_port": 54321,
        "dst_port": 80,
        "protocol": "TCP",
        "pred": "PortScan",
        "mse_ae": 0.45,
    }

    # 1. Record feedback: FALSE_POSITIVE
    res1 = record_feedback(
        incident_id=incident_id,
        human_verdict="FALSE_POSITIVE",
        analyst_notes="Scanner interne d'inventaire IT régulier.",
        flow_data=flow_data,
    )
    assert res1["status"] == "success"
    assert res1["human_verdict"] == "FALSE_POSITIVE"

    # 2. Retrieve feedback
    fb = get_feedback(incident_id)
    assert fb is not None
    assert fb["incident_id"] == incident_id
    assert fb["human_verdict"] == "FALSE_POSITIVE"
    assert "Scanner interne" in fb["analyst_notes"]

    # 3. Update feedback: KNOWN_ATTACK
    res2 = record_feedback(
        incident_id=incident_id,
        human_verdict="KNOWN_ATTACK",
        corrected_attack_type="DDoS",
        analyst_notes="Reclassifié après analyse pcap.",
        flow_data=flow_data,
    )
    assert res2["human_verdict"] == "KNOWN_ATTACK"
    fb_updated = get_feedback(incident_id)
    assert fb_updated["human_verdict"] == "KNOWN_ATTACK"
    assert fb_updated["corrected_attack_type"] == "DDoS"

    # 4. Feedback summary
    summary = get_feedback_summary()
    assert summary["total_feedback"] >= 1
    assert "top_reclassified" in summary

    # 5. Export dataset
    dataset = export_feedback_dataset()
    assert len(dataset) >= 1
    exported = next((item for item in dataset if item["incident_id"] == incident_id), None)
    assert exported is not None
    assert exported["human_verdict"] == "KNOWN_ATTACK"


def test_active_learning_api_endpoints():
    client = TestClient(app)
    incident_id = "api-inc-2002"

    payload = {
        "human_verdict": "CONFIRMED_ZERODAY",
        "corrected_attack_type": "ZERO-DAY-C2-TUNNEL",
        "analyst_notes": "Trafic chiffré anormal détecté par autoencodeur.",
        "flow_data": {
            "src_ip": "172.16.5.99",
            "dst_ip": "10.0.0.10",
            "dst_port": 443,
            "pred": "BENIGN",
            "mse_ae": 1.85,
        },
    }

    # 1. POST feedback
    res_post = client.post(f"/api/dashboard/incidents/{incident_id}/feedback", json=payload)
    assert res_post.status_code == 200
    assert res_post.json()["status"] == "success"

    # 2. GET feedback
    res_get = client.get(f"/api/dashboard/incidents/{incident_id}/feedback")
    assert res_get.status_code == 200
    data = res_get.json()
    assert data["incident_id"] == incident_id
    assert data["feedback"]["human_verdict"] == "CONFIRMED_ZERODAY"

    # 3. GET summary
    res_sum = client.get("/api/dashboard/feedback/summary")
    assert res_sum.status_code == 200
    assert "total_feedback" in res_sum.json()

    # 4. GET export JSON
    res_exp_json = client.get("/api/dashboard/feedback/export?format=json")
    assert res_exp_json.status_code == 200
    assert "dataset" in res_exp_json.json()

    # 5. GET export CSV
    res_exp_csv = client.get("/api/dashboard/feedback/export?format=csv")
    assert res_exp_csv.status_code == 200
    assert "text/csv" in res_exp_csv.headers["content-type"]
    assert "incident_id" in res_exp_csv.text
    assert "api-inc-2002" in res_exp_csv.text
