<template>
  <div v-if="store.batchPatternModalOpen" class="modal-backdrop" @click.self="store.closeBatchPatternModal" role="dialog" aria-modal="true" aria-labelledby="batch-modal-title">
    <div class="modal-window">
      <!-- Header -->
      <div class="modal-header">
        <div class="title-cluster">
          <div class="header-icon-badge">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
              <polyline points="2 17 12 22 22 17"></polyline>
              <polyline points="2 12 12 17 22 12"></polyline>
            </svg>
          </div>
          <div>
            <h2 id="batch-modal-title" class="modal-title">{{ store.t('batch.modalTitle') }}</h2>
            <p class="modal-subtitle">
              {{ store.selectedCount }} {{ store.t('batch.flowsSelected') }} &middot;
              <span class="zd-badge-text">{{ store.selectedZeroDaysCount }} {{ store.t('batch.zeroDaysCount') }}</span>
            </p>
          </div>
        </div>
        <button class="close-btn" @click="store.closeBatchPatternModal" aria-label="Fermer">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <!-- Navigation Tabs -->
      <div class="tabs-nav">
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'analysis' }" 
          @click="activeTab = 'analysis'"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"></circle>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
          </svg>
          {{ store.t('batch.aiDiagnosis') }}
        </button>

        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'prompt' }" 
          @click="activeTab = 'prompt'"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="4 17 10 11 4 5"></polyline>
            <line x1="12" y1="19" x2="20" y2="19"></line>
          </svg>
          {{ store.t('batch.promptSection') }}
        </button>

        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'triage' }" 
          @click="activeTab = 'triage'"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
            <polyline points="22 4 12 14.01 9 11.01"></polyline>
          </svg>
          {{ store.t('batch.qualificationTitle') }}
        </button>
      </div>

      <!-- Modal Body -->
      <div class="modal-body">
        <!-- Correlation Summary Stat Chips -->
        <div class="correlation-stats-grid">
          <div class="stat-card">
            <span class="stat-lbl">{{ store.t('batch.uniqueSources') }}</span>
            <div class="stat-main">
              <span class="stat-value mono">{{ correlation.unique_src_ips.length }}</span>
              <span class="stat-sub">adresses</span>
            </div>
            <div class="chips-list">
              <span v-for="ip in correlation.unique_src_ips.slice(0, 4)" :key="ip" class="ip-chip mono">{{ ip }}</span>
              <span v-if="correlation.unique_src_ips.length > 4" class="more-chip">+{{ correlation.unique_src_ips.length - 4 }}</span>
            </div>
          </div>

          <div class="stat-card">
            <span class="stat-lbl">{{ store.t('batch.targetedPorts') }}</span>
            <div class="stat-main">
              <span class="stat-value mono">{{ Object.keys(correlation.targeted_ports).length }}</span>
              <span class="stat-sub">ports visés</span>
            </div>
            <div class="chips-list">
              <span v-for="(cnt, p) in correlation.targeted_ports" :key="p" class="port-chip mono">:{{ p }} ({{ cnt }})</span>
            </div>
          </div>

          <div class="stat-card">
            <span class="stat-lbl">{{ store.t('batch.avgMse') }}</span>
            <div class="stat-main">
              <span class="stat-value mono" :class="{ 'val-anomaly': correlation.avg_mse > store.aeThreshold }">
                {{ correlation.avg_mse.toFixed(4) }}
              </span>
              <span class="stat-sub">seuil: {{ store.aeThreshold }}</span>
            </div>
            <div class="stat-bar-box">
              <div class="stat-bar-track">
                <div class="stat-bar-fill" :style="{ width: `${Math.min(100, (correlation.avg_mse / store.aeThreshold) * 50)}%` }" :class="{ 'fill-crit': correlation.avg_mse > store.aeThreshold }"></div>
              </div>
            </div>
          </div>

          <div class="stat-card">
            <span class="stat-lbl">{{ store.t('batch.distribution') }}</span>
            <div class="stat-main">
              <span class="stat-tag" :class="correlation.is_distributed ? 'tag-crit' : 'tag-neutral'">
                {{ correlation.is_distributed ? store.t('batch.distributedAttack') : 'Source Unique' }}
              </span>
            </div>
            <div class="chips-list">
              <span class="behavior-pill" :class="{ 'burst-pill': correlation.is_burst }">
                {{ correlation.is_burst ? store.t('batch.burstSync') : 'Flux Étalés' }}
              </span>
            </div>
          </div>
        </div>

        <!-- TAB 1: AI & Expert Diagnosis -->
        <div v-if="activeTab === 'analysis'" class="tab-pane">
          <div v-if="isLoadingAi" class="loading-state">
            <div class="spinner"></div>
            <p>Analyse de corrélation et inférence IA en cours sur les {{ store.selectedCount }} flux...</p>
          </div>

          <div v-else-if="aiResult" class="ai-result-view">
            <!-- Verdict Banner -->
            <div class="verdict-banner" :class="`verdict-${aiResult.determined_verdict.toLowerCase()}`">
              <div class="banner-top">
                <div class="verdict-tag-large">
                  {{ formatVerdictLabel(aiResult.determined_verdict) }}
                </div>
                <div class="confidence-pill">
                  Certitude : <b>{{ aiResult.confidence_pct }}%</b>
                </div>
              </div>
              <h3 class="campaign-title">{{ aiResult.campaign_type }}</h3>
              <p class="verdict-justification">{{ aiResult.justification }}</p>
            </div>

            <!-- Action Quick-Apply Button -->
            <div class="quick-apply-bar">
              <div class="quick-apply-info">
                <span>Étiquette recommandée :</span>
                <b class="rec-label-tag mono">{{ aiResult.suggested_label }}</b>
              </div>
              <button class="btn-primary-apply" :disabled="isSubmitting" @click="applyAiSuggestion">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                Appliquer la qualification IA aux {{ store.selectedCount }} flux
              </button>
            </div>

            <!-- MITRE ATT&CK & Firewall Script -->
            <div class="intel-split">
              <div class="card-inner mitre-card">
                <div class="card-inner-hdr">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="2" y1="12" x2="22" y2="12"></line>
                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                  </svg>
                  <span>Attribution MITRE ATT&CK</span>
                </div>
                <div class="mitre-info">
                  <div class="mitre-tech-badge mono">{{ aiResult.mitre?.id }}</div>
                  <div class="mitre-tech-name">{{ aiResult.mitre?.name }}</div>
                  <div class="mitre-tactic-tag">Tactique : {{ aiResult.mitre?.tactic }}</div>
                </div>
              </div>

              <div class="card-inner firewall-card">
                <div class="card-inner-hdr">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                  </svg>
                  <span>Script de Blocage Pare-feu (IPTables)</span>
                  <button class="copy-code-btn" @click="copyFirewallScript">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                    </svg>
                    {{ fwCopied ? 'Copié !' : 'Copier script' }}
                  </button>
                </div>
                <pre class="code-box mono"><code>{{ aiResult.iptables_rule }}</code></pre>
              </div>
            </div>

            <!-- Detailed Analysis Markdown -->
            <div class="detailed-analysis-card">
              <div class="card-inner-hdr">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                </svg>
                <span>Rapport Forensique Complet</span>
                <span class="provider-pill">{{ aiResult.provider }}</span>
              </div>
              <div class="markdown-content">
                <pre class="report-text">{{ aiResult.analysis_markdown }}</pre>
              </div>
            </div>
          </div>

          <div v-else class="trigger-analysis-box">
            <p>Aucune analyse de pattern en cache. Cliquez pour corréler les {{ store.selectedCount }} flux sélectionnés.</p>
            <button class="btn-primary" @click="runBatchAiAnalysis">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="5 3 19 12 5 21 5 3"></polygon>
              </svg>
              Lancer la Détection de Campagne
            </button>
          </div>
        </div>

        <!-- TAB 2: Formatted Forensic Prompt for External LLM -->
        <div v-if="activeTab === 'prompt'" class="tab-pane">
          <div class="prompt-tab-intro">
            <div>
              <h4 class="prompt-section-title">Prompt d'Investigation de Campagne pour LLM Externe</h4>
              <p class="prompt-section-sub">
                Ce prompt synthétise l'ensemble des {{ store.selectedCount }} flux télémétriques avec cartographie d'attaque, plage MSE et IOCs.
                Copiez-le directement dans votre modèle de langage (ChatGPT, Claude, Gemini, Mistral) pour obtenir une seconde opinion forensique.
              </p>
            </div>
            <button class="btn-copy-prompt" @click="copyPromptToClipboard">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
              {{ promptCopied ? 'Prompt copié !' : store.t('batch.copyPrompt') }}
            </button>
          </div>

          <div class="prompt-preview-container">
            <textarea readonly class="prompt-textarea mono" :value="campaignPromptText"></textarea>
          </div>
        </div>

        <!-- TAB 3: Batch Active Learning Triage Form -->
        <div v-if="activeTab === 'triage'" class="tab-pane">
          <div class="triage-intro">
            <h4 class="prompt-section-title">Qualification Humaine Groupée (Human-in-the-Loop)</h4>
            <p class="prompt-section-sub">
              Labellisez et requalifiez d'un seul coup les <b>{{ store.selectedCount }} flux</b> sélectionnés.
              Cette étiquette sera enregistrée dans SQLite (<code>feedback_flows</code>) pour ré-entraîner le classifieur DNN et ajuster la baseline de l'autoencodeur.
            </p>
          </div>

          <form class="batch-form" @submit.prevent="submitManualBatchQualification">
            <div class="form-group">
              <label class="form-label">Verdict Global de l'Analyste</label>
              <div class="verdict-options">
                <label class="verdict-opt-card" :class="{ selected: formVerdict === 'CONFIRMED_ZERODAY' }">
                  <input type="radio" v-model="formVerdict" value="CONFIRMED_ZERODAY" />
                  <div class="opt-content">
                    <span class="opt-title text-zd">Zero-Day Confirmé</span>
                    <span class="opt-desc">Nouvelle anomalie offensive sans signature cataloguée</span>
                  </div>
                </label>

                <label class="verdict-opt-card" :class="{ selected: formVerdict === 'KNOWN_ATTACK' }">
                  <input type="radio" v-model="formVerdict" value="KNOWN_ATTACK" />
                  <div class="opt-content">
                    <span class="opt-title text-atk">Attaque Connue</span>
                    <span class="opt-desc">Attaque cataloguée (DDoS, Scan, DoS, Brute-Force, etc.)</span>
                  </div>
                </label>

                <label class="verdict-opt-card" :class="{ selected: formVerdict === 'FALSE_POSITIVE' }">
                  <input type="radio" v-model="formVerdict" value="FALSE_POSITIVE" />
                  <div class="opt-content">
                    <span class="opt-title text-fp">Faux Positif</span>
                    <span class="opt-desc">Trafic légitime mal classifié par le modèle</span>
                  </div>
                </label>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">Nom de la Campagne / Menace Corrigée</label>
              <input 
                type="text" 
                v-model="formLabel" 
                class="form-input" 
                placeholder="Ex: Zero-Day-C2-Distributed, DDoS-SYN-Campaign, Scan-Horizontal..." 
                required 
              />
              <div class="label-suggestions">
                <span>Suggestions rapides :</span>
                <button 
                  v-for="sugg in quickSuggestions" 
                  :key="sugg" 
                  type="button" 
                  class="sugg-chip" 
                  @click="formLabel = sugg"
                >
                  {{ sugg }}
                </button>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">Notes d'Investigation Forensique (Optionnel)</label>
              <textarea 
                v-model="formNotes" 
                class="form-textarea" 
                rows="3" 
                placeholder="Précisez le mécanisme d'attaque, les sous-réseaux ciblés ou la justification de qualification..."
              ></textarea>
            </div>

            <div class="form-actions">
              <button type="button" class="btn-secondary" @click="store.closeBatchPatternModal">Annuler</button>
              <button type="submit" class="btn-primary" :disabled="isSubmitting">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                {{ isSubmitting ? 'Enregistrement...' : `Valider et étiqueter les ${store.selectedCount} flux` }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Toast Feedback -->
      <transition name="fade">
        <div v-if="toastMessage" class="modal-toast">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
          <span>{{ toastMessage }}</span>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useSocStore } from '@/stores/socStore'
