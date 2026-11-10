/**
 * Real-time WebSocket service with auto-reconnect and heartbeat pinging.
 */

class WebSocketClient {
  constructor() {
    this.ws = null
    this.listeners = new Map()
    this.reconnectAttempts = 0
    this.maxReconnectDelay = 10000
    this.pingInterval = null
    this.isConnected = false
  }

  connect() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
    const wsUrl = `${protocol}//${window.location.host}/ws`

    try {
      this.ws = new WebSocket(wsUrl)
    } catch (err) {
      this._scheduleReconnect()
      return
    }

    this.ws.onopen = () => {
      this.isConnected = true
      this.reconnectAttempts = 0
      this._dispatch("connection_status", { connected: true })
      this._startPing()
    }

    this.ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        if (payload.type === "pong") return
        this._dispatch(payload.type, payload.data)
        this._dispatch("*", payload)
      } catch (err) {
        // Ignore unparseable frames
      }
    }

    this.ws.onclose = () => {
      this.isConnected = false
      this._stopPing()
      this._dispatch("connection_status", { connected: false })
      this._scheduleReconnect()
    }

    this.ws.onerror = () => {
      if (this.ws) this.ws.close()
    }
  }

  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set())
    }
    this.listeners.get(eventType).add(callback)
    return () => this.listeners.get(eventType)?.delete(callback)
  }

  _dispatch(eventType, data) {
    const handlers = this.listeners.get(eventType)
    if (handlers) {
      handlers.forEach((cb) => {
        try {
          cb(data)
        } catch (e) {
          console.error(`WebSocket listener error for ${eventType}:`, e)
        }
      })
    }
  }

  _startPing() {
    this._stopPing()
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send("ping")
      }
    }, 15000)
  }

  _stopPing() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }
  }

  _scheduleReconnect() {
    const delay = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), this.maxReconnectDelay)
    this.reconnectAttempts++
    setTimeout(() => {
      this.connect()
    }, delay)
  }
}

export const wsClient = new WebSocketClient()
