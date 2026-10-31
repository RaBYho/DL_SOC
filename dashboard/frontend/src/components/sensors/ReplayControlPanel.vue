<template>
  <div class="card control-panel-card">
    <div class="card-header-row">
      <div>
        <h3 class="section-title">Injection de Scénarios d'Attaques</h3>
        <p class="section-subtitle">
          Simulez des captures réelles pour tester la robustesse et la réactivité du modèle Deep Learning.
        </p>
      </div>
      <span v-if="replayStatus.active" class="badge-running" :class="{ 'is-paused': replayStatus.is_paused }">
        {{ replayStatus.is_paused ? 'Rejeu Suspendu' : 'Rejeu Actif' }}
      </span>
    </div>

    <div class="form-flow">
      <!-- Sélecteur de fichier PCAP -->
      <div class="field-group">
        <label class="field-label">Scénario de Capture Réseau (PCAP)</label>
        <div class="select-wrapper">
          <select 
            :value="selectedPcap" 
            class="custom-select" 
            :disabled="replayStatus.active"
            @change="$emit('update:selectedPcap', $event.target.value)"
          >
            <option value="">Sélectionnez un scénario d'attaque...</option>
            <option v-for="p in pcapFiles" :key="p.filename" :value="p.filename">
              {{ p.title ? p.title : p.filename }} ({{ p.size_mb }} Mo)
            </option>
          </select>
          <span class="select-arrow">▼</span>
        </div>
      </div>

      <!-- Fiche détaillée du scénario sélectionné -->
      <div v-if="selectedPcapMeta" class="scenario-meta-card">
        <div class="scenario-meta-header">
          <div class="scenario-meta-title">
            <span class="scenario-bullet"></span>
            <b>{{ selectedPcapMeta.title }}</b>
          </div>
          <span class="sev-tag" :class="selectedPcapMeta.severity">{{ selectedPcapMeta.category }}</span>
        </div>
        <p class="scenario-desc">{{ selectedPcapMeta.description }}</p>
        <div class="scenario-chips">
          <div class="chip">
            <span class="chip-label">Fichier :</span>
            <code class="chip-val">{{ selectedPcapMeta.filename }}</code>
          </div>
          <div class="chip">
            <span class="chip-label">Taille :</span>
            <b class="chip-val">{{ selectedPcapMeta.size_mb }} Mo</b>
          </div>
          <div class="chip">
            <span class="chip-label">Niveau d'impact :</span>
            <b class="chip-val" :class="'text-' + (selectedPcapMeta.severity || 'Medium').toLowerCase()">{{ selectedPcapMeta.severity }}</b>
          </div>
        </div>
      </div>

      <!-- Sélecteur de Vitesse avec Segmented Control -->
      <div class="field-group">
        <div class="field-header">
          <label class="field-label">Vitesse d'Injection Réseau</label>
          <span class="rate-indicator">{{ (replaySpeed * 25).toFixed(0) }} flux/seconde estimés</span>
        </div>
        <div class="speed-segmented-control">
          <button 
            v-for="s in [0.5, 1.0, 2.0, 5.0, 10.0]" 
            :key="s"
            type="button"
            class="speed-btn"
            :class="{ active: replaySpeed === s }"
            @click="$emit('update:replaySpeed', s)"
            :disabled="replayStatus.active"
          >
            {{ s }}x
            <span v-if="s === 1.0" class="speed-badge-norm">Normal</span>
            <span v-else-if="s === 10.0" class="speed-badge-turbo">Turbo</span>
          </button>
        </div>
      </div>

      <!-- Carte de Progression Live -->
      <div v-if="replayStatus.active" class="replay-progress-card">
        <div class="progress-top">
          <span class="progress-file-info">
            <span class="progress-glow-dot"></span>
            Rejeu en cours : <b>{{ replayStatus.pcap_name }}</b>
          </span>
          <span class="progress-pct">{{ (replayStatus.progress_pct || 0).toFixed(1) }}%</span>
        </div>

        <div class="progress-track">
          <div class="progress-bar-fill" :style="{ width: `${replayStatus.progress_pct || 0}%` }">
            <span class="progress-laser"></span>
          </div>
        </div>

        <div class="progress-kpi-grid">
          <div class="progress-kpi">
            <span class="kpi-label">Flux Traités</span>
            <b class="kpi-val">{{ replayStatus.processed_flows }} / {{ replayStatus.total_flows }}</b>
          </div>
          <div class="progress-kpi">
            <span class="kpi-label">Vitesse Active</span>
            <b class="kpi-val text-accent">{{ replayStatus.speed }}x</b>
          </div>
          <div class="progress-kpi">
            <span class="kpi-label">Menaces Interceptées</span>
            <b class="kpi-val text-danger">{{ replayStatus.total_alerts || totalAttacks }}</b>
          </div>
        </div>
      </div>

      <!-- Commandes du Rejeu -->
      <div class="controls-row">
        <button 
          v-if="!replayStatus.active"
          type="button"
          class="btn-primary-action" 
          :disabled="!selectedPcap"
          @click="$emit('start')"
        >
          <svg class="svg-icon" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
          <span>Lancer le Rejeu PCAP</span>
        </button>

        <template v-else>
          <button 
            v-if="!replayStatus.is_paused"
            type="button"
            class="btn-secondary-action" 
            @click="$emit('pause')"
          >
            <svg class="svg-icon" viewBox="0 0 24 24" fill="currentColor">
              <rect x="6" y="4" width="4" height="16"/>
              <rect x="14" y="4" width="4" height="16"/>
            </svg>
            <span>Mettre en Pause</span>
          </button>
          <button 
            v-else
            type="button"
            class="btn-secondary-action btn-resume" 
            @click="$emit('resume')"
          >
            <svg class="svg-icon" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="5 3 19 12 5 21 5 3"/>
            </svg>
            <span>Reprendre le Rejeu</span>
          </button>

          <button 
            type="button"
            class="btn-danger-action" 
            @click="$emit('stop')"
          >
            <svg class="svg-icon" viewBox="0 0 24 24" fill="currentColor">
              <rect x="5" y="5" width="14" height="14"/>
            </svg>
            <span>Arrêter le Rejeu</span>
          </button>
        </template>
      </div>

      <!-- Accès au Terminal IA -->
      <router-link to="/models" class="link-to-terminal-card">
        <div class="terminal-card-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="4 17 10 11 4 5"/>
            <line x1="12" y1="19" x2="20" y2="19"/>
          </svg>
        </div>
        <div class="terminal-card-text">
          <b>Terminal d'Inférence IA en Direct</b>
          <span>Observez chaque batch analysé par le DNN et l'AutoEncodeur avec leur latence</span>
        </div>
        <div class="terminal-card-arrow">&rarr;</div>
      </router-link>
    </div>
  </div>