import { api } from '@/services/api'

const store = useSocStore()

const activeTab = ref('analysis')
const isLoadingAi = ref(false)
const isSubmitting = ref(false)
const aiResult = ref(null)
const serverPromptText = ref('')
const promptCopied = ref(false)
const fwCopied = ref(false)
const toastMessage = ref('')

const formVerdict = ref('CONFIRMED_ZERODAY')
const formLabel = ref('')
const formNotes = ref('')

const quickSuggestions = computed(() => {
  const dynamicClasses = store.availableAttackCategories.filter(c => c !== 'Unknown (anomaly)')
  const items = ['Zero-Day-C2-Distributed']
  if (dynamicClasses.length > 0) {
    items.push(`${dynamicClasses[0]}-Distributed`)
    if (dynamicClasses.length > 1) items.push(dynamicClasses[1])
    if (dynamicClasses.length > 2) items.push(dynamicClasses[2])
  } else {
    items.push('PortScan-Distributed', 'DDoS-Flooding-Campaign', 'SSH-Patator-Distributed')
  }
  items.push('Faux-Positif-Sauvegarde')
  return Array.from(new Set(items)).slice(0, 5)
})

const correlation = computed(() => {
  const flows = store.selectedAlerts
  if (!flows.length) {
    return {
      unique_src_ips: [],
      unique_dst_ips: [],
      targeted_ports: {},
      avg_mse: 0.0,
      is_burst: false,
      is_distributed: false
    }
  }

  const srcIps = Array.from(new Set(flows.map(f => String(f.src_ip || '0.0.0.0'))))
  const dstIps = Array.from(new Set(flows.map(f => String(f.dst_ip || '0.0.0.0'))))
  const ports = {}
  flows.forEach(f => {
    const p = f.dst_port || 0
    if (p) ports[p] = (ports[p] || 0) + 1
  })

  const mses = flows.map(f => Number(f.mse_ae || 0.0))
  const avgMse = mses.length ? (mses.reduce((a, b) => a + b, 0) / mses.length) : 0.0

  return {
    unique_src_ips: srcIps,
    unique_dst_ips: dstIps,
    targeted_ports: ports,
    avg_mse: avgMse,
    is_burst: flows.length >= 3,
    is_distributed: srcIps.length > 1
  }
})

