<template>
  <div class="card c3 critical-card" :class="{ 'has-threat': alert }">
    <!-- Consistent Card Header across all dashboard cards -->
    <div class="card-header-row">
      <div class="header-titles">
        <h2 class="card-title">{{ alert ? store.t('banner.titleThreat') : store.t('banner.titleSafe') }}</h2>
        <span class="card-subtitle">{{ alert ? store.t('banner.subThreat') : store.t('banner.subSafe') }}</span>
      </div>

      <!-- Pulse Status Indicator Badge -->
      <span class="status-indicator-pill" :class="alert ? 'pill-threat' : 'pill-safe'">
        <span class="pulse-dot"></span>
        {{ alert ? store.t('banner.badge') : store.t('banner.safePill') }}
      </span>
    </div>

    <!-- State 1: Active Critical Threat Alert -->
    <div v-if="alert" class="threat-content-box">
      <!-- Threat Classification & Engine Chip -->
      <div class="threat-header-band">
        <div class="threat-type-name">{{ alert.pred }}</div>
        <span class="threat-engine-tag">IA · XGBoost</span>
      </div>

      <!-- Network Vector Route: Attacker (SRC) -> Target (DST:PORT) -->
      <div class="network-route-card">
        <div class="route-node">
          <span class="node-role">Attaquant (SRC)</span>
          <span class="mono node-address" :title="alert.src_ip">{{ alert.src_ip }}</span>
        </div>
        <div class="route-arrow-cell">
          <svg class="arrow-svg" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-2.293-2.293a1 1 0 010-1.414z" clip-rule="evenodd" />
          </svg>
        </div>
        <div class="route-node right-node">
          <span class="node-role">Cible (DST:PORT)</span>
          <span class="mono node-address" :title="`${alert.dst_ip}:${alert.dst_port}`">
            {{ alert.dst_ip }}:{{ alert.dst_port }}
          </span>
        </div>
      </div>

      <!-- Telemetry Decision Metrics -->
      <div class="threat-metrics-strip">
        <div class="metric-cell">
          <span class="metric-key">{{ store.t('banner.confidence') }}</span>
          <b class="metric-val mono">{{ ((alert.confiance || 0.95) * 100).toFixed(1) }}%</b>
        </div>
        <div class="metric-cell" v-if="alert.mse_ae">
          <span class="metric-key">MSE AE</span>
          <b class="metric-val mono alert-crit">{{ alert.mse_ae.toFixed(3) }}</b>
        </div>
        <div class="metric-cell">
          <span class="metric-key">Sonde</span>
          <b class="metric-val mono">{{ alert.sensor_id || 'sensor-01' }}</b>
        </div>
      </div>

      <!-- Button-in-Button Inspect CTA -->
      <button 
        class="inspect-action-btn" 
        @click="store.openFlowDrawer(alert)"
        :aria-label="store.t('banner.inspect')"
      >
        <span class="btn-text">{{ store.t('banner.inspect') }}</span>
        <span class="btn-icon-wrapper">
          <svg viewBox="0 0 20 20" fill="currentColor" class="action-icon">
            <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd" />
          </svg>
        </span>
      </button>
    </div>

    <!-- State 2: Safe / Nominal State (Zero Active Critical Incidents) -->
    <div v-else class="safe-content-box">
      <!-- Shield Radar Halo with Fluid Breathing Motion -->
      <div class="safe-halo-wrapper">
        <div class="safe-shield-core">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="shield-svg">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            <path d="M9 12l2 2 4-4" />
          </svg>
        </div>
      </div>

      <div class="safe-text-stack">
        <h3 class="safe-headline">{{ store.t('banner.safeTitle') }}</h3>
        <p class="safe-body">{{ store.t('banner.safeDesc') }}</p>
      </div>

      <!-- Telemetry Health Check Strip -->
      <div class="safe-telemetry-strip">
        <div class="telemetry-chip">
          <span class="check-icon">✓</span>
          <span>Double Moteur IA</span>
        </div>
        <div class="telemetry-chip">
          <span class="check-icon">✓</span>
          <span>Flux Filtrés 100%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSocStore } from '@/stores/socStore'

