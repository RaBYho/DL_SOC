<template>
  <div class="card c3 critical-card" :class="{ 'has-threat': alert }">
    <div v-if="alert" class="threat-alert-box">
      <div class="threat-badge-row">
        <span class="threat-pill-crit">
          <span class="dot-crit"></span>
          {{ store.t('banner.badge') }}
        </span>
        <small class="sensor-tag">{{ alert.sensor_id || 'sensor-01' }}</small>
      </div>

      <div class="threat-class-title">{{ alert.pred }}</div>
      
      <div class="mono threat-route">
        <span>{{ alert.src_ip }}</span>
        <svg class="arrow-icon" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-2.293-2.293a1 1 0 010-1.414z" clip-rule="evenodd" />
        </svg>
        <span>{{ alert.dst_ip }}:{{ alert.dst_port }}</span>
      </div>

      <div class="threat-stats-row">
        <span>{{ store.t('banner.confidence') }}: <b>{{ ((alert.confiance || 0.95) * 100).toFixed(1) }}%</b></span>
        <span v-if="alert.mse_ae">MSE: <b>{{ alert.mse_ae.toFixed(3) }}</b></span>
      </div>

      <button class="inspect-btn" @click="store.openFlowDrawer(alert)">
        <span>{{ store.t('banner.inspect') }}</span>
        <svg viewBox="0 0 20 20" fill="currentColor" style="width:14px; height:14px;">
          <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd" />
        </svg>
      </button>
    </div>

    <!-- Safe / No Critical Incidents -->
    <div v-else class="safe-state-box">
      <div class="shield-safe-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          <path d="M9 12l2 2 4-4" />
        </svg>
      </div>
      <b class="safe-title">{{ store.t('banner.safeTitle') }}</b>
      <p class="safe-desc">{{ store.t('banner.safeDesc') }}</p>
      <div class="safe-pill">
        <span class="dot-safe"></span>
        {{ store.t('banner.safePill') }}
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
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  overflow: hidden;
  border-radius: 16px;
  background: linear-gradient(145deg, #1d1b2e 0%, #171824 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.critical-card.has-threat {
  background: linear-gradient(145deg, rgba(255, 77, 126, 0.15) 0%, rgba(34, 35, 51, 0.95) 100%);
  border-color: rgba(255, 77, 126, 0.4);
  box-shadow: 0 0 24px rgba(255, 77, 126, 0.12);
}

.threat-alert-box {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.threat-badge-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.threat-pill-crit {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.6px;
  color: #fff;
  background: var(--cr);
  padding: 3px 8px;
  border-radius: 6px;
}

.dot-crit {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #fff;
  animation: pulse-crit 1.2s infinite;
}

@keyframes pulse-crit {
  50% { opacity: 0.3; }
}

.sensor-tag {
  font-size: 11px;
  color: var(--mu);
}

.threat-class-title {
  font-size: 20px;
  font-weight: 800;
  color: #fff;
  letter-spacing: -0.3px;
}

.threat-route {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--tx);
  background: var(--panel2);
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.arrow-icon {
  width: 14px;
  height: 14px;
  color: var(--cr);
  flex: none;
}

.threat-stats-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--mu);
}

.threat-stats-row b {
  color: var(--tx);
}

.inspect-btn {
  margin-top: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: linear-gradient(135deg, var(--cr), #d12f5f);
  color: #fff;
  font-size: 12.5px;
  font-weight: 700;
  border: 0;
  border-radius: 10px;
  padding: 9px 14px;
  cursor: pointer;
  transition: all 0.18s ease;
  box-shadow: 0 4px 14px rgba(255, 77, 126, 0.35);
}

.inspect-btn:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

/* Safe State */
.safe-state-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 8px 4px;
}

.shield-safe-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(61, 220, 151, 0.12);
  color: var(--ok);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
  border: 1px solid rgba(61, 220, 151, 0.25);
}

.shield-safe-icon svg {
  width: 24px;
  height: 24px;
}

.safe-title {
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 4px;
}

.safe-desc {
  font-size: 12px;
  color: var(--mu);
  margin: 0 0 12px;
  line-height: 1.4;
}

.safe-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--ok);
  background: rgba(61, 220, 151, 0.1);
  padding: 3px 10px;
  border-radius: 20px;
  border: 1px solid rgba(61, 220, 151, 0.2);
}

.dot-safe {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--ok);
}
</style>