// Auto-run analysis and generate complete prompt when modal opens
watch(() => store.batchPatternModalOpen, (isOpen) => {
  if (isOpen && store.selectedCount > 0) {
    loadCampaignPrompt()
    runBatchAiAnalysis()
  } else {
    aiResult.value = null
    serverPromptText.value = ''
  }
})

async function loadCampaignPrompt() {
  if (!store.selectedCount) return
  try {
    const res = await api.generateCampaignPrompt(store.selectedAlerts)
    if (res && res.prompt) {
      serverPromptText.value = res.prompt
    }
  } catch (err) {
    console.error('Error generating campaign prompt:', err)
  }
}

async function runBatchAiAnalysis() {
  if (!store.selectedCount) return
  isLoadingAi.value = true
  try {
    const flows = store.selectedAlerts
    const res = await api.analyzeBatchIncidentsAi(flows)
    if (res && res.success) {
      aiResult.value = res
      if (res.prompt_used) {
        serverPromptText.value = res.prompt_used
      }
      formVerdict.value = res.determined_verdict || 'CONFIRMED_ZERODAY'
      formLabel.value = res.suggested_label || ''
      formNotes.value = res.justification || ''
    }
  } catch (err) {
    console.error('Batch AI analysis error:', err)
  } finally {
    isLoadingAi.value = false
  }
}

