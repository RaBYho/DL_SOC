import json
import logging
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
    """Génère le prompt forensique orienté assistance à l'étiquetage et triage."""
    src_ip = flow.get("src_ip", "0.0.0.0")
    dst_ip = flow.get("dst_ip", "0.0.0.0")
    src_port = flow.get("src_port", 0)
    dst_port = flow.get("dst_port", 0)
    proto = flow.get("protocol", "TCP")
    pred = flow.get("pred", flow.get("classification", "SUSPICIOUS"))
    conf = round(float(flow.get("confiance", flow.get("confidence", 0.0))), 1)
    if conf <= 1.0 and conf > 0:
        conf = round(conf * 100.0, 1)
    mse = round(float(flow.get("mse_ae", 0.0) or 0.0), 4)
    is_zd = bool(flow.get("anomalie_ae") == 1 or flow.get("is_zero_day"))
    sensor = flow.get("sensor_id", "probe-edge-01")

    prompt = f"""Tu es un analyste senior en cybersécurité SOC Tier-3.
Ta mission est d'AIDER À DÉTERMINER ET À ÉTIQUETER ce flux réseau suspect pour le système d'Active Learning du NIDS :

### 🌐 Télémétrie du Flux
- **Source :** `{src_ip}:{src_port}` ➔ **Destination :** `{dst_ip}:{dst_port}`
- **Protocole :** {proto} | **Sonde :** `{sensor}`
- **Prédiction DNN initiale :** {pred} (Confiance : {conf}%)
- **Score d'anomalie MSE (Autoencodeur) :** {mse} (Seuil normal : 0.6029)
- **Flag Déviation Zero-Day :** {"OUI" if is_zd else "NON"}

### 🎯 Décision d'Étiquetage Attendue :
Fournis OBLIGATOIREMENT en début de réponse les tags suivants :
[VERDICT]: FALSE_POSITIVE ou KNOWN_ATTACK ou CONFIRMED_ZERODAY
[SUGGESTED_LABEL]: Nom précis de la menace (ex: DDoS, PortScan, DoS-Hulk, SSH-Patator, Botnet, ou Bénin)
[CONFIDENCE]: Pourcentage de certitude (ex: 92%)
[JUSTIFICATION]: 1-2 phrases résumant la raison technique de cette qualification.

Puis structure ton analyse détaillée :
1. **Diagnostic Technique :** Décris le mécanisme d'attaque ou la nature du faux positif.
2. **Cartographie MITRE ATT&CK :** Technique ID (ex: T1046, T1498) et nom officiel.
3. **Remédiation Immédiate :** Règle pare-feu `iptables` pour bloquer l'IP source.
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
