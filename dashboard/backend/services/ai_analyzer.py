import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
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
    """Génère le prompt forensique normalisé pour tout LLM externe ou interne."""
    src_ip = flow.get("src_ip", "0.0.0.0")
    dst_ip = flow.get("dst_ip", "0.0.0.0")
    src_port = flow.get("src_port", 0)
    dst_port = flow.get("dst_port", 0)
    proto = flow.get("protocol", "TCP")
    pred = flow.get("pred", flow.get("classification", "SUSPICIOUS"))
    conf = round(float(flow.get("confiance", flow.get("confidence", 0.0))), 1)
    mse = round(float(flow.get("mse_ae", 0.0) or 0.0), 4)
    is_zd = bool(flow.get("anomalie_ae") == 1 or flow.get("is_zero_day"))
    sensor = flow.get("sensor_id", "probe-edge-01")

    prompt = f"""Tu es un analyste senior en cybersécurité SOC Tier-3.
Analyse le flux réseau suspect suivant intercepté par notre NIDS (Deep Learning) :

### 🌐 Métadonnées du flux
- **Horodatage :** {flow.get("received_at", "En direct")}
- **Source :** `{src_ip}:{src_port}` ➔ **Destination :** `{dst_ip}:{dst_port}`
- **Protocole :** {proto}
- **Sonde de capture :** `{sensor}`

### 🧠 Télémétrie IA du NIDS
- **Score d'anomalie MSE (Autoencodeur) :** {mse} (Seuil de référence : 0.6029)
- **Détection Zero-Day :** {"OUI (Déviation anormale avérée)" if is_zd else "NON (Signature connue)"}
- **Classification préliminaire DNN :** {pred} (Confiance : {conf}%)

### 🎯 Instructions d'analyse attendues :
1. **Diagnostic rapide :** Quelle est la nature technique probable de ce flux ?
2. **Cartographie MITRE ATT&CK :** Fournis l'ID de technique (ex: T1046, T1498) et la tactique correspondante.
3. **Niveau de criticité :** Évalue la sévérité (Faible, Moyen, Élevé, Critique) avec justification.
4. **Remédiation immédiate :** Règle `iptables` exacte pour isoler l'IP source et recommandation opérationnelle.
"""
    return prompt


class AiAnalyzerService:
    """Service d'analyse d'incidents par IA générative et moteur expert."""

    @classmethod
    async def analyze_incident(cls, flow: Dict[str, Any]) -> Dict[str, Any]:
        cfg = get_ai_config()
        provider = cfg.get("provider", "expert_rules")
        prompt = build_forensic_prompt(flow)

        if provider == "ollama":
            result = await cls._analyze_with_ollama(cfg, prompt, flow)
            if result.get("success"):
                return result
            logger.warning("Ollama call failed, falling back to expert rules analyzer")

        elif provider == "gemini":
            result = await cls._analyze_with_gemini(cfg, prompt, flow)
            if result.get("success"):
                return result
            logger.warning("Gemini API call failed, falling back to expert rules analyzer")

        # Fallback universel : Moteur expert SOC Tier-3 déterministe
        return cls._analyze_with_expert_rules(flow)

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
                        "provider": "Ollama (" + model + ")",
                        "analysis_markdown": analysis_text,
                        "iptables_rule": f"sudo iptables -A INPUT -s {src_ip} -j DROP",
                        "prompt_used": prompt,
                    }
                else:
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
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 800,
            }
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
                            "provider": "Google Gemini (" + model + ")",
                            "analysis_markdown": text,
                            "iptables_rule": f"sudo iptables -A INPUT -s {src_ip} -j DROP",
                            "prompt_used": prompt,
                        }
                return {"success": False, "error": f"Gemini API HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def _analyze_with_expert_rules(cls, flow: Dict[str, Any]) -> Dict[str, Any]:
        """Analyseur expert SOC Tier-3 autonome et déterministe (sans dépendance externe)."""
        pred = str(flow.get("pred", flow.get("classification", "SUSPICIOUS"))).upper()
        src_ip = flow.get("src_ip", "0.0.0.0")
        dst_ip = flow.get("dst_ip", "0.0.0.0")
        dst_port = flow.get("dst_port", 0)
        mse = round(float(flow.get("mse_ae", 0.0) or 0.0), 4)
        is_zd = bool(flow.get("anomalie_ae") == 1 or flow.get("is_zero_day"))

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

        if is_zd:
            severity = "CRITIQUE"
            diag = (
                f"Ce flux présente une déviation statistique massive par rapport à la baseline normale "
                f"(MSE: {mse} vs seuil 0.6029). Il s'agit d'une tentative potentielle d'évasion, d'un exploit zero-day "
                f"ou d'un protocole de commande et contrôle (C2) non catalogué."
            )
        elif "DDOS" in pred or "DOS" in pred:
            severity = "ÉLEVÉE / CRITIQUE"
            diag = (
                f"Activité d'épuisement de ressources détectée ciblant le port {dst_port}. "
                f"Inondation volumétrique susceptible d'impacter la disponibilité des services hébergés sur {dst_ip}."
            )
        elif "PATATOR" in pred:
            severity = "ÉLEVÉE"
            diag = (
                f"Tentatives répétées d'authentification forcée par dictionnaire contre le service port {dst_port}. "
                f"Risque immédiat de compromission d'identifiants administrateurs."
            )
        else:
            severity = "MOYENNE"
            diag = (
                f"Comportement réseau suspect correspondant à la signature `{pred}`. "
                f"L'adresse {src_ip} a sondé la cible {dst_ip}:{dst_port}."
            )

        iptables_cmd = f"sudo iptables -A INPUT -s {src_ip} -j DROP"

        markdown = f"""### 🛡️ Diagnostic Synthétique SOC Tier-3
{diag}

---

### 🗺️ Cartographie MITRE ATT&CK
- **Technique :** [`{tid}` {tname}](https://attack.mitre.org/techniques/{tid.split('.')[0]}/)
- **Tactique :** `{tactic}`
- **Évaluation de Gravité :** **{severity}**

---

### ⚡ Remédiation Immédiate & Blocage
Appliquer le bannissement immédiat au niveau de la couche pare-feu :

```bash
{iptables_cmd}
```

*Règle de monitoring Suricata recommandée :*
```suricata
alert tcp {src_ip} any -> $HOME_NET {dst_port} (msg:"NIDS SOC Tier-3: Bannissement actif"; threshold:type limit, track by_src, count 1, seconds 300; sid:9000001; rev:1;)
```
"""
        return {
            "success": True,
            "provider": "Moteur Expert SOC (Tier-3 Rules Engine)",
            "analysis_markdown": markdown,
            "iptables_rule": iptables_cmd,
            "prompt_used": build_forensic_prompt(flow),
        }

    @classmethod
    async def test_connection(cls, cfg: Dict[str, Any]) -> Tuple[bool, str]:
        provider = cfg.get("provider", "expert_rules")
        if provider == "expert_rules":
            return True, "Moteur Expert intégré prêt et fonctionnel (100% hors-ligne)"

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
