export const translations = {
  FR: {
    // Navigation
    nav: {
      dashboard: "Tableau de bord",
      alerts: "Alertes & Incidents",
      threatIntel: "Threat Intel",
      sensors: "Sondes & Rejeu",
      models: "Modèles d'IA",
      settings: "Paramètres",
      sensorsOnline: "sondes en ligne",
      zeroDrops: "0 paquet perdu",
      more: "Menu"
    },
    // Header
    header: {
      title: "Système de Détection d'Intrusions Réseau par IA",
      subtitle: "Classifieur supervisé DNN v4 (12 classes) + Détection d'anomalies 0-day par Autoencodeur",
      threatLevel: "Niveau de menace",
      threatNormal: "Normal",
      threatElevated: "Élevé",
      threatCritical: "Critique",
      liveWs: "Flux WebSocket",
      streamActive: "Flux actif",
      streamPaused: "En pause",
      pcapReplay: "Rejeu PCAP",
      offline: "Hors-ligne",
      reconnecting: "Reconnexion...",
      allSensors: "Toutes les sondes",
      runReplay: "Lancer rejeu",
      stopReplay: "Arrêter rejeu",
      pause: "Pause",
      resume: "Reprendre",
      lang: "Langue"
    },
    // KPIs
    kpi: {
      totalFlows: "Total flux analysés",
      totalFlowsSub: "Télémétrie SQLite indexée",
      confirmedAttacks: "Attaques confirmées",
      confirmedAttacksSub: "12 classes CIC-IDS2017",
      anomalies: "Anomalies Zero-Day",
      anomaliesSub: "Déviation MSE Autoencodeur",
      rate: "Débit d'ingestion",
      flowsSec: "flux/s",
      trafficDist: "Répartition du trafic",
      benign: "Trafic légitime",
      malicious: "Attaques & 0-Day"
    },
    // Donut
    donut: {
      title: "Répartition des Attaques",
      subtitle: "12 Familles CIC-IDS2017",
      detected: "détectées",
      attacks: "attaques"
    },
    // Timeline
    timeline: {
      title: "Chronologie de l'Activité",
      window15m: "Flux/sec (fenêtre de 15 min)",
      window1h: "Flux/sec (fenêtre d'une heure)",
      window24h: "Flux/sec (historique 24h)",
      baseline: "Baseline glissante",
      liveNow: "En direct",
      footer: "Les marqueurs indiquent les pics anormaux dépassant la baseline statistique."
    },
    // Gauge
    gauge: {
      title: "Score d'Anomalie IA",
      subtitle: "Autoencodeur AE v1",
      threshold: "Seuil",
      baselineThreshold: "Seuil de baseline",
      rollingMean: "Moyenne (1 min)",
      status: "Statut IA",
      statusNominal: "Trafic Nominal",
      statusElevated: "Seuil Approché",
      statusAnomaly: "Déviation 0-Day"
    },
    // Threat Vectors
    vectors: {
      title: "Vecteurs & Origine des Menaces",
      subtitle: "Top 5 Sources d'Attaque & Cibles Réseau",
      topIps: "Top 5 IPs Sources Attaquantes",
      topPorts: "Top 5 Ports Cibles Visés",
      window: "Fenêtre active"
    },
    // Critical Banner
    banner: {
      badge: "INCIDENT CRITIQUE",
      confidence: "Confiance",
      inspect: "Inspecter le flux",
      safeTitle: "Périmètre Sécurisé",
      safeDesc: "Aucun incident cyber critique non contenu dans la fenêtre active.",
      safePill: "IA Double Moteur",
      titleThreat: "Incident Critique Détecté",
      subThreat: "Triage & Détection Temps Réel",
      titleSafe: "Périmètre Réseau",
      subSafe: "Supervision Continue"
    },
    // Table
    table: {
      title: "Flux d'Incidents en Direct",
      autoUpdating: "Mise à jour en direct",
      searchPlaceholder: "Filtrer par IP source ou destination...",
      allCategories: "Toutes les catégories (12 classes)",
      minConfidence: "Confiance min :",
      zeroDayOnly: "Anomalies 0-Day uniquement",
      clearFilters: "Effacer les filtres",
      timestamp: "Horodatage",
      sensor: "Sonde",
      route: "Source &rarr; Destination",
      source: "IP Source",
      destination: "IP Destination",
      subtitle: "Traçabilité des flux réseau & Inférence temps réel",
      protocol: "Proto",
      classification: "Classification IA",
      confidence: "Confiance",
      autoencoder: "Autoencodeur",
      severity: "Sévérité",
      emptyMessage: "Aucun incident réseau ne correspond aux critères de filtre.",
      resetFilters: "Réinitialiser les filtres"
    },
    // Drawer
    drawer: {
      title: "Inspection Approfondie du Flux",
      close: "Fermer",
      aiDetection: "Détection par Intelligence Artificielle",
      classifierConf: "Confiance du classifieur",
      reconstructionMse: "Erreur de reconstruction MSE",
      threshold: "seuil",
      anomaly: "Anomalie (0-Day)",
      normal: "Normal",
      aeFlag: "Indicateur Autoencodeur",
      sensorOrigin: "Sonde d'origine",
      detectedAt: "Détecté à",
      telemetry: "Télémétrie Bidirectionnelle",
      duration: "Durée",
      fwdPackets: "Paquets aller (fwd)",
      bwdPackets: "Paquets retour (bwd)",
      fwdBytes: "Octets aller",
      bwdBytes: "Octets retour",
      tcpFlags: "Drapeaux TCP"
    },
    // Settings
    settings: {
      title: "Paramètres Système & Détection",
      subtitle: "Configuration du Nœud & Seuils Opérationnels IA",
      desc: "Configurez la langue d'affichage de la console HDVR, les seuils d'alerte de l'autoencodeur et les paramètres de télémétrie.",
      langTitle: "Langue de l'Interface",
      langDesc: "La console SOC applique la langue sélectionnée en temps réel sur l'ensemble des modules d'analyse.",
      thresholdsTitle: "Seuils Opérationnels de Détection",
      aeThresholdLabel: "Seuil d'Anomalie Autoencodeur (MSE)",
      aeHelp: "Baseline par défaut issue des pertes de validation bénignes (0.6029).",
      minConfLabel: "Confiance Minimale du Classifieur (%)",
      saveBtn: "Enregistrer les modifications",
      telemetryTitle: "Télémétrie Serveur & Base SQLite",
      dbFile: "Fichier Base de Données",
      indexedCols: "Colonnes Indexées",
      storageEngine: "Moteur de Stockage",
      wsStream: "Flux WebSocket",
      retention: "Politique de Rétention"
    }
  },

  EN: {
    nav: {
      dashboard: "Dashboard",
      alerts: "Alerts & Incidents",
      threatIntel: "Threat Intel",
      sensors: "Sensors & Replay",
      models: "AI Models",
      settings: "Settings",
      sensorsOnline: "sensors online",
      zeroDrops: "0 drops",
      more: "Menu"
    },
    header: {
      title: "AI Network Intrusion Detection System",
      subtitle: "Supervised DNN v4 Classifier (12 classes) + Autoencoder Zero-Day Anomaly Detection",
      threatLevel: "Threat level",
      threatNormal: "Normal",
      threatElevated: "Elevated",
      threatCritical: "Critical",
      liveWs: "Live WebSocket",
      streamActive: "Stream active",
      streamPaused: "Paused",
      pcapReplay: "PCAP Replay",
      offline: "Offline",
      reconnecting: "Reconnecting...",
      allSensors: "Live Sensors",
      runReplay: "Run Replay",
      stopReplay: "Stop Replay",
      pause: "Pause",
      resume: "Resume",
      lang: "Language"
    },
    kpi: {
      totalFlows: "Total Flows Analyzed",
      totalFlowsSub: "Indexed SQLite telemetry",
      confirmedAttacks: "Confirmed Attacks",
      confirmedAttacksSub: "12 CIC-IDS2017 classes",
      anomalies: "Zero-Day Anomalies",
      anomaliesSub: "Autoencoder MSE deviation",
      rate: "Ingestion Rate",
      flowsSec: "flows/s",
      trafficDist: "Traffic Distribution",
      benign: "Benign traffic",
      malicious: "Attacks & 0-Day"
    },
    donut: {
      title: "Attack Distribution",
      subtitle: "12 CIC-IDS2017 Families",
      detected: "detected",
      attacks: "attacks"
    },
    timeline: {
      title: "Activity Timeline",
      window15m: "Flows/sec (15-min rolling window)",
      window1h: "Flows/sec (1-hour window)",
      window24h: "Flows/sec (24-hour historical)",
      baseline: "Rolling baseline",
      liveNow: "Live Now",
      footer: "Markers show incident traffic spikes exceeding statistical baseline."
    },
    gauge: {
      title: "AI Anomaly Score",
      subtitle: "Autoencoder AE v1",
      threshold: "Threshold",
      baselineThreshold: "Baseline threshold",
      rollingMean: "Mean MSE (1 min)",
      status: "AI Status",
      statusNominal: "Nominal Traffic",
      statusElevated: "Approaching Threshold",
      statusAnomaly: "Zero-Day Deviation"
    },
    vectors: {
      title: "Threat Vectors & Attack Origins",
      subtitle: "Top 5 Attack Sources & Targeted Endpoints",
      topIps: "Top 5 Attacking Source IPs",
      topPorts: "Top 5 Targeted Destination Ports",
      window: "Active window"
    },
    banner: {
      badge: "CRITICAL INCIDENT",
      confidence: "Confidence",
      inspect: "Inspect flow",
      safeTitle: "Perimeter Defended",
      safeDesc: "No uncontained critical cyber incidents detected in current window.",
      safePill: "Dual AI Engine",
      titleThreat: "Critical Incident Detected",
      subThreat: "Real-Time Triage & Detection",
      titleSafe: "Network Perimeter",
      subSafe: "Continuous Supervision"
    },
    table: {
      title: "Live Incident Feed",
      autoUpdating: "Auto-updating",
      searchPlaceholder: "Filter by source or destination IP...",
      allCategories: "All Categories (12 classes)",
      minConfidence: "Min Confidence:",
      zeroDayOnly: "Zero-Day Anomaly Only",
      clearFilters: "Clear Filters",
      timestamp: "Timestamp",
      sensor: "Sensor ID",
      route: "Source &rarr; Destination",
      source: "Source IP",
      destination: "Destination IP",
      subtitle: "Network flow traceability & Real-time inference",
      protocol: "Protocol",
      classification: "Deep Learning Class",
      confidence: "Confidence",
      autoencoder: "Autoencoder",
      severity: "Severity",
      emptyMessage: "No network incidents match your current filter criteria.",
      resetFilters: "Reset all filters"
    },
    drawer: {
      title: "Deep Flow Inspection",
      close: "Close",
      aiDetection: "AI Detection Details",
      classifierConf: "Classifier confidence",
      reconstructionMse: "Reconstruction error MSE",
      threshold: "threshold",
      anomaly: "Anomaly (0-day)",
      normal: "Normal",
      aeFlag: "Autoencoder flag",
      sensorOrigin: "Sensor origin",
      detectedAt: "Detected at",
      telemetry: "Bidirectional Telemetry",
      duration: "Duration",
      fwdPackets: "Forward packets",
      bwdPackets: "Backward packets",
      fwdBytes: "Forward bytes",
      bwdBytes: "Backward bytes",
      tcpFlags: "TCP Flags"
    },
    // Settings
    settings: {
      title: "System Settings & Detection",
      subtitle: "Node Configuration & Operational AI Thresholds",
      desc: "Configure HDVR console display language, autoencoder anomaly thresholds, and telemetry storage parameters.",
      langTitle: "Interface Language",
      langDesc: "The SOC console applies the selected language in real time across all monitoring modules.",
      thresholdsTitle: "Detection Operational Thresholds",
      aeThresholdLabel: "Autoencoder MSE Anomaly Threshold",
      aeHelp: "Default baseline derived from benign validation loss (0.6029).",
      minConfLabel: "Classifier Minimum Confidence (%)",
      saveBtn: "Save Settings",
      telemetryTitle: "Server & SQLite Telemetry",
      dbFile: "Database File",
      indexedCols: "Indexed Columns",
      storageEngine: "Storage Engine",
      wsStream: "WebSocket Stream",
      retention: "Retention Policy"
    }
  }
}
