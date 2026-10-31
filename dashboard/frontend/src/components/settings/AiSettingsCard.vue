<template>
  <div class="card c12 ai-settings-card">
    <div class="card-header-row">
      <div class="header-icon-title">
        <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2a4 4 0 0 0-4 4v1a4 4 0 0 0-3 3.87V13a4 4 0 0 0 3 3.87V18a4 4 0 0 0 4 4h0a4 4 0 0 0 4-4v-1.13A4 4 0 0 0 19 13v-2.13A4 4 0 0 0 16 7V6a4 4 0 0 0-4-4z"/>
          <line x1="12" y1="2" x2="12" y2="22"/>
        </svg>
        <div>
          <h3 class="section-title">Assistant IA & Connecteurs LLM</h3>
          <p class="section-desc">Configuration de l'analyse cognitive automatisée d'incidents (Ollama, Gemini ou Moteur Expert SOC).</p>
        </div>
      </div>

      <div class="header-status-badge active">
        <span class="status-indicator-dot"></span>
        <span>{{ providerBadgeText }}</span>
      </div>
    </div>

    <!-- Choix du Fournisseur IA -->
    <div class="providers-selection-grid">
      <!-- 1. Moteur Expert SOC -->
      <button 
        type="button" 
        class="provider-card" 
        :class="{ active: config.provider === 'expert_rules' }"
        @click="setProvider('expert_rules')"
      >
        <div class="provider-radio">
          <div v-if="config.provider === 'expert_rules'" class="radio-dot"></div>
        </div>
        <div class="provider-meta">
          <div class="provider-name">Moteur Expert SOC (Tier-3)</div>
          <div class="provider-desc">100% autonome et hors-ligne. Règles expertes calibrées sur les anomalies statistiques de l'autoencodeur et les signatures du modèle. Zéro latence, zéro clé API.</div>
        </div>
      </button>

      <!-- 2. Ollama Local -->
      <button 
        type="button" 
        class="provider-card" 
        :class="{ active: config.provider === 'ollama' }"
        @click="setProvider('ollama')"
      >
        <div class="provider-radio">
          <div v-if="config.provider === 'ollama'" class="radio-dot"></div>
        </div>
        <div class="provider-meta">
          <div class="provider-name">Ollama Local (Hors-ligne)</div>
          <div class="provider-desc">Inférence privée sur votre machine via Mistral ou LLaMA 3. Confidentialité totale sans exfiltration de télémétrie.</div>
        </div>
      </button>

      <!-- 3. Google Gemini API -->
      <button 
        type="button" 
        class="provider-card" 
        :class="{ active: config.provider === 'gemini' }"
        @click="setProvider('gemini')"
      >
        <div class="provider-radio">
          <div v-if="config.provider === 'gemini'" class="radio-dot"></div>
        </div>
        <div class="provider-meta">
          <div class="provider-name">Google Gemini API (Cloud)</div>
          <div class="provider-desc">Raisonnement étendu rapide via les modèles Gemini 2.5 Flash pour des diagnostics forensiques détaillés.</div>
        </div>
      </button>
    </div>

    <!-- Paramètres spécifiques au fournisseur choisi -->
    <div v-if="config.provider === 'ollama'" class="provider-config-box">
      <div class="box-title">Paramètres Ollama Local</div>
      <div class="form-row-2">
        <div class="form-group flex-2">
          <label class="field-label" for="ollamaUrl">URL du Serveur Ollama</label>
          <input 
            id="ollamaUrl"
            type="text" 
            v-model="config.ollama_url" 
            placeholder="http://localhost:11434" 
            class="soc-input mono"
            @input="markModified"
          />
        </div>
        <div class="form-group flex-1">
          <label class="field-label" for="ollamaModel">Modèle Ollama</label>
          <input 
            id="ollamaModel"
            type="text" 
            v-model="config.ollama_model" 
            placeholder="mistral:latest" 
            class="soc-input mono"
            @input="markModified"
          />
        </div>
      </div>
    </div>

    <div v-if="config.provider === 'gemini'" class="provider-config-box">
      <div class="box-title">Paramètres Google Gemini API</div>
      <div class="form-row-2">
        <div class="form-group flex-2">
          <label class="field-label" for="geminiKey">Clé API Google Gemini</label>
          <div class="input-with-action">
            <input 
              id="geminiKey"
              :type="showApiKey ? 'text' : 'password'"
              v-model="config.gemini_api_key" 
              placeholder="AIzaSy..." 
              class="soc-input mono"
              @input="markModified"
            />
            <button 
              type="button" 
              class="field-icon-btn" 
              @click="showApiKey = !showApiKey" 
              :title="showApiKey ? 'Masquer' : 'Afficher'"
            >
              <svg v-if="showApiKey" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
              <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
            </button>
          </div>
        </div>
        <div class="form-group flex-1">
          <label class="field-label" for="geminiModel">Modèle Gemini</label>
          <input 
            id="geminiModel"
            type="text" 
            v-model="config.gemini_model" 
            placeholder="gemini-2.5-flash" 
            class="soc-input mono"
            @input="markModified"
          />
        </div>
      </div>
    </div>

    <!-- Zone de test et d'enregistrement -->
    <div class="ai-footer-bar">
      <div class="footer-left">
        <button 
          type="button" 
          class="test-btn" 
          :disabled="isTesting"
          @click="testConnection"
        >
          <svg v-if="!isTesting" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
          <span v-else class="btn-spinner"></span>
          <span>{{ isTesting ? 'Test en cours...' : 'Tester le Fournisseur IA' }}</span>
        </button>

        <span v-if="testMessage" class="test-result-pill" :class="testSuccess ? 'pill-ok' : 'pill-err'">
          {{ testMessage }}
        </span>
      </div>

      <div class="footer-right">
        <span v-if="isModified" class="mod-pill">Modifications non enregistrées</span>
        <button 
          type="button" 
          class="pri save-btn" 
          :disabled="isSaving || !isModified"
          @click="saveConfig"
        >
          <svg v-if="!isSaving" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
          <span v-else class="btn-spinner"></span>
          <span>{{ isSaving ? 'Enregistrement...' : 'Enregistrer la Configuration IA' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/services/api'

const config = ref({
  provider: 'expert_rules',
  ollama_url: 'http://localhost:11434',
  ollama_model: 'mistral:latest',
  gemini_api_key: '',
  gemini_model: 'gemini-2.5-flash'
})

const isModified = ref(false)
const isSaving = ref(false)
const isTesting = ref(false)
const showApiKey = ref(false)
const testMessage = ref('')
const testSuccess = ref(false)

const providerBadgeText = computed(() => {
  if (config.value.provider === 'ollama') return 'Ollama (Local)'
  if (config.value.provider === 'gemini') return 'Gemini (Cloud)'
  return 'Moteur Expert (Tier-3)'
})

const setProvider = (p) => {
  config.value.provider = p
  markModified()
}

const markModified = () => {
  isModified.value = true
}

const loadConfig = async () => {
  try {
    const res = await api.getAiSettings()
    if (res) {
      config.value = { ...config.value, ...res }
      isModified.value = false
    }
  } catch (err) {
    console.error('Erreur chargement config IA:', err)
  }
}

const saveConfig = async () => {
  isSaving.value = true
  try {
    const res = await api.updateAiSettings(config.value)
    if (res && res.status === 'success') {
      config.value = { ...config.value, ...res.config }
      isModified.value = false
    }
  } catch (err) {
    alert(`Erreur d'enregistrement : ${err.message}`)
  } finally {
    isSaving.value = false
  }
}

const testConnection = async () => {
  isTesting.value = true
  testMessage.value = ''
  try {
    const res = await api.testAiConnection(config.value)
    testSuccess.value = Boolean(res.success)
    testMessage.value = res.message || (res.success ? 'Connectivité validée' : 'Échec du test')
  } catch (err) {
    testSuccess.value = false
    testMessage.value = err.message || 'Erreur réseau'
  } finally {
    isTesting.value = false
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.ai-settings-card {
  display: flex;
  flex-direction: column;
  gap: 20px;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: var(--r);
  padding: 22px;
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--line);
}

.header-icon-title {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.section-icon {
  width: 24px;
  height: 24px;
  color: #a78bfa;
  flex-shrink: 0;
  margin-top: 2px;
}

.section-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--tx);
}

.section-desc {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--mu);
}

.header-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 12px;
  border-radius: 20px;
  background: rgba(167, 139, 250, 0.12);
  color: #c4b5fd;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid rgba(167, 139, 250, 0.3);
}

