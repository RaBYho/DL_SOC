<template>
  <div class="ai-assistant-container">
    <!-- Top Action Banner -->
    <div class="ai-action-banner">
      <div class="banner-title-wrap">
        <svg class="ai-brain-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2a4 4 0 0 0-4 4v1a4 4 0 0 0-3 3.87V13a4 4 0 0 0 3 3.87V18a4 4 0 0 0 4 4h0a4 4 0 0 0 4-4v-1.13A4 4 0 0 0 19 13v-2.13A4 4 0 0 0 16 7V6a4 4 0 0 0-4-4z"/>
          <line x1="12" y1="2" x2="12" y2="22"/>
        </svg>
        <div>
          <h4 class="ai-banner-title">Assistant IA & Forensique SOC</h4>
          <span class="ai-banner-desc">Analyse cognitive instantanée, mapping MITRE ATT&CK et remédiation</span>
        </div>
      </div>

      <div class="ai-dual-buttons">
        <!-- Bouton Mode 1 : Copier le prompt pour LLM externe -->
        <button 
          type="button" 
          class="copy-prompt-btn" 
          @click="copyPromptToClipboard" 
          title="Copier le prompt pour ChatGPT, Claude ou Gemini Web"
        >
          <svg v-if="!copiedPrompt" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
          </svg>
          <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--ok)" stroke-width="2.5">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
          <span>{{ copiedPrompt ? 'Prompt Copié !' : 'Copier pour LLM' }}</span>
        </button>

        <!-- Bouton Mode 2 : Diagnostic intégré en 1 clic -->
        <button 
          type="button" 
          class="run-diagnosis-btn" 
          :disabled="isAnalyzing"
          @click="runDiagnosis"
        >
          <svg v-if="!isAnalyzing" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
          </svg>
          <span v-else class="btn-spinner"></span>
          <span>{{ isAnalyzing ? 'Génération...' : 'Diagnostic IA' }}</span>
        </button>
      </div>
    </div>

    <!-- Squelette de chargement -->
    <div v-if="isAnalyzing" class="ai-loading-skeleton">
      <div class="skeleton-line line-header"></div>
      <div class="skeleton-line line-body-1"></div>
      <div class="skeleton-line line-body-2"></div>
      <div class="skeleton-line line-body-3"></div>
    </div>

    <!-- Rapport de Diagnostic Rendu -->
    <div v-else-if="analysisResult" class="ai-report-card">
      <div class="report-meta-header">
        <div class="provider-tag">
          <span class="active-pulse"></span>
          <span>{{ analysisResult.provider || 'Assistant IA' }}</span>
        </div>
        <span class="timestamp-tag">Généré à l'instant</span>
      </div>

      <!-- Quick Command Copy Strip (iptables) -->
      <div v-if="analysisResult.iptables_rule" class="iptables-strip">
        <div class="iptables-left">
          <span class="iptables-label">Règle de Blocage :</span>
          <code class="iptables-code">{{ analysisResult.iptables_rule }}</code>
        </div>
        <button 
          type="button" 
          class="copy-cmd-btn" 
          @click="copyRule(analysisResult.iptables_rule)"
          :title="'Copier la commande de blocage'"
        >
          <svg v-if="!copiedRule" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
          </svg>
          <svg v-else width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--ok)" stroke-width="2.5">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
          <span>{{ copiedRule ? 'Copié' : 'Copier' }}</span>
        </button>
      </div>

      <!-- Contenu Markdown structuré -->
      <div class="report-markdown-content" v-html="renderedMarkdown"></div>
    </div>

    <!-- Placeholder initial si aucune analyse lancée -->
    <div v-else class="ai-empty-prompt">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--mu)" stroke-width="1.8">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="16" x2="12" y2="12"></line>
        <line x1="12" y1="8" x2="12.01" y2="8"></line>
      </svg>
      <div class="empty-title">Aucun diagnostic généré pour ce flux</div>
      <div class="empty-desc">
        Cliquez sur <b>« Diagnostic IA »</b> pour obtenir une synthèse forensique automatique, ou sur <b>« Copier pour LLM »</b> pour exporter le prompt standardisé Tier-3 vers votre LLM habituel.
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { api } from '@/services/api'

const props = defineProps({
  flow: {
    type: Object,
    required: true
  }
})

