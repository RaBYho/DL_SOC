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
    wsConnected: false,
    isStreamPaused: false,
    activeTimeRange: '15m',
    aeThreshold: 0.6029,
    currentMse: 0.28,

    // Core Metrics (KPIs)
    kpis: {
      total_flows: 48210,
      attacks: 1842,
      anomalies: 96,
      flow_rate_sec: 1045,
      bandwidth_mbps: 3.6,
      benign_pct: 96.0,
      attack_pct: 4.0
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
    sensorsOnline: 4,

    // Filter controls for Incident Feed
    filterSearch: '',
    filterCategory: '',
    filterMinConfidence: 0,
    filterAutoencoderOnly: false,

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
      await this.loadDashboardData(this.activeTimeRange)
      this.initWebSocket()
    },

    async loadDashboardData(range = '15m') {
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
          this.alerts = data.recent_alerts.map(a => ({
            ...a,
            severity: a.severity || this.resolveSeverity(a.pred, a.anomalie_ae)
          }))
        }

        if (data.pcap_files && data.pcap_files.length > 0) {
          this.pcapFiles = data.pcap_files
        } else if (data.pcaps && data.pcaps.length > 0) {
          this.pcapFiles = data.pcaps.map(p => typeof p === 'string' ? { filename: p, size_mb: 25.0 } : p)
        }

        if (data.replay_status) this.replayStatus = data.replay_status
        if (data.ae_threshold) this.aeThreshold = data.ae_threshold
      } catch (err) {
        console.error('Failed to load initial dashboard data:', err)
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
      if (msg.type === 'connected') {
        if (msg.ae_threshold) this.aeThreshold = msg.ae_threshold
        return
      }

      if (msg.type === 'new_flows' || msg.type === 'replay_batch') {
        const received = msg.received || 0
        const alertsCount = msg.alerts_count || 0
        const anomaliesCount = msg.anomalies_count || 0

        this.kpis.total_flows += received
        this.kpis.attacks += alertsCount
        this.kpis.anomalies += anomaliesCount

        const mal = this.kpis.attacks + this.kpis.anomalies
        this.kpis.attack_pct = this.kpis.total_flows > 0 ? (mal / this.kpis.total_flows) * 100 : 0
        this.kpis.benign_pct = 100 - this.kpis.attack_pct

        // Flow rate estimate
        this.kpis.flow_rate_sec = Math.round(received * 1.5 + (this.kpis.flow_rate_sec * 0.4))
        this.kpis.bandwidth_mbps = (this.kpis.flow_rate_sec * 0.0035).toFixed(1)

        // Prepend new alerts
        if (msg.recent_alerts && msg.recent_alerts.length > 0) {
          const markedAlerts = msg.recent_alerts.map(a => ({
            ...a,
            isNew: true,
            severity: a.severity || this.resolveSeverity(a.pred, a.anomalie_ae)
          }))
          this.alerts = [...markedAlerts, ...this.alerts].slice(0, 300)

          // Update current MSE
          const latestMse = markedAlerts.find(a => a.mse_ae !== null && a.mse_ae !== undefined)
          if (latestMse) {
            this.currentMse = Number((this.currentMse * 0.7 + latestMse.mse_ae * 0.3).toFixed(3))
          }
        }

        // Update Replay progress if applicable
        if (msg.type === 'replay_batch') {
          this.replayStatus.active = true
          this.replayStatus.pcap_name = msg.pcap_name
          this.replayStatus.progress_pct = msg.progress_pct || 0
          this.replayStatus.processed_flows = (this.replayStatus.processed_flows || 0) + received
        }
      }

      if (msg.type === 'replay_completed') {
        this.replayStatus.active = false
        this.replayStatus.progress_pct = 100
      }

      if (msg.type === 'replay_stopped') {
        this.replayStatus.active = false
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
      } catch (err) {
        console.error('Error stopping PCAP replay:', err)
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

    clearFilters() {
      this.filterSearch = ''
      this.filterCategory = ''
      this.filterMinConfidence = 0
      this.filterAutoencoderOnly = false
    }
  }
})
