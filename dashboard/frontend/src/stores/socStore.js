import { defineStore } from "pinia"
import { api } from "@/services/api"
import { wsClient } from "@/services/websocket"

export const useSocStore = defineStore("soc", {
  state: () => ({
    // Connection & Stream state
    connected: false,
    streamPaused: false,
    activeTab: "triage", // "triage" | "threat-actors" | "flows" | "replay"
    searchQuery: "",
    selectedSeverityFilter: "ALL",
    excludeLoopback: true, // Filtre anti-bruit pour 127.0.0.1 (activé par défaut)

    // UI & Layout States (Loading, Error, Busy, Ergonomics)
    isLoading: true,
    initError: null,
    isPurging: false,
    isUpdatingIncident: false,
    chartsVisible: true,
    tableDensity: "compact", // "compact" | "normal"

    // KPI & Operational summaries
    kpis: {
      total_flows: 0,
      critical_alerts: 0,
      zero_days: 0,
      top_vector: "None",
      dpi_triggered: 0,
      inspection_rate_pct: 100.0,
      top_attacker_ip: "-",
      top_attacker_attacks: 0,
      top_attacker_threat: "-",
      top_targeted_ip: "-",
      top_targeted_port: "-",
      top_targeted_service: "-",
    },
    traffic: {
      status: "NORMAL",
      total_packets: 0,
      total_flows: 0,
      total_attacks: 0,
      total_zero_days: 0,
      attack_ratio_pct: 0.0,
      throughput_flows_sec: 0.0,
    },

    // Charts & Telemetry distributions
    timeline: [],
    engineDistribution: {
      dpi: 0,
      ml: 0,
      kitsune: 0,
      benign: 0,
    },
    attackDistribution: {},

    // Tabular Records
    alerts: [],
    flows: [],
    sensors: [],
    threatActors: [],
    targetedStats: {
      top_targeted_port: "-",
      top_targeted_port_service: "-",
      top_targeted_ip: "-",
      targeted_ports: [],
      targeted_victims: [],
    },
    thresholds: {
      t1: 0.5,
      t2: 0.7,
      t3: 0.01,
      models: [],
      leaky_bucket_half_life: 60.0,
    },

    // Forensics Slide-Over
    selectedForensics: null,
    isDrawerOpen: false,
    forensicsLoading: false,

    // Replay
    availablePcaps: [],
    isReplaying: false,
    replayStatus: null,
  }),

  getters: {
    filteredAlerts: (state) => {
      let list = state.alerts
      if (state.excludeLoopback) {
        list = list.filter((a) => !a.src_ip?.startsWith("127.") && !a.dst_ip?.startsWith("127."))
      }
      if (state.selectedSeverityFilter !== "ALL") {
        list = list.filter((a) => a.severity === state.selectedSeverityFilter)
      }
      if (state.searchQuery.trim()) {
        const q = state.searchQuery.toLowerCase()
        list = list.filter(
          (a) =>
            a.src_ip?.toLowerCase().includes(q) ||
            a.dst_ip?.toLowerCase().includes(q) ||
            a.attack_type?.toLowerCase().includes(q) ||
            a.incident_code?.toLowerCase().includes(q)
        )
      }
      return list
    },

    filteredFlows: (state) => {
      let list = state.flows
      if (state.excludeLoopback) {
        const nonLoop = list.filter((f) => !f.src_ip?.startsWith("127.") && !f.dst_ip?.startsWith("127."))
        list = nonLoop.length > 0 ? nonLoop : list
      }
      if (state.selectedSeverityFilter !== "ALL") {
        list = list.filter((f) => f.severity === state.selectedSeverityFilter)
      }
      if (state.searchQuery.trim()) {
        const q = state.searchQuery.toLowerCase()
        list = list.filter(
          (f) =>
            f.src_ip?.toLowerCase().includes(q) ||
            f.dst_ip?.toLowerCase().includes(q) ||
            f.threat_class?.toLowerCase().includes(q) ||
            f.pred?.toLowerCase().includes(q) ||
            String(f.dst_port).includes(q)
        )
      }
      return list
    },

    filteredThreatActors: (state) => {
      let list = state.threatActors
      if (state.excludeLoopback) {
        const filtered = list.filter((a) => !a.src_ip?.startsWith("127."))
        // Si aucun attaquant externe n'est présent, on affiche le tableau avec avertissement plutôt que vide
        list = filtered.length > 0 ? filtered : list
      }
      if (state.searchQuery.trim()) {
        const q = state.searchQuery.toLowerCase()
        list = list.filter(
          (a) =>
            a.src_ip?.toLowerCase().includes(q) ||
            a.top_attack_type?.toLowerCase().includes(q) ||
            a.targeted_ports_summary?.toLowerCase().includes(q)
        )
      }
      return list
    },

    activeSensor: (state) => {
      return state.sensors.length > 0 ? state.sensors[0] : null
    },
  },

  actions: {
    async initialize() {
      this.isLoading = true
      this.initError = null
      try {
        const initData = await api.getInitState()
        this.kpis = initData.kpis || this.kpis
        this.traffic = initData.traffic || this.traffic
        this.timeline = initData.timeline || []
        this.engineDistribution = initData.engine_distribution || this.engineDistribution
        this.attackDistribution = initData.attack_distribution || {}
        this.alerts = initData.recent_alerts || []
        this.flows = initData.recent_flows || []
        this.sensors = initData.sensors || []
        this.threatActors = initData.threat_actors || []
        this.targetedStats = initData.targeted_stats || this.targetedStats
        this.thresholds = initData.thresholds || this.thresholds

        this.setupWebSocket()
        this.loadPcaps()
      } catch (err) {
        console.error("Failed to initialize SOC store:", err)
        this.initError = err.message || "Failed to connect to NIDS backend on port 8000."
      } finally {
        this.isLoading = false
      }
    },

    reconnectWs() {
      wsClient.connect()
    },

    resetFilters() {
      this.searchQuery = ""
      this.selectedSeverityFilter = "ALL"
    },

    setupWebSocket() {
      wsClient.connect()

      wsClient.on("connection_status", ({ connected }) => {
        this.connected = connected
      })

      wsClient.on("telemetry_update", (data) => {
        if (this.streamPaused) return

        if (data.kpis) this.kpis = data.kpis
        if (data.traffic) this.traffic = data.traffic
        if (data.timeline) this.timeline = data.timeline
        if (data.engine_distribution) this.engineDistribution = data.engine_distribution
        if (data.targeted_stats) this.targetedStats = data.targeted_stats
        if (data.attack_distribution) this.attackDistribution = data.attack_distribution

        // Refresh recent lists quietly
        this.refreshFlows()
        this.refreshAlerts()
        this.refreshThreatActors()
      })

      wsClient.on("sensor_heartbeat", (heartbeat) => {
        const idx = this.sensors.findIndex((s) => s.sensor_id === heartbeat.sensor_id)
        if (idx !== -1) {
          this.sensors[idx] = { ...this.sensors[idx], ...heartbeat }
        } else {
          this.sensors.unshift(heartbeat)
        }
      })

      wsClient.on("incident_status_changed", ({ incident_id, new_status }) => {
        const target = this.alerts.find(
          (a) => a.id === incident_id || a.incident_code === incident_id
        )
        if (target) {
          target.status = new_status
        }
      })

      wsClient.on("db_reset", () => {
        this.alerts = []
        this.flows = []
        this.threatActors = []
        this.selectedForensics = null
        this.isDrawerOpen = false
        this.refreshTimeline()
        this.refreshEngineDistribution()
      })

      // Fallback heartbeat poll when WebSocket is disconnected or idle
      if (!this._liveChartInterval) {
        this._liveChartInterval = setInterval(() => {
          if (!this.streamPaused && !this.connected) {
            this.refreshTimeline()
            this.refreshEngineDistribution()
          }
        }, 5000)
      }
    },

    async refreshFlows() {
      if (this.streamPaused) return
      try {
        this.flows = await api.getRecentFlows(100, false, this.excludeLoopback)
      } catch (e) {
        // Silent background refresh
      }
    },

    async refreshAlerts() {
      if (this.streamPaused) return
      try {
        this.alerts = await api.getAlerts({ limit: 100, exclude_loopback: this.excludeLoopback })
      } catch (e) {
        // Silent background refresh
      }
    },

    async refreshThreatActors() {
      try {
        this.threatActors = await api.getThreatActors(50, this.excludeLoopback)
        this.targetedStats = await api.getTargetedStats(this.excludeLoopback)
      } catch (e) {
        // Silent background refresh
      }
    },

    async refreshTimeline() {
      if (this.streamPaused) return
      try {
        this.timeline = await api.getTimeline(15, 20, this.excludeLoopback)
      } catch (e) {
        // Silent background refresh
      }
    },

    async refreshEngineDistribution() {
      if (this.streamPaused) return
      try {
        this.engineDistribution = await api.getEngineDistribution(this.excludeLoopback)
      } catch (e) {
        // Silent background refresh
      }
    },

    toggleLoopbackFilter() {
      this.excludeLoopback = !this.excludeLoopback
      this.refreshFlows()
      this.refreshAlerts()
      this.refreshThreatActors()
      this.refreshTimeline()
      this.refreshEngineDistribution()
    },

    filterByIp(ip) {
      this.searchQuery = ip
      this.activeTab = "flows"
    },

    toggleCharts() {
      this.chartsVisible = !this.chartsVisible
    },

    toggleDensity() {
      this.tableDensity = this.tableDensity === "compact" ? "normal" : "compact"
    },

    async loadPcaps() {
      try {
        this.availablePcaps = await api.getPcaps()
      } catch (e) {
        console.warn("Could not load PCAP list:", e)
      }
    },

    async openForensics(flowId) {
      this.isDrawerOpen = true
      this.forensicsLoading = true
      try {
        this.selectedForensics = await api.getFlowForensics(flowId)
      } catch (err) {
        console.error("Failed to load forensics for flow:", flowId, err)
      } finally {
        this.forensicsLoading = false
      }
    },

    closeForensics() {
      this.isDrawerOpen = false
      this.selectedForensics = null
    },

    async changeIncidentStatus(incidentId, status, notes = "") {
      this.isUpdatingIncident = true
      try {
        await api.updateAlertStatus(incidentId, status, notes)
        const target = this.alerts.find(
          (a) => a.id === incidentId || a.incident_code === incidentId
        )
        if (target) {
          target.status = status
        }
      } catch (err) {
        console.error("Failed to update status for incident:", incidentId, err)
      } finally {
        this.isUpdatingIncident = false
      }
    },

    togglePause() {
      this.streamPaused = !this.streamPaused
    },

    async triggerReplay(pcapPath, speed = 1.0) {
      this.isReplaying = true
      this.replayStatus = "Starting replay..."
      try {
        const res = await api.startReplay(pcapPath, speed)
        this.replayStatus = res.message
      } catch (err) {
        this.replayStatus = `Error: ${err.message}`
      } finally {
        setTimeout(() => {
          this.isReplaying = false
        }, 3000)
      }
    },

    async clearAllData() {
      this.isPurging = true
      try {
        await api.resetDatabase()
        await this.initialize()
      } catch (err) {
        console.error("Failed to reset database:", err)
      } finally {
        this.isPurging = false
      }
    },
  },
})
