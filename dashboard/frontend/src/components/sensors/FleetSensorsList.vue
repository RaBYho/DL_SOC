<template>
  <div class="card fleet-list-card">
    <div class="fleet-list-header">
      <div>
        <div class="header-title-flex">
          <svg class="section-title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
            <rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>
            <line x1="6" y1="6" x2="6.01" y2="6"/>
            <line x1="6" y1="18" x2="6.01" y2="18"/>
          </svg>
          <h3 class="section-title">Parc de Sondes Actives &amp; Distantes</h3>
        </div>
        <p class="section-subtitle">
          Supervision des sondes matérielles, virtuelles et agents edge transmettant des flux au serveur NIDS.
        </p>
      </div>

      <!-- Filtre Rapide de Statut -->
      <div class="status-filter-pills">
        <button 
          type="button" 
          class="status-pill-btn" 
          :class="{ active: statusFilter === 'all' }"
          @click="statusFilter = 'all'"
        >
          Toutes ({{ sensors.length }})
        </button>
        <button 
          type="button" 
          class="status-pill-btn online" 
          :class="{ active: statusFilter === 'online' }"
          @click="statusFilter = 'online'"
        >
          <span class="pill-dot green"></span>
          En ligne ({{ onlineCount }})
        </button>
        <button 
          type="button" 
          class="status-pill-btn offline" 
          :class="{ active: statusFilter === 'offline' }"
          @click="statusFilter = 'offline'"
        >
          Inactives ({{ sensors.length - onlineCount }})
        </button>
      </div>
    </div>

    <!-- ÉTAT VIDE ÉLÉGANT AVEC RADAR -->
    <div v-if="filteredSensors.length === 0" class="fleet-empty-state">
      <div class="radar-scan-box">
        <div class="radar-circle circle-1"></div>
        <div class="radar-circle circle-2"></div>
        <div class="radar-circle circle-3"></div>
        <div class="radar-sweeper"></div>
        <div class="radar-center-dot"></div>
      </div>
      <h4 class="empty-state-title">Aucune sonde détectée pour ce filtre</h4>
      <p class="empty-state-text">
        Déployez un agent sur une machine distante avec la commande ci-contre ou lancez une simulation de rejeu PCAP pour générer des flux en direct.
      </p>
      <div class="empty-actions">
        <button type="button" class="btn-glass" @click="$emit('switchTab', 'replay')">
          <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
          </svg>
          <span>Lancer un Rejeu PCAP</span>
        </button>
        <button type="button" class="btn-glass" @click="statusFilter = 'all'">
          Réinitialiser le filtre
        </button>
      </div>
    </div>

    <!-- LISTE DES CARTES DE SONDES SOC -->
    <div v-else class="fleet-cards-grid">
      <div 
        v-for="s in filteredSensors" 
        :key="s.id" 
        class="sensor-fleet-card"
        :class="{ 'is-online': s.status === 'Online', 'is-replay': s.type === 'replay' }"
      >
        <!-- En-tête de la sonde -->
        <div class="sensor-card-top">
          <div class="sensor-badge-icon" :class="{ 'icon-replay': s.type === 'replay' }">
            <!-- Icône Fiole pour simulateur PCAP Replay -->
            <svg v-if="s.type === 'replay'" class="sensor-svg-type" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10 2v7.31L4.69 19.3A2 2 0 0 0 6.36 22h11.28a2 2 0 0 0 1.67-2.7L14 9.31V2"/>
              <line x1="8.5" y1="2" x2="15.5" y2="2"/>
              <line x1="14" y1="9" x2="10" y2="9"/>
            </svg>
            <!-- Icône Serveur Réseau pour Agent Edge Distant -->
            <svg v-else class="sensor-svg-type" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
              <rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>
              <line x1="6" y1="6" x2="6.01" y2="6"/>
              <line x1="6" y1="18" x2="6.01" y2="18"/>
            </svg>
          </div>

          <div class="sensor-headline">
            <div class="sensor-title-row">
              <b class="sensor-title">{{ s.name }}</b>
              <span 
                class="sensor-status-tag"
                :class="'tag-' + s.status.toLowerCase()"
              >
                <span class="status-indicator-dot"></span>
                {{ s.status_label || s.status }}
              </span>
            </div>

            <div class="sensor-ids-row">
              <span class="sensor-id-pill" @click="copySensorId(s.id)" title="Cliquez pour copier l'identifiant">
                ID: <code>{{ s.id }}</code>
                <svg class="copy-small-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                </svg>
              </span>
              <span class="type-pill" :class="s.type">
                {{ s.type === 'replay' ? 'Simulateur PCAP Interne' : 'Agent Edge Distant' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Corps Télémétrie Réseau -->
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
              {{ s.interface || (s.type === 'replay' ? 'Moteur PCAP' : 'eth0') }}
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
            <b class="telemetry-val">{{ (s.total_flows || 0).toLocaleString() }}</b>
          </div>

          <div class="telemetry-item">
            <div class="telemetry-lbl-row">
              <svg class="telemetry-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              </svg>
              <span class="telemetry-lbl">Attaques bloquées</span>
            </div>
            <b class="telemetry-val" :class="{ 'text-danger': (s.total_attacks || 0) > 0 }">
              {{ (s.total_attacks || 0).toLocaleString() }}
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
              {{ s.last_seen || 'En attente' }}
              <span v-if="s.elapsed_sec" class="elapsed-badge">
                ({{ formatElapsed(s.elapsed_sec) }})
              </span>
            </span>
          </div>
        </div>

        <!-- Jauge de Ratio de Menaces -->
        <div class="sensor-threat-ratio">
          <div class="ratio-labels">
            <span>Répartition du trafic</span>
            <b>{{ calculateAttackPct(s) }}% malveillant</b>
          </div>
          <div class="threat-ratio-bar">
            <div 
              class="ratio-fill-danger" 
              :style="{ width: `${calculateAttackPct(s)}%` }"
            ></div>
            <div 
              class="ratio-fill-benign" 
              :style="{ width: `${100 - calculateAttackPct(s)}%` }"
            ></div>
          </div>
        </div>

        <!-- Pied de Carte & Actions -->
        <div class="sensor-card-footer">
          <div class="sensor-protocol-tag">
            <svg class="proto-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
            </svg>
            <span>Moteur : Scorer IA v4 + AE</span>
          </div>

          <div class="sensor-actions">
            <button 
              type="button" 
              class="btn-sensor-action"
              @click="$emit('filterAlerts', s.id)"
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
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  sensors: {
    type: Array,
    default: () => []
  },
  onlineCount: {
    type: Number,
    default: 0
  }
})