const campaignPromptText = computed(() => {
  if (aiResult.value?.prompt_used) {
    return aiResult.value.prompt_used
  }
  if (serverPromptText.value) {
    return serverPromptText.value
  }

  // Exhaustive client prompt fallback
  const flows = store.selectedAlerts
  const corr = correlation.value
  const baseline = Number(store.aeThreshold) || 0.6029

  let text = `# RAPPORT D'INVESTIGATION FORENSIQUE SOC TIER-3 : DÉTECTION DE PATTERN & CAMPAGNE MULTI-FLUX\n\n`
  text += `Tu es un expert senior en Threat Intelligence et analyste forensique SOC Tier-3.\n`
  text += `Notre sonde NIDS hybride (Réseau de Neurones Profond DNN + Autoencodeur d'Anomalie) a isolé un ensemble de ${flows.length} télémétries suspectes.\n`
  text += `L'analyste a sélectionné ce lot pour détecter un schéma de corrélation (campagne Zero-Day APT, scan distribué, DDoS ou faux positif) et qualifier ces données dans le système d'Active Learning.\n\n`

  text += `### 📊 1. Synthèse Statistique du Cluster\n`
  text += `- Nombre de flux sélectionnés : ${flows.length} (${store.selectedZeroDaysCount} Zero-Days - ${flows.length ? Math.round((store.selectedZeroDaysCount / flows.length) * 100) : 0}%)\n`
  text += `- Sources distinctes (${corr.unique_src_ips.length}) : ${corr.unique_src_ips.join(', ')}\n`
  text += `- Cibles (${corr.unique_dst_ips.length}) : ${corr.unique_dst_ips.join(', ')}\n`
  text += `- Ports cibles : ${Object.entries(corr.targeted_ports).map(([p, cnt]) => `:${p} (${cnt}x)`).join(', ')}\n`
  text += `- Erreur MSE moyenne : ${corr.avg_mse.toFixed(4)} (Seuil baseline: ${baseline})\n`
  text += `- Topologie : ${corr.is_distributed ? 'Attaque Distribuée Multi-Sources' : 'Source Unique'}\n\n`

  text += `### 📋 2. Échantillon Détaillé des Télémétries\n`
  text += `| # | Horodatage | Source | Destination | Proto | Prédiction DNN | Score MSE | Statut Zero-Day |\n`
  text += `|---|---|---|---|---|---|---|---|\n`
  flows.slice(0, 20).forEach((f, idx) => {
    const ts = f.received_at || f.timestamp || 'Live'
    const mse = Number(f.mse_ae || 0).toFixed(4)
    const isZd = (f.anomalie_ae === 1 || f.is_zero_day || Number(f.mse_ae || 0) > baseline) ? 'OUI (0-Day)' : 'Nominal'
    text += `| ${idx + 1} | \`${ts}\` | \`${f.src_ip}:${f.src_port || ''}\` | \`${f.dst_ip}:${f.dst_port || ''}\` | ${f.protocol || 'TCP'} | ${f.pred || f.classification || 'SUSPICIOUS'} | ${mse} | ${isZd} |\n`
  })

  text += `\n### 🎯 3. Décision d'Étiquetage Attendue (pour l'Active Learning) :\n`
  text += `Fournis OBLIGATOIREMENT en début de réponse les balises de décision :\n`
  text += `[CAMPAGNE_DETECTEE]: OUI ou NON\n`
  text += `[TYPE_CAMPAGNE]: (ex: Campagne Zero-Day APT C2, Scan de Ports Distribué, DDoS Volumétrique L7, Brute-Force SSH Distribué, Faux Positif de Sauvegarde)\n`
  text += `[VERDICT_GLOBAL]: CONFIRMED_ZERODAY ou KNOWN_ATTACK ou FALSE_POSITIVE\n`
  text += `[SUGGESTED_LABEL]: Étiquette normalisée pour le lot (ex: Zero-Day-C2-Campaign, PortScan-Distributed, DoS-Hulk, Faux-Positif-Sauvegarde)\n`
  text += `[CONFIDENCE]: Pourcentage de certitude (ex: 95%)\n`
  text += `[ANALYSTE_JUSTIFICATION]: Résumé technique concis.\n\n`

  text += `### 📑 4. Rapport Forensique Détaillé :\n`
  text += `1. Analyse de Pattern & Corrélation spatio-temporelle.\n`
  text += `2. Diagnostic Déviationnel de l'Autoencodeur (espace latent).\n`
  text += `3. Attribution MITRE ATT&CK (Tactiques et Techniques).\n`
  text += `4. Script Pare-feu iptables/ipset pour neutraliser les sources.\n`
  text += `5. Règle de détection Suricata pérenne.\n`

  return text
})