const store = useSocStore()
const alert = computed(() => store.latestCriticalAlert)
</script>

<style scoped>
.critical-card {
  height: 330px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 16px 18px;
  position: relative;
  overflow: hidden;
  border-radius: 12px;
  background: linear-gradient(150deg, rgba(30, 32, 48, 0.95) 0%, rgba(18, 19, 28, 0.98) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.06);
  transition: transform 0.24s cubic-bezier(0.16, 1, 0.3, 1), 
              border-color 0.24s ease, 
              box-shadow 0.24s ease;
}

.critical-card:hover {
  border-color: rgba(255, 255, 255, 0.14);
}

.critical-card.has-threat {
  background: linear-gradient(150deg, rgba(255, 77, 126, 0.14) 0%, rgba(24, 25, 38, 0.98) 100%);
  border-color: rgba(255, 77, 126, 0.38);
  box-shadow: 0 4px 24px rgba(255, 77, 126, 0.12), inset 0 1px 1px rgba(255, 77, 126, 0.2);
}

/* Card Header matching dashboard design standards */
.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 6px;
  flex: none;
}

.header-titles {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.card-title {
  margin: 0;
  font-size: 14.5px;
  font-weight: 700;
  letter-spacing: -0.2px;
  color: #fff;
  line-height: 1.2;
}

.card-subtitle {
  font-size: 11px;
  font-weight: 400;
  color: var(--mu);
  line-height: 1.2;
}

/* Status Indicator Pill */
.status-indicator-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 9.5px;
  font-weight: 700;
  letter-spacing: 0.3px;
  padding: 2px 7px;
  border-radius: 12px;
  border: 1px solid;
  flex: none;
  line-height: 1.2;
}

.pill-safe {
  color: var(--ok);
  background: rgba(61, 220, 151, 0.12);
  border-color: rgba(61, 220, 151, 0.28);
}

.pill-threat {
  color: #fff;
  background: var(--cr);
  border-color: rgba(255, 255, 255, 0.2);
}

.pulse-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: currentColor;
}

