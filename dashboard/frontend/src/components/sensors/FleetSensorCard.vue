<template>
  <div 
    class="sensor-fleet-card"
    :class="{ 'is-online': sensor.status === 'Online', 'is-replay': sensor.type === 'replay' }"
  >
    <!-- En-tête de la sonde -->
    <div class="sensor-card-top">
      <div class="sensor-badge-icon" :class="{ 'icon-replay': sensor.type === 'replay' }">
        <svg v-if="sensor.type === 'replay'" class="sensor-svg-type" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M10 2v7.31L4.69 19.3A2 2 0 0 0 6.36 22h11.28a2 2 0 0 0 1.67-2.7L14 9.31V2"/>
          <line x1="8.5" y1="2" x2="15.5" y2="2"/>
          <line x1="14" y1="9" x2="10" y2="9"/>
        </svg>
        <svg v-else class="sensor-svg-type" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
          <rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>
          <line x1="6" y1="6" x2="6.01" y2="6"/>
          <line x1="6" y1="18" x2="6.01" y2="18"/>
        </svg>
      </div>

      <div class="sensor-headline">
        <div class="sensor-title-row">
          <b class="sensor-title">{{ sensor.name }}</b>
          <span class="sensor-status-tag" :class="'tag-' + sensor.status.toLowerCase()">
            <span class="status-indicator-dot"></span>
            {{ sensor.status_label || sensor.status }}
          </span>
        </div>

        <div class="sensor-ids-row">
          <span class="sensor-id-pill" @click="copySensorId(sensor.id)" title="Cliquez pour copier l'identifiant">
            ID: <code>{{ sensor.id }}</code>
            <svg class="copy-small-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
            </svg>
          </span>
          <span class="type-pill">
            {{ sensor.type === 'replay' ? 'Simulateur PCAP Interne' : 'Agent Edge Distant' }}
          </span>
        </div>
      </div>
    </div>

    <!-- Télémétrie Réseau -->
    <div class="sensor-telemetry-box">
      <div class="telemetry-item">
        <div class="telemetry-lbl-row">
          <svg class="telemetry-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
            <line x1="6" y1="6" x2="6.01" y2="6"/>
          </svg>
          <span class="telemetry-lbl">Interface d'écoute</span>
        </div>
        <b class="telemetry-val">
          <span class="eth-bullet"></span>
          {{ sensor.interface || (sensor.type === 'replay' ? 'Moteur PCAP' : 'eth0') }}
        </b>
      </div>

      <div class="telemetry-item">
        <div class="telemetry-lbl-row">
          <svg class="telemetry-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="20" x2="18" y2="10"/>
            <line x1="12" y1="20" x2="12" y2="4"/>
            <line x1="6" y1="20" x2="6" y2="14"/>
          </svg>
          <span class="telemetry-lbl">Flux analysés</span>
        </div>
        <b class="telemetry-val">{{ (sensor.total_flows || 0).toLocaleString() }}</b>
      </div>

      <div class="telemetry-item">
        <div class="telemetry-lbl-row">
          <svg class="telemetry-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
          </svg>
          <span class="telemetry-lbl">Attaques bloquées</span>
        </div>
        <b class="telemetry-val" :class="{ 'text-danger': (sensor.total_attacks || 0) > 0 }">
          {{ (sensor.total_attacks || 0).toLocaleString() }}
        </b>
      </div>

      <div class="telemetry-item">
        <div class="telemetry-lbl-row">
          <svg class="telemetry-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
          <span class="telemetry-lbl">Dernier Heartbeat</span>
        </div>
        <span class="telemetry-val text-muted">
          {{ sensor.last_seen || 'En attente' }}
          <span v-if="sensor.elapsed_sec" class="elapsed-badge">({{ formatElapsed(sensor.elapsed_sec) }})</span>
        </span>
      </div>
    </div>

    <!-- Jauge de Ratio -->
    <div class="sensor-threat-ratio">
      <div class="ratio-labels">
        <span>Répartition du trafic</span>
        <b>{{ attackPct }}% malveillant</b>
      </div>
      <div class="threat-ratio-bar">
        <div class="ratio-fill-danger" :style="{ width: `${attackPct}%` }"></div>
        <div class="ratio-fill-benign" :style="{ width: `${100 - attackPct}%` }"></div>
      </div>
    </div>

    <!-- Pied de carte -->
    <div class="sensor-card-footer">
      <div class="sensor-protocol-tag">
        <svg class="proto-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
        </svg>
        <span>Moteur : Scorer IA v4 + AE</span>
      </div>

      <button 
        type="button" 
        class="btn-sensor-action"
        @click="$emit('filterAlerts', sensor.id)"
        title="Voir toutes les alertes de cette sonde dans la table d'incidents"
      >
        <svg class="action-btn-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <span>Voir les alertes</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  sensor: {
    type: Object,
    required: true
  }
})

defineEmits(['filterAlerts'])

const attackPct = computed(() => {
  if (!props.sensor.total_flows) return 0
  const pct = ((props.sensor.total_attacks || 0) / props.sensor.total_flows) * 100
  return Math.min(100, Math.max(0, Math.round(pct * 10) / 10))
})

