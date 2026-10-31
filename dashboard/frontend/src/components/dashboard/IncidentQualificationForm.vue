<template>
  <div class="qualification-form-container">
    <div class="section-badge-header">
      <div class="title-with-icon">
        <svg class="header-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          <path d="m9 12 2 2 4-4"/>
        </svg>
        <div>
          <h4 class="form-title">Triage Humain & Active Learning</h4>
          <span class="form-subtitle">Enregistrement de la décision analyste pour le ré-entraînement du NIDS</span>
        </div>
      </div>

      <div v-if="existingFeedback" class="verdict-status-pill" :class="verdictPillClass">
        <span class="status-dot"></span>
        <span>{{ verdictLabel }}</span>
      </div>
    </div>

    <!-- Choix du Verdict (3 cartes) -->
    <div class="verdict-cards-grid">
      <!-- 1. Faux Positif -->
      <button 
        type="button" 
        class="verdict-card" 
        :class="{ selected: selectedVerdict === 'FALSE_POSITIVE' }"
        @click="selectedVerdict = 'FALSE_POSITIVE'"
      >
        <div class="card-radio-circle">
          <div v-if="selectedVerdict === 'FALSE_POSITIVE'" class="radio-inner"></div>
        </div>
        <div class="card-content">
          <div class="verdict-name fp-color">Faux Positif (Bénin)</div>
          <div class="verdict-desc">Trafic légitime. Réduira les fausses alertes sur ce profil.</div>
        </div>
      </button>

      <!-- 2. Attaque Connue Reclassifiée -->
      <button 
        type="button" 
        class="verdict-card" 
        :class="{ selected: selectedVerdict === 'KNOWN_ATTACK' }"
        @click="selectedVerdict = 'KNOWN_ATTACK'"
      >
        <div class="card-radio-circle">
          <div v-if="selectedVerdict === 'KNOWN_ATTACK'" class="radio-inner"></div>
        </div>
        <div class="card-content">
          <div class="verdict-name reclass-color">Attaque Reclassifiée</div>
          <div class="verdict-desc">Signature connue mal classée par l'IA ou suspectée à tort comme ZD.</div>
        </div>
      </button>

      <!-- 3. Nouveau Zero-Day Confirmé -->
      <button 
        type="button" 
        class="verdict-card" 
        :class="{ selected: selectedVerdict === 'CONFIRMED_ZERODAY' }"
        @click="selectedVerdict = 'CONFIRMED_ZERODAY'"
      >
        <div class="card-radio-circle">
          <div v-if="selectedVerdict === 'CONFIRMED_ZERODAY'" class="radio-inner"></div>
        </div>
        <div class="card-content">
          <div class="verdict-name zd-color">Zero-Day Confirmé</div>
          <div class="verdict-desc">Comportement offensif inconnu. Étiqueté pour le fine-tuning.</div>
        </div>
      </button>
    </div>

    <!-- Champ conditionnel : Catégorie d'attaque reclassifiée -->
    <div v-if="selectedVerdict === 'KNOWN_ATTACK'" class="subform-group">
      <label class="input-label" for="correctedAttackSelect">Vraie catégorie d'attaque identifiée :</label>
      <select id="correctedAttackSelect" v-model="correctedAttack" class="soc-select">
        <option value="" disabled>-- Sélectionner la menace réelle --</option>
        <option value="DDoS">DDoS Volumétrique (LOIC / UDP Flood)</option>
        <option value="PortScan">PortScan (Nmap TCP/SYN Stealth)</option>
        <option value="DoS-Hulk">DoS Hulk (HTTP Request Flooding)</option>
        <option value="DoS-GoldenEye">DoS GoldenEye</option>
        <option value="DoS-slowloris">DoS Slowloris</option>
        <option value="Botnet">Botnet Ares / Mirai (C2 Traffic)</option>
        <option value="Infiltration">Infiltration Réseau / Pivotement</option>
        <option value="SSH-Patator">SSH-Patator (Brute Force)</option>
        <option value="FTP-Patator">FTP-Patator (Brute Force)</option>
        <option value="WebAttack-XSS">Attaque Web XSS</option>
        <option value="WebAttack-SQLi">Attaque Web Injection SQL</option>
        <option value="Heartbleed">Heartbleed (CVE-2014-0160)</option>
      </select>
    </div>

    <!-- Champ conditionnel : Nom du nouveau Zero-Day -->
    <div v-if="selectedVerdict === 'CONFIRMED_ZERODAY'" class="subform-group">
      <label class="input-label" for="zdNameInput">Identifiant / Tag de la nouvelle menace :</label>
      <input 
        id="zdNameInput"
        type="text" 
        v-model="correctedAttack" 
        placeholder="ex: ZERO-DAY-C2-TUNNEL-X" 
        class="soc-text-input mono"
      />
    </div>

    <!-- Commentaires libres de l'analyste -->
    <div class="subform-group">
      <label class="input-label" for="analystNotes">Notes d'investigation forensique (optionnel) :</label>
      <textarea 
        id="analystNotes"
        v-model="analystNotes" 
        rows="3" 
        placeholder="Raison de la qualification, payload suspect, contexte d'évasion..."
        class="soc-textarea"
      ></textarea>
    </div>

    <!-- Bouton d'enregistrement -->
    <div class="form-actions-row">
      <div v-if="feedbackSuccessMsg" class="success-alert">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
        <span>{{ feedbackSuccessMsg }}</span>
      </div>

      <button 
        type="button" 
        class="save-qualification-btn" 
        :disabled="isSubmitting || !selectedVerdict || (selectedVerdict === 'KNOWN_ATTACK' && !correctedAttack)"
        @click="submit"
      >
        <svg v-if="!isSubmitting" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>
        <span v-else class="btn-spinner"></span>
        <span>{{ isSubmitting ? 'Enregistrement...' : 'Enregistrer la Qualification' }}</span>
      </button>
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

