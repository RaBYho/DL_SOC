<template>
  <div v-if="threat" class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-card">
      <!-- En-tête de la Modale -->
      <div class="modal-header">
        <div class="modal-header-left">
          <div class="threat-badge-icon" :class="'icon-' + threat.severity.toLowerCase()">
            <svg class="svg-modal-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="12 2 2 7 12 12 22 7 12 2"/>
              <polyline points="2 17 12 22 22 17"/>
              <polyline points="2 12 12 17 22 12"/>
            </svg>
          </div>
          <div>
            <div class="modal-title-row">
              <h3 class="modal-title">Playbook de Remédiation : {{ threat.name }}</h3>
              <span class="sev-tag" :class="'tag-' + threat.severity.toLowerCase()">{{ threat.severity }}</span>
            </div>
            <p class="modal-subtitle">
              Technique MITRE ATT&amp;CK : <code>{{ threat.mitreId }} ({{ threat.mitreName }})</code> &middot; Tactique : {{ threat.mitreTactic }}
            </p>
          </div>
        </div>

        <button type="button" class="btn-close-modal" @click="$emit('close')">✕</button>
      </div>

      <div class="modal-body-scroll">
        <!-- 1. Règle Pare-feu / Blocage d'urgence -->
        <div class="playbook-section">
          <div class="section-badge-header">
            <span class="badge-num">1</span>
            <h4 class="section-subheading">Isolement d'Urgence &amp; Règle Pare-feu (iptables)</h4>
          </div>
          <p class="section-help-text">
            Appliquez cette règle de filtrage immédiate sur la passerelle ou le serveur cible pour juguler le flux d'attaque :
          </p>
          <div class="code-box-wrapper">
            <pre class="code-block">{{ threat.playbook.iptablesRule }}</pre>
            <button 
              type="button" 
              class="btn-copy-code"
              @click="copyText(threat.playbook.iptablesRule)"
            >
              {{ copiedText === threat.playbook.iptablesRule ? 'Copié !' : 'Copier' }}
            </button>
          </div>
        </div>

        <!-- 2. Règle de Détection IDS Suricata / Snort -->
        <div class="playbook-section">
          <div class="section-badge-header">
            <span class="badge-num">2</span>
            <h4 class="section-subheading">Signature de Détection IDS / IPS (Suricata)</h4>
          </div>
          <p class="section-help-text">
            Injectez cette signature dans votre moteur Suricata pour tracer et alerter sur les tentatives de récidive :
          </p>
          <div class="code-box-wrapper">
            <pre class="code-block">{{ threat.playbook.suricataRule }}</pre>
            <button 
              type="button" 
              class="btn-copy-code"
              @click="copyText(threat.playbook.suricataRule)"
            >
              {{ copiedText === threat.playbook.suricataRule ? 'Copié !' : 'Copier' }}
            </button>
          </div>
        </div>

        <!-- 3. Procédure de réponse étape par étape -->
        <div class="playbook-section">
          <div class="section-badge-header">
            <span class="badge-num">3</span>
            <h4 class="section-subheading">Protocole d'Investigation &amp; Réponse SOC</h4>
          </div>
          <div class="steps-flow">
            <div 
              v-for="(step, idx) in threat.playbook.containmentSteps" 
              :key="idx" 
              class="step-item"
            >
              <div class="step-circle">Étape {{ idx + 1 }}</div>
              <p class="step-text">{{ step }}</p>
            </div>
          </div>
        </div>

        <!-- 4. Conseil de durcissement préventif -->
        <div class="playbook-tip-box">
          <svg class="tip-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
          </svg>
          <div class="tip-body">
            <b>Mesure de Durcissement Préventif :</b>
            <span>{{ threat.playbook.hardeningTips }}</span>
          </div>
        </div>
      </div>

      <!-- Pied de la Modale -->
      <div class="modal-footer">
        <button 
          type="button" 
          class="btn-filter-alerts"
          @click="$emit('filterAlerts', threat.datasetLabel)"
        >
          <svg class="btn-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <span>Consulter les alertes liées dans les Incidents</span>
        </button>

        <button 
          type="button" 
          class="btn-close-bottom" 
          @click="$emit('close')"
        >
          Fermer
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  threat: {
    type: Object,
    default: null
  }
})

defineEmits(['close', 'filterAlerts'])

const copiedText = ref('')

