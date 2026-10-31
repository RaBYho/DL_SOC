import json
import logging
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import httpx
from dashboard.backend.config import PROJECT_ROOT

logger = logging.getLogger("nids.ai_analyzer")

AI_CONFIG_FILE = PROJECT_ROOT / "config" / "ai_config.json"

DEFAULT_AI_CONFIG = {
    "provider": "expert_rules",  # "expert_rules", "ollama", "gemini"
    "ollama_url": "http://localhost:11434",
    "ollama_model": "mistral:latest",
    "gemini_api_key": "",
    "gemini_model": "gemini-2.5-flash",
}


def get_ai_config() -> Dict[str, Any]:
    if AI_CONFIG_FILE.exists():
        try:
            with open(AI_CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                return {**DEFAULT_AI_CONFIG, **saved}
        except Exception as e:
            logger.error(f"Failed to read AI config from {AI_CONFIG_FILE}: {e}")
    return dict(DEFAULT_AI_CONFIG)


def save_ai_config(data: Dict[str, Any]) -> Dict[str, Any]:
    current = get_ai_config()
    for k, v in data.items():
        if k in current:
            if k == "gemini_api_key" and isinstance(v, str) and v.startswith("••••"):
                continue
            current[k] = v

    AI_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(AI_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save AI config: {e}")

    return current


def get_masked_ai_config() -> Dict[str, Any]:
    cfg = get_ai_config()
    res = dict(cfg)
    key = res.get("gemini_api_key", "")
    if key:
        res["gemini_api_key"] = f"{key[:4]}••••••••{key[-4:]}" if len(key) > 8 else "••••••••"
    return res


def build_forensic_prompt(flow: Dict[str, Any]) -> str:
    """Génère le prompt forensique expert SOC Tier-3 exhaustif pour qualification d'incident."""
    src_ip = flow.get("src_ip", "0.0.0.0")
    dst_ip = flow.get("dst_ip", "0.0.0.0")
    src_port = flow.get("src_port", 0)
    dst_port = flow.get("dst_port", 0)
    proto_raw = flow.get("protocol", "TCP")
    proto = "TCP" if str(proto_raw) in ("6", "TCP") else ("UDP" if str(proto_raw) in ("17", "UDP") else ("ICMP" if str(proto_raw) in ("1", "ICMP") else str(proto_raw)))
    pred = flow.get("pred", flow.get("classification", "SUSPICIOUS"))
    conf = round(float(flow.get("confiance", flow.get("confidence", 0.0))), 1)
    if conf <= 1.0 and conf > 0:
        conf = round(conf * 100.0, 1)
    mse = round(float(flow.get("mse_ae", 0.0) or 0.0), 4)
    baseline_threshold = 0.6029
    is_zd = bool(flow.get("anomalie_ae") == 1 or flow.get("is_zero_day") or mse > baseline_threshold)
    sensor = flow.get("sensor_id", "probe-edge-01")
    received_at = flow.get("received_at", flow.get("timestamp", "Temps Réel"))

    fwd_pkts = int(flow.get("src2dst_packets", flow.get("bidirectional_packets", 14)) or 14)
    bwd_pkts = int(flow.get("dst2src_packets", 8) or 8)
    total_pkts = fwd_pkts + bwd_pkts
    fwd_bytes = int(flow.get("src2dst_bytes", 1420) or 1420)
    bwd_bytes = int(flow.get("dst2src_bytes", 980) or 980)
    total_bytes = fwd_bytes + bwd_bytes
    duration_ms = flow.get("bidirectional_duration_ms", 45.0)
    duration_sec = round(float(duration_ms) / 1000.0, 4) if duration_ms else 0.045
    deviation_pct = round(((mse - baseline_threshold) / baseline_threshold) * 100.0, 1) if mse > baseline_threshold else 0.0

    flags_list = []
    if flow.get("flag_syn") or flow.get("syn"): flags_list.append("SYN")
    if flow.get("flag_ack") or flow.get("ack", True): flags_list.append("ACK")
    if flow.get("flag_psh") or flow.get("psh"): flags_list.append("PSH")
    if flow.get("flag_fin") or flow.get("fin"): flags_list.append("FIN")
    if flow.get("flag_rst") or flow.get("rst"): flags_list.append("RST")
    flags_str = " | ".join(flags_list) if flags_list else "SYN | ACK (Établi)"

    known_ports = {
        21: "FTP (Contrôle Fichiers)", 22: "SSH (Administration Chiffrée)", 23: "Telnet (Non-sécurisé)",
        25: "SMTP (Relais Messagerie)", 53: "DNS (Résolution de Noms)", 80: "HTTP (Web Non-chiffré)",
        443: "HTTPS (Web TLS/SSL)", 445: "SMB (Partage Windows/Samba)", 3389: "RDP (Bureau à Distance)",
        8080: "HTTP-Alt / Proxy", 8443: "HTTPS-Alt / Management"
    }
    svc_desc = known_ports.get(int(dst_port), "Port Dynamique / Non-standard" if int(dst_port) > 1024 else "Service Système")

    prompt = f"""# RAPPORT D'INVESTIGATION FORENSIQUE SOC TIER-3 : ANALYSE D'INCIDENT & QUALIFICATION

Tu es un analyste senior en cybersécurité, Lead Incident Responder et Threat Hunter dans un SOC Tier-3.
Tu opères sur la plateforme HDVR Autonomous Defense, un système NIDS hybride temps réel composé de :
1. **Classifieur supervisé DNN v4** : 12 classes entraînées sur CIC-IDS2017 (DDoS, DoS-Hulk, DoS-GoldenEye, DoS-Slowloris, DoS-Slowhttptest, PortScan, SSH-Patator, FTP-Patator, WebAttack-SQLi/XSS, Botnet, Scan-Vista, BENIGN).
2. **Autoencodeur profond non-supervisé** : dédié à la détection de déviations Zero-Day sans signature (seuil d'anomalie normalisé $\\theta = {baseline_threshold}$).

L'analyste SOC sollicite ton expertise pour **analyser, contextualiser, déterminer formellement et étiqueter** ce flux réseau pour le cycle d'Active Learning / Human-in-the-Loop.

---

### 🌐 1. TÉLÉMÉTRIE DÉTAILLÉE DU FLUX RÉSEAU
- **Horodatage d'Ingestion :** `{received_at}` | **Sonde de Capture :** `{sensor}`
- **Vecteur Réseau :** `{src_ip}:{src_port}` ➔ `{dst_ip}:{dst_port}` (Protocole : **{proto}**)
- **Service Cible Présumé :** Port `{dst_port}` ({svc_desc})
- **Volumétrie Paquets :** {total_pkts} paquets (Forward: {fwd_pkts} | Backward: {bwd_pkts})
- **Volumétrie Octets :** {total_bytes} octets (Forward: {fwd_bytes} B | Backward: {bwd_bytes} B)
- **Ratio & Débit Moyen :** ~{round(total_bytes / max(1, total_pkts))} octets/paquet | Durée de session : `{duration_sec}s`
- **Drapeaux TCP Observés :** `{flags_str}`

---

### 🧠 2. SIGNAUX DES MOTEURS D'INTELLIGENCE ARTIFICIELLE
- **Inférence Superposée DNN :** Classe prédite = **`{pred}`** (Indice de confiance : **{conf}%**)
- **Score de Reconstruction Autoencodeur (MSE) :** **`{mse:.4f}`** (Seuil baseline normale : `{baseline_threshold}`)
- **Écart Statistique Relatif au Seuil :** **{f"+{deviation_pct}% (Anomalie Majeure)" if deviation_pct > 0 else "Nominal (< seuil)"}**
- **Flag Déviation Zero-Day :** **{"[OUI - ANOMALIE ZERO-DAY DÉTECTÉE]" if is_zd else "[NON - SIGNATURE STANDARD]"}**

---

### ⚖️ 3. ÉVALUATION DES HYPOTHÈSES FORENSIQUES CONCURRENTES
Examine obligatoirement les trois scénarios plausibles :
- **Scénario A (Menace Zero-Day / APT furtive) :** Exploitation d'une vulnérabilité n'existant pas dans le jeu d'entraînement CIC-IDS2017, canal de commande & contrôle (C2) obfusqué, exfiltration chiffrée hors profil nominal.
- **Scénario B (Attaque Réseau Répertoriée) :** Attaque par déni de service, balayage de ports ou tentative de force brute correspondant aux classes connues du DNN.
- **Scénario C (Faux Positif d'Infrastructure) :** Tâche système légitime (sauvegarde réseau, transfert volumineux, heartbeat de supervision, scan de vulnérabilité interne autorisé).

---

### 🎯 4. BORDEREAU STRUCTURÉ DE DÉCISION ACTIVE LEARNING
Fournis OBLIGATOIREMENT en tête de ton analyse les balises machine-readable suivantes pour insertion automatisée dans la base `feedback_flows` :

[VERDICT]: FALSE_POSITIVE ou KNOWN_ATTACK ou CONFIRMED_ZERODAY
[SUGGESTED_LABEL]: Dénomination standardisée (ex: Zero-Day-C2-Tunnel, PortScan, DoS-Hulk, SSH-Patator, WebAttack-SQLi, Benign-Admin-Traffic)
[CONFIDENCE]: Pourcentage de certitude de ta décision (ex: 95%)
[SEVERITE]: CRITIQUE ou ELEVEE ou MOYENNE ou FAIBLE
[JUSTIFICATION]: 2 phrases synthétisant la démonstration technique de cette décision.

---

### 📑 5. RAPPORT D'ANALYSE FORENSIQUE STRUCTURÉ
Développe ensuite ton rapport d'incident complet :
1. **Diagnostic Technique Approfondi :** Décris précisément la cinématique de l'attaque ou la nature du faux positif en t'appuyant sur les ports, le ratio volumétrique et l'écart MSE.
2. **Attribution & Cartographie MITRE ATT&CK :** Tactique principale, Technique ID formelle (ex: `T1046`, `T1071.001`, `T1498`, `T1110`, `T1190`, `T1205`) et description.
3. **Plan de Remédiation Réseau Immédiat :**
   - Règle pare-feu `iptables` pour bloquer la source suspecte : `sudo iptables -A INPUT -s {src_ip} -j DROP`
   - Recommandations d'investigation complémentaire sur les endpoints cibles.
4. **Signature de Détection Pérenne (Règle Suricata) :** Fournis une règle `alert ...` complète permettant d'intercepter de futurs flux similaires sur le réseau.
"""
    return prompt


def compute_campaign_correlations(flows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extrait et corrèle les indicateurs clés et statistiques avancées d'un cluster multi-télémétries."""
    if not flows:
        return {
            "total_flows": 0,
            "zero_day_count": 0,
            "zero_day_pct": 0.0,
            "unique_src_ips": [],
            "unique_dst_ips": [],
            "src_subnets_24": {},
            "targeted_ports": {},
            "protocols": {},
            "avg_mse": 0.0,
            "min_mse": 0.0,
            "max_mse": 0.0,
            "std_mse": 0.0,
            "median_mse": 0.0,
            "avg_deviation_pct": 0.0,
            "total_packets": 0,
            "total_bytes": 0,
            "duration_sec": 0.0,
            "flow_rate_sec": 0.0,
            "is_burst": False,
            "is_distributed": False,
            "dominant_threat": "SUSPICIOUS",
            "preds_distribution": {},
            "flags_distribution": {},
        }

    total = len(flows)
    baseline_threshold = 0.6029
    zd_count = sum(
        1 for f in flows
        if f.get("anomalie_ae") == 1 or f.get("is_zero_day") or (float(f.get("mse_ae") or 0.0) > baseline_threshold)
    )
    zd_pct = round((zd_count / total) * 100.0, 1) if total > 0 else 0.0

    src_ips = list(dict.fromkeys(str(f.get("src_ip", "0.0.0.0")) for f in flows if f.get("src_ip")))
    dst_ips = list(dict.fromkeys(str(f.get("dst_ip", "0.0.0.0")) for f in flows if f.get("dst_ip")))

    subnets: Dict[str, int] = {}
    for ip in src_ips:
        parts = ip.split(".")
        if len(parts) == 4:
            sub = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
            subnets[sub] = subnets.get(sub, 0) + 1

    ports_counter: Dict[int, int] = {}
    for f in flows:
        p = int(f.get("dst_port", 0) or 0)
        if p > 0:
            ports_counter[p] = ports_counter.get(p, 0) + 1
    sorted_ports = dict(sorted(ports_counter.items(), key=lambda item: item[1], reverse=True))

    protos_counter: Dict[str, int] = {}
    flags_counter: Dict[str, int] = {}
    total_pkts = 0
    total_bytes = 0

    for f in flows:
        p_raw = f.get("protocol", "TCP")
        p_str = "TCP" if str(p_raw) in ("6", "TCP") else ("UDP" if str(p_raw) in ("17", "UDP") else ("ICMP" if str(p_raw) in ("1", "ICMP") else str(p_raw)))
        protos_counter[p_str] = protos_counter.get(p_str, 0) + 1

        fwd_p = int(f.get("src2dst_packets", f.get("bidirectional_packets", 14)) or 14)
        bwd_p = int(f.get("dst2src_packets", 8) or 8)
        total_pkts += (fwd_p + bwd_p)

        fwd_b = int(f.get("src2dst_bytes", 1420) or 1420)
        bwd_b = int(f.get("dst2src_bytes", 980) or 980)
        total_bytes += (fwd_b + bwd_b)

        for fl in ("syn", "ack", "rst", "psh", "fin", "urg"):
            if f.get(f"flag_{fl}") or f.get(fl):
                u_fl = fl.upper()
                flags_counter[u_fl] = flags_counter.get(u_fl, 0) + 1

    mses = [float(f.get("mse_ae", 0.0) or 0.0) for f in flows]
    min_mse = round(min(mses), 4) if mses else 0.0
    max_mse = round(max(mses), 4) if mses else 0.0
    avg_mse = round(sum(mses) / len(mses), 4) if mses else 0.0

    if len(mses) > 1:
        variance = sum((x - avg_mse) ** 2 for x in mses) / (len(mses) - 1)
        std_mse = round(math.sqrt(variance), 4)
    else:
        std_mse = 0.0

    sorted_mses = sorted(mses)
    mid = len(sorted_mses) // 2
    if len(sorted_mses) % 2 == 0 and len(sorted_mses) > 0:
        median_mse = round((sorted_mses[mid - 1] + sorted_mses[mid]) / 2.0, 4)
    elif sorted_mses:
        median_mse = round(sorted_mses[mid], 4)
    else:
        median_mse = 0.0

    avg_deviation_pct = round(((avg_mse - baseline_threshold) / baseline_threshold) * 100.0, 1) if avg_mse > baseline_threshold else 0.0

    preds_counter: Dict[str, int] = {}
    for f in flows:
        pred_label = str(f.get("pred", f.get("classification", "SUSPICIOUS")))
        preds_counter[pred_label] = preds_counter.get(pred_label, 0) + 1

    ts_list = []
    for f in flows:
        ts = f.get("received_at", f.get("timestamp"))
        if isinstance(ts, (int, float)):
            ts_list.append(ts)

    duration_sec = 0.0
    if len(ts_list) >= 2:
        duration_sec = round(max(ts_list) - min(ts_list), 2)
    elif total >= 2:
        duration_sec = 1.25

    flow_rate_sec = round(total / max(0.1, duration_sec), 2)
    is_burst = bool(duration_sec < 10.0 and total >= 3)
    is_distributed = bool(len(src_ips) > 1 and len(dst_ips) >= 1)
    top_pred = max(preds_counter.items(), key=lambda x: x[1])[0] if preds_counter else "SUSPICIOUS"

    return {
        "total_flows": total,
        "zero_day_count": zd_count,
        "zero_day_pct": zd_pct,
        "unique_src_ips": src_ips,
        "unique_dst_ips": dst_ips,
        "src_subnets_24": subnets,
        "targeted_ports": sorted_ports,
        "protocols": protos_counter,
        "flags_distribution": flags_counter,
        "avg_mse": avg_mse,
        "min_mse": min_mse,
        "max_mse": max_mse,
        "std_mse": std_mse,
        "median_mse": median_mse,
        "avg_deviation_pct": avg_deviation_pct,
        "total_packets": total_pkts,
        "total_bytes": total_bytes,
        "duration_sec": duration_sec,
        "flow_rate_sec": flow_rate_sec,
        "is_burst": is_burst,
        "is_distributed": is_distributed,
        "dominant_threat": top_pred,
        "preds_distribution": preds_counter,
    }


def build_campaign_forensic_prompt(flows: List[Dict[str, Any]]) -> str:
    """Génère le prompt forensique expert SOC Tier-3 exhaustif pour détection de pattern & campagne multi-flux."""
    corr = compute_campaign_correlations(flows)
    baseline_threshold = 0.6029

    known_ports = {
        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
        80: "HTTP", 443: "HTTPS", 445: "SMB", 3389: "RDP", 8080: "HTTP-Alt", 8443: "HTTPS-Alt"
    }

    src_list_str = ", ".join(f"`{ip}`" for ip in corr["unique_src_ips"][:12])
    if len(corr["unique_src_ips"]) > 12:
        src_list_str += f" ... (+{len(corr['unique_src_ips']) - 12} autres adresses)"

    dst_list_str = ", ".join(f"`{ip}`" for ip in corr["unique_dst_ips"][:8])

    subnets_str = ", ".join(f"`{sub}` ({cnt} IPs)" for sub, cnt in list(corr["src_subnets_24"].items())[:6])
    if not subnets_str:
        subnets_str = "Hôtes dispersés ou adresses locales"

    ports_detailed = []
    for p, cnt in list(corr["targeted_ports"].items())[:8]:
        p_name = known_ports.get(p, "Dynamic/App")
        ports_detailed.append(f"`{p}/{p_name}` ({cnt} flux - {round((cnt/corr['total_flows'])*100)}%)")
    ports_summary = ", ".join(ports_detailed) if ports_detailed else "Ports multiples"

    protos_summary = ", ".join(f"{proto}: {cnt}" for proto, cnt in corr["protocols"].items())
    flags_summary = ", ".join(f"{fl}: {cnt}" for fl, cnt in corr["flags_distribution"].items()) if corr["flags_distribution"] else "SYN/ACK dominants"
    preds_summary = ", ".join(f"`{pred}`: {cnt}" for pred, cnt in corr["preds_distribution"].items())

    # Homogeneity analysis based on standard deviation
    if corr["std_mse"] < 0.08 and corr["total_flows"] >= 2:
        homogeneity_note = f"Forte homogénéité statistique (Écart-type $\\sigma = {corr['std_mse']:.4f}$) ➔ Signature d'un payload ou d'un outil offensif unique et automatisé."
    elif corr["std_mse"] < 0.20:
        homogeneity_note = f"Homogénéité modérée (Écart-type $\\sigma = {corr['std_mse']:.4f}$) ➔ Variantes d'une même charge utile ou variations de taille réseau."
    else:
        homogeneity_note = f"Dispersion statistique élevée (Écart-type $\\sigma = {corr['std_mse']:.4f}$) ➔ Menace polymorphe, scan multi-facettes ou mélange de flux hétérogènes."

    # Build exhaustive flow table (up to 25 rows)
    table_rows = []
    for i, f in enumerate(flows[:25], start=1):
        ts = f.get("received_at", f.get("timestamp", "Live"))
        s_ip = f.get("src_ip", "0.0.0.0")
        s_port = f.get("src_port", "")
        d_ip = f.get("dst_ip", "0.0.0.0")
        d_port = f.get("dst_port", "")
        proto = f.get("protocol", "TCP")
        pred = f.get("pred", f.get("classification", "SUSPICIOUS"))
        conf = round(float(f.get("confiance", f.get("confidence", 0.0))), 1)
        if conf <= 1.0 and conf > 0: conf = round(conf * 100.0, 1)
        mse = round(float(f.get("mse_ae", 0.0) or 0.0), 4)
        is_zd = (f.get("anomalie_ae") == 1 or f.get("is_zero_day") or mse > baseline_threshold)
        dev = f"+{int(((mse - baseline_threshold) / baseline_threshold) * 100)}%" if mse > baseline_threshold else "Nominal"

        fwd_p = int(f.get("src2dst_packets", f.get("bidirectional_packets", 12)) or 12)
        bwd_p = int(f.get("dst2src_packets", 8) or 8)
        fwd_b = int(f.get("src2dst_bytes", 1200) or 1200)

        zd_tag = "**OUI (0-Day)**" if is_zd else "Nominal"
        table_rows.append(
            f"| {i} | `{ts}` | `{s_ip}:{s_port}` | `{d_ip}:{d_port}` | {proto} | {fwd_p}/{bwd_p} pkts ({fwd_b} B) | {pred} ({conf}%) | `{mse:.4f}` | {dev} | {zd_tag} |"
        )

    table_md = "\n".join(table_rows)
    extra_note = f"\n*(+ {len(flows) - 25} autres flux du même cluster présentent des caractéristiques corrélées)*" if len(flows) > 25 else ""

    prompt = f"""# RAPPORT D'INVESTIGATION FORENSIQUE SOC TIER-3 : DÉTECTION DE PATTERN & CAMPAGNE MULTI-FLUX

Tu es un expert senior en Threat Intelligence, Lead DFIR (Digital Forensics & Incident Response) et Analyste Principal SOC Tier-3.
Tu opères sur la console de défense autonome **HDVR**, un système NIDS hybride de pointe articulé autour de deux moteurs d'inférence complémentaires :
1. **Moteur Supervisé (Réseau de Neurones Profond DNN v4)** : 12 classes formées sur l'ontologie CIC-IDS2017 (DDoS, DoS-Hulk, DoS-GoldenEye, DoS-Slowloris, DoS-Slowhttptest, PortScan, SSH-Patator, FTP-Patator, WebAttack-SQLi/XSS, Botnet, Scan-Vista, BENIGN).
2. **Moteur Non-Supervisé (Autoencodeur de Déviation Profonde)** : modélisant l'espace latent du trafic bénin pour détecter les anomalies Zero-Day sans signature préalable (seuil critique de reconstruction $\\theta = {baseline_threshold}$).

L'analyste de garde a sélectionné ce **cluster corrélé de {corr['total_flows']} télémétries réseau suspectes**.
Ta mission est de procéder à une **détection de pattern approfondie**, de déterminer si ce faisceau d'alertes constitue une **campagne offensive coordonnée**, de formuler un diagnostic de menace et d'émettre les recommandations d'étiquetage pour le ré-entraînement du modèle (boucle Active Learning / Human-in-the-Loop).

---

### 📊 1. SYNTHÈSE TOPOLOGIQUE & STATISTIQUE DU CLUSTER DE TÉLÉMÉTRIE
- **Volume Global du Cluster :** **{corr['total_flows']} flux réseau** (Paquets cumulés : **{corr['total_packets']:,}** | Volume : **{corr['total_bytes']:,} octets**)
- **Taux de Déviation Zero-Day :** **{corr['zero_day_count']} / {corr['total_flows']} flux ({corr['zero_day_pct']}%)** dépassent le seuil de l'autoencodeur.
- **Répartition Prédictive DNN Initiale :** {preds_summary}
- **Vecteurs Sources Offensifs :** **{len(corr['unique_src_ips'])} adresse(s) IP unique(s)**
  - Adresses recensées : {src_list_str}
  - Sous-réseaux /24 impliqués : {subnets_str}
- **Périmètre Cible & Cibles Réseau :** **{len(corr['unique_dst_ips'])} cible(s)** : {dst_list_str}
- **Spectre des Ports et Services Visés :** {ports_summary}
- **Couche Transport & Drapeaux TCP :** {protos_summary} | Flags TCP observés : `{flags_summary}`
- **Profil Chronologique & Cadence :**
  - Durée totale d'émission : **`{corr['duration_sec']}s`** (Débit moyen : **`{corr['flow_rate_sec']} flux/sec`**)
  - Comportement temporel : **{"[RAFALE SYNCHRONISÉE - Burst automatisé agressif]" if corr['is_burst'] else "[ACTIVITÉ ÉTALÉE / Low-and-Slow - Démarche furtive]"}**
  - Schéma de dispersion : **{"[ATTAQUE DISTRIBUÉE MULTI-SOURCES]" if corr['is_distributed'] else "[SOURCE FOCALISÉE SUR CIBLES MULTIPLES]"}**

---

### 🔬 2. ANALYSE STATISTIQUE DE L'ESPACE LATENT (AUTOENCODEUR ZERO-DAY)
- **Seuil d'Anomalie Nominal :** $\\theta = {baseline_threshold}$
- **Plage d'Erreur MSE Observée :** Min: **`{corr['min_mse']:.4f}`** | Médiane: **`{corr['median_mse']:.4f}`** | Moyenne: **`{corr['avg_mse']:.4f}`** | Max: **`{corr['max_mse']:.4f}`**
- **Déviation Statistique Moyenne :** **{f"+{corr['avg_deviation_pct']}% au-dessus de la baseline" if corr['avg_deviation_pct'] > 0 else "Conforme à la baseline"}**
- **Dispersion & Homogénéité :** {homogeneity_note}

---

### 📋 3. MATRICE FORENSIQUE DES TÉLÉMÉTRIES DU CLUSTER
| # | Horodatage | Source (IP:Port) | Destination (IP:Port) | Proto | Volumétrie | Préd DNN (Conf) | Score MSE | Écart | Statut Zero-Day |
|---|---|---|---|---|---|---|---|---|---|
{table_md}{extra_note}

---

### ⚖️ 4. ANALYSE DES HYPOTHÈSES CONCURRENTES (ACH FRAMEWORK)
Évalue rigoureusement les 4 hypothèses concurrentes avant de trancher :
- **Hypothèse 1 (Campagne APT / Exploitation Zero-Day Coordonnée) :** Exploitation distribuée d'une vulnérabilité non cataloguée dans CIC-IDS2017, infrastructure de botnet C2 de nouvelle génération, évasion de signature.
- **Hypothèse 2 (Attaque Réseau Volumétrique ou Brute-Force Distribuée) :** Inondation distribuée de type DDoS SYN/UDP flood, balayage de ports horizontal Nmap, ou credential stuffing coordonné contre les services d'accès.
- **Hypothèse 3 (Reconnaissance Pré-Offensive Furtive) :** Cartographie ciblée de services avant phase d'exploitation, sondage de bannières applicatives.
- **Hypothèse 4 (Faux Positif Systémique d'Infrastructure) :** Tâche programmée légitime d'administration, synchronisation de bases de données, sauvegarde automatisée, scan de conformité autorisé (ex: Qualys/Nessus) ou télémétrie cloud.

---

### 🎯 5. BORDEREAU STRUCTURÉ DE DÉCISION ACTIVE LEARNING
Fournis OBLIGATOIREMENT en tout début de réponse les balises standardisées suivantes pour insertion directe dans la base de données Active Learning :

[CAMPAGNE_DETECTEE]: OUI ou NON
[TYPE_CAMPAGNE]: (ex: Campagne Zero-Day APT (C2 Distribué), Scan de Ports Horizontal Multi-Sources, DDoS Volumétrique SYN-Flood, Brute-Force SSH Distribué, Faux Positif de Sauvegarde)
[VERDICT_GLOBAL]: CONFIRMED_ZERODAY ou KNOWN_ATTACK ou FALSE_POSITIVE
[SUGGESTED_LABEL]: Étiquette normalisée pour le ré-entraînement du DNN (ex: Zero-Day-C2-Distributed, PortScan-Horizontal, DDoS-Flooding, Benign-Backup-Job)
[CONFIDENCE]: Pourcentage de certitude de ta qualification (ex: 95%)
[SEVERITE_CLUSTER]: CRITIQUE ou ELEVEE ou MOYENNE ou FAIBLE
[ANALYSTE_JUSTIFICATION]: Résumé technique concis (2-3 phrases) justifiant la corrélation et le verdict global retenu.

---

### 📑 6. RAPPORT D'ANALYSE FORENSIQUE APPROFONDI
Structure ton rapport d'incident complet selon les 5 chapitres standards du SOC Tier-3 :
1. **Caractérisation du Pattern & Corrélation Spatio-Temporelle :** Développe la logique d'attaque (synchronisation, sous-réseaux sources, ciblage des ports, signatures volumétriques communes).
2. **Diagnostic Déviationnel de l'Autoencodeur :** Analyse pourquoi l'autoencodeur rejette la reconstruction de ce lot et quelles caractéristiques sont en rupture avec le trafic nominal.
3. **Attribution & Cartographie MITRE ATT&CK Matrix :**
   - Tactiques (Initial Access, Discovery, Defense Evasion, Impact, Command and Control, Credential Access).
   - Techniques et Sous-techniques officielles avec identifiants (ex: `T1046`, `T1071.001`, `T1498.001`, `T1205`, `T1110.001`, `T1190`).
   - Profil de l'acteur de menace (APT étatique, groupe cybercriminel de ransomware, botnet opportuniste, scanner automatisé, maintenance IT).
4. **Plan de Neutralisation Pare-feu Immédiat :**
   - Script bash haute performance utilisant `ipset` et `iptables` pour bloquer instantanément toutes les adresses sources offensives en une seule opération noyau sans dégradation de performance.
5. **Signature de Détection Réseau Déployable (Règle Suricata) :**
   - Règle Suricata prête à l'emploi (`alert tcp ...`) basée sur les ports cibles, flags et caractéristiques anormales observées pour immuniser le réseau face à de futurs flux de cette campagne.
"""
    return prompt


class AiAnalyzerService:
    """Service d'analyse d'incidents et d'aide à l'étiquetage Active Learning."""

    @classmethod
    async def analyze_incident(cls, flow: Dict[str, Any]) -> Dict[str, Any]:
        cfg = get_ai_config()
        provider = cfg.get("provider", "expert_rules")
        prompt = build_forensic_prompt(flow)

        # Moteur Expert de base pour garantir des valeurs déterministes et structurées
        expert_res = cls._analyze_with_expert_rules(flow)

        if provider == "ollama":
            llm_res = await cls._analyze_with_ollama(cfg, prompt, flow)
            if llm_res.get("success"):
                return cls._merge_llm_result(llm_res, expert_res)
            logger.warning("Ollama call failed, using expert rules analyzer")

        elif provider == "gemini":
            llm_res = await cls._analyze_with_gemini(cfg, prompt, flow)
            if llm_res.get("success"):
                return cls._merge_llm_result(llm_res, expert_res)
            logger.warning("Gemini API call failed, using expert rules analyzer")

        return expert_res

    @classmethod
    async def analyze_campaign(cls, flows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyse un ensemble de télémétries pour détecter des schémas de campagne / attaque coordonnée."""
        cfg = get_ai_config()
        provider = cfg.get("provider", "expert_rules")
        corr = compute_campaign_correlations(flows)
        prompt = build_campaign_forensic_prompt(flows)

        expert_res = cls._analyze_campaign_with_expert_rules(flows, corr)

        if provider == "ollama":
            llm_res = await cls._analyze_campaign_with_ollama(cfg, prompt, corr)
            if llm_res.get("success"):
                return cls._merge_campaign_llm_result(llm_res, expert_res)
            logger.warning("Ollama batch call failed, using expert rules analyzer")

        elif provider == "gemini":
            llm_res = await cls._analyze_campaign_with_gemini(cfg, prompt, corr)
            if llm_res.get("success"):
                return cls._merge_campaign_llm_result(llm_res, expert_res)
            logger.warning("Gemini API batch call failed, using expert rules analyzer")

        return expert_res

    @classmethod
    async def _analyze_campaign_with_ollama(cls, cfg: Dict[str, Any], prompt: str, corr: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{cfg.get('ollama_url', 'http://localhost:11434').rstrip('/')}/api/generate"
        model = cfg.get("ollama_model", "mistral:latest")
        payload = {"model": model, "prompt": prompt, "stream": False}

        try:
            async with httpx.AsyncClient(timeout=35.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "success": True,
                        "provider": f"Ollama ({model})",
                        "analysis_markdown": data.get("response", ""),
                        "prompt_used": prompt,
                    }
                return {"success": False, "error": f"Ollama HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    async def _analyze_campaign_with_gemini(cls, cfg: Dict[str, Any], prompt: str, corr: Dict[str, Any]) -> Dict[str, Any]:
        api_key = cfg.get("gemini_api_key", "").strip()
        if not api_key:
            return {"success": False, "error": "Clé API Gemini non configurée"}
        model = cfg.get("gemini_model", "gemini-2.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1200},
        }

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        text = "".join(p.get("text", "") for p in parts)
                        return {
                            "success": True,
                            "provider": f"Google Gemini ({model})",
                            "analysis_markdown": text,
                            "prompt_used": prompt,
                        }
                return {"success": False, "error": f"Gemini API HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def _merge_campaign_llm_result(cls, llm_res: Dict[str, Any], expert_res: Dict[str, Any]) -> Dict[str, Any]:
        text = llm_res.get("analysis_markdown", "")
        merged = dict(expert_res)
        merged["provider"] = llm_res.get("provider", expert_res["provider"])
        merged["analysis_markdown"] = text

        v_match = re.search(r"\[VERDICT_GLOBAL\]:\s*([A-Z_]+)", text, re.IGNORECASE)
        if v_match:
            v_val = v_match.group(1).upper()
            if v_val in ("FALSE_POSITIVE", "KNOWN_ATTACK", "CONFIRMED_ZERODAY"):
                merged["determined_verdict"] = v_val

        tc_match = re.search(r"\[TYPE_CAMPAGNE\]:\s*([^\n\r]+)", text, re.IGNORECASE)
        if tc_match:
            merged["campaign_type"] = tc_match.group(1).strip()

        l_match = re.search(r"\[SUGGESTED_LABEL\]:\s*([^\n\r]+)", text, re.IGNORECASE)
        if l_match:
            merged["suggested_label"] = l_match.group(1).strip()

        c_match = re.search(r"\[CONFIDENCE\]:\s*(\d+)", text, re.IGNORECASE)
        if c_match:
            try:
                merged["confidence_pct"] = int(c_match.group(1))
            except Exception:
                pass

        j_match = re.search(r"\[ANALYSTE_JUSTIFICATION\]:\s*([^\n\r]+)", text, re.IGNORECASE)
        if j_match:
            merged["justification"] = j_match.group(1).strip()

        return merged

    @classmethod
    def _analyze_campaign_with_expert_rules(cls, flows: List[Dict[str, Any]], corr: Dict[str, Any]) -> Dict[str, Any]:
        total = corr["total_flows"]
        zd_count = corr["zero_day_count"]
        zd_pct = corr["zero_day_pct"]
        unique_src = corr["unique_src_ips"]
        targeted_ports = corr["targeted_ports"]
        dominant = str(corr["dominant_threat"]).upper()
        avg_mse = corr["avg_mse"]
        is_distributed = corr["is_distributed"]
        is_burst = corr["is_burst"]

        if len(unique_src) > 1:
            ips_str = " ".join(unique_src)
            iptables_cmd = f"# Blocage groupé de {len(unique_src)} sources offensives\nfor ip in {ips_str}; do\n  sudo iptables -A INPUT -s $ip -j DROP\ndone"
        elif unique_src:
            iptables_cmd = f"sudo iptables -A INPUT -s {unique_src[0]} -j DROP"
        else:
            iptables_cmd = "# Aucune adresse source identifiée"

        if zd_count > 0 and (zd_pct >= 40.0 or avg_mse > 0.6029):
            determined_verdict = "CONFIRMED_ZERODAY"
            severity = "CRITIQUE"
            has_web_ports = any(p in targeted_ports for p in (443, 8080, 8443))

            if is_distributed:
                campaign_type = "Campagne Zero-Day Distribuée (C2 / Evasion Coordonnée)"
                suggested_label = "Zero-Day-C2-Distributed" if has_web_ports else "Zero-Day-Distributed-Cluster"
                tid, tname, tactic = ("T1205", "Traffic Signaling / Zero-Day Defense Evasion", "Defense Evasion")
                justification = f"Cluster critique de {zd_count} anomalies Zero-Day (MSE moyen {avg_mse:.4f}) distribuées sur {len(unique_src)} sources différentes."
            else:
                campaign_type = "Infiltration Zero-Day Ciblée (Séquence d'Exploitation)"
                suggested_label = "Zero-Day-APT-Exploit"
                tid, tname, tactic = ("T1190", "Exploit Public-Facing Application", "Initial Access")
                justification = f"Séquence répétée d'anomalies Zero-Day (MSE moyen {avg_mse:.4f}) émanant de la source {unique_src[0] if unique_src else 'inconnue'}."
            confidence_pct = min(99, max(85, int(avg_mse * 50) + 60))

        elif dominant != "BENIGN" and dominant != "SUSPICIOUS":
            determined_verdict = "KNOWN_ATTACK"
            if "SCAN" in dominant or len(targeted_ports) >= 3:
                campaign_type = "Campagne de Reconnaissance Réseau (Scan de Ports Distribué)"
                suggested_label = "PortScan-Distributed" if is_distributed else "PortScan"
                tid, tname, tactic = ("T1046", "Network Service Discovery", "Reconnaissance")
                severity = "ÉLEVÉE"
                justification = f"Reconnaissance méthodique ciblant {len(targeted_ports)} port(s) distinct(s) via {len(unique_src)} adresse(s) source."
            elif "DOS" in dominant or "DDOS" in dominant:
                campaign_type = "Attaque par Déni de Service Volumétrique (DDoS Coordonné)"
                suggested_label = "DDoS-Flooding-Campaign" if is_distributed else "DoS-Hulk-Burst"
                tid, tname, tactic = ("T1498", "Network Denial of Service", "Impact")
                severity = "CRITIQUE"
                justification = f"Inondation volumétrique coordonnée ({total} flux en rafale) avec saturation des cibles."
            elif "PATATOR" in dominant or 22 in targeted_ports or 21 in targeted_ports:
                campaign_type = "Campagne de Force Brute Distribuée (Credential Stuffing)"
                suggested_label = "SSH-Patator-Distributed" if 22 in targeted_ports else "FTP-Patator"
                tid, tname, tactic = ("T1110.001", "Brute Force (Password Guessing)", "Credential Access")
                severity = "ÉLEVÉE"
                justification = f"Tentatives répétées d'authentification forcée contre les services d'accès."
            elif "BOT" in dominant:
                campaign_type = "Activité de Botnet Coordonnée (Communication C2)"
                suggested_label = "Botnet-C2-Activity"
                tid, tname, tactic = ("T1071", "Application Layer Protocol (C2)", "Command and Control")
                severity = "CRITIQUE"
                justification = f"Flux caractéristiques de trafic Botnet / Command and Control synchronisé."
            else:
                campaign_type = f"Campagne Offensive Coordonnée ({dominant})"
                suggested_label = f"{dominant}-Campaign"
                tid, tname, tactic = ("T1046", "Network Service Scanning", "Discovery")
                severity = "ÉLEVÉE"
                justification = f"Signature offensive concordante avec la catégorie {dominant} sur {total} flux."
            confidence_pct = 90

        else:
            determined_verdict = "FALSE_POSITIVE"
            campaign_type = "Trafic Réseau Bénin / Faux Positifs Groupés"
            suggested_label = "Trafic-Legitime-Groupe"
            tid, tname, tactic = ("T0000", "Baseline Traffic Activity", "Operational")
            severity = "FAIBLE"
            justification = f"L'ensemble des {total} flux présente des métriques nominales sans indicateur de compromission actif."
            confidence_pct = 88

        markdown = f"""### 🛡️ Diagnostic de Campagne SOC Tier-3
**Type de Campagne :** **`{campaign_type}`**  
**Verdict Global Recommandé :** `{determined_verdict}`  
**Étiquette Suggérée pour le Lot :** **`{suggested_label}`** (Confiance : **{confidence_pct}%**)  
**Motif analytique :** {justification}

---

### 📊 Corrélation & Topologie
- **Total flux analysés :** {total} flux ({zd_count} Zero-Days - {zd_pct}%)
- **Sources distinctes :** {len(unique_src)} IPs | **Ports cibles :** {', '.join(f'{p}' for p in list(targeted_ports.keys())[:5])}
- **Score MSE moyen :** `{avg_mse:.4f}` (Seuil : 0.6029)
- **Comportement temporel :** {"Rafale synchronisée" if is_burst else "Distribution continue"}

---

### 🗺️ Attribution MITRE ATT&CK
- **Technique :** [`{tid}` {tname}](https://attack.mitre.org/techniques/{tid.split('.')[0]}/)
- **Tactique :** `{tactic}`
- **Gravité du Cluster :** **{severity}**

---

### ⚡ Script de Neutralisation Pare-feu
```bash
{iptables_cmd}
```
"""

        return {
            "success": True,
            "provider": "Moteur Expert SOC (Tier-3 Campaign Correlator)",
            "campaign_type": campaign_type,
            "determined_verdict": determined_verdict,
            "suggested_label": suggested_label,
            "confidence_pct": confidence_pct,
            "justification": justification,
            "correlation_summary": corr,
            "mitre": {
                "id": tid,
                "name": tname,
                "tactic": tactic,
                "severity": severity,
            },
            "analysis_markdown": markdown,
            "iptables_rule": iptables_cmd,
            "prompt_used": build_campaign_forensic_prompt(flows),
        }

    @classmethod
    def _merge_llm_result(cls, llm_res: Dict[str, Any], expert_res: Dict[str, Any]) -> Dict[str, Any]:
        """Fusionne la réponse générative LLM avec la structure d'étiquetage expert."""
        text = llm_res.get("analysis_markdown", "")
        merged = dict(expert_res)
        merged["provider"] = llm_res.get("provider", expert_res["provider"])
        merged["analysis_markdown"] = text

        # Extraction des balises structurées si retournées par le LLM
        v_match = re.search(r"\[VERDICT\]:\s*([A-Z_]+)", text, re.IGNORECASE)
        if v_match:
            v_val = v_match.group(1).upper()
            if v_val in ("FALSE_POSITIVE", "KNOWN_ATTACK", "CONFIRMED_ZERODAY"):
                merged["determined_verdict"] = v_val

        l_match = re.search(r"\[SUGGESTED_LABEL\]:\s*([^\n\r]+)", text, re.IGNORECASE)
        if l_match:
            merged["suggested_label"] = l_match.group(1).strip()

        c_match = re.search(r"\[CONFIDENCE\]:\s*(\d+)", text, re.IGNORECASE)
        if c_match:
            try:
                merged["confidence_pct"] = int(c_match.group(1))
            except Exception:
                pass

        j_match = re.search(r"\[JUSTIFICATION\]:\s*([^\n\r]+)", text, re.IGNORECASE)
        if j_match:
            merged["justification"] = j_match.group(1).strip()

        return merged

    @classmethod
    async def _analyze_with_ollama(cls, cfg: Dict[str, Any], prompt: str, flow: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{cfg.get('ollama_url', 'http://localhost:11434').rstrip('/')}/api/generate"
        model = cfg.get("ollama_model", "mistral:latest")

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    analysis_text = data.get("response", "")
                    src_ip = flow.get("src_ip", "0.0.0.0")
                    return {
                        "success": True,
                        "provider": f"Ollama ({model})",
                        "analysis_markdown": analysis_text,
                        "iptables_rule": f"sudo iptables -A INPUT -s {src_ip} -j DROP",
                        "prompt_used": prompt,
                    }
                return {"success": False, "error": f"Ollama HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    async def _analyze_with_gemini(cls, cfg: Dict[str, Any], prompt: str, flow: Dict[str, Any]) -> Dict[str, Any]:
        api_key = cfg.get("gemini_api_key", "").strip()
        if not api_key:
            return {"success": False, "error": "Clé API Gemini non configurée"}

        model = cfg.get("gemini_model", "gemini-2.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800},
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        text = "".join(p.get("text", "") for p in parts)
                        src_ip = flow.get("src_ip", "0.0.0.0")
                        return {
                            "success": True,
                            "provider": f"Google Gemini ({model})",
                            "analysis_markdown": text,
                            "iptables_rule": f"sudo iptables -A INPUT -s {src_ip} -j DROP",
                            "prompt_used": prompt,
                        }
                return {"success": False, "error": f"Gemini API HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def _analyze_with_expert_rules(cls, flow: Dict[str, Any]) -> Dict[str, Any]:
        """Moteur d'aide à la décision et d'étiquetage forensique Tier-3."""
        pred = str(flow.get("pred", flow.get("classification", "SUSPICIOUS"))).upper()
        src_ip = flow.get("src_ip", "0.0.0.0")
        dst_ip = flow.get("dst_ip", "0.0.0.0")
        dst_port = int(flow.get("dst_port", 0) or 0)
        mse = round(float(flow.get("mse_ae", 0.0) or 0.0), 4)
        is_zd = bool(flow.get("anomalie_ae") == 1 or flow.get("is_zero_day"))
        raw_conf = float(flow.get("confiance", flow.get("confidence", 0.85)) or 0.85)
        conf_pct = round(raw_conf * 100.0 if raw_conf <= 1.0 else raw_conf, 1)

        mitre_map = {
            "PORTSCAN": ("T1046", "Network Service Discovery", "Reconnaissance"),
            "DDOS": ("T1498", "Network Denial of Service", "Impact"),
            "DOS-HULK": ("T1499", "Endpoint DoS (HTTP Flooding)", "Impact"),
            "DOS-GOLDENEYE": ("T1499", "Endpoint DoS (Keep-Alive Exhaustion)", "Impact"),
            "DOS-SLOWLORIS": ("T1499", "Endpoint DoS (Slowloris)", "Impact"),
            "SSH-PATATOR": ("T1110.001", "Brute Force (Password Guessing)", "Credential Access"),
            "FTP-PATATOR": ("T1110.001", "Brute Force (FTP Credential Guessing)", "Credential Access"),
            "BOTNET": ("T1071", "Application Layer Protocol (C2)", "Command and Control"),
            "INFILTRATION": ("T1203", "Exploitation for Client Execution", "Execution"),
            "WEBATTACK": ("T1190", "Exploit Public-Facing Application", "Initial Access"),
        }

        matched_key = next((k for k in mitre_map if k in pred), None)
        if matched_key:
            tid, tname, tactic = mitre_map[matched_key]
        elif is_zd:
            tid, tname, tactic = ("T1205", "Traffic Signaling / Zero-Day Evasion", "Defense Evasion")
        else:
            tid, tname, tactic = ("T1046", "Network Service Scanning", "Discovery")

        # 1. Détermination du Verdict et Suggestion d'Étiquette
        if is_zd:
            determined_verdict = "CONFIRMED_ZERODAY"
            suggested_label = "ZERO-DAY-C2-ANOMALY" if dst_port in (443, 8080, 8443) else "ZERO-DAY-DEVIATION"
            confidence_pct = min(99, max(82, int(mse * 55) + 60))
            justification = (
                f"Déviation statistique critique de l'autoencodeur (MSE {mse:.4f} > 0.6029). "
                f"Comportement offensif sans signature cataloguée : étiquetage Zero-Day recommandé."
            )
            severity = "CRITIQUE"
        elif pred != "BENIGN":
            determined_verdict = "KNOWN_ATTACK"
            # Nettoyage du label standard
            if "DOS" in pred:
                suggested_label = "DDoS" if "DDOS" in pred else "DoS-Hulk"
            elif "PATATOR" in pred:
                suggested_label = "SSH-Patator" if dst_port == 22 else "FTP-Patator"
            elif "SCAN" in pred:
                suggested_label = "PortScan"
            elif "BOT" in pred:
                suggested_label = "Botnet"
            elif "WEB" in pred:
                suggested_label = "WebAttack-SQLi" if dst_port == 80 else "WebAttack-XSS"
            else:
                suggested_label = pred

            confidence_pct = max(78, int(conf_pct))
            justification = f"Signature concordante avec l'attaque {suggested_label} ({tactic} - MITRE {tid})."
            severity = "ÉLEVÉE"
        else:
            determined_verdict = "FALSE_POSITIVE"
            suggested_label = "Trafic Légitime (Bénin)"
            confidence_pct = 88
            justification = "Télémétrie nominale sans indicateur de compromission actif. Faux positif confirmé."
            severity = "FAIBLE"

        # 2. Caractéristiques divergentes comparées à la baseline
        pkts = flow.get("src2dst_packets", flow.get("bidirectional_packets", 14))
        bytes_cnt = flow.get("src2dst_bytes", 1420)

        key_divergent_features: List[Dict[str, str]] = [
            {
                "feature": "Erreur de Reconstruction (MSE)",
                "observed": f"{mse:.4f}",
                "baseline": "< 0.6029 (Normale)",
                "deviation": f"+{int((mse / 0.6029 - 1) * 100)}%" if mse > 0.6029 else "Nominale",
            },
            {
                "feature": "Cible & Port Réseau",
                "observed": f"{dst_ip}:{dst_port} ({flow.get('protocol', 'TCP')})",
                "baseline": "Services autorisés",
                "deviation": "Port critique / d'écoute" if dst_port in (21, 22, 23, 80, 443, 445, 3389, 8080) else "Standard",
            },
            {
                "feature": "Volume & Taille Paquets",
                "observed": f"{pkts} paquets ({bytes_cnt} octets)",
                "baseline": "< 30 paquets / session",
                "deviation": "Intensité anormale" if pkts > 50 else "Conforme",
            },
        ]

        iptables_cmd = f"sudo iptables -A INPUT -s {src_ip} -j DROP"

        markdown = f"""### 🛡️ Diagnostic de Détermination SOC Tier-3
**Verdict suggéré :** `{determined_verdict}`  
**Étiquette recommandée :** **`{suggested_label}`** (Confiance : **{confidence_pct}%**)  
**Motif analytique :** {justification}

---

### 🗺️ Cartographie MITRE ATT&CK
- **Technique :** [`{tid}` {tname}](https://attack.mitre.org/techniques/{tid.split('.')[0]}/)
- **Tactique :** `{tactic}`
- **Évaluation de Gravité :** **{severity}**

---

### ⚡ Commande de Remédiation Immédiate
```bash
{iptables_cmd}
```
"""

        return {
            "success": True,
            "provider": "Moteur Expert SOC (Tier-3 Determination Engine)",
            "determined_verdict": determined_verdict,
            "suggested_label": suggested_label,
            "confidence_pct": confidence_pct,
            "justification": justification,
            "key_divergent_features": key_divergent_features,
            "mitre": {
                "id": tid,
                "name": tname,
                "tactic": tactic,
                "severity": severity,
            },
            "analysis_markdown": markdown,
            "iptables_rule": iptables_cmd,
            "prompt_used": build_forensic_prompt(flow),
        }

    @classmethod
    async def test_connection(cls, cfg: Dict[str, Any]) -> Tuple[bool, str]:
        provider = cfg.get("provider", "expert_rules")
        if provider == "expert_rules":
            return True, "Moteur Expert intégré opérationnel (100% hors-ligne, zéro dépendance)"

        if provider == "ollama":
            url = f"{cfg.get('ollama_url', 'http://localhost:11434').rstrip('/')}/api/tags"
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        models = [m.get("name") for m in resp.json().get("models", [])]
                        return True, f"Connexion Ollama réussie ({len(models)} modèle(s) disponibles)"
                    return False, f"Ollama HTTP {resp.status_code}: {resp.text}"
            except Exception as e:
                return False, f"Impossible de joindre le serveur Ollama: {str(e)}"

        if provider == "gemini":
            api_key = cfg.get("gemini_api_key", "").strip()
            if not api_key:
                return False, "Clé API Gemini requise"
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        return True, "Clé API Google Gemini validée avec succès"
                    return False, f"Erreur validation Gemini ({resp.status_code})"
            except Exception as e:
                return False, f"Erreur de connexion Gemini: {str(e)}"

        return False, "Fournisseur inconnu"
