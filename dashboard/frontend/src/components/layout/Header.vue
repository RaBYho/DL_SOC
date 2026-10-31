<template>
  <header class="soc-header">
    <!-- Top Row on Mobile: Hamburger, Title, Threat & Language -->
    <div class="header-top-bar">
      <!-- Hamburger Toggle on Mobile -->
      <button 
        class="mobile-menu-trigger" 
        @click="store.toggleMobileNav" 
        aria-label="Toggle navigation menu"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>

      <!-- App Title Group -->
      <div class="header-main-title">
        <h1>
          <span class="hdvr-badge">{{ store.appName }}</span>
          <span class="header-text">{{ store.t('header.title') }}</span>
          <small>{{ store.t('header.subtitle') }}</small>
        </h1>
      </div>

      <!-- Threat Level Indicator -->
      <div class="threat-pill" aria-label="Global threat level">
        <div class="threat-top">
          <span class="threat-label">{{ store.t('header.threatLevel') }}</span>
          <b :style="{ color: store.globalThreatLevel.color }">
            {{ store.globalThreatLevel.label }}
          </b>
        </div>
        <div class="threat-seg">
          <i 
            v-for="idx in [0, 1, 2]" 
            :key="idx" 
            :style="{ 
              background: idx <= store.globalThreatLevel.level 
                ? store.globalThreatLevel.color 
                : 'rgba(255, 255, 255, 0.1)' 
            }"
          ></i>
        </div>
      </div>
    </div>

    <!-- Live Stream / Replay Status Indicator -->
    <div class="stat-pill" aria-live="polite">
      <span 
        class="pulse-dot" 
        :class="{ 
          off: !store.wsConnected || store.isStreamPaused,
          err: !store.wsConnected 
        }"
      ></span>
      <div class="stat-meta">
        <b class="stat-title">{{ statusTitle }}</b>
        <span class="stat-subtitle">{{ statusSubtitle }}</span>
      </div>
    </div>

    <div class="header-spacer"></div>

    <!-- Controls & Tools (PCAP Replay & Time Range) -->
    <div class="header-tools">
      <!-- PCAP Select Dropdown -->
      <div class="select-wrapper">
        <svg class="select-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6">
          <path d="M4 4h12v12H4z" />
          <path d="M4 8h12M8 4v12" />
        </svg>
        <select 
          v-model="selectedPcap" 
          aria-label="PCAP file replay"
          :disabled="store.replayStatus.active"
        >
          <option value="">{{ store.t('header.allSensors') }}</option>
          <option 
            v-for="pcap in store.pcapFiles" 
            :key="pcap.filename" 
            :value="pcap.filename"
          >
            {{ pcap.filename }} ({{ pcap.size_mb }} MB)
          </option>
        </select>
      </div>

      <!-- Action Button (Play / Pause / Stop) -->
      <button 
        class="action-btn"
        :class="{ 'btn-running': store.replayStatus.active }" 
        @click="handleActionClick"
      >
        <svg v-if="!store.replayStatus.active && selectedPcap" viewBox="0 0 20 20" fill="currentColor">
          <polygon points="6 4 16 10 6 16 6 4" />
        </svg>
        <svg v-else-if="store.replayStatus.active" viewBox="0 0 20 20" fill="currentColor">
          <rect x="5" y="5" width="10" height="10" rx="1.5" />
        </svg>
        <svg v-else viewBox="0 0 20 20" fill="currentColor">
          <rect x="5" y="4" width="3.5" height="12" rx="1" />
          <rect x="11.5" y="4" width="3.5" height="12" rx="1" />
        </svg>
        <span>{{ actionButtonLabel }}</span>
      </button>

      <!-- Time Range Selector -->
      <div class="time-range-group" role="group" aria-label="Time range">
        <button 
          v-for="r in ['15m', '1h', '24h']" 
          :key="r"
          :class="{ active: store.activeTimeRange === r }"
          :aria-pressed="store.activeTimeRange === r"
          @click="changeRange(r)"
        >
          {{ r }}
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useSocStore } from '@/stores/socStore'

const store = useSocStore()
const selectedPcap = ref('')

const statusTitle = computed(() => {
  if (store.replayStatus.active) return store.t('header.pcapReplay')
  if (!store.wsConnected) return store.t('header.offline')
  return store.t('header.liveWs')
})

const statusSubtitle = computed(() => {
  if (store.replayStatus.active) {
    return `${store.replayStatus.pcap_name} (${(store.replayStatus.progress_pct || 0).toFixed(0)}%)`
  }
  if (!store.wsConnected) return store.t('header.reconnecting')
  return store.isStreamPaused ? store.t('header.streamPaused') : store.t('header.streamActive')
})

const actionButtonLabel = computed(() => {
  if (store.replayStatus.active) return store.t('header.stopReplay')
  if (selectedPcap.value) return store.t('header.runReplay')
  return store.isStreamPaused ? store.t('header.resume') : store.t('header.pause')
})