const isAnalyzing = ref(false)
const analysisResult = ref(null)
const copiedPrompt = ref(false)
const copiedRule = ref(false)

const incidentId = computed(() => {
  return props.flow ? (props.flow.id || `${props.flow.src_ip}-${props.flow.dst_port}-${props.flow.received_at}`) : 'inc-01'
})

// Conversion markdown simple et sécurisée pour le dashboard
const renderedMarkdown = computed(() => {
  if (!analysisResult.value || !analysisResult.value.analysis_markdown) return ''
  let text = analysisResult.value.analysis_markdown

  // Échappement HTML basique
  text = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

  // Headers
  text = text.replace(/^### (.*$)/gim, '<h4 class="md-h4">$1</h4>')
  text = text.replace(/^## (.*$)/gim, '<h3 class="md-h3">$1</h3>')

  // Code blocks ```bash ... ```
  text = text.replace(/```(?:bash|suricata|python)?\n([\s\S]*?)```/g, '<pre class="md-pre"><code>$1</code></pre>')

  // Inline code `...`
  text = text.replace(/`([^`]+)`/g, '<code class="md-code">$1</code>')

  // Bold **...**
  text = text.replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>')

  // Listes
  text = text.replace(/^\s*-\s+(.*$)/gim, '<li class="md-li">$1</li>')

  // Liens markdown [texte](url)
  text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener" class="md-link">$1</a>')

  // Lignes de séparation ---
  text = text.replace(/^---$/gim, '<hr class="md-hr" />')

  // Retours à la ligne
  text = text.replace(/\n\n/g, '<br class="md-break" />')

  return text
})

// Réinitialisation si changement de flux sélectionné
watch(() => props.flow, () => {
  analysisResult.value = null
  copiedPrompt.value = false
  copiedRule.value = false
})

const buildClientPrompt = () => {
  const f = props.flow || {}
  const isZd = Boolean(f.anomalie_ae === 1 || f.is_anomaly)
  return `Tu es un analyste senior en cybersécurité SOC Tier-3.
Analyse le flux réseau suspect suivant intercepté par notre NIDS (Deep Learning) :

### 🌐 Métadonnées du flux
- **Horodatage :** ${f.received_at || 'En direct'}
- **Source :** ${f.src_ip || '0.0.0.0'}:${f.src_port || 0} ➔ **Destination :** ${f.dst_ip || '0.0.0.0'}:${f.dst_port || 0}
- **Protocole :** ${f.protocol || 'TCP'}
- **Sonde :** ${f.sensor_id || 'probe-lan-01'}

### 🧠 Télémétrie IA du NIDS
- **Score d'anomalie MSE :** ${f.mse_ae !== undefined ? f.mse_ae : 0.0} (Seuil : 0.6029)
- **Détection Zero-Day :** ${isZd ? 'OUI (Anomalie avérée)' : 'NON (Signature connue)'}
- **Classification préliminaire DNN :** ${f.pred || f.classification || 'SUSPECT'} (Confiance : ${f.confidence || 90}%)

### 🎯 Instructions d'analyse attendues :
1. **Diagnostic rapide :** Quelle est la nature technique probable de ce flux ?
2. **Cartographie MITRE ATT&CK :** Fournis l'ID de technique (ex: T1046, T1498) et la tactique correspondante.
3. **Niveau de criticité :** Évalue la sévérité (Faible, Moyen, Élevé, Critique) avec justification.
4. **Remédiation immédiate :** Règle iptables exacte pour isoler l'IP source et recommandation opérationnelle.`
}

const copyPromptToClipboard = async () => {
  try {
    const text = buildClientPrompt()
    await navigator.clipboard.writeText(text)
    copiedPrompt.value = true
    setTimeout(() => {
      copiedPrompt.value = false
    }, 2500)
  } catch (err) {
    alert('Impossible de copier dans le presse-papiers')
  }
}

const copyRule = async (rule) => {
  if (!rule) return
  try {
    await navigator.clipboard.writeText(rule)
    copiedRule.value = true
    setTimeout(() => {
      copiedRule.value = false
    }, 2500)
  } catch (err) {
    // fallback
  }
}

const runDiagnosis = async () => {
  if (!incidentId.value) return
  isAnalyzing.value = true
  try {
    const res = await api.analyzeIncidentAi(incidentId.value, props.flow)
    if (res && res.success) {
      analysisResult.value = res
    } else {
      alert(`Erreur d'analyse : ${res?.error || 'Erreur inattendue'}`)
    }
  } catch (err) {
    alert(`Erreur réseau : ${err.message}`)
  } finally {
    isAnalyzing.value = false
  }
}
</script>

<style scoped>
.ai-assistant-container {
  display: flex;
  flex-direction: column;
  gap: 14px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 16px;
  margin-top: 14px;
}

.ai-action-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.banner-title-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ai-brain-icon {
  width: 22px;
  height: 22px;
  color: #a78bfa;
  flex-shrink: 0;
}

.ai-banner-title {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: var(--tx);
}

.ai-banner-desc {
  font-size: 11.5px;
  color: var(--mu);
}

.ai-dual-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.copy-prompt-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 12px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 7px;
  color: var(--tx);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.copy-prompt-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.22);
}

