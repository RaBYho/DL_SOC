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
          <h4 class="ai-banner-title">Assistant IA &amp; Aide à l'Étiquetage</h4>
          <span class="ai-banner-desc">Détermination automatique de la menace et qualification Active Learning</span>
        </div>
      </div>

      <div class="ai-dual-buttons">
        <!-- Bouton Mode 1 : Copier le prompt pour LLM externe -->
        <button 
          type="button" 
          class="copy-prompt-btn" 
          @click="copyPromptToClipboard" 
          title="Copier le prompt forensique pour ChatGPT, Claude ou Gemini Web"
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

        <!-- Bouton Mode 2 : Déterminer la menace en 1 clic -->
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
          <span>{{ isAnalyzing ? 'Analyse...' : 'Déterminer l\'Attaque' }}</span>
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

    <!-- Rapport de Diagnostic & Aide à l'Étiquetage -->
    <div v-else-if="analysisResult" class="ai-report-card">
      <div class="report-meta-header">
        <div class="provider-tag">
          <span class="active-pulse"></span>
          <span>{{ analysisResult.provider || 'Assistant IA' }}</span>
        </div>
        <span class="timestamp-tag">Analyse en direct</span>
      </div>

      <!-- CARTE DE DÉCISION & ÉTIQUETAGE ACTIF -->
      <div class="labeling-decision-card" :class="decisionCardClass">
        <div class="decision-top-row">
          <div class="decision-verdict-title">
            <span class="decision-pill" :class="verdictPillClass">
              {{ verdictLabel }}
            </span>
            <b class="suggested-name">{{ analysisResult.suggested_label }}</b>
          </div>
          <span class="confidence-tag mono">{{ analysisResult.confidence_pct }}% certitude</span>
        </div>

        <p class="decision-justification">{{ analysisResult.justification }}</p>

        <!-- Bouton 1-clic pour appliquer l'étiquette au système Active Learning -->
        <div class="decision-action-strip">
          <button 
            type="button" 
            class="apply-label-btn" 
            :disabled="isLabeling || isAlreadyApplied"
            @click="applyLabelDirectly"
          >
            <svg v-if="!isLabeling && !isAlreadyApplied" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <path d="m9 12 2 2 4-4"/>
            </svg>
            <span v-else-if="isLabeling" class="btn-spinner"></span>
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            <span>{{ isAlreadyApplied ? 'Étiquetage Validé & Synchronisé' : 'Appliquer cet Étiquetage (Active Learning)' }}</span>
          </button>
        </div>
      </div>

      <!-- Tableau des caractéristiques les plus divergentes -->
      <div v-if="analysisResult.key_divergent_features && analysisResult.key_divergent_features.length > 0" class="features-divergence-box">
        <div class="box-title-row">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
          <span>Facteurs ayant déclenché la détection :</span>
        </div>
        <div class="features-table">
          <div v-for="(feat, idx) in analysisResult.key_divergent_features" :key="'feat-' + idx" class="feat-row">
            <span class="feat-name">{{ feat.feature }}</span>
            <span class="feat-observed mono">{{ feat.observed }}</span>
            <span class="feat-baseline">{{ feat.baseline }}</span>
            <span class="feat-deviation" :class="{ 'dev-alert': feat.deviation !== 'Nominale' && feat.deviation !== 'Standard' && feat.deviation !== 'Conforme' }">
              {{ feat.deviation }}
            </span>
          </div>
        </div>
      </div>

      <!-- Commande iptables rapide -->
      <div v-if="analysisResult.iptables_rule" class="iptables-strip">
        <div class="iptables-left">
          <span class="iptables-label">Règle Pare-feu :</span>
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

      <!-- Contenu Markdown détaillé -->
      <div class="report-markdown-content" v-html="renderedMarkdown"></div>
    </div>

    <!-- Placeholder initial si aucune analyse lancée -->
    <div v-else class="ai-empty-prompt">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--mu)" stroke-width="1.8">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="16" x2="12" y2="12"></line>
        <line x1="12" y1="8" x2="12.01" y2="8"></line>
      </svg>
      <div class="empty-title">Assistant d'Étiquetage en Attente</div>
      <div class="empty-desc">
        Cliquez sur <b>« Déterminer l'Attaque »</b> pour que l'IA identifie la vraie menace, quantifie les déviations statistiques et prépare l'étiquette Active Learning.
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useSocStore } from '@/stores/socStore'
import { api } from '@/services/api'

