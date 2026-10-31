// Resilient WebSocket Client for DL_SOC Real-Time Stream

export class SocWebSocket {
  constructor(options = {}) {
    this.onMessage = options.onMessage || (() => {})
    this.onStatusChange = options.onStatusChange || (() => {})
    this.ws = null
    this.reconnectTimer = null
    this.reconnectInterval = 2000
    this.maxReconnectInterval = 10000
    this.isConnected = false
    this.isPaused = false
  }

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const url = `${protocol}//${host}/ws`

    try {
      this.ws = new WebSocket(url)

      this.ws.onopen = () => {
        this.isConnected = true
        this.reconnectInterval = 2000
        this.onStatusChange({ connected: true, status: 'connected' })
      }

      this.ws.onmessage = (event) => {
        if (this.isPaused) return
        try {
          const data = JSON.parse(event.data)
          this.onMessage(data)
        } catch (err) {
          console.warn('[WS Parse Error]:', err, event.data)
        }
      }

      this.ws.onclose = () => {
        this.isConnected = false
        this.onStatusChange({ connected: false, status: 'disconnected' })
        this.scheduleReconnect()
      }

      this.ws.onerror = (err) => {
        console.warn('[WS Error]:', err)
        this.ws.close()
      }
    } catch (err) {
      console.error('[WS Init Error]:', err)
      this.scheduleReconnect()
    }
  }

  scheduleReconnect() {
    if (this.reconnectTimer) return
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.reconnectInterval = Math.min(this.reconnectInterval * 1.5, this.maxReconnectInterval)
      this.connect()
    }, this.reconnectInterval)
  }

  pause() {
    this.isPaused = true
    this.onStatusChange({ connected: this.isConnected, paused: true, status: 'paused' })
  }

  resume() {
    this.isPaused = false
    this.onStatusChange({ connected: this.isConnected, paused: false, status: 'streaming' })
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.isConnected = false
  }
}
