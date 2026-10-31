from typing import Any, Dict, List


def format_kpis(kpis: Dict[str, Any]) -> Dict[str, Any]:
    """Assure la compatibilité des clés entre le frontend et le backend."""
    total = kpis.get("total_flows", 0)
    attacks = kpis.get("confirmed_attacks", 0)
    anomalies = kpis.get("zero_day_anomalies", 0)
    rate = kpis.get("rate_flows_sec", 0.0)
    benign_pct = kpis.get("benign_pct", 100.0)
    malicious_pct = kpis.get("malicious_pct", 0.0)
    current_mse = kpis.get("current_mse", 0.0)

    return {
        "total_flows": total,
        "confirmed_attacks": attacks,
        "attacks": attacks,
        "zero_day_anomalies": anomalies,
        "anomalies": anomalies,
        "rate_flows_sec": rate,
        "flow_rate_sec": rate,
        "bandwidth_mbps": round(rate * 0.0035, 1),
        "benign_pct": benign_pct,
        "malicious_pct": malicious_pct,
        "attack_pct": malicious_pct,
        "current_mse": current_mse,
    }


def format_distribution(dist: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not dist:
        return []
    out = []
    tot = sum(d.get("count", 0) for d in dist) or 1
    for d in dist:
        label = d.get("label") or d.get("name") or "Attack"
        cnt = d.get("count", 0)
        out.append({
            "label": label,
            "name": label,
            "count": cnt,
            "pct": d.get("pct", round(cnt / tot * 100, 1)),
            "color": d.get("color", "var(--ac)"),
        })
    return out


def format_threat_vectors(tv: Dict[str, Any]) -> Dict[str, Any]:
    top_ips = tv.get("top_ips", [])
    top_ports = tv.get("top_ports", [])
    return {
        "top_ips": top_ips,
        "top_source_ips": top_ips,
        "top_ports": top_ports,
        "top_dest_ports": top_ports,
    }


def enrich_alert(alert: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise l'alerte pour garantir la présence de toutes les clés attendues."""
    a = dict(alert)
    pred = a.get("pred") or a.get("classification") or "BENIGN"
    anom = 1 if (a.get("anomalie_ae") == 1 or a.get("is_anomaly")) else 0
    
    if pred in ("DDoS", "Bot"):
        sev = "Critical"
    elif pred.startswith("DoS") or pred == "WebAttack" or (anom == 1 and pred != "BENIGN"):
        sev = "High"
    elif anom == 1 and pred == "BENIGN":
        sev = "High"
    elif "Patator" in pred or pred == "PortScan":
        sev = "Medium"
    elif pred == "BENIGN" and anom == 0:
        sev = "Benign"
    else:
        sev = "Low"

    time_val = a.get("received_at") or a.get("timestamp") or ""
    sensor_val = a.get("sensor_id") or a.get("sensor") or "sensor-edge-01"
    conf_val = a.get("confiance")
    if conf_val is None and a.get("confidence") is not None:
        conf_val = float(a["confidence"]) / 100.0
    elif conf_val is None:
        conf_val = 0.9

    a["pred"] = pred
    a["classification"] = pred
    a["received_at"] = time_val
    a["timestamp"] = time_val
    a["sensor_id"] = sensor_val
    a["sensor"] = sensor_val
    a["confiance"] = float(conf_val)
    a["confidence"] = round(float(conf_val) * 100.0, 1)
    a["anomalie_ae"] = anom
    a["is_anomaly"] = bool(anom)
    a["severity"] = a.get("severity") or sev
    return a