function showToast(msg) {
  toastMessage.value = msg
  setTimeout(() => {
    toastMessage.value = ''
  }, 3500)
}

async function copyPromptToClipboard() {
  let text = campaignPromptText.value
  if (!text || text.length < 200) {
    try {
      const res = await api.generateCampaignPrompt(store.selectedAlerts)
      if (res && res.prompt) {
        text = res.prompt
        serverPromptText.value = res.prompt
      }
    } catch (e) {
      console.error(e)
    }
  }
  await navigator.clipboard.writeText(text)
  promptCopied.value = true
  showToast(store.t('batch.promptCopied'))
  setTimeout(() => {
    promptCopied.value = false
  }, 2500)
}

function copyFirewallScript() {
  if (!aiResult.value?.iptables_rule) return
  navigator.clipboard.writeText(aiResult.value.iptables_rule).then(() => {
    fwCopied.value = true
    showToast('Script de blocage pare-feu copié dans le presse-papiers !')
    setTimeout(() => {
      fwCopied.value = false
    }, 2500)
  })
}

async function applyAiSuggestion() {
  if (!aiResult.value) return
  isSubmitting.value = true
  try {
    await store.submitBatchFeedback(
      aiResult.value.determined_verdict,
      aiResult.value.suggested_label,
      aiResult.value.justification
    )
    showToast(`${store.selectedCount || 'Tous les'} flux qualifiés avec succès !`)
    setTimeout(() => {
      store.closeBatchPatternModal()
    }, 1200)
  } catch (err) {
    console.error('Error applying AI batch qualification:', err)
  } finally {
    isSubmitting.value = false
  }
}