</template>

<script setup>
defineProps({
  selectedPcap: {
    type: String,
    default: ''
  },
  replaySpeed: {
    type: Number,
    default: 1.0
  },
  selectedPcapMeta: {
    type: Object,
    default: null
  },
  pcapFiles: {
    type: Array,
    default: () => []
  },
  replayStatus: {
    type: Object,
    default: () => ({ active: false })
  },
  totalAttacks: {
    type: Number,
    default: 0
  }
})

defineEmits(['update:selectedPcap', 'update:replaySpeed', 'start', 'pause', 'resume', 'stop'])
</script>

<style scoped>
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

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.badge-running {
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 7px;
  background: rgba(61, 220, 151, 0.15);
  color: #3ddc97;
  border: 1px solid rgba(61, 220, 151, 0.35);
}

.badge-running.is-paused {
  background: rgba(255, 181, 71, 0.15);
  color: #ffb547;
  border-color: rgba(255, 181, 71, 0.35);
}

.form-flow {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.field-label {
  font-size: 12px;
  font-weight: 600;
  color: #c4ccff;
}

.rate-indicator {
  font-size: 11.5px;
  color: #8fa0ff;
  font-weight: 600;
}

.select-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.custom-select {
  width: 100%;
  height: 44px;
  background: #141524;
  color: #ffffff;
  border: 1px solid #2e3047;
  border-radius: 10px;
  padding: 0 36px 0 14px;
  font-size: 13px;
  font-weight: 500;
  outline: none;
  cursor: pointer;
  appearance: none;
  transition: all 0.2s;
}

.custom-select:focus {
  border-color: #5865f2;
  box-shadow: 0 0 0 3px rgba(88, 101, 242, 0.25);
}

.select-arrow {
  position: absolute;
  right: 14px;
  font-size: 10px;
  color: #8b8ea8;
  pointer-events: none;
}

.scenario-meta-card {
  background: #131422;
  border: 1px solid #282a40;
  border-left: 3px solid #5865f2;
  border-radius: 10px;
  padding: 14px;
}

.scenario-meta-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.scenario-meta-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13.5px;
  color: #ffffff;
}

.scenario-bullet {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #5865f2;
}

.scenario-desc {
  font-size: 12.5px;
  color: #9aa5ce;
  margin: 0 0 12px;
  line-height: 1.45;
}

.scenario-chips {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
  background: rgba(255, 255, 255, 0.04);
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.chip-label {
  color: #7982a9;
}

.chip-val {
  color: #ffffff;
}

.speed-segmented-control {
  display: flex;
  background: #121320;
  padding: 4px;
  border-radius: 10px;
  border: 1px solid #26283d;
  gap: 4px;
}

.speed-btn {
  flex: 1;
  height: 36px;
  background: transparent;
  border: none;
  border-radius: 7px;
  color: #8b8ea8;
  font-size: 12.5px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: all 0.2s;
}

.speed-btn:hover:not(:disabled) {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.05);
}

