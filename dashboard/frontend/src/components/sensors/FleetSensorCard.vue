<template>
  <div 
    class="sensor-fleet-card"
    :class="{ 'is-online': sensor.status === 'Online', 'is-replay': sensor.type === 'replay' }"
  >
    <!-- 1. En-tête Principal de la Sonde -->
    <div class="sensor-header-row">
      <div class="sensor-identity">
        <div class="sensor-icon-box" :class="{ 'icon-replay': sensor.type === 'replay' }">
          <svg v-if="sensor.type === 'replay'" class="sensor-type-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10 2v7.31L4.69 19.3A2 2 0 0 0 6.36 22h11.28a2 2 0 0 0 1.67-2.7L14 9.31V2"/>
            <line x1="8.5" y1="2" x2="15.5" y2="2"/>
            <line x1="14" y1="9" x2="10" y2="9"/>
          </svg>
          <svg v-else class="sensor-type-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
            <rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>
            <line x1="6" y1="6" x2="6.01" y2="6"/>
            <line x1="6" y1="18" x2="6.01" y2="18"/>
          </svg>
        </div>

        <div class="sensor-title-group">
          <div class="title-line">
            <b class="sensor-name">{{ sensor.name }}</b>
            <span class="type-pill" :class="sensor.type">
              {{ sensor.type === 'replay' ? 'Simulateur PCAP Interne' : 'Agent Réseau Edge' }}
            </span>
          </div>

          <div class="id-line">
            <span class="sensor-id-pill" @click="copySensorId(sensor.id)" title="Cliquer pour copier l'ID">
              <code>ID: {{ sensor.id }}</code>
              <svg class="copy-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
              </svg>
            </span>
            <span v-if="copied" class="copied-feedback">Copié ✓</span>
          </div>
        </div>
      </div>

      <div class="sensor-actions-top">
        <span class="sensor-status-badge" :class="'status-' + sensor.status.toLowerCase()">
          <span class="status-pulse-dot"></span>
          {{ sensor.status_label || sensor.status }}
        </span>

        <button 
          type="button" 
          class="btn-view-alerts"
          @click="$emit('filterAlerts', sensor.id)"
          title="Consulter les alertes associées à cette sonde"
        >
          <svg class="action-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <span>Voir les alertes</span>
        </button>
      </div>
    </div>

    <!-- 2. Grille de Télémétrie Opérationnelle -->
    <div class="telemetry-grid">
      <div class="telemetry-tile">
        <div class="tile-header">
          <svg class="tile-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
            <line x1="6" y1="6" x2="6.01" y2="6"/>
          </svg>
          <span class="tile-label">Interface</span>
        </div>
        <b class="tile-val text-accent" :title="sensor.interface || (sensor.type === 'replay' ? 'Moteur PCAP' : 'eth0')">
          {{ sensor.interface || (sensor.type === 'replay' ? 'Moteur PCAP' : 'eth0') }}
        </b>
      </div>

      <div class="telemetry-tile">
        <div class="tile-header">
          <svg class="tile-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="20" x2="18" y2="10"/>
            <line x1="12" y1="20" x2="12" y2="4"/>
            <line x1="6" y1="20" x2="6" y2="14"/>
          </svg>
          <span class="tile-label">Flux Traités</span>
        </div>
        <b class="tile-val">
          {{ (sensor.total_flows || 0).toLocaleString() }}
        </b>
      </div>

      <div class="telemetry-tile">
        <div class="tile-header">
          <svg class="tile-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
          </svg>
          <span class="tile-label">Menaces Détectées</span>
        </div>
        <b class="tile-val" :class="(sensor.total_attacks || 0) > 0 ? 'text-danger' : 'text-success'">
          {{ (sensor.total_attacks || 0).toLocaleString() }}
        </b>
      </div>

      <div class="telemetry-tile">
        <div class="tile-header">
          <svg class="tile-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
          <span class="tile-label">Dernier Heartbeat</span>
        </div>
        <div class="tile-val-stack">
          <span class="tile-val-main">{{ sensor.last_seen || 'En attente' }}</span>
          <span v-if="sensor.elapsed_sec" class="tile-val-sub">
            ({{ formatElapsed(sensor.elapsed_sec) }})
          </span>
        </div>
      </div>
    </div>

    <!-- 3. Barre de Répartition et Santé du Trafic -->
    <div class="traffic-health-row">
      <div class="health-meta">
        <div class="health-labels">
          <span class="health-title">Répartition du trafic réseau</span>
          <span class="health-breakdown">
            <span class="benign-dot"></span> {{ (100 - attackPct).toFixed(1) }}% bénin
            <span class="sep">&middot;</span>
            <span class="attack-dot"></span> {{ attackPct.toFixed(1) }}% malveillant
          </span>
        </div>
        <span class="engine-tag">Moteur DNN-v4 + AE</span>
      </div>

      <div class="health-bar-track">
        <div class="bar-fill-attack" :style="{ width: `${attackPct}%` }" :title="`Attaques : ${attackPct}%`"></div>
        <div class="bar-fill-benign" :style="{ width: `${100 - attackPct}%` }" :title="`Trafic sain : ${100 - attackPct}%`"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  sensor: {
    type: Object,
    required: true
  }
})

defineEmits(['filterAlerts'])

const copied = ref(false)

const attackPct = computed(() => {
  if (!props.sensor.total_flows) return 0
  const pct = ((props.sensor.total_attacks || 0) / props.sensor.total_flows) * 100
  return Math.min(100, Math.max(0, Math.round(pct * 10) / 10))
})

const formatElapsed = (sec) => {
  if (!sec && sec !== 0) return ''
  if (sec < 60) return `il y a ${Math.round(sec)}s`
  if (sec < 3600) return `il y a ${Math.round(sec / 60)} min`
  return `il y a ${(sec / 3600).toFixed(1)} h`
}

