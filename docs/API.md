# Spécification API & WebSockets — Sentinel NIDS

Sentinel NIDS expose une API REST haute performance (FastAPI) et un canal bidirectionnel WebSocket (`/ws`) pour la télémétrie, la commande et l'intégration externe avec des outils SIEM/SOAR (Splunk, Elastic, TheHive, Wazuh, etc.).

---

## 1. Vue d'Ensemble & Authentification

- **Base URL** : `http://<HOST>:<PORT>/api/dashboard`
- **Format d'échange** : JSON (UTF-8)
- **Documentation interactive** : `http://<HOST>:<PORT>/docs` (Swagger UI)
- **Schéma OpenAPI** : `http://<HOST>:<PORT>/openapi.json`
- **En-tête Content-Type** : `application/json`

---

## 2. Endpoints de Télémétrie et Ingestion des Flux

### 2.1 Ingestion d'un Micro-Batch de Flux
`POST /flows/ingest`

Reçoit un lot de flux réseau analysés par une sonde physique ou un module de rejeu.

#### Exemple de Requête :
```json
{
  "sensor_id": "sensor-eth0",
  "interface": "eth0",
  "flows": [
    {
      "timestamp": 1794310477.68,
      "src_ip": "172.20.10.5",
      "dst_ip": "142.251.216.78",
      "src_port": 35409,
      "dst_port": 443,
      "protocol": "TCP",
      "packet_count": 4,
      "verdict": "BENIGN",
      "stage1_score": 0.05,
      "confidence": 0.0,
      "kitsune_score": 0.0012,
      "decision_path": "STAGE1_BENIGN",
      "dpi_rule": "",
      "is_anomaly": false,
      "raw_metrics": {
        "flow_duration": 0.001399,
        "flow_bytes_s": 2857040.74,
        "flow_packets_s": 2859.18,
        "total_fwd_packets": 4,
        "total_bwd_packets": 0,
        "avg_packet_size": 999.25,
        "syn_flag_count": 0,
        "ack_flag_count": 0,
        "psh_flag_count": 0,
        "down_up_ratio": 0.0,
        "all_features": {
          "Flow Duration": 0.0014,
          "Flow Bytes/s": 2857040.74,
          "Total Fwd Packets": 4
        }
      }
    }
  ]
}
```

#### Réponse (200 OK) :
```json
{
  "status": "success",
  "inserted": 1,
  "inserted_flows": 1,
  "alerts": 0,
  "generated_incidents": 0,
  "traffic_status": "NORMAL"
}
```

---

### 2.2 Consultation des Flux Récents
`GET /flows/recent`

Retourne la liste paginée des derniers flux réseau ingérés avec enrichissement sémantique (sévérité, moteur, métriques).

#### Paramètres Query :
- `limit` (int, défaut : `50`) : Nombre de flux à récupérer.
- `offset` (int, défaut : `0`) : Décalage de pagination.
- `severity` (string, optionnel) : Filtre par sévérité (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `BENIGN`).
- `exclude_loopback` (bool, défaut : `false`) : Exclut le trafic `127.0.0.1`.

#### Exemple de Réponse :
```json
[
  {
    "id": 142,
    "received_at": 1794310477.68,
    "src_ip": "172.20.10.5",
    "dst_ip": "142.251.216.78",
    "src_port": 35409,
    "dst_port": 443,
    "protocol": 6,
    "pred": "BENIGN",
    "confiance": 0.0,
    "mse_ae": 0.0012,
    "anomalie_ae": 0,
    "packet_count": 4,
    "severity": "BENIGN",
    "threat_class": "BENIGN",
    "engine": "Filtrage Rapide"
  }
]
```

---

### 2.3 Investigation Médico-Légale d'un Flux (Forensics)
`GET /flows/{flow_id}/forensics`

Fournit l'ensemble des données d'investigation médico-légale d'un flux spécifique : quintuplet réseau, scores ML détaillés, métriques brutes, matrice intégrale des caractéristiques CICFlowMeter et historique de l'IP émettrice.

