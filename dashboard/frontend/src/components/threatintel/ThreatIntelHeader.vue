<template>
  <div class="card threat-header-card">
    <div class="threat-header-main">
      <div class="threat-title-group">
        <div class="title-with-badge">
          <div class="header-icon-box">
            <svg class="header-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
          </div>
          <h2 class="page-title">Threat Intelligence &amp; Taxonomie MITRE ATT&amp;CK</h2>
          <span 
            class="live-intel-pill"
            :class="{ 'has-threats': activeThreatsCount > 0 }"
          >
            <span class="status-pulse-dot"></span>
            {{ activeThreatsCount > 0 ? `${activeThreatsCount} famille(s) active(s) dans le SOC` : 'Aucune menace active détectée' }}
          </span>
        </div>
        <p class="page-desc">
          Référentiel des profils d'attaques <b>CIC-IDS2017</b>, signatures de flux réseau, cartographie tactique <b>MITRE ATT&amp;CK</b> et playbooks de remédiation opérationnelle.
        </p>
      </div>

      <div class="threat-quick-stats">
        <div class="quick-stat-chip">
          <span class="stat-label">Modèle IA Actif</span>
          <b class="stat-val text-accent">DNN-v4 + AE</b>
        </div>
        <div class="quick-stat-chip">
          <span class="stat-label">Seuil Autoencodeur</span>
          <b class="stat-val">{{ aeThreshold.toFixed(4) }} MSE</b>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  activeThreatsCount: {
    type: Number,
    default: 0
  },
  aeThreshold: {
    type: Number,
    default: 0.6029
  }
})
</script>

<style scoped>
.threat-header-card {
  padding: 18px 22px;
  background: linear-gradient(180deg, rgba(28, 30, 48, 0.95) 0%, rgba(20, 21, 34, 0.95) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--r);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
  margin-bottom: 16px;
}

.threat-header-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.threat-title-group {
  flex: 1;
  min-width: 300px;
}

.title-with-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.header-icon-box {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: rgba(88, 101, 242, 0.15);
  border: 1px solid rgba(88, 101, 242, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8fa0ff;
  flex-shrink: 0;
}

.header-svg {
  width: 20px;
  height: 20px;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.3px;
}

.live-intel-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(61, 220, 151, 0.12);
  color: #3ddc97;
  border: 1px solid rgba(61, 220, 151, 0.28);
}

.live-intel-pill.has-threats {
  background: rgba(255, 77, 126, 0.15);
  color: #ff4d7e;
  border-color: rgba(255, 77, 126, 0.35);
  box-shadow: 0 0 12px rgba(255, 77, 126, 0.2);
}

.status-pulse-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 6px currentColor;
}

.has-threats .status-pulse-dot {
  animation: pulse-threat 1.2s infinite;
}

@keyframes pulse-threat {
  0% { transform: scale(0.9); opacity: 0.7; }
  50% { transform: scale(1.4); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.7; }
}

.page-desc {
  margin: 6px 0 0;
  font-size: 12.5px;
  color: #8b8ea8;
  line-height: 1.45;
}

.page-desc b {
  color: #c4ccff;
}

.threat-quick-stats {
  display: flex;
  align-items: center;
  gap: 10px;
}

.quick-stat-chip {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 6px 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 10px;
  color: #7982a9;
  text-transform: uppercase;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.stat-val {
  font-size: 12px;
  font-weight: 700;
  color: #ffffff;
}

.text-accent {
  color: #8fa0ff !important;
}
</style>