const props = defineProps({
  flow: {
    type: Object,
    required: true
  }
})

const store = useSocStore()

const isAnalyzing = ref(false)
const isLabeling = ref(false)
const isAlreadyApplied = ref(false)
const analysisResult = ref(null)
const copiedPrompt = ref(false)
const copiedRule = ref(false)

const incidentId = computed(() => {
  return props.flow ? (props.flow.id || `${props.flow.src_ip}-${props.flow.dst_port}-${props.flow.received_at}`) : 'inc-01'
})

const verdictPillClass = computed(() => {
  if (!analysisResult.value) return ''
  const v = analysisResult.value.determined_verdict
  if (v === 'FALSE_POSITIVE') return 'pill-fp'
  if (v === 'KNOWN_ATTACK') return 'pill-reclass'
  if (v === 'CONFIRMED_ZERODAY') return 'pill-zd'
  return ''
})

const decisionCardClass = computed(() => {
  if (!analysisResult.value) return ''
  const v = analysisResult.value.determined_verdict
  if (v === 'FALSE_POSITIVE') return 'card-fp'
  if (v === 'KNOWN_ATTACK') return 'card-reclass'
  if (v === 'CONFIRMED_ZERODAY') return 'card-zd'
  return ''
})

const verdictLabel = computed(() => {
  if (!analysisResult.value) return 'Verdict'
  const v = analysisResult.value.determined_verdict
  if (v === 'FALSE_POSITIVE') return 'Faux Positif'
  if (v === 'KNOWN_ATTACK') return 'Attaque Identifiée'
  if (v === 'CONFIRMED_ZERODAY') return 'Zero-Day Confirmé'
  return v
})