#### Réponse (200 OK) :
```json
{
  "flow_id": 142,
  "five_tuple": {
    "src_ip": "172.20.10.5",
    "src_port": 35409,
    "dst_ip": "142.251.216.78",
    "dst_port": 443,
    "protocol": 6
  },
  "ml_scores": {
    "stage1_prediction": "BENIGN",
    "stage2_confidence": 0.0,
    "kitsune_rmse": 0.0012,
    "is_anomaly": false,
    "decision_engine": "Filtrage Rapide",
    "severity": "BENIGN"
  },
  "raw_metrics": {
    "flow_duration": 0.001399,
    "flow_bytes_s": 2857040.74,
    "flow_packets_s": 2859.18,
    "total_fwd_packets": 4,
    "total_bwd_packets": 0,
    "fwd_packet_length_mean": 999.25,
    "bwd_packet_length_mean": 0.0,
    "syn_flag_count": 0,
    "ack_flag_count": 0,
    "psh_flag_count": 0,
    "fin_flag_count": 0,
    "rst_flag_count": 0,
    "down_up_ratio": 0.0,
    "avg_packet_size": 999.25,
    "dpi_rule": "",
    "all_features": {
      "Flow Duration": 0.0014,
      "Flow Bytes/s": 2857040.74,
      "Packet Length Variance": 257107.68
    }
  },
  "incident": null,
  "ip_history": [
    {
      "id": 140,
      "received_at": 1794310470.12,
      "dst_port": 443,
      "pred": "BENIGN",
      "confiance": 0.0,
      "mse_ae": 0.0014
    }
  ]
}
```

---

## 3. Endpoints de Gestion des Incidents & Alertes

### 3.1 Liste des Incidents Consolidés
`GET /alerts`

#### Paramètres Query :
- `limit` (int, défaut : `50`)
- `offset` (int, défaut : `0`)
- `severity` (string, optionnel) : `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`
- `status` (string, optionnel) : `OPEN`, `INVESTIGATING`, `RESOLVED`, `FALSE_POSITIVE`
- `search` (string, optionnel) : Recherche par IP ou type d'attaque
- `exclude_loopback` (bool, défaut : `false`)

### 3.2 Mise à Jour du Statut d'un Incident
`POST /alerts/{incident_id}/status`

Permet à l'analyste SOC de modifier l'état d'un incident avec commentaire d'audit.

#### Corps de Requête :
```json
{
  "status": "INVESTIGATING",
  "comment": "Prise en charge par analyste N2 - scan SYN confirmé sur port 80/443"
}
```

#### Valeurs de Statut Supportées :
- `OPEN` : Incident nouvellement créé, en attente de prise en charge.
- `INVESTIGATING` : Triage actif en cours par un analyste.
- `RESOLVED` : Menace neutralisée ou incident clos.
- `FALSE_POSITIVE` : Faux positif confirmé, archivé pour réentraînement.

---

## 4. Endpoints Statistiques & Séries Temporelles

### 4.1 Chronologie du Trafic Réseau
`GET /stats/timeline`

Retourne la série temporelle segmentée par tranches pour le graphique `TrafficTimeline`.
- `window_minutes` (int, défaut : `15`)
- `buckets` (int, défaut : `20`)
- `exclude_loopback` (bool, défaut : `false`)

### 4.2 Ventilation par Moteur de Détection
`GET /stats/engine-distribution`

Retourne le décompte des détections attribuées à chaque moteur (`DPI Signature`, `ML Supervised (1D-DNN)`, `Kitsune KitNET (0-Day)`, `Benign Traffic`).

### 4.3 Principaux Acteurs Hostiles
`GET /threat-actors`

Fournit la liste des adresses IP source les plus agressives avec classification des menaces et sévérité globale.

### 4.4 Statistiques des Cibles
`GET /stats/targets`

Fournit l'IP la plus ciblée, le port le plus attaqué (`top_targeted_port`), le service associé (`top_targeted_service`) et la distribution des victimes.

---

## 5. Spécification du Canal WebSocket (`/ws`)

Le serveur expose un point de terminaison WebSocket temps réel à l'adresse `ws://<HOST>:<PORT>/ws`.

### Format des Messages Émis :
```json
{
  "type": "<EVENT_TYPE>",
  "data": { ... }
}
```

### Types d'Événements :
1. `telemetry_update` : Émis à chaque nouveau micro-batch ingéré. Contient les KPI actualisés, les données de séries temporelles et le résumé du trafic.
2. `incident_alert` : Émis lors de la création ou de la mise à jour d'un incident de sécurité.
3. `incident_status_update` : Diffusé lorsque le statut d'un incident est modifié (`OPEN` $\to$ `INVESTIGATING` $\to$ `RESOLVED`).
4. `sensor_heartbeat` : Signal de pulsation émis périodiquement par les sondes réseau connectées.
5. `db_reset` : Signal de purge globale de la base de données (pour sessions de test).