async function submitManualBatchQualification() {
  isSubmitting.value = true
  try {
    await store.submitBatchFeedback(
      formVerdict.value,
      formLabel.value,
      formNotes.value
    )
    showToast(`${store.selectedCount || 'Tous les'} flux qualifiés avec succès !`)
    setTimeout(() => {
      store.closeBatchPatternModal()
    }, 1200)
  } catch (err) {
    console.error('Error submitting manual batch qualification:', err)
  } finally {
    isSubmitting.value = false
  }
}

function formatVerdictLabel(verdict) {
  if (verdict === 'CONFIRMED_ZERODAY') return 'Anomalie Zero-Day Confirmée'
  if (verdict === 'KNOWN_ATTACK') return 'Attaque Connue Validée'
  return 'Faux Positif (Trafic Légitime)'
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(4, 8, 16, 0.78);
  backdrop-filter: blur(8px);
  z-index: 1200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
}

.modal-window {
  width: 100%;
  max-width: 880px;
  max-height: 90vh;
  background: var(--bg-card, #0f172a);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.65), 0 0 0 1px rgba(0, 229, 255, 0.12);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(15, 23, 42, 0.6);
}

.title-cluster {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.header-icon-badge {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  background: rgba(0, 229, 255, 0.12);
  border: 1px solid rgba(0, 229, 255, 0.28);
  color: var(--ac, #00e5ff);
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-icon-badge svg {
  width: 22px;
  height: 22px;
}

.modal-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--tx, #f8fafc);
}

.modal-subtitle {
  margin: 0.15rem 0 0;
  font-size: 0.82rem;
  color: var(--tx-dim, #94a3b8);
}

.zd-badge-text {
  color: #f43f5e;
  font-weight: 600;
}

.close-btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--tx-dim, #94a3b8);
  border-radius: 8px;
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--tx, #fff);
  border-color: rgba(255, 255, 255, 0.2);
}

.close-btn svg {
  width: 18px;
  height: 18px;
}

/* Tabs */
.tabs-nav {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(11, 19, 38, 0.5);
}

.tab-btn {
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--tx-dim, #94a3b8);
  padding: 0.65rem 1rem;
  font-size: 0.84rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn svg {
  width: 16px;
  height: 16px;
}

.tab-btn:hover {
  color: var(--tx, #fff);
}

.tab-btn.active {
  color: var(--ac, #00e5ff);
  border-bottom-color: var(--ac, #00e5ff);
}

/* Modal Body */
.modal-body {
  padding: 1.25rem 1.5rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

/* Stats Cards */
.correlation-stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.85rem;
}

.stat-card {
  background: rgba(17, 24, 39, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 10px;
  padding: 0.85rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.stat-lbl {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--tx-dim, #94a3b8);
  font-weight: 600;
}

.stat-main {
  display: flex;
  align-items: baseline;
  gap: 0.4rem;
}

.stat-value {
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--tx, #fff);
}

.stat-value.val-anomaly {
  color: #f43f5e;
}

.stat-sub {
  font-size: 0.75rem;
  color: var(--tx-dim, #64748b);
}

.chips-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  margin-top: 0.2rem;
}

.ip-chip, .port-chip, .more-chip {
  font-size: 0.7rem;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #cbd5e1;
}

.port-chip {
  background: rgba(0, 229, 255, 0.08);
  border-color: rgba(0, 229, 255, 0.2);
  color: var(--ac, #00e5ff);
}

.stat-tag {
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.2rem 0.5rem;
  border-radius: 6px;
}

.tag-crit {
  background: rgba(244, 63, 94, 0.15);
  border: 1px solid rgba(244, 63, 94, 0.3);
  color: #fb7185;
}

.tag-neutral {
  background: rgba(148, 163, 184, 0.12);
  border: 1px solid rgba(148, 163, 184, 0.2);
  color: #94a3b8;
}

.behavior-pill {
  font-size: 0.72rem;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.05);
  color: #94a3b8;
}

.burst-pill {
  background: rgba(245, 158, 11, 0.15);
  border: 1px solid rgba(245, 158, 11, 0.3);
  color: #fbbf24;
}

.stat-bar-box {
  margin-top: 0.3rem;
}

.stat-bar-track {
  height: 4px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 2px;
  overflow: hidden;
}

.stat-bar-fill {
  height: 100%;
  background: var(--ok, #10b981);
}

.stat-bar-fill.fill-crit {
  background: #f43f5e;
}

/* Tab 1: AI Result View */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  gap: 1rem;
  color: var(--tx-dim, #94a3b8);
}

.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(0, 229, 255, 0.2);
  border-top-color: var(--ac, #00e5ff);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.verdict-banner {
  border-radius: 10px;
  padding: 1.15rem 1.35rem;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.verdict-confirmed_zeroday {
  background: rgba(244, 63, 94, 0.12);
  border: 1px solid rgba(244, 63, 94, 0.3);
}

.verdict-known_attack {
  background: rgba(245, 158, 11, 0.12);
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.verdict-false_positive {
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.banner-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.verdict-tag-large {
  font-size: 0.85rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--tx, #fff);
}

.confidence-pill {
  font-size: 0.78rem;
  color: var(--tx-dim, #cbd5e1);
}

.campaign-title {
  margin: 0;
  font-size: 1.15rem;
  color: var(--tx, #fff);
}

.verdict-justification {
  margin: 0;
  font-size: 0.85rem;
  color: #cbd5e1;
  line-height: 1.45;
}

/* Quick Apply Bar */
.quick-apply-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.85rem 1.15rem;
  background: rgba(0, 229, 255, 0.06);
  border: 1px solid rgba(0, 229, 255, 0.2);
  border-radius: 8px;
}

.quick-apply-info {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.85rem;
  color: #e2e8f0;
}

.rec-label-tag {
  background: rgba(0, 229, 255, 0.18);
  border: 1px solid rgba(0, 229, 255, 0.35);
  padding: 0.2rem 0.55rem;
  border-radius: 4px;
  color: var(--ac, #00e5ff);
}

.btn-primary-apply {
  background: var(--ac, #00e5ff);
  color: #040810;
  font-weight: 700;
  font-size: 0.82rem;
  border: none;
  border-radius: 6px;
  padding: 0.55rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.45rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary-apply:hover:not(:disabled) {
  filter: brightness(1.15);
  box-shadow: 0 0 16px rgba(0, 229, 255, 0.4);
}

.btn-primary-apply svg {
  width: 16px;
  height: 16px;
}

/* Intel Split */
.intel-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.85rem;
  margin-top: 0.85rem;
}

.card-inner {
  background: rgba(17, 24, 39, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 0.85rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.card-inner-hdr {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--tx-dim, #94a3b8);
  text-transform: uppercase;
}

.card-inner-hdr svg {
  width: 15px;
  height: 15px;
  color: var(--ac, #00e5ff);
}

.mitre-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.mitre-tech-badge {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--ac, #00e5ff);
}

.mitre-tech-name {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--tx, #fff);
}

.mitre-tactic-tag {
  font-size: 0.78rem;
  color: var(--tx-dim, #94a3b8);
}

.copy-code-btn {
  margin-left: auto;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #cbd5e1;
  font-size: 0.72rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.copy-code-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}

.copy-code-btn svg {
  width: 13px;
  height: 13px;
}

.code-box {
  margin: 0;
  padding: 0.6rem;
  background: rgba(4, 8, 16, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  font-size: 0.78rem;
  color: #7dd3fc;
  overflow-x: auto;
  line-height: 1.4;
}

/* Detailed Analysis Card */
.detailed-analysis-card {
  margin-top: 0.85rem;
  background: rgba(17, 24, 39, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 1rem;
}

.provider-pill {
  margin-left: auto;
  font-size: 0.7rem;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.06);
  color: #94a3b8;
}

.report-text {
  margin: 0.75rem 0 0;
  font-family: inherit;
  font-size: 0.84rem;
  color: #e2e8f0;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

/* TAB 2: Prompt */
.prompt-tab-intro {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 0.85rem;
}

.prompt-section-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--tx, #fff);
}

.prompt-section-sub {
  margin: 0.25rem 0 0;
  font-size: 0.82rem;
  color: var(--tx-dim, #94a3b8);
  line-height: 1.4;
}

.btn-copy-prompt {
  background: var(--ac, #00e5ff);
  color: #040810;
  font-weight: 700;
  font-size: 0.85rem;
  border: none;
  border-radius: 8px;
  padding: 0.65rem 1.15rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.btn-copy-prompt:hover {
  filter: brightness(1.15);
  box-shadow: 0 0 16px rgba(0, 229, 255, 0.4);
}

.btn-copy-prompt svg {
  width: 17px;
  height: 17px;
}

.prompt-preview-container {
  height: 380px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  overflow: hidden;
  background: rgba(4, 8, 16, 0.8);
}

.prompt-textarea {
  width: 100%;
  height: 100%;
  background: transparent;
  border: none;
  padding: 1rem;
  color: #e2e8f0;
  font-size: 0.8rem;
  line-height: 1.5;
  resize: none;
  outline: none;
  font-family: 'JetBrains Mono', monospace;
}

/* TAB 3: Batch Triage Form */
.triage-intro {
  margin-bottom: 1.25rem;
}

.batch-form {
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.form-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #cbd5e1;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.verdict-options {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.85rem;
}

.verdict-opt-card {
  background: rgba(17, 24, 39, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 0.85rem 1rem;
  cursor: pointer;
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  transition: all 0.2s ease;
}

.verdict-opt-card:hover {
  border-color: rgba(255, 255, 255, 0.2);
  background: rgba(17, 24, 39, 0.85);
}

.verdict-opt-card.selected {
  border-color: var(--ac, #00e5ff);
  background: rgba(0, 229, 255, 0.08);
  box-shadow: 0 0 12px rgba(0, 229, 255, 0.15);
}

.opt-content {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.opt-title {
  font-size: 0.85rem;
  font-weight: 700;
}

.text-zd { color: #f43f5e; }
.text-atk { color: #f59e0b; }
.text-fp { color: #10b981; }

.opt-desc {
  font-size: 0.74rem;
  color: var(--tx-dim, #94a3b8);
  line-height: 1.3;
}

.form-input, .form-textarea {
  background: rgba(17, 24, 39, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  padding: 0.65rem 0.85rem;
  color: var(--tx, #fff);
  font-size: 0.85rem;
  outline: none;
  transition: border-color 0.2s ease;
}

.form-input:focus, .form-textarea:focus {
  border-color: var(--ac, #00e5ff);
}

.label-suggestions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.4rem;
  font-size: 0.74rem;
  color: var(--tx-dim, #94a3b8);
  margin-top: 0.2rem;
}

.sugg-chip {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #cbd5e1;
  font-size: 0.72rem;
  padding: 0.2rem 0.45rem;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sugg-chip:hover {
  background: rgba(0, 229, 255, 0.12);
  border-color: rgba(0, 229, 255, 0.3);
  color: var(--ac, #00e5ff);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.btn-secondary {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #cbd5e1;
  font-size: 0.84rem;
  font-weight: 600;
  padding: 0.65rem 1.15rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.btn-primary {
  background: var(--ac, #00e5ff);
  color: #040810;
  font-size: 0.84rem;
  font-weight: 700;
  padding: 0.65rem 1.25rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.45rem;
  transition: all 0.2s ease;
}

.btn-primary:hover:not(:disabled) {
  filter: brightness(1.15);
  box-shadow: 0 0 16px rgba(0, 229, 255, 0.35);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary svg {
  width: 16px;
  height: 16px;
}

/* Toast */
.modal-toast {
  position: absolute;
  bottom: 1.5rem;
  right: 1.5rem;
  background: #0f172a;
  border: 1px solid var(--ok, #10b981);
  color: #e2e8f0;
  padding: 0.75rem 1.15rem;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.85rem;
  font-weight: 600;
  z-index: 100;
}

.modal-toast svg {
  width: 18px;
  height: 18px;
  color: var(--ok, #10b981);
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

@media (max-width: 768px) {
  .correlation-stats-grid {
    grid-template-columns: 1fr 1fr;
  }
  .verdict-options {
    grid-template-columns: 1fr;
  }
  .intel-split {
    grid-template-columns: 1fr;
  }
}
</style>