defineEmits(['filterAlerts', 'switchTab'])

const statusFilter = ref('all')

const filteredSensors = computed(() => {
  let list = props.sensors || []
  if (statusFilter.value === 'online') {
    list = list.filter(s => s.status === 'Online')
  } else if (statusFilter.value === 'offline') {
    list = list.filter(s => s.status !== 'Online')
  }
  return list
})

const calculateAttackPct = (sensor) => {
  if (!sensor.total_flows || sensor.total_flows === 0) return 0
  const pct = ((sensor.total_attacks || 0) / sensor.total_flows) * 100
  return Math.min(100, Math.max(0, Math.round(pct * 10) / 10))
}

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
.fleet-list-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 18px;
}

.header-title-flex {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title-icon {
  width: 18px;
  height: 18px;
  color: #8fa0ff;
}

.section-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.2px;
}

.section-subtitle {
  margin: 4px 0 0;
  font-size: 12px;
  color: #8b8ea8;
  line-height: 1.4;
}

.status-filter-pills {
  display: flex;
  gap: 6px;
  background: #121320;
  padding: 4px;
  border-radius: 9px;
  border: 1px solid #282a40;
}

.status-pill-btn {
  height: 28px;
  padding: 0 10px;
  border-radius: 6px;
  background: transparent;
  border: none;
  font-size: 11px;
  font-weight: 600;
  color: #8b8ea8;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.status-pill-btn:hover {
  color: #ffffff;
}

.status-pill-btn.active {
  background: #25283f;
  color: #ffffff;
}

.status-pill-btn.online.active {
  background: rgba(61, 220, 151, 0.2);
  color: #3ddc97;
}

