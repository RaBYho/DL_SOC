<template>
  <div 
    class="threat-card"
    :class="[
      'sev-border-' + threat.severity.toLowerCase(),
      { 'is-active-in-soc': detectedCount > 0 }
    ]"
  >
    <!-- 1. En-tête de la Menace -->
    <div class="card-header-row">
      <div class="threat-identity">
        <div class="threat-icon-box" :class="'icon-' + threat.severity.toLowerCase()">
          <!-- Icônes vectorielles thématiques SVG -->
          <svg v-if="threat.iconType === 'radar'" class="threat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 2a10 10 0 0 1 10 10"/>
            <path d="M12 6a6 6 0 0 1 6 6"/>
            <circle cx="12" cy="12" r="2"/>
          </svg>
          <svg v-else-if="threat.iconType === 'zap'" class="threat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
          </svg>
          <svg v-else-if="threat.iconType === 'terminal'" class="threat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="4 17 10 11 4 5"/>
            <line x1="12" y1="19" x2="20" y2="19"/>
          </svg>
          <svg v-else-if="threat.iconType === 'code'" class="threat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="16 18 22 12 16 6"/>
            <polyline points="8 6 2 12 8 18"/>
          </svg>
          <svg v-else-if="threat.iconType === 'bug'" class="threat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="8" y="6" width="8" height="14" rx="4"/>
            <path d="M19 7l-3 2"/>
            <path d="M5 7l3 2"/>
            <path d="M19 19l-3-2"/>
            <path d="M5 19l3-2"/>
            <path d="M20 13h-4"/>
            <path d="M4 13h4"/>
            <path d="M10 4l-1-2"/>
            <path d="M14 4l1-2"/>
          </svg>
          <svg v-else-if="threat.iconType === 'server-crash'" class="threat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
            <rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>
            <line x1="6" y1="6" x2="6.01" y2="6"/>
            <line x1="6" y1="18" x2="6.01" y2="18"/>
            <line x1="18" y1="10" x2="14" y2="14"/>
            <line x1="14" y1="10" x2="18" y2="14"/>
          </svg>
          <svg v-else-if="threat.iconType === 'hourglass'" class="threat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 22h14"/>
            <path d="M5 2h14"/>
            <path d="M17 22v-4.172a2 2 0 0 0-.586-1.414L12 12l-4.414 4.414A2 2 0 0 0 7 17.828V22"/>
            <path d="M7 2v4.172a2 2 0 0 0 .586 1.414L12 12l4.414-4.414A2 2 0 0 0 17 6.172V2"/>
          </svg>
          <svg v-else class="threat-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
        </div>

        <div class="threat-name-group">
          <div class="name-line">
            <b class="threat-name">{{ threat.name }}</b>
            <span class="category-pill">{{ threat.category }}</span>
          </div>
          <span class="dataset-tag">Classe NIDS : {{ threat.datasetLabel }}</span>
        </div>
      </div>

      <div class="threat-badges-top">
        <span class="sev-badge" :class="'badge-' + threat.severity.toLowerCase()">
          {{ threat.severity }}
        </span>
      </div>
    </div>

    <!-- 2. Corrélation Live SOC (si alertes détectées) -->
    <div v-if="detectedCount > 0" class="live-soc-alert-banner">
      <div class="live-banner-left">
        <span class="live-beacon-dot"></span>
        <b class="live-alert-text">Détecté dans votre réseau :</b>
        <span class="live-count-highlight">{{ detectedCount.toLocaleString() }} alerte(s)</span>
        <span v-if="detectedPct > 0" class="live-pct-pill">({{ detectedPct.toFixed(1) }}% du trafic d'attaque)</span>
      </div>
      <button 
        type="button" 
        class="btn-live-filter"
        @click="$emit('filterAlerts', threat.datasetLabel)"
      >
        <span>Inspecter dans Incidents</span>
        <svg class="arrow-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="5" y1="12" x2="19" y2="12"/>
          <polyline points="12 5 19 12 12 19"/>
        </svg>
      </button>
    </div>

    <!-- 3. Description Technique -->
    <p class="threat-desc">
      {{ threat.description }}
    </p>

    <!-- 4. Données MITRE ATT&CK & Vecteurs -->
    <div class="threat-meta-grid">
      <div class="meta-row">
        <span class="meta-label">Technique MITRE :</span>
        <a 
          :href="threat.mitreUrl" 
          target="_blank" 
          rel="noopener noreferrer" 
          class="mitre-link"
          title="Consulter la fiche officielle sur le framework MITRE ATT&CK"
        >
          <code class="mitre-code">{{ threat.mitreId }}</code>
          <span class="mitre-name">{{ threat.mitreName }}</span>
          <svg class="ext-link-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
            <polyline points="15 3 21 3 21 9"/>
            <line x1="10" y1="14" x2="21" y2="3"/>
          </svg>
        </a>
      </div>

      <div class="meta-row">
        <span class="meta-label">Tactique :</span>
        <span class="tactic-tag">{{ threat.mitreTactic }}</span>
      </div>

      <div class="meta-row">
        <span class="meta-label">Cibles &amp; Ports :</span>
        <span class="meta-val">{{ threat.target }}</span>
      </div>

      <div class="meta-row">
        <span class="meta-label">Signature Flux :</span>
        <span class="meta-val sig-val">{{ threat.networkSignature }}</span>
      </div>

      <!-- Top Attaquant corrélé en direct -->
      <div v-if="associatedTopIp" class="meta-row top-ip-row">
        <span class="meta-label">Top Assaillant (SOC) :</span>
        <span class="top-ip-val">
          <svg class="ip-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="2" x2="12" y2="6"/>
            <line x1="12" y1="18" x2="12" y2="22"/>
            <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/>
            <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/>
          </svg>
          <code>{{ associatedTopIp }}</code>
        </span>
      </div>
    </div>

    <!-- 5. Actions & Playbook -->
    <div class="threat-footer-actions">
      <button 
        type="button" 
        class="btn-playbook"
        @click="$emit('openPlaybook', threat)"
      >
        <svg class="action-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="12 2 2 7 12 12 22 7 12 2"/>
          <polyline points="2 17 12 22 22 17"/>
          <polyline points="2 12 12 17 22 12"/>
        </svg>
        <span>Playbook de Remédiation &amp; Règles</span>
      </button>

      <button 
        type="button" 
        class="btn-view-incidents"
        @click="$emit('filterAlerts', threat.datasetLabel)"
        title="Filtrer les incidents associés dans le SOC"
      >
        <svg class="action-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <span>Voir les incidents</span>
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  threat: {
    type: Object,
    required: true
  },
  detectedCount: {
    type: Number,
    default: 0
  },
  detectedPct: {
    type: Number,
    default: 0
  },
  associatedTopIp: {
    type: String,
    default: ''
  }
})