.status-indicator-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}

/* Providers Grid */
.providers-selection-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}

@media (max-width: 900px) {
  .providers-selection-grid {
    grid-template-columns: 1fr;
  }
}

.provider-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: var(--panel2);
  border: 1px solid var(--line);
  border-radius: 10px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.provider-card:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.16);
}

.provider-card.active {
  background: rgba(167, 139, 250, 0.08);
  border-color: #a78bfa;
  box-shadow: 0 0 12px rgba(167, 139, 250, 0.1);
}

.provider-radio {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 1.5px solid var(--mu);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.provider-card.active .provider-radio {
  border-color: #a78bfa;
}

.radio-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #a78bfa;
}

.provider-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.provider-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--tx);
}

.provider-desc {
  font-size: 11.5px;
  line-height: 1.45;
  color: var(--mu);
}

/* Config Box */
.provider-config-box {
  background: var(--panel2);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.box-title {
  font-size: 13px;
  font-weight: 700;
  color: #c4b5fd;
}

.form-row-2 {
  display: flex;
  gap: 14px;
}

.flex-1 { flex: 1; }
.flex-2 { flex: 2; }

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--mu);
}

.soc-input {
  width: 100%;
  padding: 8px 12px;
  background: var(--bg);
  border: 1px solid var(--line);
  border-radius: 8px;
  color: var(--tx);
  font-size: 13px;
  outline: none;
}

.soc-input:focus {
  border-color: #a78bfa;
}

.input-with-action {
  position: relative;
  display: flex;
  align-items: center;
}

.input-with-action input {
  padding-right: 36px;
}

.field-icon-btn {
  position: absolute;
  right: 8px;
  background: none;
  border: none;
  color: var(--mu);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
}

.field-icon-btn:hover {
  color: var(--tx);
}

/* Footer Bar */
.ai-footer-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 14px;
  border-top: 1px solid var(--line);
  flex-wrap: wrap;
  gap: 12px;
}

.footer-left, .footer-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.test-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(167, 139, 250, 0.1);
  border: 1px solid rgba(167, 139, 250, 0.25);
  border-radius: 8px;
  color: #c4b5fd;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.test-btn:hover:not(:disabled) {
  background: rgba(167, 139, 250, 0.2);
  border-color: #a78bfa;
}

.test-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.test-result-pill {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 6px;
}

.pill-ok {
  background: rgba(61, 220, 151, 0.1);
  color: var(--ok);
  border: 1px solid rgba(61, 220, 151, 0.25);
}

.pill-err {
  background: rgba(255, 77, 126, 0.1);
  color: var(--cr);
  border: 1px solid rgba(255, 77, 126, 0.25);
}

.mod-pill {
  font-size: 12px;
  font-weight: 600;
  color: var(--md);
}

.save-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 20px;
  background: #7c3aed;
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.save-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.save-btn:disabled {
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
