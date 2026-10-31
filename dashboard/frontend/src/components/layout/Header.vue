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

    <div class="header-spacer"></div>

    <div class="header-right-actions">
      <!-- Pastille de Santé Système (Plan 1 : Infrastructure & Diagnostic) -->
      <button 
        type="button" 
        class="stat-pill health-pill" 
        :class="'health-' + (store.systemHealth?.status || 'healthy').toLowerCase()"
        @click="store.toggleSystemDrawer"
        title="Consulter le diagnostic de santé système (infrastructure)"
      >
        <span class="health-dot"></span>
        <div class="stat-meta">
          <b class="stat-title">{{ healthTitle }}</b>
          <span class="stat-subtitle">{{ healthSubtitle }}</span>
        </div>
      </button>

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
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useSocStore } from '@/stores/socStore'

const store = useSocStore()

const healthTitle = computed(() => {
  const s = store.systemHealth?.status
  if (s === 'HEALTHY') return 'Système Nominal'
  if (s === 'DEGRADED') return 'Vigilance Système'
  return 'Incident Système'
})

const healthSubtitle = computed(() => {
  const issues = store.systemHealth?.issues?.length || 0
  if (issues > 0) return `${issues} anomalie(s)`
  return `${store.systemHealth?.score || 100}% santé`
})

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

.header-spacer {
  flex: 1;
}

.header-right-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.health-pill {
  cursor: pointer;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.health-pill:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
}

.health-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.health-healthy .health-dot {
  background: #3ddc97;
  box-shadow: 0 0 8px #3ddc97;
}

.health-degraded .health-dot {
  background: #ffb547;
  box-shadow: 0 0 8px #ffb547;
  animation: pulse-health 1.5s infinite;
}

.health-critical .health-dot {
  background: #ff4d7e;
  box-shadow: 0 0 8px #ff4d7e;
  animation: pulse-health 1s infinite;
}

@keyframes pulse-health {
  0% { transform: scale(0.9); opacity: 0.7; }
  50% { transform: scale(1.3); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.7; }
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
  .header-right-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.health-pill {
  cursor: pointer;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.health-pill:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
}

.health-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.health-healthy .health-dot {
  background: #3ddc97;
  box-shadow: 0 0 8px #3ddc97;
}

.health-degraded .health-dot {
  background: #ffb547;
  box-shadow: 0 0 8px #ffb547;
  animation: pulse-health 1.5s infinite;
}

.health-critical .health-dot {
  background: #ff4d7e;
  box-shadow: 0 0 8px #ff4d7e;
  animation: pulse-health 1s infinite;
}

@keyframes pulse-health {
  0% { transform: scale(0.9); opacity: 0.7; }
  50% { transform: scale(1.3); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.7; }
}

.stat-pill {
    display: none;
  }
}
</style>