defineEmits(['openPlaybook', 'filterAlerts'])
</script>

<style scoped>
.threat-card {
  background: linear-gradient(180deg, rgba(26, 28, 44, 0.95) 0%, rgba(18, 19, 30, 0.95) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.25);
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.threat-card:hover {
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.18);
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.38);
}

.sev-border-critical { border-left: 3px solid #ff4d7e; }
.sev-border-high     { border-left: 3px solid #ff7a45; }
.sev-border-medium   { border-left: 3px solid #ffb547; }
.sev-border-info     { border-left: 3px solid #3ddc97; }

.threat-card.is-active-in-soc {
  background: linear-gradient(180deg, rgba(32, 26, 42, 0.95) 0%, rgba(20, 18, 30, 0.95) 100%);
  border-color: rgba(255, 77, 126, 0.3);
}

/* 1. Header */
.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.threat-identity {
  display: flex;
  align-items: center;
  gap: 12px;
}

.threat-icon-box {
  width: 42px;
  height: 42px;
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.threat-icon-box.icon-critical { background: rgba(255, 77, 126, 0.15); border: 1px solid rgba(255, 77, 126, 0.3); color: #ff4d7e; }
.threat-icon-box.icon-high     { background: rgba(255, 122, 69, 0.15); border: 1px solid rgba(255, 122, 69, 0.3); color: #ff7a45; }
.threat-icon-box.icon-medium   { background: rgba(255, 181, 71, 0.15); border: 1px solid rgba(255, 181, 71, 0.3); color: #ffb547; }
.threat-icon-box.icon-info     { background: rgba(61, 220, 151, 0.15); border: 1px solid rgba(61, 220, 151, 0.3); color: #3ddc97; }

.threat-svg {
  width: 20px;
  height: 20px;
}

.threat-name-group {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.name-line {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.threat-name {
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.2px;
}

.category-pill {
  font-size: 10.5px;
  font-weight: 600;
  color: #8fa0ff;
  background: rgba(88, 101, 242, 0.12);
  border: 1px solid rgba(88, 101, 242, 0.25);
  padding: 1px 7px;
  border-radius: 5px;
}

.dataset-tag {
  font-size: 11px;
  color: #7982a9;
}

.sev-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: 6px;
  text-transform: uppercase;
}

.badge-critical { background: rgba(255, 77, 126, 0.18); color: #ff4d7e; border: 1px solid rgba(255, 77, 126, 0.35); }
.badge-high     { background: rgba(255, 122, 69, 0.18); color: #ff7a45; border: 1px solid rgba(255, 122, 69, 0.35); }
.badge-medium   { background: rgba(255, 181, 71, 0.18); color: #ffb547; border: 1px solid rgba(255, 181, 71, 0.35); }
.badge-info     { background: rgba(61, 220, 151, 0.18); color: #3ddc97; border: 1px solid rgba(61, 220, 151, 0.35); }

/* 2. Live SOC Banner */
.live-soc-alert-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  background: rgba(255, 77, 126, 0.1);
  border: 1px solid rgba(255, 77, 126, 0.28);
  border-radius: 8px;
  padding: 8px 12px;
  flex-wrap: wrap;
}

.live-banner-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.live-beacon-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #ff4d7e;
  box-shadow: 0 0 8px #ff4d7e;
  animation: pulse-beacon 1.2s infinite;
}

@keyframes pulse-beacon {
  0% { transform: scale(0.9); opacity: 0.7; }
  50% { transform: scale(1.4); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.7; }
}

.live-alert-text { color: #ffffff; }
.live-count-highlight { color: #ff85a5; font-weight: 700; }
.live-pct-pill { font-size: 11px; color: #7982a9; }

.btn-live-filter {
  height: 24px;
  padding: 0 8px;
  font-size: 11px;
  font-weight: 700;
  background: rgba(255, 77, 126, 0.18);
  color: #ff85a5;
  border: 1px solid rgba(255, 77, 126, 0.35);
  border-radius: 5px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  transition: all 0.2s;
}

.btn-live-filter:hover {
  background: #ff4d7e;
  color: #ffffff;
}

.arrow-svg { width: 11px; height: 11px; }

/* 3. Description */
.threat-desc {
  margin: 0;
  font-size: 12.5px;
  color: #8b8ea8;
  line-height: 1.5;
}

/* 4. Meta Grid */
.threat-meta-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #11121d;
  border: 1px solid #232538;
  border-radius: 10px;
  padding: 12px 14px;
}

.meta-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 12px;
}

.meta-label {
  color: #7982a9;
  font-weight: 600;
  min-width: 130px;
  flex-shrink: 0;
}

.meta-val {
  color: #ffffff;
}

.sig-val {
  color: #c4ccff;
  font-size: 11.5px;
  line-height: 1.4;
}

.mitre-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #8fa0ff;
  text-decoration: none;
  transition: color 0.2s;
}

.mitre-link:hover {
  color: #ffffff;
}

.mitre-code {
  font-size: 11.5px;
  font-weight: 700;
  background: rgba(88, 101, 242, 0.15);
  border: 1px solid rgba(88, 101, 242, 0.3);
  padding: 1px 6px;
  border-radius: 4px;
}

.mitre-name {
  font-size: 12px;
}

.ext-link-svg {
  width: 11px;
  height: 11px;
  color: #7982a9;
}

.tactic-tag {
  font-size: 11px;
  font-weight: 600;
  color: #c4ccff;
  background: rgba(255, 255, 255, 0.05);
  padding: 1px 7px;
  border-radius: 4px;
}

.top-ip-row {
  background: rgba(255, 181, 71, 0.06);
  border-radius: 6px;
  padding: 4px 8px;
  margin-top: 2px;
}

.top-ip-val {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #ffb547;
  font-weight: 700;
}

.ip-svg { width: 12px; height: 12px; }

/* 5. Footer Actions */
.threat-footer-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  flex-wrap: wrap;
}

.btn-playbook {
  height: 32px;
  padding: 0 12px;
  font-size: 11.5px;
  font-weight: 700;
  border-radius: 8px;
  background: rgba(88, 101, 242, 0.15);
  border: 1px solid rgba(88, 101, 242, 0.35);
  color: #8fa0ff;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  transition: all 0.2s;
}

.btn-playbook:hover {
  background: #5865f2;
  color: #ffffff;
  border-color: #5865f2;
  box-shadow: 0 2px 10px rgba(88, 101, 242, 0.35);
}

.btn-view-incidents {
  height: 32px;
  padding: 0 12px;
  font-size: 11.5px;
  font-weight: 600;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #8b8ea8;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.btn-view-incidents:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

.action-svg {
  width: 13px;
  height: 13px;
}
</style>
