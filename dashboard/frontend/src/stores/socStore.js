import { defineStore } from 'pinia'
import { api } from '@/services/api'
import { SocWebSocket } from '@/services/websocket'
import { translations } from '@/i18n/translations'

export const useSocStore = defineStore('soc', {
  state: () => ({
    // Internationalization & Branding
    lang: localStorage.getItem('soc_lang') || 'FR',
    appName: 'HDVR',
    appSubName: 'Autonomous Defense',

    // Mobile Responsive State
    mobileNavOpen: false,

    // Connection & status
    _initialized: false,
    _initPromise: null,
    wsConnected: false,
    isStreamPaused: false,
    activeTimeRange: '15m',
    isLoading: true,
    aeThreshold: (() => {
      const stored = Number(localStorage.getItem('soc_ae_threshold'))
      // Si la valeur stockée correspond à l'ancien seuil v1 (0.6029) ou est invalide, migrer vers le seuil Auto-Encodeur v2 (1.4810)
      if (!stored || isNaN(stored) || stored <= 0.61) {
        return 1.4810
      }
      return stored
    })(),
    currentMse: 0.28,

    // Core Metrics (KPIs)
    kpis: {
      total_flows: 0,
      attacks: 0,
      anomalies: 0,
      flow_rate_sec: 0,
      bandwidth_mbps: 0.0,
      benign_pct: 100.0,
      attack_pct: 0.0
    },

    // Visualizations
    attackDistribution: [],
    timelineSeries: [],
    threatVectors: {
      top_source_ips: [],
      top_dest_ports: []
    },

    // Feed & Inspection
    alerts: [],
    selectedFlow: null,
    drawerOpen: false,
    incidentFeedbackMap: {},
    selectedAlertIds: [],
    batchPatternModalOpen: false,

    // PCAP Replay
    pcapFiles: [],
    selectedPcap: '',
    replaySpeed: 1.0,
    replayStatus: {
      active: false,
      pcap_name: null,
      speed: 1.0,
      processed_flows: 0,
      total_alerts: 0,
      total_anomalies: 0,
      progress_pct: 0.0
    },

    // Sensor status
    sensorsOnline: 0,
    sensorsList: [],

    // Filter controls for Incident Feed
    filterSearch: '',
    filterCategory: '',
    filterMinConfidence: 0,
    filterAutoencoderOnly: false,

    // Model inference logs terminal
    modelLogs: [],
    modelLogsAutoScroll: true,

    // Model Agility & Dynamic Non-Frozen Classes
    modelClasses: [],
    dynamicAttackCategories: [],
    modelMeta: {
      version: 'v4',
      ae_version: 'v1',
      total_classes: 0
    },

    // System Health & Infrastructure Monitoring (Plan 1)
    systemHealth: {
      status: 'HEALTHY',
      score: 100,
      uptime_sec: 0,
      uptime_str: '0s',
      components: {
        sensors: { status: 'ONLINE', total_sensors: 0, online_sensors: 0 },
        ai_engine: { status: 'OPERATIONAL', avg_inference_ms: 12.5 },
        database: { status: 'HEALTHY', latency_ms: 1.0, file_size_mb: 0 },
        websocket: { status: 'ONLINE', connected_clients: 1 },
        host: { cpu_pct: 0, ram_pct: 0, disk_pct: 0 }
      },
      issues: []
    },
    systemLogs: [],
    systemDrawerOpen: false,

    _socket: null
  }),

  getters: {
    // Translation helper t('kpi.totalFlows')
    t: (state) => (path) => {
      const dict = translations[state.lang] || translations.FR
      const parts = path.split('.')
      let curr = dict
      for (const p of parts) {
        if (!curr || curr[p] === undefined) return path
        curr = curr[p]
      }
      return curr
    },

    globalThreatLevel: (state) => {
      const dict = translations[state.lang]?.header || translations.FR.header
      const recentCrit = state.alerts.slice(0, 25).filter(a => a.severity === 'Critical' || a.pred === 'DDoS' || a.pred === 'Bot').length
      if (recentCrit >= 4 || state.currentMse > state.aeThreshold) {
        return { level: 2, label: dict.threatCritical, color: 'var(--cr)' }
      }
      if (recentCrit >= 1 || state.currentMse > 0.45) {
        return { level: 1, label: dict.threatElevated, color: 'var(--md)' }
      }
      return { level: 0, label: dict.threatNormal, color: 'var(--ok)' }
    },

    filteredAlerts: (state) => {
      const q = state.filterSearch.trim().toLowerCase()
      const cat = state.filterCategory
      const minConf = state.filterMinConfidence
      const aeOnly = state.filterAutoencoderOnly

      return state.alerts.filter(a => {
        const matchesQ = !q || (a.src_ip && a.src_ip.toLowerCase().includes(q)) || (a.dst_ip && a.dst_ip.toLowerCase().includes(q))
        const matchesCat = !cat || a.pred === cat || (cat === 'Unknown (anomaly)' && a.anomalie_ae === 1)
        const matchesConf = ((a.confiance || 0) * 100) >= minConf
        const matchesAe = !aeOnly || a.anomalie_ae === 1
        return matchesQ && matchesCat && matchesConf && matchesAe
      })
    },

    latestCriticalAlert: (state) => {
      return state.alerts.find(a => a.severity === 'Critical' || a.pred === 'DDoS' || a.pred === 'Bot') || null
    },

    selectedAlerts: (state) => {
      const idSet = new Set(state.selectedAlertIds.map(String))
      return state.alerts.filter(a => {
        const id = String(a.id || `${a.src_ip}-${a.dst_port}-${a.received_at}`)
        return idSet.has(id)
      })
    },

    selectedCount: (state) => state.selectedAlertIds.length,

    selectedZeroDaysCount: (state) => {
      const idSet = new Set(state.selectedAlertIds.map(String))
      return state.alerts.filter(a => {
        const id = String(a.id || `${a.src_ip}-${a.dst_port}-${a.received_at}`)
        const isZd = Boolean(a.anomalie_ae === 1 || a.anomalie_ae === true || a.is_anomaly === true || a.is_zero_day === true)
        return idSet.has(id) && isZd
      }).length
    },

    totalZeroDaysCount: (state) => {
      return state.alerts.filter(a => Boolean(a.anomalie_ae === 1 || a.anomalie_ae === true || a.is_anomaly === true || a.is_zero_day === true)).length
    },

    isAlertSelected: (state) => (alert) => {
      const id = String(alert.id || `${alert.src_ip}-${alert.dst_port}-${alert.received_at}`)
      return state.selectedAlertIds.includes(id)
    },

    isAllFilteredSelected: (state) => {
      const filtered = state.filteredAlerts
      if (!filtered.length) return false
      const idSet = new Set(state.selectedAlertIds.map(String))
      return filtered.every(a => {
        const id = String(a.id || `${a.src_ip}-${a.dst_port}-${a.received_at}`)
        return idSet.has(id)
      })
    },

    availableAttackCategories: (state) => {
      const set = new Set(state.dynamicAttackCategories || [])
      // Add all non-benign classes from modelClasses
      for (const c of (state.modelClasses || [])) {
        if (c && c.toUpperCase() !== 'BENIGN') {
          set.add(c)
        }
      }
      // Add any distinct attack label present in current alerts
      for (const a of state.alerts) {
        const p = a.pred || a.classification
        if (p && p.toUpperCase() !== 'BENIGN' && p !== 'Unknown (anomaly)') {
          set.add(p)
        }
      }
      const list = Array.from(set).sort()
      if (!list.includes('Unknown (anomaly)')) {
        list.push('Unknown (anomaly)')
      }
      return list
    }
  },

  actions: {
    setLanguage(newLang) {
      if (newLang === 'FR' || newLang === 'EN') {
        this.lang = newLang
        localStorage.setItem('soc_lang', newLang)
      }
    },

    toggleMobileNav() {
      this.mobileNavOpen = !this.mobileNavOpen
    },

    closeMobileNav() {
      this.mobileNavOpen = false
    },

    async init() {
      if (this._initialized) return
      if (this._initPromise) return this._initPromise
      this._initPromise = (async () => {
        try {
          await this.loadDashboardData(this.activeTimeRange)
          await this.fetchSystemHealth()
          this.initWebSocket()
          this._initialized = true
        } finally {
          this._initPromise = null
        }
      })()
      return this._initPromise
    },

    async loadDashboardData(range = '15m') {
      this.isLoading = true
      try {
        this.activeTimeRange = range
        const data = await api.getInitData(range)

        if (data.kpis) {
          this.kpis = {
            total_flows: data.kpis.total_flows ?? this.kpis.total_flows,
            attacks: data.kpis.attacks ?? data.kpis.confirmed_attacks ?? this.kpis.attacks,
            anomalies: data.kpis.anomalies ?? data.kpis.zero_day_anomalies ?? this.kpis.anomalies,
            flow_rate_sec: data.kpis.flow_rate_sec ?? data.kpis.rate_flows_sec ?? this.kpis.flow_rate_sec,
            bandwidth_mbps: data.kpis.bandwidth_mbps ?? ((data.kpis.flow_rate_sec || 1000) * 0.0035).toFixed(1),
            benign_pct: data.kpis.benign_pct ?? 96.0,
            attack_pct: data.kpis.attack_pct ?? data.kpis.malicious_pct ?? 4.0
          }
          if (data.kpis.current_mse !== undefined) {
            this.currentMse = Number(data.kpis.current_mse)
          }
        }

        const dist = data.distribution || data.attack_distribution
        if (dist && dist.length > 0) {
          this.attackDistribution = dist
        }

        if (data.timeline && data.timeline.length > 0) {
          this.timelineSeries = data.timeline
        }

        if (data.threat_vectors) {
          this.threatVectors = {
            top_source_ips: data.threat_vectors.top_source_ips || data.threat_vectors.top_ips || [],
            top_dest_ports: data.threat_vectors.top_dest_ports || data.threat_vectors.top_ports || []
          }
        }

        if (data.recent_alerts && data.recent_alerts.length > 0) {
          this.alerts = data.recent_alerts.map(a => {
            const pred = a.pred || a.classification || 'BENIGN'
            const anom = a.anomalie_ae !== undefined ? a.anomalie_ae : (a.is_anomaly ? 1 : 0)
            const conf = a.confiance !== undefined ? a.confiance : (a.confidence ? a.confidence / 100 : 0.9)
            return {
              ...a,
              pred: pred,
              classification: pred,
              confiance: conf,
              confidence: a.confidence !== undefined ? a.confidence : Math.round(conf * 100),
              sensor: a.sensor || a.sensor_id || 'sensor-edge-01',
              sensor_id: a.sensor_id || a.sensor || 'sensor-edge-01',
              received_at: a.received_at || a.timestamp || '',
              timestamp: a.timestamp || a.received_at || '',
              anomalie_ae: anom,
              is_anomaly: Boolean(anom),
              severity: a.severity || this.resolveSeverity(pred, anom)
            }
          })
        }

        if (data.pcap_files && data.pcap_files.length > 0) {
          this.pcapFiles = data.pcap_files
        } else if (data.pcaps && data.pcaps.length > 0) {
          this.pcapFiles = data.pcaps.map(p => typeof p === 'string' ? { filename: p, size_mb: 25.0 } : p)
        }

        if (data.replay_status) this.replayStatus = data.replay_status
        if (data.ae_threshold) this.aeThreshold = data.ae_threshold
        if (data.system_health) this.systemHealth = data.system_health
        if (data.model_classes) this.modelClasses = data.model_classes
        if (data.attack_categories) this.dynamicAttackCategories = data.attack_categories
        if (data.model_meta) this.modelMeta = data.model_meta
        if (data.sensors && Array.isArray(data.sensors)) {
          this.sensorsList = data.sensors
          this.sensorsOnline = data.sensors.filter(s => s.status === 'Online').length
        }
      } catch (err) {
        console.error('Failed to load initial dashboard data:', err)
      } finally {
        setTimeout(() => {
          this.isLoading = false
        }, 380)
      }
    },

    initWebSocket() {
      if (this._socket) return

      this._socket = new SocWebSocket({
        onStatusChange: ({ connected, paused }) => {
          this.wsConnected = connected
          if (paused !== undefined) this.isStreamPaused = paused
        },
        onMessage: (msg) => {
          this.handleLiveMessage(msg)
        }
      })

      this._socket.connect()
    },

    handleLiveMessage(msg) {
      if (msg.type === 'model_log' && msg.log) {
        this.modelLogs.push(msg.log)
        if (this.modelLogs.length > 300) {
          this.modelLogs.shift()
        }
        return
      }

      if (msg.type === 'init') {
        if (msg.recent_model_logs && Array.isArray(msg.recent_model_logs)) {
          this.modelLogs = msg.recent_model_logs
        }
        if (msg.system_health) {
          this.systemHealth = msg.system_health
        }
        if (msg.model_classes) {
          this.modelClasses = msg.model_classes
        }
        if (msg.attack_categories) {
          this.dynamicAttackCategories = msg.attack_categories
        }
        if (msg.model_meta) {
          this.modelMeta = msg.model_meta
        }
      }

      if (msg.type === 'system_health' && msg.system_health) {
        this.systemHealth = msg.system_health
      }

      if (msg.type === 'incident_feedback' && msg.incident_id) {
        this.incidentFeedbackMap = {
          ...this.incidentFeedbackMap,
          [msg.incident_id]: {
            human_verdict: msg.human_verdict,
            corrected_attack_type: msg.corrected_attack_type
          }
        }
      }

      if (msg.type === 'batch_incident_feedback' && Array.isArray(msg.incident_ids)) {
        const newMap = { ...this.incidentFeedbackMap }
        for (const id of msg.incident_ids) {
          newMap[id] = {
            human_verdict: msg.human_verdict,
            corrected_attack_type: msg.corrected_attack_type
          }
        }
        this.incidentFeedbackMap = newMap
      }

      if (msg.type === 'database_reset') {
        this.kpis = msg.kpis || {
          total_flows: 0,
          attacks: 0,
          anomalies: 0,
          flow_rate_sec: 0,
          bandwidth_mbps: 0.0,
          benign_pct: 100.0,
          attack_pct: 0.0
        }
        this.alerts = []
        this.attackDistribution = msg.distribution || []
        this.timelineSeries = msg.timeline || []
        this.threatVectors = msg.threat_vectors || { top_source_ips: [], top_dest_ports: [] }
        this.currentMse = 0.0
        return
      }

      if (msg.type === 'connected') {
        if (msg.ae_threshold) this.aeThreshold = msg.ae_threshold
        return
      }

      if (msg.type === 'new_flows' || msg.type === 'replay_batch') {
        const received = msg.received || 0
        const alertsCount = msg.alerts_count || 0
        const anomaliesCount = msg.anomalies_count || 0

        // Synchroniser les KPIs réels
        if (msg.kpis) {
          this.kpis = { ...this.kpis, ...msg.kpis }
        } else {
          this.kpis.total_flows += received
          this.kpis.attacks += alertsCount
          this.kpis.anomalies += anomaliesCount

          const mal = this.kpis.attacks + this.kpis.anomalies
          this.kpis.attack_pct = this.kpis.total_flows > 0 ? (mal / this.kpis.total_flows) * 100 : 0
          this.kpis.benign_pct = 100 - this.kpis.attack_pct

          this.kpis.flow_rate_sec = Math.round(received * 1.5 + (this.kpis.flow_rate_sec * 0.4))
          this.kpis.bandwidth_mbps = (this.kpis.flow_rate_sec * 0.0035).toFixed(1)
        }

        // Mettre à jour la répartition des attaques (Attack Donut)
        if (msg.distribution && Array.isArray(msg.distribution) && msg.distribution.length > 0) {
          this.attackDistribution = msg.distribution
        }

        // Mettre à jour la chronologie d'activité (Timeline Chart)
        if (msg.timeline && Array.isArray(msg.timeline) && msg.timeline.length > 0) {
          this.timelineSeries = msg.timeline
        }

        // Mettre à jour les vecteurs de menaces (Threat Vectors: IPs & Ports)
        if (msg.threat_vectors) {
          this.threatVectors = msg.threat_vectors
        }

        // Mettre à jour le statut du rejeu
        if (msg.replay_status) {
          this.replayStatus = { ...this.replayStatus, ...msg.replay_status }
        }

        // Normaliser et ajouter les nouvelles alertes
        if (msg.recent_alerts && msg.recent_alerts.length > 0) {
          const markedAlerts = msg.recent_alerts.map(a => {
            const pred = a.pred || a.classification || 'BENIGN'
            const anom = a.anomalie_ae !== undefined ? a.anomalie_ae : (a.is_anomaly ? 1 : 0)
            const conf = a.confiance !== undefined ? a.confiance : (a.confidence ? a.confidence / 100 : 0.9)
            return {
              ...a,
              isNew: true,
              pred: pred,
              classification: pred,
              confiance: conf,
              confidence: a.confidence !== undefined ? a.confidence : Math.round(conf * 100),
              sensor: a.sensor || a.sensor_id || 'sensor-edge-01',
              sensor_id: a.sensor_id || a.sensor || 'sensor-edge-01',
              received_at: a.received_at || a.timestamp || '',
              timestamp: a.timestamp || a.received_at || '',
              anomalie_ae: anom,
              is_anomaly: Boolean(anom),
              severity: a.severity || this.resolveSeverity(pred, anom)
            }
          })
          this.alerts = [...markedAlerts, ...this.alerts].slice(0, 300)

          // Update current MSE
          const latestMse = markedAlerts.find(a => a.mse_ae !== null && a.mse_ae !== undefined)
          if (latestMse) {
            this.currentMse = Number((this.currentMse * 0.7 + latestMse.mse_ae * 0.3).toFixed(3))
          }
        }
      }

      if (msg.type === 'replay_finished') {
        this.replayStatus.active = false
        this.replayStatus.is_paused = false
        this.replayStatus.progress_pct = 100
        if (msg.kpis) this.kpis = { ...this.kpis, ...msg.kpis }
        if (msg.distribution && Array.isArray(msg.distribution)) this.attackDistribution = msg.distribution
        if (msg.timeline && Array.isArray(msg.timeline)) this.timelineSeries = msg.timeline
        if (msg.threat_vectors) this.threatVectors = msg.threat_vectors
      }

      if (msg.type === 'replay_stopped') {
        this.replayStatus.active = false
        this.replayStatus.is_paused = false
      }
    },

    resolveSeverity(pred, isAnomaly) {
      if (pred === 'DDoS' || pred === 'Bot') return 'Critical'
      if (pred.startsWith('DoS') || pred === 'WebAttack' || (isAnomaly && pred !== 'BENIGN')) return 'High'
      if (isAnomaly && pred === 'BENIGN') return 'High'
      if (pred.includes('Patator') || pred === 'PortScan') return 'Medium'
      if (pred === 'BENIGN' && !isAnomaly) return 'Benign'
      return 'Low'
    },

    toggleStreamPause() {
      if (!this._socket) return
      if (this.isStreamPaused) {
        this._socket.resume()
      } else {
        this._socket.pause()
      }
    },

    async startPcapReplay(pcapName, speed = 1.0) {
      if (!pcapName) return
      try {
        await api.startReplay(pcapName, speed)
        this.replayStatus.active = true
        this.replayStatus.pcap_name = pcapName
        this.replayStatus.speed = speed
      } catch (err) {
        console.error('Error starting PCAP replay:', err)
      }
    },

    async stopPcapReplay() {
      try {
        await api.stopReplay()
        this.replayStatus.active = false
        this.replayStatus.is_paused = false
      } catch (err) {
        console.error('Error stopping PCAP replay:', err)
      }
    },

    async pausePcapReplay() {
      try {
        await api.pauseReplay()
        this.replayStatus.is_paused = true
      } catch (err) {
        console.error('Error pausing PCAP replay:', err)
      }
    },

    async resumePcapReplay() {
      try {
        await api.resumeReplay()
        this.replayStatus.is_paused = false
      } catch (err) {
        console.error('Error resuming PCAP replay:', err)
      }
    },

    async fetchSensors() {
      try {
        const res = await api.getSensors()
        if (res && res.sensors) {
          this.sensorsList = res.sensors
          this.sensorsOnline = res.online_count || 0
        }
      } catch (err) {
        console.error('Error fetching sensors:', err)
      }
    },

    openFlowDrawer(flow) {
      this.selectedFlow = flow
      this.drawerOpen = true
    },

    closeFlowDrawer() {
      this.drawerOpen = false
      this.selectedFlow = null
    },

    async submitFeedback(incidentId, verdict, correctedType, notes, flowData) {
      try {
        const res = await api.submitIncidentFeedback(incidentId, {
          human_verdict: verdict,
          corrected_attack_type: correctedType,
          analyst_notes: notes,
          flow_data: flowData
        })
        this.incidentFeedbackMap = {
          ...this.incidentFeedbackMap,
          [incidentId]: {
            human_verdict: verdict,
            corrected_attack_type: correctedType
          }
        }
        return res
      } catch (err) {
        console.error('Error submitting incident feedback:', err)
        throw err
      }
    },

    toggleSelectAlert(alert) {
      const id = String(alert.id || `${alert.src_ip}-${alert.dst_port}-${alert.received_at}`)
      const idx = this.selectedAlertIds.indexOf(id)
      if (idx > -1) {
        this.selectedAlertIds.splice(idx, 1)
      } else {
        this.selectedAlertIds.push(id)
      }
    },

    selectAllZeroDays() {
      // Sélectionner exclusivement les flux anormaux Zero-Day confirmés (anomalie_ae === 1 ou is_anomaly === true)
      const targetList = this.filteredAlerts.length < this.alerts.length ? this.filteredAlerts : this.alerts
      const zdAlerts = targetList.filter(
        a => Boolean(a.anomalie_ae === 1 || a.anomalie_ae === true || a.is_anomaly === true || a.is_zero_day === true)
      )
      const ids = zdAlerts.map(a => String(a.id || `${a.src_ip}-${a.dst_port}-${a.received_at}`))
      this.selectedAlertIds = Array.from(new Set(ids))
    },

    selectAllFiltered() {
      const ids = this.filteredAlerts.map(a => String(a.id || `${a.src_ip}-${a.dst_port}-${a.received_at}`))
      this.selectedAlertIds = Array.from(new Set(ids))
    },

    clearSelectedAlerts() {
      this.selectedAlertIds = []
    },

    toggleSelectAllFiltered() {
      if (this.isAllFilteredSelected) {
        const filteredIdSet = new Set(this.filteredAlerts.map(a => String(a.id || `${a.src_ip}-${a.dst_port}-${a.received_at}`)))
        this.selectedAlertIds = this.selectedAlertIds.filter(id => !filteredIdSet.has(id))
      } else {
        this.selectAllFiltered()
      }
    },

    openBatchPatternModal() {
      this.batchPatternModalOpen = true
    },

    closeBatchPatternModal() {
      this.batchPatternModalOpen = false
    },

    async submitBatchFeedback(verdict, correctedType, notes) {
      const selected = this.selectedAlerts
      if (!selected.length) return

      const incidentIds = selected.map(a => String(a.id || `${a.src_ip}-${a.dst_port}-${a.received_at}`))
      try {
        const res = await api.submitBatchIncidentFeedback({
          incident_ids: incidentIds,
          human_verdict: verdict,
          corrected_attack_type: correctedType,
          analyst_notes: notes,
          flows: selected
        })

        const newMap = { ...this.incidentFeedbackMap }
        for (const id of incidentIds) {
          newMap[id] = {
            human_verdict: verdict,
            corrected_attack_type: correctedType
          }
        }
        this.incidentFeedbackMap = newMap
        this.clearSelectedAlerts()
        return res
      } catch (err) {
        console.error('Error submitting batch feedback:', err)
        throw err
      }
    },

    async fetchModelLogs(limit = 100) {
      try {
        const data = await api.getModelLogs(limit)
        if (data && data.logs) {
          this.modelLogs = data.logs
        }
      } catch (err) {
        console.error('Error fetching model logs:', err)
      }
    },

    async clearModelLogs() {
      try {
        await api.clearModelLogs()
        this.modelLogs = []
      } catch (err) {
        console.error('Error clearing model logs:', err)
      }
    },

    clearFilters() {
      this.filterSearch = ''
      this.filterCategory = ''
      this.filterMinConfidence = 0
      this.filterAutoencoderOnly = false
    },

    async applySettings({ lang, aeThreshold, minConfidence }) {
      if (lang) {
        this.setLanguage(lang)
      }
      if (aeThreshold !== undefined && aeThreshold !== null) {
        this.aeThreshold = Number(aeThreshold)
        localStorage.setItem('soc_ae_threshold', String(aeThreshold))
      }
      if (minConfidence !== undefined && minConfidence !== null) {
        this.filterMinConfidence = Number(minConfidence)
        localStorage.setItem('soc_min_confidence', String(minConfidence))
      }
      try {
        await api.updateSettings({
          ae_threshold: aeThreshold,
          min_confidence: minConfidence
        })
      } catch (err) {
        console.warn('Could not persist settings to server, saved locally:', err)
      }
    },

    async fetchSystemHealth() {
      try {
        const res = await api.getSystemHealth()
        if (res && res.status) {
          this.systemHealth = res
        }
      } catch (err) {
        console.error('Failed to fetch system health:', err)
      }
    },

    async fetchSystemLogs(limit = 50, level = null) {
      try {
        const logs = await api.getSystemLogs(limit, level)
        if (Array.isArray(logs)) {
          this.systemLogs = logs
        }
      } catch (err) {
        console.error('Failed to fetch system logs:', err)
      }
    },

    async optimizeDatabase() {
      try {
        const res = await api.optimizeDatabase()
        await this.fetchSystemHealth()
        return res
      } catch (err) {
        console.error('Database optimization error:', err)
        throw err
      }
    },

    async testComponent(component = 'all') {
      try {
        return await api.testComponent(component)
      } catch (err) {
        console.error(`Component test error (${component}):`, err)
        throw err
      }
    },

    openSystemDrawer() {
      this.systemDrawerOpen = true
      this.fetchSystemHealth()
      this.fetchSystemLogs()
    },

    closeSystemDrawer() {
      this.systemDrawerOpen = false
    },

    toggleSystemDrawer() {
      if (this.systemDrawerOpen) {
        this.closeSystemDrawer()
      } else {
        this.openSystemDrawer()
      }
    },

    async fetchModelClasses() {
      try {
        const res = await api.getModelClasses()
        if (res) {
          this.modelClasses = res.classes || []
          this.dynamicAttackCategories = res.all_categories || []
          this.modelMeta = res
        }
      } catch (err) {
        console.warn('Failed to fetch dynamic model classes:', err)
      }
    },

    async resetDatabase() {
      this.isLoading = true
      try {
        await api.resetDatabase()
        this.kpis = {
          total_flows: 0,
          attacks: 0,
          anomalies: 0,
          flow_rate_sec: 0,
          bandwidth_mbps: 0.0,
          benign_pct: 100.0,
          attack_pct: 0.0
        }
        this.attackDistribution = []
        this.timelineSeries = []
        this.threatVectors = { top_source_ips: [], top_dest_ports: [] }
        this.alerts = []
        this.currentMse = 0.0
        this.sensorsList = []
        this.sensorsOnline = 0
        await this.loadDashboardData(this.activeTimeRange)
      } catch (err) {
        console.error('Failed to reset database:', err)
        throw err
      } finally {
        setTimeout(() => {
          this.isLoading = false
        }, 300)
      }
    }
  }
})
