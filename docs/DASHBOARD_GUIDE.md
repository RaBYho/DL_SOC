# Guide Opérateur — SOC Command Center Dashboard

Ce guide s'adresse aux analystes de sécurité SOC, ingénieurs détection et opérateurs réseau exploitant l'interface **Sentinel NIDS SOC Command Center**.

---

## 1. Démarrage et Accès au Dashboard

### 1.1 Mode Intégré (Recommandé en Production)
Lance simultanément la sonde de capture réseau (sur carte physique ou virtuelle) et le serveur Web de commande SOC :
```bash
python main.py -i enx3ecd36af7cdb -b 5 --dashboard
```
- `-i, --interface` : Nom de l'interface réseau (ex : `eth0`, `enx3ecd36af7cdb`, `wlan0`).
- `-b, --duration` : Durée des micro-batchs de capture en secondes (défaut : `5` ou `15`).
- `--dashboard` : Active le couplage temps réel avec l'API et l'interface Web SOC.

### 1.2 Mode Standalone (Serveur Dashboard Seul)
Démarre uniquement l'interface Web et l'API de commande pour consulter l'historique ou recevoir les flux de sondes distantes :
```bash
python main.py --dashboard-only --host 0.0.0.0 --port 8000
```

### 1.3 Mode Analyse Hors-Ligne (Fichier PCAP)
Analyse un fichier PCAP capturé préalablement avec rejeu visuel dans le dashboard :
```bash
python main.py --pcap pcap/demo_nmap.pcap --dashboard --allow-loopback
```

---

## 2. Accès aux Interfaces Web & API