.run-diagnosis-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  background: linear-gradient(135deg, #7c3aed 0%, #6366f1 100%);
  border: none;
  border-radius: 7px;
  color: white;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.run-diagnosis-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.run-diagnosis-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Squelette de chargement */
.ai-loading-skeleton {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.skeleton-line {
  height: 12px;
  background: linear-gradient(90deg, rgba(255,255,255,0.04) 25%, rgba(255,255,255,0.09) 50%, rgba(255,255,255,0.04) 75%);
  background-size: 200% 100%;
  animation: skeletonPulse 1.4s ease infinite;
  border-radius: 4px;
}

.line-header {
  width: 40%;
  height: 16px;
}

.line-body-1 {
  width: 90%;
}

.line-body-2 {
  width: 75%;
}

.line-body-3 {
  width: 60%;
}

@keyframes skeletonPulse {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Rapport de diagnostic */
.ai-report-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: rgba(15, 23, 42, 0.4);
  border: 1px solid rgba(99, 102, 241, 0.25);
  border-radius: 8px;
  padding: 14px;
}

.report-meta-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.provider-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
  font-weight: 700;
  color: #a78bfa;
}

.active-pulse {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #a78bfa;
}

.timestamp-tag {
  font-size: 11px;
  color: var(--mu);
}

/* iptables command strip */
.iptables-strip {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: #090d16;
  border: 1px solid rgba(255, 77, 126, 0.25);
  border-radius: 6px;
}

.iptables-left {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow-x: auto;
}

.iptables-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--cr);
  text-transform: uppercase;
  flex-shrink: 0;
}

.iptables-code {
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-size: 12px;
  color: #fca5a5;
  white-space: nowrap;
}

.copy-cmd-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: rgba(255, 255, 255, 0.08);
  border: none;
  border-radius: 4px;
  color: var(--tx);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  flex-shrink: 0;
}

.copy-cmd-btn:hover {
  background: rgba(255, 255, 255, 0.16);
}

/* Markdown styling inside report */
.report-markdown-content {
  font-size: 12.5px;
  line-height: 1.55;
  color: #cbd5e1;
}

:deep(.md-h4) {
  margin: 10px 0 4px;
  font-size: 13px;
  color: #f1f5f9;
  font-weight: 700;
}

:deep(.md-h3) {
  margin: 12px 0 6px;
  font-size: 14px;
  color: #38bdf8;
  font-weight: 700;
}

:deep(.md-pre) {
  background: #090d16;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  padding: 8px 10px;
  overflow-x: auto;
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-size: 11.5px;
  color: #38bdf8;
  margin: 6px 0;
}

:deep(.md-code) {
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-size: 11.5px;
  background: rgba(255, 255, 255, 0.08);
  padding: 1px 5px;
  border-radius: 4px;
  color: #38bdf8;
}

:deep(.md-link) {
  color: #818cf8;
  text-decoration: none;
}

:deep(.md-link:hover) {
  text-decoration: underline;
}

:deep(.md-hr) {
  border: none;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  margin: 10px 0;
}

:deep(.md-li) {
  margin-left: 16px;
  margin-bottom: 3px;
}

/* Placeholder */
.ai-empty-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 8px;
  padding: 24px 16px;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 8px;
  border: 1px dashed rgba(255, 255, 255, 0.1);
}

.empty-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--tx);
}

.empty-desc {
  font-size: 12px;
  color: var(--mu);
  max-width: 380px;
  line-height: 1.45;
}

.btn-spinner {
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