const copyText = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    copiedText.value = text
    setTimeout(() => {
      if (copiedText.value === text) copiedText.value = ''
    }, 2500)
  } catch (err) {
    console.error('Erreur copie presse-papiers:', err)
  }
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 999;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.modal-card {
  width: 100%;
  max-width: 800px;
  max-height: 90vh;
  background: #141524;
  border: 1px solid #2d304a;
  border-radius: 16px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.6);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: modal-pop 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes modal-pop {
  0% { transform: scale(0.96); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}

.modal-header {
  padding: 18px 24px;
  background: #191b2c;
  border-bottom: 1px solid #282a42;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.threat-badge-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.threat-badge-icon.icon-critical { background: rgba(255, 77, 126, 0.15); border: 1px solid rgba(255, 77, 126, 0.3); color: #ff4d7e; }
.threat-badge-icon.icon-high     { background: rgba(255, 122, 69, 0.15); border: 1px solid rgba(255, 122, 69, 0.3); color: #ff7a45; }
.threat-badge-icon.icon-medium   { background: rgba(255, 181, 71, 0.15); border: 1px solid rgba(255, 181, 71, 0.3); color: #ffb547; }
.threat-badge-icon.icon-info     { background: rgba(61, 220, 151, 0.15); border: 1px solid rgba(61, 220, 151, 0.3); color: #3ddc97; }

.svg-modal-icon { width: 22px; height: 22px; }

.modal-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.modal-title {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: #ffffff;
}

.sev-tag {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 5px;
  text-transform: uppercase;
}

.tag-critical { background: rgba(255, 77, 126, 0.2); color: #ff4d7e; }
.tag-high     { background: rgba(255, 122, 69, 0.2); color: #ff7a45; }
.tag-medium   { background: rgba(255, 181, 71, 0.2); color: #ffb547; }
.tag-info     { background: rgba(61, 220, 151, 0.2); color: #3ddc97; }

.modal-subtitle {
  margin: 4px 0 0;
  font-size: 12px;
  color: #8b8ea8;
}

.modal-subtitle code {
  color: #8fa0ff;
  background: rgba(88, 101, 242, 0.15);
  padding: 1px 5px;
  border-radius: 4px;
}

.btn-close-modal {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #8b8ea8;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-close-modal:hover {
  background: rgba(255, 77, 126, 0.15);
  color: #ff4d7e;
  border-color: rgba(255, 77, 126, 0.35);
}

.modal-body-scroll {
  padding: 20px 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.playbook-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-badge-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.badge-num {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #5865f2;
  color: #ffffff;
  font-size: 11px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.section-subheading {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #ffffff;
}

.section-help-text {
  margin: 0;
  font-size: 12px;
  color: #8b8ea8;
}

.code-box-wrapper {
  position: relative;
  background: #0d0e16;
  border: 1px solid #23253b;
  border-radius: 8px;
  overflow: hidden;
}

.code-block {
  margin: 0;
  padding: 12px 14px;
  padding-right: 70px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 11.5px;
  color: #c4ccff;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
}

.btn-copy-code {
  position: absolute;
  top: 8px;
  right: 8px;
  height: 26px;
  padding: 0 10px;
  font-size: 11px;
  font-weight: 700;
  background: #25283f;
  color: #eceefa;
  border: 1px solid #3c4266;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-copy-code:hover {
  background: #5865f2;
  color: #ffffff;
}

.steps-flow {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 4px;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: #11121d;
  border: 1px solid #212338;
  border-radius: 8px;
  padding: 10px 12px;
}

.step-circle {
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  background: rgba(88, 101, 242, 0.15);
  color: #8fa0ff;
  border: 1px solid rgba(88, 101, 242, 0.3);
  padding: 2px 7px;
  border-radius: 4px;
  flex-shrink: 0;
  margin-top: 1px;
}

.step-text {
  margin: 0;
  font-size: 12px;
  color: #c4ccff;
  line-height: 1.45;
}

.playbook-tip-box {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: rgba(255, 181, 71, 0.08);
  border: 1px solid rgba(255, 181, 71, 0.22);
  border-radius: 10px;
  padding: 12px 14px;
}

.tip-icon {
  width: 18px;
  height: 18px;
  color: #ffb547;
  flex-shrink: 0;
  margin-top: 2px;
}

.tip-body {
  font-size: 12px;
  color: #ffb547;
  line-height: 1.45;
}

.tip-body b {
  color: #ffd08a;
  display: block;
  margin-bottom: 2px;
}

.modal-footer {
  padding: 14px 24px;
  background: #171827;
  border-top: 1px solid #26283d;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.btn-filter-alerts {
  height: 36px;
  padding: 0 16px;
  font-size: 12px;
  font-weight: 700;
  background: #5865f2;
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 14px rgba(88, 101, 242, 0.35);
  transition: all 0.2s;
}

.btn-filter-alerts:hover {
  background: #4752c4;
}

.btn-close-bottom {
  height: 36px;
  padding: 0 16px;
  font-size: 12px;
  font-weight: 600;
  background: transparent;
  color: #8b8ea8;
  border: 1px solid #2a2d42;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-close-bottom:hover {
  background: #25283f;
  color: #ffffff;
}

.btn-svg {
  width: 14px;
  height: 14px;
}
</style>