- **Dashboard Web SOC** : [http://localhost:8000](http://localhost:8000)
- **Documentation API Interactive (Swagger UI)** : [http://localhost:8000/docs](http://localhost:8000/docs)
- **Spécification OpenAPI (JSON)** : [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)
- **Flux WebSocket Temps Réel** : `ws://localhost:8000/ws`

---

## 3. Description des Éléments du Dashboard

### 3.1 Barre d'État Supérieure (`TopStatusBar`)
- **Indicateur Sonde & Statut** : Nom de l'interface réseau active, état `ONLINE` avec point vert pulsant.
- **Métriques Live** : Débit de paquets par seconde (`pkt/s`) et flux analysés par seconde (`flow/s`).
- **Seuils Opérationnels** :
  - `T1: 0.50` : Seuil de suspicion Étage 1 (CatBoost / XGBoost).
  - `T2: 0.70` : Seuil de confiance Étage 2 (1D-DNN multiclasse).
  - `T3: 0.0100` : Seuil d'anomalie dynamique Kitsune (auto-calibré).
- **Contrôles Analyste** :
  - `LIVE / PAUSED` : Met en pause l'affichage des nouveaux flux pour figer l'écran pendant une analyse d'incident.
  - `Exclude Loopback` : Masque le trafic local `127.0.0.1` pour se concentrer exclusivement sur les échanges réseau réels.

### 3.2 Bandeau des 5 Indicateurs Clés (`KpiStrip`)
1. **Total Flows** : Nombre total de flux réseau ingérés et traités.
2. **Critical Attacks** : Alertes confirmées de haute gravité (DDoS, Bot, Exploits Web, Brute-Force).
3. **0-Day Anomalies** : Déviations statistiques non-supervisées détectées par Kitsune sans signature connue.
4. **DPI Triggered** : Règle d'inspection de contenu applicatif L7 déclenchée (SQLi, XSS, Log4j).
5. **Inspection Rate** : Pourcentage du trafic ayant franchi le pré-filtrage et analysé par l'inférence neuronale.

### 3.3 Graphique Temporel (`TrafficTimeline`)
- Canvas Chart.js à double courbe et histogramme empilé avec transition fluide (350ms) :
  - **Zone Grise (Zinc)** : Volume de trafic normal bénin (`BENIGN`).
  - **Pics Rouges** : Attaques confirmées détectées par les étages supervisés ou le DPI.
  - **Pics Jaunes / Ambre** : Anomalies non supervisées (suspicions 0-day).
- **Synchronisation d'Horloge** : Les tranches temporelles sont alignées par intervalles de 30 secondes pour éliminer tout scintillement ou réinitialisation d'échelle.

### 3.4 Répartition par Moteur (`EngineDonut`)
Graphique circulaire à anneau montrant la contribution de chaque moteur de défense :
- **Orange (#f97316)** : Moteur Signature DPI (L7).
- **Rouge (#ef4444)** : Modèle 1D-DNN Supervisé (L4-L7).
- **Jaune (#eab308)** : Autoencodeur Kitsune KitNET (0-Day).
- **Émeraude (#10b981)** : Trafic Bénin validé.

### 3.5 Tableau de Triage des Flux (`FlowTriageTable`)
- Tableau haute densité adapté aux écrans SOC :
  - **Horodatage** : Heure locale avec millisecondes (`HH:MM:SS.mmm`).
  - **Quintuplet Réseau** : IP Source, Port Source, IP Cible, Port Cible, Protocole (TCP/UDP/ICMP).
  - **Verdict & Menace** : Libellé de la menace (`DDoS`, `PortScan`, `Web Attack`, etc.).
  - **Sévérité** : Badge sémantique (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `BENIGN`).
  - **Moteur Responsable** : Indication du sous-système ayant pris la décision.
  - **Scores** : Probabilité Étage 1, Confiance Étage 2, RMSE Kitsune.
- **Filtres & Recherche** : Recherche plein texte par IP ou port, filtrage par niveau de sévérité.
- **Sélection d'un flux** : Cliquer sur une ligne ouvre instantanément le tiroir médico-légal (*Forensics Drawer*).

---

## 4. Tiroir d'Investigation Médico-Légale (`ForensicsDrawer`)

Le tiroir latéral permet d'approfondir l'investigation sur un flux suspect sans quitter l'interface principale :

### 4.1 Identité Réseau 5-Tuple
- Endpoints source et cible complets (IP:Port).
- Protocole de transport résolu (`TCP (Transmission Control Protocol)`, `UDP`, `ICMP`).
- Moteur ayant pris la décision finale.

### 4.2 Décomposition des Scores Multicouches
- **Étage 1** : Jauge de suspicion avec seuil de basculement ($t_1 = 0.50$).
- **Étage 2** : Jauge de confiance de classification DNN ($t_2 = 0.70$).
- **Kitsune RMSE** : Erreur de reconstruction de l'autoencodeur comparée au seuil dynamique $t_3$.

### 4.3 Inspection de Contenu L7 (DPI)
- Signature déclenchée le cas échéant (`DPI-SQLI`, `DPI-XSS`, `DPI-RCE-LOG4J`, `DPI-WEB-FUZZ`).
- Libellé `None (Traffic Clean)` en l'absence de motif hostile dans la charge utile.

### 4.4 Métriques Télémétriques Brutes & Matrice des 84 Features
- **Indicateurs Clés Formatés** :
  - Durée du flux : Formatée lisiblement (`µs`, `ms` ou `s`).
  - Paquets : Répartition avant / arrière (`Total Fwd / Bwd`).
  - Débit : Exprimé en `B/s`, `KB/s` ou `MB/s`.
  - Taille Moyenne des Paquets : Exprimée en octets (`B`).
  - Drapeaux TCP : Indicateurs `SYN / ACK / PSH / FIN / RST`.
  - Ratio Down/Up : Ratio volumétrique entrant/sortant.
- **Inspecteur Intégral 84 Caractéristiques** :
  - Bouton **Inspect All** dépliant la liste complète des 84 colonnes CICFlowMeter.
  - **Barre de Recherche Filtrante** : Taper `IAT`, `Length`, `Flag`, `Header`, etc. filtre instantanément les caractéristiques affichées en mode monospace haute précision.

### 4.5 Historique IP & Triage de l'Incident
- **Activité Récente de l'IP Source** : Affiche les 10 derniers flux émis par le même hôte avec le port ciblé et le verdict.
- **Actions sur l'Incident SOC** :
  - `Investigate` : Marque l'incident en cours d'analyse (`INVESTIGATING`).
  - `Resolve` : Clôture l'incident avec résolution confirmée (`RESOLVED`).
  - `False Positive` : Déclasse l'incident comme faux positif (`FALSE_POSITIVE`) pour audit ultérieur.
