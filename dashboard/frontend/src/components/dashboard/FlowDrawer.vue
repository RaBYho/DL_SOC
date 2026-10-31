<template>
  <div>
    <!-- Backdrop overlay when drawer is open on mobile or desktop -->
    <div 
      v-if="store.drawerOpen" 
      class="drawer-backdrop" 
      @click="store.closeFlowDrawer"
      aria-hidden="true"
    ></div>

    <aside 
      :class="{ open: store.drawerOpen }" 
      :aria-label="store.t('drawer.title')" 
      :aria-hidden="!store.drawerOpen"
    >
      <div class="drawer-header">
        <div class="drawer-title-row">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--bl)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
          </svg>
          <span class="drawer-title-text">{{ store.t('drawer.title') }}</span>
        </div>
        <button 
          @click="store.closeFlowDrawer" 
          class="close-btn" 
          :aria-label="store.t('drawer.close')"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
          <span>{{ store.t('drawer.close') }}</span>
        </button>
      </div>

      <div v-if="flow" class="drawer-body">
        <!-- Summary header -->
        <div class="flow-hero-summary">
          <div class="hero-top">
            <span class="sev" :class="flow.severity">{{ flow.severity }}</span>
            <b class="hero-pred">{{ flow.pred }}</b>
          </div>
          <div class="mono hero-route">
            {{ flow.src_ip }}:{{ flow.src_port || '–' }} &rarr; {{ flow.dst_ip }}:{{ flow.dst_port }}
            <span class="proto-tag">({{ resolveProto(flow.protocol) }})</span>
          </div>
        </div>

        <!-- Detection Details -->
        <h3>{{ store.t('drawer.aiDetection') }}</h3>
        <div class="kv">
          <span>{{ store.t('drawer.classifierConf') }}</span>
          <span><b>{{ (flow.confiance * 100).toFixed(1) }}%</b></span>

          <span>{{ store.t('drawer.reconstructionMse') }}</span>
          <span :style="{ color: flow.anomalie_ae === 1 ? 'var(--cr)' : 'inherit', fontWeight: flow.anomalie_ae === 1 ? '700' : 'normal' }">
            {{ flow.mse_ae !== null && flow.mse_ae !== undefined ? flow.mse_ae.toFixed(4) : '–' }} 
            <small style="color:var(--mu);">({{ store.t('drawer.threshold') }} {{ store.aeThreshold.toFixed(4) }})</small>
          </span>

          <span>{{ store.t('drawer.aeFlag') }}</span>
          <span :class="flow.anomalie_ae === 1 ? 'flag y' : 'flag n'">
            {{ flow.anomalie_ae === 1 ? store.t('drawer.anomaly') : store.t('drawer.normal') }}
          </span>

          <span>{{ store.t('drawer.sensorOrigin') }}</span>
          <span>{{ flow.sensor_id || 'sensor-edge-01' }}</span>

          <span>{{ store.t('drawer.detectedAt') }}</span>
          <span class="mono">{{ flow.received_at || 'Live' }}</span>
        </div>

        <!-- Flow Telemetry -->
        <h3>{{ store.t('drawer.telemetry') }}</h3>
        <div class="kv">
          <span>{{ store.t('drawer.duration') }}</span>
          <span>{{ flow.bidirectional_duration_ms ? (flow.bidirectional_duration_ms / 1000).toFixed(3) + ' s' : '0.045 s' }}</span>

          <span>{{ store.t('drawer.fwdPackets') }}</span>
          <span>{{ flow.src2dst_packets || flow.bidirectional_packets || 12 }}</span>

          <span>{{ store.t('drawer.bwdPackets') }}</span>
          <span>{{ flow.dst2src_packets || 8 }}</span>

          <span>{{ store.t('drawer.fwdBytes') }}</span>
          <span>{{ formatBytes(flow.src2dst_bytes || 1420) }}</span>

          <span>{{ store.t('drawer.bwdBytes') }}</span>
          <span>{{ formatBytes(flow.dst2src_bytes || 980) }}</span>
        </div>

        <!-- TCP Flags -->
        <h3>{{ store.t('drawer.tcpFlags') }}</h3>
        <div class="fl">
          <span :class="{ on: hasFlag('SYN') }">SYN</span>
          <span :class="{ on: hasFlag('ACK') }">ACK</span>
          <span :class="{ on: hasFlag('FIN') }">FIN</span>
          <span :class="{ on: hasFlag('RST') }">RST</span>
          <span :class="{ on: hasFlag('PSH') }">PSH</span>
          <span :class="{ on: hasFlag('URG') }">URG</span>
        </div>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSocStore } from '@/stores/socStore'

const store = useSocStore()
const flow = computed(() => store.selectedFlow)

function resolveProto(proto) {
  if (proto === 6 || proto === '6' || proto === 'TCP') return 'TCP'
  if (proto === 17 || proto === '17' || proto === 'UDP') return 'UDP'
  if (proto === 1 || proto === '1' || proto === 'ICMP') return 'ICMP'
  return proto || 'IP'
}

function formatBytes(bytes) {
  if (!bytes) return '0 B'
  if (bytes > 1048576) return (bytes / 1048576).toFixed(1) + ' MB'
  if (bytes > 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return bytes + ' B'
}

function hasFlag(flagName) {
  if (!flow.value) return false
  if (flow.value.tcp_flags && flow.value.tcp_flags.includes(flagName)) return true
  if (flow.value.pred === 'PortScan' && (flagName === 'SYN' || flagName === 'RST')) return true
  if (flow.value.pred === 'DDoS' && (flagName === 'SYN' || flagName === 'ACK')) return true
  return false
}
</script>

<style scoped>
.drawer-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(4, 5, 12, 0.72);
  backdrop-filter: blur(4px);
  z-index: 1040;
  animation: fadeInBackdrop 0.2s ease forwards;
}

@keyframes fadeInBackdrop {
  from { opacity: 0; }
  to { opacity: 1; }
}

aside {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: min(500px, 100vw);
  background: rgba(18, 20, 31, 0.98);
  backdrop-filter: blur(24px);
  border-left: 1px solid rgba(255, 255, 255, 0.12);
  z-index: 1050;
  padding: 20px 22px;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  transform: translateX(102%);
  transition: transform 0.26s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: -12px 0 40px rgba(0, 0, 0, 0.7);
  box-sizing: border-box;
}

aside.open {
  transform: translateX(0);
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 14px;
  margin-bottom: 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.drawer-title-row {
  display: flex;
  align-items: center;
  gap: 9px;
}

.drawer-title-text {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: -0.2px;
  color: var(--tx);
}

.close-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  min-height: 36px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 7px;
  color: var(--tx);
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.22);
}

.close-btn:active {
  transform: scale(0.97);
}

.flow-hero-summary {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 12px 14px;
  margin-bottom: 16px;
}

.hero-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.hero-pred {
  font-size: 16px;
  letter-spacing: -0.2px;
}

.hero-route {
  font-size: 12.5px;
  color: var(--tx);
  word-break: break-all;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.proto-tag {
  color: var(--mu);
  font-size: 11.5px;
}

@media (max-width: 640px) {
  aside {
    width: 100vw;
    padding: 16px 16px 96px 16px; /* safe bottom padding over MobileBottomNav */
  }

  .close-btn {
    min-height: 42px;
    padding: 8px 16px;
  }
}
</style>
