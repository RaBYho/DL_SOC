<template>
  <header class="soc-header">
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
          {{ store.t('header.title') }}
          <small>{{ store.t('header.subtitle') }}</small>
        </h1>
      </div>
    </div>

    <!-- Live Stream / Replay Status Indicator -->
    <div class="stat-pill" aria-live="polite">
      <span 
        class="pulse-dot" 
        :class="{ 
          off: !store.wsConnected,
          err: !store.wsConnected 
        }"
      ></span>
      <div class="stat-meta">
        <b class="stat-title">{{ statusTitle }}</b>
        <span class="stat-subtitle">{{ statusSubtitle }}</span>
      </div>
    </div>

    <div class="header-spacer"></div>

    <!-- Controls & Tools (Time Range Selector) -->
    <div class="header-tools">
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
import { computed } from 'vue'
import { useSocStore } from '@/stores/socStore'

const store = useSocStore()

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
  return store.t('header.streamActive')
})

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

.header-main-title h1 {
  font-size: 17px;
  margin: 0;
  font-weight: 700;
  letter-spacing: -0.2px;
  color: #fff;
  line-height: 1.2;
}

.header-main-title small {
  display: block;
  font-weight: 400;
  color: var(--mu);
  font-size: 12px;
  margin-top: 2px;
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

.header-spacer {
  flex: 1;
}

.header-tools {
  display: flex;
  gap: 10px;
  align-items: center;
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
  padding: 5px 12px;
  border-radius: 7px;
  font-size: 12px;
  font-weight: 500;
  color: var(--mu);
  cursor: pointer;
  transition: all 0.15s ease;
}

.time-range-group button.active {
  background: var(--ac);
  color: #fff;
  font-weight: 600;
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
    font-size: 15px;
  }
  .header-main-title small {
    display: none;
  }
  .header-tools {
    width: 100%;
    justify-content: flex-end;
  }
  .stat-pill {
    display: none;
  }
}
</style>
