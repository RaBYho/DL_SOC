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
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--ac)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
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
        <!-- Hero summary banner -->
        <div class="flow-hero-summary">
          <div class="hero-top">
            <span class="sev" :class="flow.severity">{{ flow.severity }}</span>
            <b class="hero-pred">{{ flow.classification || flow.pred }}</b>
            <span v-if="flowVerdict" class="verdict-mini-badge" :class="verdictBadgeClass">
              {{ verdictBadgeText }}
            </span>
          </div>
          <div class="mono hero-route">
            {{ flow.src_ip }}:{{ flow.src_port || '–' }} &rarr; {{ flow.dst_ip }}:{{ flow.dst_port }}
            <span class="proto-tag">({{ resolveProto(flow.protocol) }})</span>
          </div>
        </div>

        <!-- 3-Tab Navigation Bar -->
        <div class="drawer-nav-tabs">
          <button 
            type="button" 
            class="tab-btn" 
            :class="{ active: activeTab === 'telemetry' }"
            @click="activeTab = 'telemetry'"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
            <span>Télémétrie</span>
          </button>

          <button 
            type="button" 
            class="tab-btn" 
            :class="{ active: activeTab === 'qualification' }"
            @click="activeTab = 'qualification'"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>
            <span>Triage Active Learning</span>
          </button>

          <button 
            type="button" 
            class="tab-btn" 
            :class="{ active: activeTab === 'ai' }"
            @click="activeTab = 'ai'"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a4 4 0 0 0-4 4v1a4 4 0 0 0-3 3.87V13a4 4 0 0 0 3 3.87V18a4 4 0 0 0 4 4h0a4 4 0 0 0 4-4v-1.13A4 4 0 0 0 19 13v-2.13A4 4 0 0 0 16 7V6a4 4 0 0 0-4-4z"/><line x1="12" y1="2" x2="12" y2="22"/></svg>
            <span>Assistant IA</span>
          </button>
        </div>

        <!-- Tab 1: Telemetry & Network Details -->
        <div v-show="activeTab === 'telemetry'" class="tab-pane">
          <!-- Detection Details -->
          <h3>{{ store.t('drawer.aiDetection') }}</h3>
          <div class="kv">
            <span>{{ store.t('drawer.classifierConf') }}</span>
            <span><b>{{ ((flow.confiance !== undefined ? flow.confiance : (flow.confidence ? flow.confidence / 100 : 0.9)) * 100).toFixed(1) }}%</b></span>

            <span>{{ store.t('drawer.reconstructionMse') }}</span>
            <span :style="{ color: (flow.anomalie_ae === 1 || flow.is_anomaly) ? 'var(--cr)' : 'inherit', fontWeight: (flow.anomalie_ae === 1 || flow.is_anomaly) ? '700' : 'normal' }">
              {{ flow.mse_ae !== null && flow.mse_ae !== undefined ? Number(flow.mse_ae).toFixed(4) : '–' }} 
              <small style="color:var(--mu);">({{ store.t('drawer.threshold') }} {{ Number(store.aeThreshold).toFixed(4) }})</small>
            </span>

            <span>{{ store.t('drawer.aeFlag') }}</span>
            <span :class="(flow.anomalie_ae === 1 || flow.is_anomaly) ? 'flag y' : 'flag n'">
              {{ (flow.anomalie_ae === 1 || flow.is_anomaly) ? store.t('drawer.anomaly') : store.t('drawer.normal') }}
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

        <!-- Tab 2: Qualification Form (Active Learning) -->
        <div v-show="activeTab === 'qualification'" class="tab-pane">
          <IncidentQualificationForm :flow="flow" />
        </div>

        <!-- Tab 3: AI Assistant & Forensic Diagnosis -->
        <div v-show="activeTab === 'ai'" class="tab-pane">
          <IncidentAiAssistant :flow="flow" />
        </div>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useSocStore } from '@/stores/socStore'
import IncidentQualificationForm from './IncidentQualificationForm.vue'
import IncidentAiAssistant from './IncidentAiAssistant.vue'

const store = useSocStore()
const flow = computed(() => store.selectedFlow)
const activeTab = ref('telemetry')

const incidentId = computed(() => {
  return flow.value ? (flow.value.id || `${flow.value.src_ip}-${flow.value.dst_port}-${flow.value.received_at}`) : ''
})

const flowVerdict = computed(() => {
  return store.incidentFeedbackMap[incidentId.value] || null
})

const verdictBadgeClass = computed(() => {
  if (!flowVerdict.value) return ''
  const v = flowVerdict.value.human_verdict
  if (v === 'FALSE_POSITIVE') return 'badge-fp'
  if (v === 'KNOWN_ATTACK') return 'badge-reclass'
  if (v === 'CONFIRMED_ZERODAY') return 'badge-zd'
  return ''
})

const verdictBadgeText = computed(() => {
  if (!flowVerdict.value) return ''
  const v = flowVerdict.value.human_verdict
  if (v === 'FALSE_POSITIVE') return 'Faux Positif'
  if (v === 'KNOWN_ATTACK') return `Reclassifié : ${flowVerdict.value.corrected_attack_type}`
  if (v === 'CONFIRMED_ZERODAY') return `Zero-Day : ${flowVerdict.value.corrected_attack_type}`
  return v
})

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
  width: min(540px, 100vw);
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
  margin-bottom: 14px;
}

.hero-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  flex-wrap: wrap;
}

.hero-pred {
  font-size: 16px;
  letter-spacing: -0.2px;
}

.verdict-mini-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 12px;
}

.badge-fp {
  background: rgba(61, 220, 151, 0.15);
  color: var(--ok);
  border: 1px solid rgba(61, 220, 151, 0.3);
}

.badge-reclass {
  background: rgba(255, 181, 71, 0.15);
  color: var(--md);
  border: 1px solid rgba(255, 181, 71, 0.3);
}

.badge-zd {
  background: rgba(178, 102, 255, 0.15);
  color: var(--zd);
  border: 1px solid rgba(178, 102, 255, 0.3);
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

/* Tabs Navigation */
.drawer-nav-tabs {
  display: flex;
  gap: 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding-bottom: 8px;
  margin-bottom: 14px;
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 12px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  color: var(--mu);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
}

.tab-btn:hover {
  color: var(--tx);
  background: rgba(255, 255, 255, 0.04);
}

.tab-btn.active {
  color: var(--tx);
  background: rgba(88, 101, 242, 0.15);
  border-color: rgba(88, 101, 242, 0.3);
}

.tab-pane {
  display: flex;
  flex-direction: column;
}

@media (max-width: 640px) {
  aside {
    width: 100vw;
    padding: 16px 16px 96px 16px;
  }

  .close-btn {
    min-height: 42px;
    padding: 8px 16px;
  }
}
</style>