.status-pill-btn.offline.active {
  background: rgba(99, 107, 142, 0.3);
  color: #c4ccff;
}

.pill-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.pill-dot.green {
  background: #3ddc97;
  box-shadow: 0 0 6px #3ddc97;
}

/* État vide */
.fleet-empty-state {
  text-align: center;
  padding: 48px 24px;
  background: #131422;
  border: 1px dashed #2d3049;
  border-radius: 14px;
  margin-top: 10px;
}

.radar-scan-box {
  position: relative;
  width: 90px;
  height: 90px;
  margin: 0 auto 16px;
  border-radius: 50%;
  border: 1px solid rgba(88, 101, 242, 0.4);
  background: radial-gradient(circle, rgba(88, 101, 242, 0.08) 0%, rgba(15, 16, 23, 0) 70%);
}

.radar-circle {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  border: 1px solid rgba(88, 101, 242, 0.25);
}

.circle-1 { width: 30px; height: 30px; }
.circle-2 { width: 60px; height: 60px; }
.circle-3 { width: 90px; height: 90px; }

.radar-center-dot {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #5865f2;
  box-shadow: 0 0 8px #5865f2;
}

.radar-sweeper {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: conic-gradient(from 0deg, rgba(88, 101, 242, 0.35) 0deg, transparent 60deg, transparent 360deg);
  animation: radar-sweep 3s linear infinite;
}

@keyframes radar-sweep {
  100% { transform: rotate(360deg); }
}

.empty-state-title {
  margin: 0 0 8px;
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
}

.empty-state-text {
  font-size: 12.5px;
  color: #7982a9;
  max-width: 440px;
  margin: 0 auto 18px;
  line-height: 1.5;
}

.empty-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.btn-glass {
  height: 36px;
  padding: 0 14px;
  font-size: 12.5px;
  font-weight: 600;
  color: #d1d6f5;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 9px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.btn-glass:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.25);
  transform: translateY(-1px);
}

.btn-glass .svg-icon {
  width: 15px;
  height: 15px;
}

/* Grille de cartes */
.fleet-cards-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

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

.sensor-fleet-card.is-online {
  border-left: 3px solid #3ddc97;
}

.sensor-fleet-card.is-replay {
  border-left: 3px solid #5865f2;
}

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

.sensor-svg-type {
  width: 22px;
  height: 22px;
}

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

.sensor-title {
  font-size: 15px;
  color: #ffffff;
}

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

.copy-small-svg {
  width: 12px;
  height: 12px;
  color: #8fa0ff;
}

.type-pill {
  font-size: 11px;
  color: #7982a9;
}

/* Télémétrie */
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
  .sensor-telemetry-box {
    grid-template-columns: repeat(2, 1fr);
  }
}

.telemetry-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.telemetry-lbl-row {
  display: flex;
  align-items: center;
  gap: 5px;
}

.telemetry-icon {
  width: 12px;
  height: 12px;
  color: #7982a9;
}

.telemetry-lbl {
  font-size: 10.5px;
  color: #7982a9;
  text-transform: uppercase;
}

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

.elapsed-badge {
  font-size: 10.5px;
  color: #8b8ea8;
  font-weight: normal;
}

/* Jauge de ratio */
.sensor-threat-ratio {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ratio-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #7982a9;
}

.ratio-labels b {
  color: #ff4d7e;
}

.threat-ratio-bar {
  height: 5px;
  background: #1c1d2c;
  border-radius: 999px;
  overflow: hidden;
  display: flex;
}

.ratio-fill-danger {
  height: 100%;
  background: #ff4d7e;
  transition: width 0.3s;
}

.ratio-fill-benign {
  height: 100%;
  background: #3ddc97;
  transition: width 0.3s;
}

/* Pied de carte */
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

.proto-svg {
  width: 13px;
  height: 13px;
  color: #3ddc97;
}

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

.btn-sensor-action:hover {
  background: #5865f2;
  color: #ffffff;
}

.action-btn-svg {
  width: 12px;
  height: 12px;
}

.text-danger { color: #ff4d7e !important; }
.text-muted  { color: #7982a9 !important; }
</style>