const selectedVerdict = ref('FALSE_POSITIVE')
const correctedAttack = ref('')
const analystNotes = ref('')
const isSubmitting = ref(false)
const feedbackSuccessMsg = ref('')

const incidentId = computed(() => {
  return props.flow ? (props.flow.id || `${props.flow.src_ip}-${props.flow.dst_port}-${props.flow.received_at}`) : ''
})

const existingFeedback = computed(() => {
  return store.incidentFeedbackMap[incidentId.value] || null
})

const verdictPillClass = computed(() => {
  if (!existingFeedback.value) return ''
  const v = existingFeedback.value.human_verdict
  if (v === 'FALSE_POSITIVE') return 'pill-fp'
  if (v === 'KNOWN_ATTACK') return 'pill-reclass'
  if (v === 'CONFIRMED_ZERODAY') return 'pill-zd'
  return ''
})

const verdictLabel = computed(() => {
  if (!existingFeedback.value) return 'Non Qualifié'
  const v = existingFeedback.value.human_verdict
  if (v === 'FALSE_POSITIVE') return 'Faux Positif (Validé)'
  if (v === 'KNOWN_ATTACK') return `Reclassifié : ${existingFeedback.value.corrected_attack_type || 'Attaque'}`
  if (v === 'CONFIRMED_ZERODAY') return `Zero-Day : ${existingFeedback.value.corrected_attack_type || 'Confirmé'}`
  return v
})

const loadExisting = async () => {
  if (!incidentId.value) return
  try {
    const res = await api.getIncidentFeedback(incidentId.value)
    if (res && res.feedback) {
      selectedVerdict.value = res.feedback.human_verdict
      correctedAttack.value = res.feedback.corrected_attack_type || ''
      analystNotes.value = res.feedback.analyst_notes || ''
      store.incidentFeedbackMap[incidentId.value] = {
        human_verdict: res.feedback.human_verdict,
        corrected_attack_type: res.feedback.corrected_attack_type
      }
    }
  } catch (e) {
    // Silently ignore if not found
  }
}

watch(() => props.flow, () => {
  feedbackSuccessMsg.value = ''
  loadExisting()
}, { immediate: true })

const submit = async () => {
  if (!incidentId.value || !selectedVerdict.value) return
  isSubmitting.value = true
  feedbackSuccessMsg.value = ''
  try {
    await store.submitFeedback(
      incidentId.value,
      selectedVerdict.value,
      correctedAttack.value,
      analystNotes.value,
      props.flow
    )
    feedbackSuccessMsg.value = 'Qualification enregistrée pour l\'Active Learning'
    setTimeout(() => {
      feedbackSuccessMsg.value = ''
    }, 4000)
  } catch (err) {
    alert(`Erreur d'enregistrement : ${err.message}`)
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.qualification-form-container {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 16px;
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.section-badge-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.title-with-icon {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.header-icon {
  width: 20px;
  height: 20px;
  color: var(--bl);
  flex-shrink: 0;
  margin-top: 2px;
}

.form-title {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: var(--tx);
}

.form-subtitle {
  font-size: 11.5px;
  color: var(--mu);
}

.verdict-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 11.5px;
  font-weight: 600;
  flex-shrink: 0;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.pill-fp {
  background: rgba(61, 220, 151, 0.12);
  color: var(--ok);
  border: 1px solid rgba(61, 220, 151, 0.3);
}

.pill-reclass {
  background: rgba(255, 181, 71, 0.12);
  color: var(--md);
  border: 1px solid rgba(255, 181, 71, 0.3);
}

.pill-zd {
  background: rgba(178, 102, 255, 0.12);
  color: var(--zd);
  border: 1px solid rgba(178, 102, 255, 0.3);
}

/* Verdict Cards */
.verdict-cards-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.verdict-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  cursor: pointer;
  text-align: left;
  transition: all 0.18s ease;
}

.verdict-card:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.16);
}

.verdict-card.selected {
  background: rgba(88, 101, 242, 0.1);
  border-color: var(--bl);
}

.card-radio-circle {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 1.5px solid var(--mu);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.verdict-card.selected .card-radio-circle {
  border-color: var(--bl);
}

.radio-inner {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--bl);
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.verdict-name {
  font-size: 13px;
  font-weight: 700;
}

.fp-color {
  color: var(--ok);
}

.reclass-color {
  color: var(--md);
}

.zd-color {
  color: var(--zd);
}

.verdict-desc {
  font-size: 11.5px;
  color: var(--mu);
}

/* Subform inputs */
.subform-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.input-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--mu);
}

.soc-select, .soc-text-input, .soc-textarea {
  width: 100%;
  padding: 8px 12px;
  background: #0d0e15;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 6px;
  color: var(--tx);
  font-size: 13px;
  outline: none;
  box-sizing: border-box;
}

.soc-select:focus, .soc-text-input:focus, .soc-textarea:focus {
  border-color: var(--bl);
}

.soc-textarea {
  resize: vertical;
  line-height: 1.4;
}

.form-actions-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-top: 6px;
}

.success-alert {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--ok);
}

.save-qualification-btn {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--bl);
  border: none;
  border-radius: 7px;
  color: white;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.save-qualification-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.save-qualification-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
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
