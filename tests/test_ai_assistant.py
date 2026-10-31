import pytest
from fastapi.testclient import TestClient
from nids_server import app
from dashboard.backend.services.ai_analyzer import (
    AiAnalyzerService,
    build_forensic_prompt,
    get_ai_config,
    save_ai_config,
)


def test_build_forensic_prompt():
    flow = {
        "src_ip": "192.168.1.120",
        "dst_ip": "10.0.0.5",
        "src_port": 49152,
        "dst_port": 445,
        "protocol": "TCP",
        "pred": "PortScan",
        "confiance": 97.5,
        "mse_ae": 0.88,
        "anomalie_ae": 1,
    }
    prompt = build_forensic_prompt(flow)
    assert "192.168.1.120:49152" in prompt
    assert "10.0.0.5:445" in prompt
    assert "PortScan" in prompt
    assert "0.88" in prompt
    assert "OUI" in prompt
    assert "MITRE ATT&CK" in prompt
    assert "iptables" in prompt


@pytest.mark.anyio
async def test_ai_analyzer_expert_rules():
    flow = {
        "src_ip": "10.10.10.50",
        "dst_ip": "192.168.1.1",
        "dst_port": 80,
        "pred": "DDoS",
        "confiance": 99.0,
        "mse_ae": 0.42,
    }
    res = await AiAnalyzerService.analyze_incident(flow)
    assert res["success"] is True
    assert "Moteur Expert" in res["provider"]
    assert "iptables_rule" in res
    assert "10.10.10.50" in res["iptables_rule"]
    assert "T1498" in res["analysis_markdown"]


def test_ai_assistant_api_endpoints():
    client = TestClient(app)

    # 1. GET settings/ai
    res_get = client.get("/api/dashboard/settings/ai")
    assert res_get.status_code == 200
    data = res_get.json()
    assert "provider" in data

    # 2. POST settings/ai
    res_post = client.post("/api/dashboard/settings/ai", json={"provider": "expert_rules"})
    assert res_post.status_code == 200
    assert res_post.json()["status"] == "success"

    # 3. POST ai/test
    res_test = client.post("/api/dashboard/ai/test", json={"provider": "expert_rules"})
    assert res_test.status_code == 200
    assert res_test.json()["success"] is True

    # 4. POST incidents/{id}/ai-analysis
    flow_payload = {
        "flow": {
            "src_ip": "192.168.10.200",
            "dst_ip": "10.0.0.1",
            "dst_port": 22,
            "pred": "SSH-Patator",
            "confiance": 95.0,
            "mse_ae": 0.25,
        }
    }
    res_analysis = client.post("/api/dashboard/incidents/inc-test-ai/ai-analysis", json=flow_payload)
    assert res_analysis.status_code == 200
    res_data = res_analysis.json()
    assert res_data["success"] is True
    assert "sudo iptables -A INPUT -s 192.168.10.200 -j DROP" in res_data["iptables_rule"]
    assert "T1110.001" in res_data["analysis_markdown"]