const formatElapsed = (sec) => {
  if (!sec && sec !== 0) return ''
  if (sec < 60) return `${Math.round(sec)}s`
  if (sec < 3600) return `${Math.round(sec / 60)} min`
  return `${(sec / 3600).toFixed(1)} h`
}

const copySensorId = async (id) => {
  try {
    await navigator.clipboard.writeText(id)
  } catch (e) {
    console.error('Clipboard copy error:', e)
  }
}
</script>

<style scoped>
.sensor-fleet-card {
  background: linear-gradient(180deg, rgba(22, 24, 38, 0.95) 0%, rgba(16, 17, 28, 0.95) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 16px 18px;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.sensor-fleet-card:hover {
  border-color: rgba(255, 255, 255, 0.18);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  transform: translateY(-1px);
}

.sensor-fleet-card.is-online { border-left: 3px solid #3ddc97; }
.sensor-fleet-card.is-replay { border-left: 3px solid #5865f2; }

.sensor-card-top {
  display: flex;
  align-items: center;
  gap: 14px;
}

.sensor-badge-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  background: #1b1d2e;
  border: 1px solid #2e314a;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8fa0ff;
  flex-shrink: 0;
}

.sensor-badge-icon.icon-replay {
  color: #c4b5fd;
  border-color: rgba(155, 92, 246, 0.3);
  background: rgba(155, 92, 246, 0.1);
}

.sensor-svg-type { width: 22px; height: 22px; }

.sensor-headline {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sensor-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sensor-title { font-size: 15px; color: #ffffff; }

.sensor-status-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 6px;
}

.sensor-status-tag.tag-online {
  background: rgba(61, 220, 151, 0.15);
  color: #3ddc97;
  border: 1px solid rgba(61, 220, 151, 0.35);
}

.sensor-status-tag.tag-idle {
  background: rgba(255, 181, 71, 0.15);
  color: #ffb547;
  border: 1px solid rgba(255, 181, 71, 0.35);
}

.sensor-status-tag.tag-offline {
  background: rgba(99, 107, 142, 0.2);
  color: #8b8ea8;
  border: 1px solid rgba(99, 107, 142, 0.3);
}

.status-indicator-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.tag-online .status-indicator-dot {
  box-shadow: 0 0 6px #3ddc97;
  animation: pulse-dot 1.2s infinite;
}

@keyframes pulse-dot {
  0% { transform: scale(0.9); opacity: 0.7; }
  50% { transform: scale(1.4); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.7; }
}

.sensor-ids-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 11.5px;
}

.sensor-id-pill {
  color: #c4ccff;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.04);
  padding: 2px 8px;
  border-radius: 5px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: all 0.2s;
}

.sensor-id-pill:hover {
  background: rgba(88, 101, 242, 0.2);
  border-color: #5865f2;
}

.copy-small-svg { width: 12px; height: 12px; color: #8fa0ff; }
.type-pill { font-size: 11px; color: #7982a9; }

.sensor-telemetry-box {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  background: #11121d;
  border: 1px solid #232538;
  border-radius: 9px;
  padding: 10px 14px;
}

@media (max-width: 900px) {
  .sensor-telemetry-box { grid-template-columns: repeat(2, 1fr); }
}

.telemetry-item { display: flex; flex-direction: column; gap: 3px; }
.telemetry-lbl-row { display: flex; align-items: center; gap: 5px; }
.telemetry-icon { width: 12px; height: 12px; color: #7982a9; }
.telemetry-lbl { font-size: 10.5px; color: #7982a9; text-transform: uppercase; }

.telemetry-val {
  font-size: 13px;
  font-weight: 700;
  color: #ffffff;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.eth-bullet {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #5865f2;
}

.elapsed-badge { font-size: 10.5px; color: #8b8ea8; font-weight: normal; }

.sensor-threat-ratio { display: flex; flex-direction: column; gap: 4px; }
.ratio-labels { display: flex; justify-content: space-between; font-size: 11px; color: #7982a9; }
.ratio-labels b { color: #ff4d7e; }

.threat-ratio-bar {
  height: 5px;
  background: #1c1d2c;
  border-radius: 999px;
  overflow: hidden;
  display: flex;
}

.ratio-fill-danger { height: 100%; background: #ff4d7e; transition: width 0.3s; }
.ratio-fill-benign { height: 100%; background: #3ddc97; transition: width 0.3s; }

.sensor-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.sensor-protocol-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #7982a9;
}

.proto-svg { width: 13px; height: 13px; color: #3ddc97; }

.btn-sensor-action {
  height: 30px;
  padding: 0 12px;
  font-size: 11.5px;
  font-weight: 600;
  border-radius: 6px;
  background: rgba(88, 101, 242, 0.12);
  border: 1px solid rgba(88, 101, 242, 0.3);
  color: #8fa0ff;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.btn-sensor-action:hover { background: #5865f2; color: #ffffff; }
.action-btn-svg { width: 12px; height: 12px; }

.text-danger { color: #ff4d7e !important; }
.text-muted  { color: #7982a9 !important; }
</style>