// Conversion markdown simple et sécurisée pour le dashboard
const renderedMarkdown = computed(() => {
  if (!analysisResult.value || !analysisResult.value.analysis_markdown) return ''
  let text = analysisResult.value.analysis_markdown

  text = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  text = text.replace(/^### (.*$)/gim, '<h4 class="md-h4">$1</h4>')
  text = text.replace(/^## (.*$)/gim, '<h3 class="md-h3">$1</h3>')
  text = text.replace(/```(?:bash|suricata|python)?\n([\s\S]*?)```/g, '<pre class="md-pre"><code>$1</code></pre>')
  text = text.replace(/`([^`]+)`/g, '<code class="md-code">$1</code>')
  text = text.replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>')
  text = text.replace(/^\s*-\s+(.*$)/gim, '<li class="md-li">$1</li>')
  text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener" class="md-link">$1</a>')
  text = text.replace(/^---$/gim, '<hr class="md-hr" />')
  text = text.replace(/\n\n/g, '<br class="md-break" />')

  return text
})

// Réinitialisation si changement de flux sélectionné
watch(() => props.flow, () => {
  analysisResult.value = null
  isAlreadyApplied.value = Boolean(store.incidentFeedbackMap[incidentId.value])
  copiedPrompt.value = false
  copiedRule.value = false
}, { immediate: true })

const buildClientPrompt = () => {
  if (analysisResult.value?.prompt_used) {
    return analysisResult.value.prompt_used
  }
  const f = props.flow || {}
  const baseline = 0.6029
  const mse = f.mse_ae !== undefined ? Number(f.mse_ae) : 0.0
  const isZd = Boolean(f.anomalie_ae === 1 || f.is_anomaly || mse > baseline)
  const devPct = mse > baseline ? Math.round(((mse - baseline) / baseline) * 100) : 0
  const conf = f.confiance ? Math.round(Number(f.confiance) * 100) : (f.confidence || 90)
  const modelClasses = store.modelClasses && store.modelClasses.length ? store.modelClasses : ['BENIGN', 'DDoS', 'PortScan', 'Bot', 'WebAttack']
  const modelVersion = store.modelMeta?.version || 'v4'
  const classesSummary = `${modelClasses.length} classes configurées (${modelClasses.join(', ')})`

  return `# RAPPORT D'INVESTIGATION FORENSIQUE SOC TIER-3 : ANALYSE D'INCIDENT & QUALIFICATION

Tu es un analyste senior en cybersécurité, Lead Incident Responder et Threat Hunter dans un SOC Tier-3.
Tu opères sur la plateforme HDVR Autonomous Defense, un système NIDS hybride temps réel composé de :
1. **Classifieur supervisé DNN (${modelVersion})** : ${classesSummary}.
2. **Autoencodeur profond non-supervisé** : détection de déviations Zero-Day sans signature (seuil normalisé $\\theta = ${baseline}$).

L'analyste SOC sollicite ton expertise pour **analyser, contextualiser, déterminer formellement et étiqueter** ce flux réseau pour le cycle d'Active Learning / Human-in-the-Loop.

---

### 🌐 1. TÉLÉMÉTRIE DÉTAILLÉE DU FLUX RÉSEAU
- **Horodatage :** \`${f.received_at || f.timestamp || 'En direct'}\` | **Sonde :** \`${f.sensor_id || 'sensor-edge-01'}\`
- **Vecteur Réseau :** \`${f.src_ip || '0.0.0.0'}:${f.src_port || 0}\` ➔ \`${f.dst_ip || '0.0.0.0'}:${f.dst_port || 0}\` (Protocole : **${f.protocol || 'TCP'}**)
- **Volumétrie :** ${f.src2dst_packets || f.bidirectional_packets || 14} paquets Forward, ${f.dst2src_packets || 8} paquets Backward (${(f.src2dst_bytes || 1420) + (f.dst2src_bytes || 980)} octets)
- **Durée de Session :** ${f.bidirectional_duration_ms ? (f.bidirectional_duration_ms / 1000).toFixed(3) + 's' : '0.045s'}

---

### 🧠 2. SIGNAUX DES MOTEURS D'IA
- **Inférence DNN préliminaire :** **\`${f.pred || f.classification || 'SUSPECT'}\`** (Confiance : **${conf}%**)
- **Score Autoencodeur (MSE) :** **\`${mse.toFixed(4)}\`** (Seuil baseline : \`${baseline}\`)
- **Écart Statistique :** **${devPct > 0 ? `+${devPct}% (Déviation Anormale)` : 'Nominal (< seuil)'}**
- **Détection Zero-Day :** **${isZd ? '[OUI - ANOMALIE ZERO-DAY DÉTECTÉE]' : '[NON - SIGNATURE STANDARD]'}**

---

### ⚖️ 3. ÉVALUATION DES HYPOTHÈSES FORENSIQUES CONCURRENTES
Examine obligatoirement :
- **Scénario A (Zero-Day / APT furtive) :** Exploitation non répertoriée dans le périmètre d'entraînement du modèle actif, C2 obfusqué.
- **Scénario B (Attaque Réseau Répertoriée) :** Attaque correspondant aux classes supervisées (${modelClasses.filter(c => c !== 'BENIGN').slice(0, 4).join(', ')}...).
- **Scénario C (Faux Positif d'Infrastructure) :** Sauvegarde réseau, heartbeat de supervision, scan interne légitime.

---

### 🎯 4. BORDEREAU STRUCTURÉ DE DÉCISION ACTIVE LEARNING
Fournis OBLIGATOIREMENT en tête de ton analyse :
[VERDICT]: FALSE_POSITIVE ou KNOWN_ATTACK ou CONFIRMED_ZERODAY
[SUGGESTED_LABEL]: Dénomination standardisée (ex: Zero-Day-C2-Tunnel, PortScan, DoS-Hulk, SSH-Patator, WebAttack-SQLi, Benign-Admin-Traffic)
[CONFIDENCE]: Pourcentage de certitude (ex: 95%)
[SEVERITE]: CRITIQUE ou ELEVEE ou MOYENNE ou FAIBLE
[JUSTIFICATION]: 2 phrases synthétisant la démonstration technique.

---

### 📑 5. RAPPORT D'ANALYSE FORENSIQUE STRUCTURÉ
1. **Diagnostic Technique Approfondi :** Mécanisme d'attaque ou nature du faux positif.
2. **Attribution & Cartographie MITRE ATT&CK :** Tactique et Technique ID officielle (ex: T1046, T1071.001, T1498, T1110, T1190, T1205).
3. **Plan de Remédiation Réseau Immédiat :** Règle iptables : \`sudo iptables -A INPUT -s ${f.src_ip || '0.0.0.0'} -j DROP\`.
4. **Signature de Détection Pérenne (Règle Suricata) :** Règle \`alert ...\` pour immuniser le réseau face à ce flux.`
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
      isAlreadyApplied.value = Boolean(store.incidentFeedbackMap[incidentId.value])
    } else {
      alert(`Erreur d'analyse : ${res?.error || 'Erreur inattendue'}`)
    }
  } catch (err) {
    alert(`Erreur réseau : ${err.message}`)
  } finally {
    isAnalyzing.value = false
  }
}