const copySensorId = async (id) => {
  try {
    await navigator.clipboard.writeText(id)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch (e) {
    console.error('Clipboard copy error:', e)
  }
}
</script>

<style scoped>
.sensor-fleet-card {
  background: linear-gradient(180deg, rgba(24, 26, 40, 0.95) 0%, rgba(18, 19, 30, 0.95) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.25);
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.sensor-fleet-card:hover {
  border-color: rgba(255, 255, 255, 0.16);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
  transform: translateY(-1px);
}

.sensor-fleet-card.is-online { border-left: 3px solid #3ddc97; }
.sensor-fleet-card.is-replay { border-left: 3px solid #5865f2; }

/* 1. Header */
.sensor-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.sensor-identity {
  display: flex;
  align-items: center;
  gap: 14px;
}

.sensor-icon-box {
  width: 44px;
  height: 44px;
  border-radius: 11px;
  background: rgba(88, 101, 242, 0.12);
  border: 1px solid rgba(88, 101, 242, 0.25);
  color: #8fa0ff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sensor-icon-box.icon-replay {
  background: rgba(155, 92, 246, 0.12);
  border-color: rgba(155, 92, 246, 0.3);
  color: #c4b5fd;
}

.sensor-type-svg { width: 22px; height: 22px; }

.sensor-title-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title-line {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.sensor-name {
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.2px;
}

.type-pill {
  font-size: 11px;
  font-weight: 600;
  color: #8b8ea8;
  background: rgba(255, 255, 255, 0.05);
  padding: 2px 8px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.id-line {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sensor-id-pill {
  font-size: 11.5px;
  color: #c4ccff;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: rgba(255, 255, 255, 0.03);
  padding: 1px 7px;
  border-radius: 5px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  transition: all 0.2s;
}

.sensor-id-pill:hover {
  background: rgba(88, 101, 242, 0.15);
  border-color: #5865f2;
}

.copy-svg { width: 11px; height: 11px; color: #8fa0ff; }
.copied-feedback { font-size: 10.5px; color: #3ddc97; font-weight: 700; }

.sensor-actions-top {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sensor-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 6px;
}

.sensor-status-badge.status-online {
  background: rgba(61, 220, 151, 0.15);
  color: #3ddc97;
  border: 1px solid rgba(61, 220, 151, 0.35);
}

.sensor-status-badge.status-idle {
  background: rgba(255, 181, 71, 0.15);
  color: #ffb547;
  border: 1px solid rgba(255, 181, 71, 0.35);
}

.sensor-status-badge.status-offline {
  background: rgba(99, 107, 142, 0.2);
  color: #8b8ea8;
  border: 1px solid rgba(99, 107, 142, 0.3);
}

.status-pulse-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.status-online .status-pulse-dot {
  box-shadow: 0 0 6px #3ddc97;
  animation: pulse-dot 1.2s infinite;
}

@keyframes pulse-dot {
  0% { transform: scale(0.9); opacity: 0.7; }
  50% { transform: scale(1.4); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.7; }
}

.btn-view-alerts {
  height: 30px;
  padding: 0 12px;
  font-size: 11.5px;
  font-weight: 600;
  border-radius: 7px;
  background: rgba(88, 101, 242, 0.12);
  border: 1px solid rgba(88, 101, 242, 0.3);
  color: #8fa0ff;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.btn-view-alerts:hover {
  background: #5865f2;
  color: #ffffff;
  border-color: #5865f2;
}

.action-icon-svg { width: 12px; height: 12px; }

/* 2. Telemetry Grid */
.telemetry-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  background: #11121d;
  border: 1px solid #232538;
  border-radius: 10px;
  padding: 12px 14px;
}

@media (max-width: 900px) {
  .telemetry-grid { grid-template-columns: repeat(2, 1fr); }
}

.telemetry-tile {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.tile-header {
  display: flex;
  align-items: center;
  gap: 5px;
}

.tile-icon { width: 12px; height: 12px; color: #7982a9; }
.tile-label { font-size: 10.5px; color: #7982a9; text-transform: uppercase; font-weight: 600; }

.tile-val {
  font-size: 13.5px;
  font-weight: 700;
  color: #ffffff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tile-val-stack {
  display: flex;
  align-items: baseline;
  gap: 5px;
  overflow: hidden;
}

.tile-val-main { 
  font-size: 13.5px; 
  font-weight: 700; 
  color: #ffffff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tile-val-sub { font-size: 10.5px; color: #7982a9; }

.text-accent  { color: #8fa0ff !important; }
.text-danger  { color: #ff4d7e !important; }
.text-success { color: #3ddc97 !important; }

/* 3. Traffic Health */
.traffic-health-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.health-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
}

.health-labels {
  display: flex;
  align-items: center;
  gap: 12px;
}

.health-title { color: #8b8ea8; font-weight: 600; }
.health-breakdown { color: #c4ccff; }
.benign-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #3ddc97; margin-right: 3px; }
.attack-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #ff4d7e; margin-right: 3px; }
.sep { color: #4e5270; margin: 0 4px; }

.engine-tag {
  font-size: 10px;
  color: #7982a9;
  background: rgba(255, 255, 255, 0.04);
  padding: 1px 6px;
  border-radius: 4px;
}

.health-bar-track {
  height: 6px;
  background: #1a1c2a;
  border-radius: 999px;
  overflow: hidden;
  display: flex;
}

.bar-fill-attack {
  height: 100%;
  background: #ff4d7e;
  transition: width 0.3s;
}

.bar-fill-benign {
  height: 100%;
  background: #3ddc97;
  transition: width 0.3s;
}
</style>
