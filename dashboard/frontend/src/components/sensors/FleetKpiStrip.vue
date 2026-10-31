<template>
  <div class="fleet-kpis-strip">
    <div class="fleet-kpi-card">
      <div class="kpi-icon-wrap icon-blue">
        <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
          <rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>
          <line x1="6" y1="6" x2="6.01" y2="6"/>
          <line x1="6" y1="18" x2="6.01" y2="18"/>
        </svg>
      </div>
      <div class="kpi-content">
        <span class="kpi-card-label">Sondes Enregistrées</span>
        <div class="kpi-card-val-row">
          <b class="kpi-card-num">{{ sensorsCount }}</b>
          <span class="kpi-card-unit">source(s)</span>
        </div>
      </div>
    </div>

    <div class="fleet-kpi-card">
      <div class="kpi-icon-wrap icon-emerald">
        <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          <polyline points="9 12 11 14 15 10"/>
        </svg>
      </div>
      <div class="kpi-content">
        <span class="kpi-card-label">Sondes En Ligne (Direct)</span>
        <div class="kpi-card-val-row">
          <b class="kpi-card-num text-success">{{ sensorsOnline }}</b>
          <span class="kpi-card-unit">actives</span>
        </div>
      </div>
    </div>

    <div class="fleet-kpi-card">
      <div class="kpi-icon-wrap icon-indigo">
        <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="20" x2="18" y2="10"/>
          <line x1="12" y1="20" x2="12" y2="4"/>
          <line x1="6" y1="20" x2="6" y2="14"/>
        </svg>
      </div>
      <div class="kpi-content">
        <span class="kpi-card-label">Flux Transmis (Parc)</span>
        <div class="kpi-card-val-row">
          <b class="kpi-card-num">{{ totalFlows.toLocaleString() }}</b>
          <span class="kpi-card-unit">flux analysés</span>
        </div>
      </div>
    </div>

    <div class="fleet-kpi-card">
      <div class="kpi-icon-wrap icon-rose">
        <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
          <line x1="12" y1="9" x2="12" y2="13"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
      </div>
      <div class="kpi-content">
        <span class="kpi-card-label">Menaces Interceptées</span>
        <div class="kpi-card-val-row">
          <b class="kpi-card-num text-danger">{{ totalAttacks.toLocaleString() }}</b>
          <span class="kpi-card-unit">alertes</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  sensorsCount: {
    type: Number,
    default: 0
  },
  sensorsOnline: {
    type: Number,
    default: 0
  },
  totalFlows: {
    type: Number,
    default: 0
  },
  totalAttacks: {
    type: Number,
    default: 0
  }
})
</script>

<style scoped>
.fleet-kpis-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}

@media (max-width: 1024px) {
  .fleet-kpis-strip {
    grid-template-columns: repeat(2, 1fr);
  }
}

.fleet-kpi-card {
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

.fleet-kpi-card:hover {
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

.svg-icon {
  width: 22px;
  height: 22px;
}

.kpi-icon-wrap.icon-blue { background: rgba(88, 101, 242, 0.15); border: 1px solid rgba(88, 101, 242, 0.3); color: #8fa0ff; }
.kpi-icon-wrap.icon-emerald { background: rgba(61, 220, 151, 0.15); border: 1px solid rgba(61, 220, 151, 0.3); color: #3ddc97; }
.kpi-icon-wrap.icon-indigo { background: rgba(155, 92, 246, 0.15); border: 1px solid rgba(155, 92, 246, 0.3); color: #c4b5fd; }
.kpi-icon-wrap.icon-rose { background: rgba(255, 77, 126, 0.15); border: 1px solid rgba(255, 77, 126, 0.3); color: #ff85a5; }

.kpi-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.kpi-card-label {
  font-size: 11.5px;
  font-weight: 600;
  color: #8b8ea8;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.kpi-card-val-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.kpi-card-num {
  font-size: 22px;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: -0.5px;
  line-height: 1.1;
}

.kpi-card-unit {
  font-size: 11.5px;
  color: #7982a9;
}

.text-success { color: #3ddc97 !important; }
.text-danger  { color: #ff4d7e !important; }
</style>