.pill-threat .pulse-dot {
  animation: pulse-threat-dot 1.8s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse-threat-dot {
  0% { transform: scale(0.92); opacity: 0.85; }
  50% { transform: scale(1.22); opacity: 1; }
  100% { transform: scale(0.92); opacity: 0.85; }
}

/* --- STATE 1: THREAT CONTENT BOX --- */
.threat-content-box {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  flex: 1;
  min-height: 0;
  margin-top: 4px;
  gap: 8px;
}

.threat-header-band {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.threat-type-name {
  font-size: 19px;
  font-weight: 800;
  color: #fff;
  letter-spacing: -0.3px;
  line-height: 1.1;
}

.threat-engine-tag {
  font-size: 9.5px;
  font-weight: 700;
  color: var(--cr);
  background: rgba(255, 77, 126, 0.15);
  border: 1px solid rgba(255, 77, 126, 0.3);
  padding: 2px 6px;
  border-radius: 4px;
}

/* Network Hop Card */
.network-route-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(0, 0, 0, 0.28);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  padding: 8px 10px;
  gap: 8px;
  transition: border-color 0.2s ease;
}

.network-route-card:hover {
  border-color: rgba(255, 255, 255, 0.12);
}

.route-node {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.right-node {
  text-align: right;
}

.node-role {
  font-size: 9px;
  font-weight: 600;
  color: var(--mu);
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

.node-address {
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.route-arrow-cell {
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

.arrow-svg {
  width: 14px;
  height: 14px;
  color: var(--cr);
  animation: arrow-drift 2s cubic-bezier(0.4, 0, 0.2, 1) infinite;
  will-change: transform;
}

@keyframes arrow-drift {
  0%, 100% { transform: translateX(0); opacity: 0.7; }
  50% { transform: translateX(3px); opacity: 1; }
}

/* Decision Metrics Strip */
.threat-metrics-strip {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  padding: 5px 8px;
}

.metric-cell {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.metric-key {
  font-size: 9px;
  color: var(--mu);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.metric-val {
  font-size: 11.5px;
  color: #fff;
}

.alert-crit {
  color: var(--cr);
}

/* Button-in-Button Pattern with fluid spring hover */
.inspect-action-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, var(--cr) 0%, #d12f5f 100%);
  color: #fff;
  border: 0;
  border-radius: 8px;
  padding: 6px 8px 6px 14px;
  cursor: pointer;
  box-shadow: 0 3px 12px rgba(255, 77, 126, 0.35);
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), 
              box-shadow 0.2s cubic-bezier(0.16, 1, 0.3, 1), 
              filter 0.2s ease;
  flex: none;
  will-change: transform;
}

.inspect-action-btn:hover {
  filter: brightness(1.08);
  transform: translateY(-1.5px);
  box-shadow: 0 5px 18px rgba(255, 77, 126, 0.45);
}

.inspect-action-btn:active {
  transform: translateY(0) scale(0.98);
}

.inspect-action-btn:focus-visible {
  outline: 2px solid #fff;
  outline-offset: 2px;
}

.btn-text {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.1px;
}

.btn-icon-wrapper {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.22);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1);
  will-change: transform;
}

.inspect-action-btn:hover .btn-icon-wrapper {
  transform: translateX(3px);
}

.action-icon {
  width: 12px;
  height: 12px;
  color: #fff;
}

/* --- STATE 2: SAFE / NOMINAL CONTENT BOX --- */
.safe-content-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  flex: 1;
  min-height: 0;
  gap: 12px;
  padding: 6px 0;
}

/* Soft breathing animation without reflow */
.safe-halo-wrapper {
  width: 54px;
  height: 54px;
  border-radius: 50%;
  background: rgba(61, 220, 151, 0.08);
  border: 1px solid rgba(61, 220, 151, 0.22);
  box-shadow: 0 0 24px rgba(61, 220, 151, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: shield-breathing 4s cubic-bezier(0.4, 0, 0.2, 1) infinite;
  will-change: transform, box-shadow;
}

@keyframes shield-breathing {
  0%, 100% { 
    transform: translateY(0); 
    box-shadow: 0 0 20px rgba(61, 220, 151, 0.12); 
  }
  50% { 
    transform: translateY(-2px); 
    box-shadow: 0 0 28px rgba(61, 220, 151, 0.22); 
  }
}

.safe-shield-core {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: rgba(61, 220, 151, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
}

.shield-svg {
  width: 20px;
  height: 20px;
  color: var(--ok);
}

.safe-text-stack {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.safe-headline {
  margin: 0;
  font-size: 14.5px;
  font-weight: 700;
  color: #fff;
  letter-spacing: -0.2px;
}

.safe-body {
  margin: 0;
  font-size: 11.5px;
  color: var(--mu);
  line-height: 1.4;
  max-width: 250px;
}

.safe-telemetry-strip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}

.telemetry-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  font-weight: 600;
  color: var(--ok);
  background: rgba(61, 220, 151, 0.09);
  padding: 2px 8px;
  border-radius: 12px;
  border: 1px solid rgba(61, 220, 151, 0.2);
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), 
              background-color 0.2s ease;
}

.telemetry-chip:hover {
  transform: translateY(-1px);
  background: rgba(61, 220, 151, 0.15);
}

.check-icon {
  font-size: 9px;
  font-weight: 800;
}

@media (max-width: 768px) {
  .critical-card {
    height: auto;
    min-height: auto;
    padding: 14px 16px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .safe-halo-wrapper,
  .arrow-svg,
  .pulse-dot {
    animation: none !important;
  }
  .inspect-action-btn,
  .btn-icon-wrapper,
  .critical-card {
    transition: none !important;
  }
}
</style>
