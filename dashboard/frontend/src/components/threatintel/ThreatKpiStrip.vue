<template>
  <div class="threat-kpis-strip">
    <!-- KPI 1 : Signatures Répertoriées -->
    <div class="threat-kpi-card">
      <div class="kpi-icon-wrap icon-blue">
        <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        </svg>
      </div>
      <div class="kpi-content">
        <span class="kpi-label">Profils Supervisés</span>
        <div class="kpi-val-row">
          <b class="kpi-num">{{ totalThreatsCount }}</b>
          <span class="kpi-unit">classes d'attaques</span>
        </div>
      </div>
    </div>

    <!-- KPI 2 : Alertes Actives SOC -->
    <div class="threat-kpi-card">
      <div class="kpi-icon-wrap" :class="activeAttacksTotal > 0 ? 'icon-rose' : 'icon-emerald'">
        <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
          <line x1="12" y1="9" x2="12" y2="13"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
      </div>
      <div class="kpi-content">
        <span class="kpi-label">Incidents dans le SOC</span>
        <div class="kpi-val-row">
          <b class="kpi-num" :class="activeAttacksTotal > 0 ? 'text-danger' : 'text-success'">
            {{ activeAttacksTotal.toLocaleString() }}
          </b>
          <span class="kpi-unit">flux confirmés</span>
        </div>
      </div>
    </div>

    <!-- KPI 3 : Couverture MITRE ATT&CK -->
    <div class="threat-kpi-card">
      <div class="kpi-icon-wrap icon-indigo">
        <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="7" height="7"/>
          <rect x="14" y="3" width="7" height="7"/>
          <rect x="14" y="14" width="7" height="7"/>
          <rect x="3" y="14" width="7" height="7"/>
        </svg>
      </div>
      <div class="kpi-content">
        <span class="kpi-label">Couverture MITRE</span>
        <div class="kpi-val-row">
          <b class="kpi-num text-accent">6</b>
          <span class="kpi-unit">tactiques ATT&amp;CK</span>
        </div>
      </div>
    </div>

    <!-- KPI 4 : Posture de Défense Globale -->
    <div class="threat-kpi-card">
      <div class="kpi-icon-wrap" :class="threatLevelClass">
        <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <polyline points="12 6 12 12 14 14"/>
        </svg>
      </div>
      <div class="kpi-content">
        <span class="kpi-label">Posture de Menace</span>
        <div class="kpi-val-row">
          <b class="kpi-num" :class="threatTextClass">{{ threatLevelLabel }}</b>
          <span class="kpi-unit">indice de risque</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  totalThreatsCount: {
    type: Number,
    default: 12
  },
  activeAttacksTotal: {
    type: Number,
    default: 0
  },
  globalThreatLevel: {
    type: Object,
    default: () => ({ level: 0, label: 'Normal' })
  }
})

const threatLevelLabel = computed(() => {
  return props.globalThreatLevel?.label || 'Normal'
})

const threatLevelClass = computed(() => {
  const lvl = props.globalThreatLevel?.level || 0
  if (lvl >= 2) return 'icon-rose'
  if (lvl === 1) return 'icon-amber'
  return 'icon-emerald'
})

const threatTextClass = computed(() => {
  const lvl = props.globalThreatLevel?.level || 0
  if (lvl >= 2) return 'text-danger'
  if (lvl === 1) return 'text-warning'
  return 'text-success'
})
</script>

<style scoped>
.threat-kpis-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 18px;
}

@media (max-width: 1024px) {
  .threat-kpis-strip { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 580px) {
  .threat-kpis-strip { grid-template-columns: 1fr; }
}

.threat-kpi-card {
  background: linear-gradient(180deg, rgba(26, 28, 44, 0.95) 0%, rgba(18, 19, 30, 0.95) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 16px 18px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.22);
  transition: transform 0.2s, border-color 0.2s;
}

.threat-kpi-card:hover {
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.18);
}

.kpi-icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.kpi-icon-wrap .svg-icon {
  width: 22px;
  height: 22px;
}

.kpi-icon-wrap.icon-blue    { background: rgba(88, 101, 242, 0.15); border: 1px solid rgba(88, 101, 242, 0.3); color: #8fa0ff; }
.kpi-icon-wrap.icon-emerald { background: rgba(61, 220, 151, 0.15); border: 1px solid rgba(61, 220, 151, 0.3); color: #3ddc97; }
.kpi-icon-wrap.icon-indigo  { background: rgba(155, 92, 246, 0.15); border: 1px solid rgba(155, 92, 246, 0.3); color: #c4b5fd; }
.kpi-icon-wrap.icon-amber   { background: rgba(255, 181, 71, 0.15); border: 1px solid rgba(255, 181, 71, 0.3); color: #ffb547; }
.kpi-icon-wrap.icon-rose    { background: rgba(255, 77, 126, 0.15); border: 1px solid rgba(255, 77, 126, 0.3); color: #ff85a5; }

.kpi-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.kpi-label {
  font-size: 11px;
  font-weight: 600;
  color: #8b8ea8;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.kpi-val-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.kpi-num {
  font-size: 20px;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: -0.5px;
  line-height: 1.1;
}

.kpi-unit {
  font-size: 11.5px;
  color: #7982a9;
}

.text-accent  { color: #8fa0ff !important; }
.text-success { color: #3ddc97 !important; }
.text-danger  { color: #ff4d7e !important; }
.text-warning { color: #ffb547 !important; }
</style>