function handleActionClick() {
  if (store.replayStatus.active) {
    store.stopPcapReplay()
  } else if (selectedPcap.value) {
    store.startPcapReplay(selectedPcap.value)
  } else {
    store.toggleStreamPause()
  }
}

function changeRange(range) {
  if (store.activeTimeRange !== range) {
    store.loadDashboardData(range)
  }
}
</script>

<style scoped>
.soc-header {
  position: sticky;
  top: 0;
  z-index: 20;
  background: rgba(15, 16, 23, 0.92);
  backdrop-filter: blur(16px);
  padding: 14px 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px 18px;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.header-top-bar {
  display: flex;
  align-items: center;
  gap: 14px;
}

.mobile-menu-trigger {
  display: none;
  background: var(--panel2);
  border: 1px solid var(--line);
  color: var(--tx);
  width: 38px;
  height: 38px;
  border-radius: 9px;
  padding: 0;
  align-items: center;
  justify-content: center;
  flex: none;
  cursor: pointer;
}

.mobile-menu-trigger svg {
  width: 20px;
  height: 20px;
}

@media (max-width: 900px) {
  .mobile-menu-trigger {
    display: flex;
  }
  .soc-header {
    padding: 12px 16px;
  }
  .header-top-bar {
    width: 100%;
    justify-content: space-between;
  }
  .header-main-title h1 {
    font-size: 16px !important;
  }
  .header-main-title small {
    display: none !important;
  }
  .header-tools {
    width: 100%;
    justify-content: space-between;
  }
  .select-wrapper {
    flex: 1;
    min-width: 140px;
  }
  .select-wrapper select {
    width: 100%;
  }
  .stat-pill {
    display: none !important;
  }
}

.header-main-title h1 {
  font-size: 18px;
  margin: 0;
  font-weight: 800;
  letter-spacing: -0.3px;
  color: #fff;
  line-height: 1.15;
}

.header-main-title small {
  display: block;
  font-weight: 400;
  color: var(--mu);
  font-size: 12px;
  margin-top: 2px;
}

.hdvr-badge {
  display: inline-block;
  padding: 2px 7px;
  margin-right: 8px;
  border-radius: 6px;
  background: linear-gradient(135deg, rgba(88, 101, 242, 0.28), rgba(155, 92, 246, 0.28));
  border: 1px solid rgba(88, 101, 242, 0.45);
  color: #fff;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.8px;
  vertical-align: middle;
}

.stat-pill {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px;
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(28, 29, 43, 0.9) 0%, rgba(22, 23, 34, 0.9) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--ok);
  box-shadow: 0 0 0 0 var(--ok);
  animation: pulse-ring 1.8s infinite;
  flex: none;
}

.pulse-dot.off {
  background: var(--md);
  animation: none;
}

.pulse-dot.err {
  background: var(--cr);
  animation: none;
}

@keyframes pulse-ring {
  70% {
    box-shadow: 0 0 0 6px transparent;
  }
}

.stat-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.stat-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--tx);
}

.stat-subtitle {
  font-size: 10.5px;
  color: var(--mu);
}

.threat-pill {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 125px;
  padding: 5px 12px;
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(28, 29, 43, 0.9) 0%, rgba(22, 23, 34, 0.9) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.threat-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
}

.threat-label {
  color: var(--mu);
}

.threat-seg {
  display: flex;
  gap: 3px;
}

.threat-seg i {
  flex: 1;
  height: 4px;
  border-radius: 2px;
  transition: background 0.3s ease;
}

.header-spacer {
  flex: 1;
}

.header-tools {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.select-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.select-icon {
  position: absolute;
  left: 10px;
  width: 14px;
  height: 14px;
  color: var(--mu);
  pointer-events: none;
}

select {
  font: inherit;
  color: var(--tx);
  background: var(--panel2);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 7px 12px 7px 30px;
  font-size: 12.5px;
  outline: none;
  cursor: pointer;
  min-height: 38px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  font: inherit;
  background: linear-gradient(135deg, var(--ac), var(--ac2));
  border: 0;
  color: #fff;
  font-weight: 600;
  font-size: 12.5px;
  padding: 8px 14px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 4px 14px rgba(88, 101, 242, 0.35);
  min-height: 38px;
}

.action-btn svg {
  width: 13px;
  height: 13px;
}

.action-btn:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

.action-btn.btn-running {
  background: linear-gradient(135deg, #d12f5f, #ff4d7e);
  box-shadow: 0 4px 14px rgba(255, 77, 126, 0.35);
}

.time-range-group {
  display: flex;
  background: var(--panel2);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 2px;
  min-height: 38px;
  align-items: center;
}

.time-range-group button {
  border: 0;
  background: none;
  padding: 5px 10px;
  border-radius: 7px;
  font-size: 12px;
  font-weight: 500;
  color: var(--mu);
  cursor: pointer;
}

.time-range-group button.active {
  background: var(--ac);
  color: #fff;
  font-weight: 600;
}
</style>