const applyLabelDirectly = async () => {
  if (!analysisResult.value || !incidentId.value) return
  isLabeling.value = true
  try {
    await store.submitFeedback(
      incidentId.value,
      analysisResult.value.determined_verdict,
      analysisResult.value.suggested_label,
      analysisResult.value.justification,
      props.flow
    )
    isAlreadyApplied.value = true
  } catch (err) {
    alert(`Erreur d'enregistrement de l'étiquette : ${err.message}`)
  } finally {
    isLabeling.value = false
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

/* CARTE DE DÉCISION & ÉTIQUETAGE */
.labeling-decision-card {
  border-radius: 8px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: rgba(18, 20, 31, 0.6);
  border: 1px solid var(--line);
}

.card-fp {
  border-color: rgba(61, 220, 151, 0.4);
  background: rgba(61, 220, 151, 0.06);
}

.card-reclass {
  border-color: rgba(255, 181, 71, 0.4);
  background: rgba(255, 181, 71, 0.06);
}

.card-zd {
  border-color: rgba(178, 102, 255, 0.4);
  background: rgba(178, 102, 255, 0.06);
}

.decision-top-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.decision-verdict-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.decision-pill {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 3px 8px;
  border-radius: 4px;
  letter-spacing: 0.03em;
}

.pill-fp {
  background: rgba(61, 220, 151, 0.2);
  color: var(--ok);
}

.pill-reclass {
  background: rgba(255, 181, 71, 0.2);
  color: var(--md);
}

.pill-zd {
  background: rgba(178, 102, 255, 0.2);
  color: var(--zd);
}

.suggested-name {
  font-size: 14px;
  color: var(--tx);
}

.confidence-tag {
  font-size: 11.5px;
  color: #c4b5fd;
  background: rgba(167, 139, 250, 0.12);
  padding: 2px 8px;
  border-radius: 12px;
}

.decision-justification {
  margin: 0;
  font-size: 12.5px;
  color: #cbd5e1;
  line-height: 1.45;
}

.decision-action-strip {
  display: flex;
  justify-content: flex-end;
  padding-top: 6px;
}

.apply-label-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 14px;
  background: var(--ac);
  border: none;
  border-radius: 6px;
  color: white;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.apply-label-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.apply-label-btn:disabled {
  background: rgba(61, 220, 151, 0.2);
  color: var(--ok);
  cursor: default;
  border: 1px solid rgba(61, 220, 151, 0.4);
}

/* Tableau des divergences */
.features-divergence-box {
  background: #090d16;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.box-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 700;
  color: #93c5fd;
}

.features-table {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.feat-row {
  display: grid;
  grid-template-columns: 2fr 1.5fr 1.5fr 1fr;
  align-items: center;
  font-size: 11.5px;
  padding: 4px 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.feat-row:last-child {
  border-bottom: none;
}

.feat-name {
  color: #cbd5e1;
  font-weight: 600;
}

.feat-observed {
  color: #f1f5f9;
}

.feat-baseline {
  color: var(--mu);
}

.feat-deviation {
  text-align: right;
  color: var(--mu);
}

.feat-deviation.dev-alert {
  color: var(--cr);
  font-weight: 700;
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

.line-header { width: 40%; height: 16px; }
.line-body-1 { width: 90%; }
.line-body-2 { width: 75%; }
.line-body-3 { width: 60%; }

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