.speed-btn.active {
  background: #5865f2;
  color: #ffffff;
  box-shadow: 0 2px 10px rgba(88, 101, 242, 0.4);
}

.speed-badge-norm, .speed-badge-turbo {
  font-size: 9px;
  padding: 1px 4px;
  border-radius: 4px;
}

.speed-badge-norm { background: rgba(255, 255, 255, 0.2); }
.speed-badge-turbo { background: rgba(255, 77, 126, 0.3); color: #ff85a5; }

.replay-progress-card {
  background: #121320;
  border: 1px solid #2d3049;
  border-radius: 12px;
  padding: 14px 16px;
}

.progress-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12.5px;
  margin-bottom: 8px;
}

.progress-file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #c4ccff;
}

.progress-glow-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #3ddc97;
  box-shadow: 0 0 8px #3ddc97;
  animation: pulse-dot 1s infinite;
}

@keyframes pulse-dot {
  0% { transform: scale(0.9); opacity: 0.7; }
  50% { transform: scale(1.4); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.7; }
}

.progress-pct {
  font-size: 14px;
  font-weight: 800;
  color: #3ddc97;
}

.progress-track {
  height: 8px;
  background: #1c1d2e;
  border-radius: 999px;
  overflow: hidden;
  position: relative;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #5865f2 0%, #3ddc97 100%);
  border-radius: 999px;
  transition: width 0.3s ease;
  position: relative;
}

.progress-laser {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 12px;
  background: #ffffff;
  box-shadow: 0 0 10px #ffffff;
  opacity: 0.8;
}

.progress-kpi-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.progress-kpi {
  display: flex;
  flex-direction: column;
}

.kpi-label {
  font-size: 10.5px;
  color: #7982a9;
  text-transform: uppercase;
}

.kpi-val {
  font-size: 13px;
  font-weight: 700;
  color: #ffffff;
  margin-top: 2px;
}

.controls-row {
  display: flex;
  gap: 10px;
}

.btn-primary-action, .btn-secondary-action, .btn-danger-action {
  height: 44px;
  padding: 0 20px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.btn-primary-action {
  width: 100%;
  background: linear-gradient(135deg, #5865f2 0%, #4a57e0 100%);
  color: #ffffff;
  border: 1px solid #6b77ff;
  box-shadow: 0 4px 16px rgba(88, 101, 242, 0.35);
}

.btn-primary-action:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 22px rgba(88, 101, 242, 0.5);
}

.btn-primary-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary-action {
  flex: 1;
  background: #202235;
  color: #d1d6f5;
  border: 1px solid #363a56;
}

.btn-secondary-action:hover {
  background: #282b44;
  color: #ffffff;
}

.btn-secondary-action.btn-resume {
  background: rgba(61, 220, 151, 0.15);
  color: #3ddc97;
  border-color: rgba(61, 220, 151, 0.35);
}

.btn-danger-action {
  flex: 1;
  background: rgba(255, 77, 126, 0.12);
  color: #ff4d7e;
  border: 1px solid rgba(255, 77, 126, 0.35);
}

.btn-danger-action:hover {
  background: rgba(255, 77, 126, 0.22);
}

.link-to-terminal-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  border-radius: 10px;
  background: rgba(88, 101, 242, 0.08);
  border: 1px solid rgba(88, 101, 242, 0.22);
  text-decoration: none;
  transition: all 0.2s;
}

.link-to-terminal-card:hover {
  background: rgba(88, 101, 242, 0.16);
  border-color: rgba(88, 101, 242, 0.4);
  transform: translateX(2px);
}

.terminal-card-icon {
  width: 24px;
  height: 24px;
  color: #8fa0ff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.terminal-card-icon svg {
  width: 22px;
  height: 22px;
}

.terminal-card-text {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.terminal-card-text b {
  font-size: 13px;
  color: #ffffff;
}

.terminal-card-text span {
  font-size: 11.5px;
  color: #8b8ea8;
  margin-top: 2px;
}

.terminal-card-arrow {
  font-size: 18px;
  color: #8fa0ff;
}

.svg-icon {
  width: 16px;
  height: 16px;
}

.text-accent  { color: #5865f2 !important; }
.text-danger  { color: #ff4d7e !important; }

.sev-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 5px;
  text-transform: uppercase;
}

.sev-tag.Critical { background: rgba(255, 77, 126, 0.2); color: #ff4d7e; border: 1px solid rgba(255, 77, 126, 0.4); }
.sev-tag.High     { background: rgba(255, 122, 69, 0.2); color: #ff7a45; border: 1px solid rgba(255, 122, 69, 0.4); }
.sev-tag.Medium   { background: rgba(255, 181, 71, 0.2); color: #ffb547; border: 1px solid rgba(255, 181, 71, 0.4); }
.sev-tag.Info     { background: rgba(61, 220, 151, 0.2); color: #3ddc97; border: 1px solid rgba(61, 220, 151, 0.4); }
</style>
