#!/usr/bin/env python3
"""Script de génération des diagrammes et schémas d'architecture en images (SVG et PNG)."""

from pathlib import Path
import subprocess

DOCS_IMAGES_DIR = Path(__file__).resolve().parent.parent / "docs" / "images"
DOCS_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def build_architecture_svg() -> str:
    """Génère le diagramme SVG haute définition de l'architecture globale Sentinel NIDS."""
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 900" width="1200" height="900">
  <defs>
    <!-- Gradients -->
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#09090b"/>
      <stop offset="100%" stop-color="#121217"/>
    </linearGradient>
    <linearGradient id="cardGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#18181b"/>
      <stop offset="100%" stop-color="#111114"/>
    </linearGradient>
    <linearGradient id="cyanGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0284c7"/>
      <stop offset="100%" stop-color="#38bdf8"/>
    </linearGradient>
    <linearGradient id="redGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#be123c"/>
      <stop offset="100%" stop-color="#f43f5e"/>
    </linearGradient>
    <linearGradient id="amberGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#b45309"/>
      <stop offset="100%" stop-color="#f59e0b"/>
    </linearGradient>
    <linearGradient id="orangeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#c2410c"/>
      <stop offset="100%" stop-color="#f97316"/>
    </linearGradient>
    <linearGradient id="emeraldGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#047857"/>
      <stop offset="100%" stop-color="#10b981"/>
    </linearGradient>
    <linearGradient id="purpleGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#6d28d9"/>
      <stop offset="100%" stop-color="#8b5cf6"/>
    </linearGradient>

    <!-- Markers -->
    <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 8 5 L 0 9 z" fill="#71717a"/>
    </marker>
    <marker id="arrowCyan" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 8 5 L 0 9 z" fill="#38bdf8"/>
    </marker>
    <marker id="arrowEmerald" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 8 5 L 0 9 z" fill="#10b981"/>
    </marker>
    <marker id="arrowRed" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 8 5 L 0 9 z" fill="#f43f5e"/>
    </marker>

    <!-- Shadow -->
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000000" flood-opacity="0.6"/>
    </filter>
  </defs>

  <style>
    .title { font-family: DejaVu Sans, Arial, sans-serif; font-weight: 700; fill: #f43f5e; font-size: 22px; letter-spacing: 0.5px; }
    .subtitle { font-family: DejaVu Sans, Arial, sans-serif; font-size: 13px; fill: #a1a1aa; }
    .node-title { font-family: DejaVu Sans, Arial, sans-serif; font-weight: 600; font-size: 13px; fill: #f4f4f5; }
    .node-sub { font-family: monospace; font-size: 11px; fill: #a1a1aa; }
    .badge { font-family: monospace; font-size: 10px; font-weight: 600; text-transform: uppercase; }
    .edge-label { font-family: monospace; font-size: 10px; fill: #71717a; }
  </style>

  <!-- Background -->
  <rect width="1200" height="900" fill="url(#bgGrad)"/>
  <rect x="15" y="15" width="1170" height="870" fill="none" stroke="#27272a" stroke-width="1.5" rx="12"/>

  <!-- Header -->
  <g transform="translate(40, 45)">
    <circle cx="12" cy="12" r="6" fill="#f43f5e"/>
    <text x="28" y="18" class="title">SENTINEL NIDS | Architecture Globale du Système</text>
    <text x="28" y="38" class="subtitle">Pipeline de Détection d'Intrusions Multicouche &amp; Centre de Commandement SOC</text>
  </g>

  <!-- ==================== NIVEAU 1: CAPTURE & EXTRACTION ==================== -->
  <!-- 1.1 Ingestion / Carte Réseau -->
  <g transform="translate(60, 110)" filter="url(#shadow)">
    <rect width="240" height="65" rx="8" fill="url(#cardGrad)" stroke="#38bdf8" stroke-width="1.5"/>
    <rect x="0" y="0" width="6" height="65" rx="3" fill="url(#cyanGrad)"/>
    <text x="18" y="28" class="node-title">Interface Réseau Physique</text>
    <text x="18" y="48" class="node-sub">eth0 / enx3ecd36af7cdb / PCAP</text>
  </g>

  <!-- Arrow 1.1 -> 1.2 -->
  <path d="M 300 142 L 360 142" stroke="#38bdf8" stroke-width="1.5" marker-end="url(#arrowCyan)"/>

  <!-- 1.2 Sniffer BPF -->
  <g transform="translate(365, 110)" filter="url(#shadow)">
    <rect width="230" height="65" rx="8" fill="url(#cardGrad)" stroke="#27272a" stroke-width="1.5"/>
    <text x="18" y="28" class="node-title">Sniffer dumpcap / tcpdump</text>
    <text x="18" y="48" class="node-sub">Filtre BPF Noyau (not SSDP/MDNS)</text>
  </g>

  <!-- Arrow 1.2 -> 1.3 -->
  <path d="M 595 142 L 655 142" stroke="#71717a" stroke-width="1.5" marker-end="url(#arrow)"/>

  <!-- 1.3 Micro-batches PCAP -->
  <g transform="translate(660, 110)" filter="url(#shadow)">
    <rect width="210" height="65" rx="8" fill="url(#cardGrad)" stroke="#27272a" stroke-width="1.5"/>
    <text x="18" y="28" class="node-title">Micro-batches PCAP</text>
    <text x="18" y="48" class="node-sub">Tranches de 5s à 15s</text>
  </g>

  <!-- Arrow 1.3 -> 1.4 -->
  <path d="M 870 142 L 925 142" stroke="#71717a" stroke-width="1.5" marker-end="url(#arrow)"/>

  <!-- 1.4 CICFlowMeter -->
  <g transform="translate(930, 110)" filter="url(#shadow)">
    <rect width="210" height="65" rx="8" fill="url(#cardGrad)" stroke="#0ea5e9" stroke-width="1.5"/>
    <rect x="0" y="0" width="6" height="65" rx="3" fill="url(#cyanGrad)"/>
    <text x="18" y="28" class="node-title">CICFlowMeter Engine</text>
    <text x="18" y="48" class="node-sub">84 Métriques &amp; Normalisation</text>
  </g>

  <!-- Arrow 1.4 Down to Pre-Filter -->
  <path d="M 1035 175 L 1035 220 L 735 220" stroke="#71717a" stroke-width="1.5" marker-end="url(#arrow)"/>

  <!-- ==================== NIVEAU 2: PRÉ-FILTRAGE ==================== -->
  <g transform="translate(440, 200)" filter="url(#shadow)">
    <rect width="290" height="60" rx="8" fill="url(#cardGrad)" stroke="#10b981" stroke-width="1.5"/>
    <text x="18" y="26" class="node-title">Pré-filtrage Déterministe</text>
    <text x="18" y="46" class="node-sub">SessionTracker + Filtrage Bruit Réseau</text>
  </g>

  <!-- Branche Bénigne Vers Dashboard -->
  <path d="M 440 230 L 180 230 L 180 300" stroke="#10b981" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#arrowEmerald)"/>
  <rect x="195" y="235" width="125" height="20" rx="4" fill="#064e3b" stroke="#10b981" stroke-width="1"/>
  <text x="257" y="249" fill="#a7f3d0" class="badge" text-anchor="middle">Trafic Bénin Validé</text>

  <!-- Branche Suspecte Vers Étage 1 -->
  <path d="M 585 260 L 585 300" stroke="#f43f5e" stroke-width="1.5" marker-end="url(#arrowRed)"/>
  <rect x="595" y="268" width="130" height="20" rx="4" fill="#881337" stroke="#f43f5e" stroke-width="1"/>
  <text x="660" y="282" fill="#fecdd3" class="badge" text-anchor="middle">Trafic Suspect</text>

  <!-- ==================== NIVEAU 3: FILTRAGE ÉTAGE 1 ==================== -->
  <g transform="translate(410, 305)" filter="url(#shadow)">
    <rect width="350" height="70" rx="8" fill="url(#cardGrad)" stroke="#f43f5e" stroke-width="1.8"/>
    <rect x="0" y="0" width="6" height="70" rx="3" fill="url(#redGrad)"/>
    <text x="20" y="28" class="node-title">ÉTAGE 1 : Filtrage Binaire Rapide</text>
    <text x="20" y="46" class="node-sub">CatBoost (76 fts) + XGBoost (30 fts)</text>
    <text x="20" y="62" class="badge" fill="#fb7185">SEUIL OPÉRATIONNEL : t₁ = 0.50</text>
  </g>

  <!-- Sortie Étage 1 Bénin -->
  <path d="M 410 340 L 290 340 L 290 540" stroke="#10b981" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#arrowEmerald)"/>
  <text x="315" y="360" class="edge-label">Score &lt; t₁ (Bénin)</text>

  <!-- Sortie Étage 1 Suspecte -> 3 Branches Parallèles -->
  <path d="M 585 375 L 585 410" stroke="#f43f5e" stroke-width="1.5"/>
  <path d="M 585 410 L 230 410 L 230 435" stroke="#f43f5e" stroke-width="1.5" marker-end="url(#arrowRed)"/>
  <path d="M 585 410 L 585 435" stroke="#f59e0b" stroke-width="1.5" marker-end="url(#arrow)"/>
  <path d="M 585 410 L 960 410 L 960 435" stroke="#f97316" stroke-width="1.5" marker-end="url(#arrow)"/>

  <!-- ==================== NIVEAU 4: ÉTAGE 2 / KITSUNE / DPI ==================== -->
  <!-- 4.1 Étage 2 DNN-1D -->
  <g transform="translate(70, 440)" filter="url(#shadow)">
    <rect width="320" height="85" rx="8" fill="url(#cardGrad)" stroke="#ef4444" stroke-width="1.5"/>
    <rect x="0" y="0" width="6" height="85" rx="3" fill="url(#redGrad)"/>
    <text x="18" y="26" class="node-title">ÉTAGE 2 : DNN-1D PyTorch</text>
    <text x="18" y="44" class="node-sub">14 Classes Multiclasses (DDoS, Bot, Scan)</text>
    <text x="18" y="60" class="node-sub">BatchNorm1d, MaxPool, Dropout</text>
    <text x="18" y="76" class="badge" fill="#f87171">SEUIL CONFIANCE : t₂ = 0.70</text>
  </g>

  <!-- 4.2 Kitsune Anomaly Detector -->
  <g transform="translate(425, 440)" filter="url(#shadow)">
    <rect width="320" height="85" rx="8" fill="url(#cardGrad)" stroke="#f59e0b" stroke-width="1.5"/>
    <rect x="0" y="0" width="6" height="85" rx="3" fill="url(#amberGrad)"/>
    <text x="18" y="26" class="node-title">BRANCHE 0-DAY : Kitsune (KitNET)</text>
    <text x="18" y="44" class="node-sub">Ensemble d'Autoencodeurs L3</text>
    <text x="18" y="60" class="node-sub">Calibration Dynamique Anti-Empoisonnement</text>
    <text x="18" y="76" class="badge" fill="#fbbf24">SEUIL ANOMALIE : t₃ = 0.0100</text>
  </g>

  <!-- 4.3 DPI Inspector -->
  <g transform="translate(780, 440)" filter="url(#shadow)">
    <rect width="350" height="85" rx="8" fill="url(#cardGrad)" stroke="#f97316" stroke-width="1.5"/>
    <rect x="0" y="0" width="6" height="85" rx="3" fill="url(#orangeGrad)"/>
    <text x="18" y="26" class="node-title">INSPECTION L7 : DPI Inspector</text>
    <text x="18" y="44" class="node-sub">Signatures Regex Charge Utile (Payload)</text>
    <text x="18" y="60" class="node-sub">SQLi, XSS, RCE Log4j, Web Fuzzing</text>
    <text x="18" y="76" class="badge" fill="#fb923c">FUSION IMMÉDIATE SUR MOTIF</text>
  </g>

  <!-- Descentes vers Moteur de Fusion -->
  <path d="M 230 525 L 230 560 L 520 560" stroke="#ef4444" stroke-width="1.5" marker-end="url(#arrow)"/>
  <path d="M 585 525 L 585 580" stroke="#f59e0b" stroke-width="1.5" marker-end="url(#arrow)"/>
  <path d="M 960 525 L 960 560 L 650 560" stroke="#f97316" stroke-width="1.5" marker-end="url(#arrow)"/>

  <!-- ==================== NIVEAU 5: MOTEUR DE FUSION ==================== -->
  <g transform="translate(410, 585)" filter="url(#shadow)">
    <rect width="350" height="65" rx="8" fill="url(#cardGrad)" stroke="#a855f7" stroke-width="1.8"/>
    <rect x="0" y="0" width="6" height="65" rx="3" fill="url(#purpleGrad)"/>
    <text x="20" y="26" class="node-title">MOTEUR DE FUSION DÉCISIONNELLE</text>
    <text x="20" y="44" class="node-sub">Arbitrage Matrice à 6 Cas (Supervisé vs 0-Day)</text>
    <text x="20" y="58" class="badge" fill="#c084fc">BENIGN · ATTAQUE · 0-DAY · INCERTAIN</text>
  </g>

  <!-- Arrow Fusion -> LiveAlertGuard -->
  <path d="M 585 650 L 585 690" stroke="#a855f7" stroke-width="1.5" marker-end="url(#arrow)"/>

  <!-- ==================== NIVEAU 6: LIVE ALERT GUARD ==================== -->
  <g transform="translate(360, 695)" filter="url(#shadow)">
    <rect width="450" height="65" rx="8" fill="url(#cardGrad)" stroke="#6366f1" stroke-width="1.5"/>
    <text x="20" y="24" class="node-title">LiveAlertGuard : Consolidation &amp; Anti-Flood</text>
    <text x="20" y="42" class="node-sub">• Quorum Volumétrique (anti-faux positifs)</text>
    <text x="20" y="57" class="node-sub">• Score Cumulé Hôte (Leaky Bucket) &amp; Cooldown 30s</text>
  </g>

  <!-- Arrow LiveAlertGuard -> Backend / SOC -->
  <path d="M 585 760 L 585 795" stroke="#6366f1" stroke-width="1.5" marker-end="url(#arrow)"/>

  <!-- ==================== NIVEAU 7: SOC DASHBOARD & PERSISTENCE ==================== -->
  <!-- 7.1 SQLite WAL -->
  <g transform="translate(70, 795)" filter="url(#shadow)">
    <rect width="300" height="65" rx="8" fill="url(#cardGrad)" stroke="#0284c7" stroke-width="1.5"/>
    <text x="18" y="26" class="node-title">Base SQLite WAL (nids.db)</text>
    <text x="18" y="44" class="node-sub">Corrélation d'Incidents Automatique</text>
    <text x="18" y="58" class="badge" fill="#38bdf8">HAUTE CONCURRENCE &amp; 84 FEATURES</text>
  </g>

  <!-- 7.2 FastAPI Backend -->
  <g transform="translate(425, 795)" filter="url(#shadow)">
    <rect width="320" height="65" rx="8" fill="url(#cardGrad)" stroke="#059669" stroke-width="1.5"/>
    <text x="18" y="26" class="node-title">Serveur FastAPI Asynchrone</text>
    <text x="18" y="44" class="node-sub">REST API (/api/dashboard) &amp; WebSocket (/ws)</text>
    <text x="18" y="58" class="badge" fill="#34d399">DIFFUSION TÉLÉMÉTRIE 60 FPS</text>
  </g>

  <!-- 7.3 Frontend SOC Command Dashboard -->
  <g transform="translate(795, 795)" filter="url(#shadow)">
    <rect width="335" height="65" rx="8" fill="url(#cardGrad)" stroke="#f43f5e" stroke-width="1.8"/>
    <rect x="0" y="0" width="6" height="65" rx="3" fill="url(#redGrad)"/>
    <text x="18" y="26" class="node-title">SOC Command Center (Vue 3)</text>
    <text x="18" y="44" class="node-sub">Timeline Chart.js, Donut, Triage Table</text>
    <text x="18" y="58" class="badge" fill="#fb7185">TIROIR FORENSICS MATRICE 84 CARACT.</text>
  </g>

  <!-- Connexions Horizontales Niveau 7 -->
  <path d="M 370 827 L 420 827" stroke="#71717a" stroke-width="1.5" marker-end="url(#arrow)"/>
  <path d="M 745 827 L 790 827" stroke="#71717a" stroke-width="1.5" marker-end="url(#arrow)"/>
</svg>"""


def build_dataflow_svg() -> str:
    """Génère le diagramme SVG haute définition du flux de données et du cycle de décision."""
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800" width="1200" height="800">
  <defs>
    <linearGradient id="bgGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#09090b"/>
      <stop offset="100%" stop-color="#111116"/>
    </linearGradient>
    <linearGradient id="cardGrad2" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#18181b"/>
      <stop offset="100%" stop-color="#111114"/>
    </linearGradient>
    <linearGradient id="roseGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#e11d48"/>
      <stop offset="100%" stop-color="#fb7185"/>
    </linearGradient>

    <marker id="arrow2" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 8 5 L 0 9 z" fill="#71717a"/>
    </marker>
    <marker id="arrowRed2" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 8 5 L 0 9 z" fill="#fb7185"/>
    </marker>
    <marker id="arrowGreen2" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 8 5 L 0 9 z" fill="#34d399"/>
    </marker>
  </defs>

  <style>
    .df-title { font-family: DejaVu Sans, Arial, sans-serif; font-weight: 700; fill: #38bdf8; font-size: 20px; }
    .df-sub { font-family: DejaVu Sans, Arial, sans-serif; font-size: 13px; fill: #a1a1aa; }
    .df-box-title { font-family: DejaVu Sans, Arial, sans-serif; font-weight: 600; font-size: 13px; fill: #f4f4f5; }
    .df-box-sub { font-family: monospace; font-size: 11px; fill: #a1a1aa; }
    .df-pill { font-family: monospace; font-size: 10px; font-weight: 600; }
  </style>

  <rect width="1200" height="800" fill="url(#bgGrad2)"/>
  <rect x="15" y="15" width="1170" height="770" fill="none" stroke="#27272a" stroke-width="1.5" rx="12"/>

  <!-- Header -->
  <g transform="translate(40, 45)">
    <circle cx="12" cy="12" r="6" fill="#38bdf8"/>
    <text x="28" y="18" class="df-title">SENTINEL NIDS | Flux de Données &amp; Cycle de Décision</text>
    <text x="28" y="38" class="df-sub">Parcours séquentiel d'un flux réseau à travers les moteurs de filtrage, inférence et corrélation</text>
  </g>

  <!-- Step 1: Capture -->
  <g transform="translate(50, 100)">
    <rect width="240" height="110" rx="8" fill="url(#cardGrad2)" stroke="#27272a" stroke-width="1.5"/>
    <text x="18" y="28" class="df-box-title">1. Capture &amp; Ingestion</text>
    <text x="18" y="50" class="df-box-sub">• dumpcap / tcpdump</text>
    <text x="18" y="70" class="df-box-sub">• Filtre BPF noyau anti-broadcast</text>
    <text x="18" y="90" class="df-box-sub">• Découpage micro-batchs (5-15s)</text>
  </g>

  <path d="M 290 155 L 340 155" stroke="#71717a" stroke-width="1.5" marker-end="url(#arrow2)"/>

  <!-- Step 2: Extraction CICFlowMeter -->
  <g transform="translate(345, 100)">
    <rect width="250" height="110" rx="8" fill="url(#cardGrad2)" stroke="#0284c7" stroke-width="1.5"/>
    <text x="18" y="28" class="df-box-title">2. Extraction Vectorielle</text>
    <text x="18" y="50" class="df-box-sub">• CICFlowMeter 84 caractéristiques</text>
    <text x="18" y="70" class="df-box-sub">• Normalisation MTU 1514 (TSO/GSO)</text>
    <text x="18" y="90" class="df-box-sub">• Clé quintuplet 5-tuple canonique</text>
  </g>

  <path d="M 595 155 L 645 155" stroke="#71717a" stroke-width="1.5" marker-end="url(#arrow2)"/>

  <!-- Step 3: Pré-filtrage Déterministe -->
  <g transform="translate(650, 100)">
    <rect width="250" height="110" rx="8" fill="url(#cardGrad2)" stroke="#10b981" stroke-width="1.5"/>
    <text x="18" y="28" class="df-box-title">3. Pré-filtrage LiveFilter</text>
    <text x="18" y="50" class="df-box-sub">• Whitelist IP &amp; DNS/DHCP bénin</text>
    <text x="18" y="70" class="df-box-sub">• SessionTracker (suivi connexions)</text>
    <text x="18" y="90" class="df-box-sub">• Isolation paquets orphelins</text>
  </g>

  <!-- Step 3 bifurcation -->
  <path d="M 775 210 L 775 260 L 980 260 L 980 300" stroke="#10b981" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#arrowGreen2)"/>
  <path d="M 775 210 L 775 260 L 450 260 L 450 300" stroke="#fb7185" stroke-width="1.5" marker-end="url(#arrowRed2)"/>

  <!-- Step 4A: Benign Fast Path -->
  <g transform="translate(860, 305)">
    <rect width="240" height="90" rx="8" fill="url(#cardGrad2)" stroke="#10b981" stroke-width="1.5"/>
    <text x="18" y="26" class="df-box-title">4A. Fast Path Bénin</text>
    <text x="18" y="46" class="df-box-sub">Trafic légitime validé</text>
    <text x="18" y="64" class="df-box-sub">Évite surcharge CPU</text>
    <text x="18" y="80" class="df-pill" fill="#34d399">VERDICT : BENIGN</text>
  </g>

  <!-- Step 4B: Étage 1 -->
  <g transform="translate(320, 305)">
    <rect width="260" height="90" rx="8" fill="url(#cardGrad2)" stroke="#f43f5e" stroke-width="1.5"/>
    <text x="18" y="26" class="df-box-title">4B. Étage 1 : CatBoost / XGBoost</text>
    <text x="18" y="46" class="df-box-sub">Calcul probabilité suspicion</text>
    <text x="18" y="64" class="df-box-sub">Si score &lt; 0.50 ➔ Bénin</text>
    <text x="18" y="80" class="df-pill" fill="#fb7185">SI SCORE &gt;= 0.50 ➔ ESCALADE</text>
  </g>

  <!-- Step 4B to Step 5 (3 Parallel Branches) -->
  <path d="M 450 395 L 450 440" stroke="#f43f5e" stroke-width="1.5"/>
  <path d="M 450 440 L 150 440 L 150 470" stroke="#f43f5e" stroke-width="1.5" marker-end="url(#arrowRed2)"/>
  <path d="M 450 440 L 450 470" stroke="#f59e0b" stroke-width="1.5" marker-end="url(#arrow2)"/>
  <path d="M 450 440 L 750 440 L 750 470" stroke="#f97316" stroke-width="1.5" marker-end="url(#arrow2)"/>

  <!-- Step 5A: DNN-1D -->
  <g transform="translate(50, 475)">
    <rect width="240" height="90" rx="8" fill="url(#cardGrad2)" stroke="#ef4444" stroke-width="1.5"/>
    <text x="16" y="26" class="df-box-title">5A. 1D-DNN Multiclasse</text>
    <text x="16" y="46" class="df-box-sub">14 classes d'attaques</text>
    <text x="16" y="64" class="df-box-sub">Vecteur confiance &gt;= 0.70</text>
    <text x="16" y="80" class="df-pill" fill="#f87171">DDoS, PortScan, Bot, Patator...</text>
  </g>

  <!-- Step 5B: Kitsune 0-Day -->
  <g transform="translate(340, 475)">
    <rect width="240" height="90" rx="8" fill="url(#cardGrad2)" stroke="#f59e0b" stroke-width="1.5"/>
    <text x="16" y="26" class="df-box-title">5B. Kitsune KitNET</text>
    <text x="16" y="46" class="df-box-sub">Autoencodeurs paquets</text>
    <text x="16" y="64" class="df-box-sub">RMSE reconstruction</text>
    <text x="16" y="80" class="df-pill" fill="#fbbf24">DÉTECTION 0-DAY NON SUPERVISÉE</text>
  </g>

  <!-- Step 5C: DPI Inspector -->
  <g transform="translate(630, 475)">
    <rect width="240" height="90" rx="8" fill="url(#cardGrad2)" stroke="#f97316" stroke-width="1.5"/>
    <text x="16" y="26" class="df-box-title">5C. DPI L7 Regex</text>
    <text x="16" y="46" class="df-box-sub">Analyse charge utile</text>
    <text x="16" y="64" class="df-box-sub">SQLi, XSS, Log4j, Fuzz</text>
    <text x="16" y="80" class="df-pill" fill="#fb923c">CONFIRMATION APPLICATIVE</text>
  </g>

  <!-- Step 6: Fusion & LiveGuard -->
  <path d="M 170 565 L 170 600 L 400 600" stroke="#71717a" stroke-width="1.5" marker-end="url(#arrow2)"/>
  <path d="M 460 565 L 460 615" stroke="#71717a" stroke-width="1.5" marker-end="url(#arrow2)"/>
  <path d="M 750 565 L 750 600 L 520 600" stroke="#71717a" stroke-width="1.5" marker-end="url(#arrow2)"/>

  <g transform="translate(300, 620)">
    <rect width="320" height="110" rx="8" fill="url(#cardGrad2)" stroke="#8b5cf6" stroke-width="1.8"/>
    <text x="20" y="26" class="df-box-title">6. Moteur de Fusion &amp; LiveGuard</text>
    <text x="20" y="48" class="df-box-sub">• Résolution selon matrice de fusion à 6 cas</text>
    <text x="20" y="68" class="df-box-sub">• Quorum volumétrique &amp; Leaky bucket</text>
    <text x="20" y="88" class="df-box-sub">• Cooldown anti-flood &amp; seuils adaptatifs</text>
  </g>

  <!-- Final Delivery: Dashboard & Alerting -->
  <path d="M 620 675 L 720 675" stroke="#8b5cf6" stroke-width="1.5" marker-end="url(#arrow2)"/>

  <g transform="translate(725, 620)">
    <rect width="380" height="110" rx="8" fill="url(#cardGrad2)" stroke="#38bdf8" stroke-width="1.8"/>
    <text x="20" y="26" class="df-box-title">7. Stockage &amp; Centre SOC</text>
    <text x="20" y="48" class="df-box-sub">• Base SQLite WAL (flux &amp; incidents corrélés)</text>
    <text x="20" y="68" class="df-box-sub">• Télémétrie WebSocket (/ws) en temps réel</text>
    <text x="20" y="88" class="df-box-sub">• Console Vue 3 : Triage, Graphiques &amp; Forensics</text>
  </g>
</svg>"""


def build_milestones_svg() -> str:
    """Génère le diagramme SVG des jalons d'implémentation (Milestones)."""
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 200" width="1000" height="200">
  <defs>
    <linearGradient id="mBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#09090b"/>
      <stop offset="100%" stop-color="#18181b"/>
    </linearGradient>
    <linearGradient id="mCard" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#27272a"/>
      <stop offset="100%" stop-color="#18181b"/>
    </linearGradient>
    <marker id="mArrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 8 5 L 0 9 z" fill="#38bdf8"/>
    </marker>
  </defs>
  <style>
    .m-title { font-family: DejaVu Sans, Arial, sans-serif; font-weight: 700; font-size: 13px; fill: #f4f4f5; }
    .m-sub { font-family: DejaVu Sans, Arial, sans-serif; font-size: 11px; fill: #a1a1aa; }
    .m-badge { font-family: monospace; font-size: 10px; font-weight: 600; fill: #38bdf8; }
  </style>
  <rect width="1000" height="200" fill="url(#mBg)" rx="8" stroke="#27272a"/>
  
  <!-- M1 -->
  <g transform="translate(30, 45)">
    <rect width="160" height="110" rx="8" fill="url(#mCard)" stroke="#38bdf8" stroke-width="1.5"/>
    <text x="15" y="30" class="m-badge">JALON 1</text>
    <text x="15" y="55" class="m-title">Socle &amp; Audit</text>
    <text x="15" y="75" class="m-sub">Models Inspection</text>
    <text x="15" y="92" class="m-sub">CI/CD &amp; TDD Setup</text>
  </g>

  <!-- M1 -> M2 -->
  <path d="M 190 80 L 235 60" stroke="#38bdf8" stroke-width="1.5" marker-end="url(#mArrow)"/>
  <!-- M1 -> M3 -->
  <path d="M 190 120 L 235 140" stroke="#38bdf8" stroke-width="1.5" marker-end="url(#mArrow)"/>

  <!-- M2 -->
  <g transform="translate(240, 15)">
    <rect width="170" height="80" rx="8" fill="url(#mCard)" stroke="#27272a" stroke-width="1.5"/>
    <text x="15" y="25" class="m-badge">JALON 2</text>
    <text x="15" y="46" class="m-title">Pipeline Supervisé</text>
    <text x="15" y="66" class="m-sub">CatBoost + DNN-1D</text>
  </g>

  <!-- M3 -->
  <g transform="translate(240, 105)">
    <rect width="170" height="80" rx="8" fill="url(#mCard)" stroke="#27272a" stroke-width="1.5"/>
    <text x="15" y="25" class="m-badge" fill="#f59e0b">JALON 3</text>
    <text x="15" y="46" class="m-title">Kitsune &amp; Alignement</text>
    <text x="15" y="66" class="m-sub">KitNET + Paquets</text>
  </g>

  <!-- M2 -> M4 -->
  <path d="M 410 55 L 475 80" stroke="#38bdf8" stroke-width="1.5" marker-end="url(#mArrow)"/>
  <!-- M3 -> M4 -->
  <path d="M 410 145 L 475 120" stroke="#38bdf8" stroke-width="1.5" marker-end="url(#mArrow)"/>

  <!-- M4 -->
  <g transform="translate(480, 45)">
    <rect width="180" height="110" rx="8" fill="url(#mCard)" stroke="#a855f7" stroke-width="1.5"/>
    <text x="15" y="30" class="m-badge" fill="#c084fc">JALON 4</text>
    <text x="15" y="55" class="m-title">Fusion &amp; Calibration</text>
    <text x="15" y="75" class="m-sub">Matrice à 6 Cas</text>
    <text x="15" y="92" class="m-sub">Seuils t1, t2, t3</text>
  </g>

  <!-- M4 -> M5 -->
  <path d="M 660 100 L 725 100" stroke="#38bdf8" stroke-width="1.5" marker-end="url(#mArrow)"/>

  <!-- M5 -->
  <g transform="translate(730, 45)">
    <rect width="230" height="110" rx="8" fill="url(#mCard)" stroke="#10b981" stroke-width="1.5"/>
    <text x="15" y="30" class="m-badge" fill="#34d399">JALON 5</text>
    <text x="15" y="55" class="m-title">SOC &amp; Généralisation</text>
    <text x="15" y="75" class="m-sub">FastAPI + Vue 3 Dashboard</text>
    <text x="15" y="92" class="m-sub">Évaluation CSE-CIC-IDS2018</text>
  </g>
</svg>"""


def build_tdd_svg() -> str:
    """Génère le diagramme SVG du cycle de développement TDD."""
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 180" width="900" height="180">
  <defs>
    <linearGradient id="tBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#09090b"/>
      <stop offset="100%" stop-color="#18181b"/>
    </linearGradient>
    <linearGradient id="tCard" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#27272a"/>
      <stop offset="100%" stop-color="#18181b"/>
    </linearGradient>
    <marker id="tArrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 8 5 L 0 9 z" fill="#a1a1aa"/>
    </marker>
  </defs>
  <style>
    .t-title { font-family: DejaVu Sans, Arial, sans-serif; font-weight: 700; font-size: 13px; fill: #f4f4f5; }
    .t-sub { font-family: DejaVu Sans, Arial, sans-serif; font-size: 11px; fill: #a1a1aa; }
    .t-step { font-family: monospace; font-size: 10px; font-weight: 600; text-transform: uppercase; }
  </style>
  <rect width="900" height="180" fill="url(#tBg)" rx="8" stroke="#27272a"/>

  <!-- Step 1 (Rouge) -->
  <g transform="translate(30, 45)">
    <rect width="180" height="90" rx="8" fill="url(#tCard)" stroke="#f43f5e" stroke-width="1.8"/>
    <text x="15" y="26" class="t-step" fill="#fb7185">ÉTAPE 1 · ROUGE</text>
    <text x="15" y="50" class="t-title">Écrire le Test d'Abord</text>
    <text x="15" y="70" class="t-sub">Échec attendu (pytest)</text>
  </g>

  <path d="M 210 90 L 255 90" stroke="#a1a1aa" stroke-width="1.5" marker-end="url(#tArrow)"/>

  <!-- Step 2 (Minimal) -->
  <g transform="translate(260, 45)">
    <rect width="180" height="90" rx="8" fill="url(#tCard)" stroke="#38bdf8" stroke-width="1.5"/>
    <text x="15" y="26" class="t-step" fill="#38bdf8">ÉTAPE 2 · CODE</text>
    <text x="15" y="50" class="t-title">Implémentation</text>
    <text x="15" y="70" class="t-sub">Code minimal nécessaire</text>
  </g>

  <path d="M 440 90 L 485 90" stroke="#a1a1aa" stroke-width="1.5" marker-end="url(#tArrow)"/>

  <!-- Step 3 (Vert) -->
  <g transform="translate(490, 45)">
    <rect width="180" height="90" rx="8" fill="url(#tCard)" stroke="#10b981" stroke-width="1.8"/>
    <text x="15" y="26" class="t-step" fill="#34d399">ÉTAPE 3 · VERT</text>
    <text x="15" y="50" class="t-title">Le Test Passe</text>
    <text x="15" y="70" class="t-sub">100% Succès (Vert)</text>
  </g>

  <path d="M 670 90 L 715 90" stroke="#a1a1aa" stroke-width="1.5" marker-end="url(#tArrow)"/>

  <!-- Step 4 (Refactor) -->
  <g transform="translate(720, 45)">
    <rect width="150" height="90" rx="8" fill="url(#tCard)" stroke="#a855f7" stroke-width="1.5"/>
    <text x="15" y="26" class="t-step" fill="#c084fc">ÉTAPE 4 · REFACTOR</text>
    <text x="15" y="50" class="t-title">Refactorisation</text>
    <text x="15" y="70" class="t-sub">Typage &amp; Performance</text>
  </g>

  <!-- Boucle vers l'Étape 1 -->
  <path d="M 795 135 L 795 160 L 120 160 L 120 135" stroke="#71717a" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#tArrow)"/>
</svg>"""


def main():
    print("🎨 Génération des diagrammes vectoriels SVG...")
    arch_svg_path = DOCS_IMAGES_DIR / "sentinel_architecture.svg"
    arch_png_path = DOCS_IMAGES_DIR / "sentinel_architecture.png"
    dataflow_svg_path = DOCS_IMAGES_DIR / "sentinel_dataflow.svg"
    dataflow_png_path = DOCS_IMAGES_DIR / "sentinel_dataflow.png"
    milestones_svg_path = DOCS_IMAGES_DIR / "milestones_pipeline.svg"
    milestones_png_path = DOCS_IMAGES_DIR / "milestones_pipeline.png"
    tdd_svg_path = DOCS_IMAGES_DIR / "tdd_cycle.svg"
    tdd_png_path = DOCS_IMAGES_DIR / "tdd_cycle.png"

    # 1. Écriture des SVG
    arch_svg_path.write_text(build_architecture_svg(), encoding="utf-8")
    dataflow_svg_path.write_text(build_dataflow_svg(), encoding="utf-8")
    milestones_svg_path.write_text(build_milestones_svg(), encoding="utf-8")
    tdd_svg_path.write_text(build_tdd_svg(), encoding="utf-8")
    print(f"  ✓ {arch_svg_path.name}")
    print(f"  ✓ {dataflow_svg_path.name}")
    print(f"  ✓ {milestones_svg_path.name}")
    print(f"  ✓ {tdd_svg_path.name}")

    # 2. Conversion en PNG haute définition via convert
    print("🖼️ Conversion en images PNG (haute résolution 300 DPI)...")
    for svg_file, png_file in [
        (arch_svg_path, arch_png_path),
        (dataflow_svg_path, dataflow_png_path),
        (milestones_svg_path, milestones_png_path),
        (tdd_svg_path, tdd_png_path),
    ]:
        subprocess.run(
            ["convert", "-density", "300", "-background", "#09090b", str(svg_file), str(png_file)],
            check=True,
        )
        print(f"  ✓ {png_file.name}")

    print("\n✅ Tous les graphiques et diagrammes ont été générés en images avec succès !")


if __name__ == "__main__":
    main()
