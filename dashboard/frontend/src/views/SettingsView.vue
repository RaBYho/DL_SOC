<template>
  <main class="settings-page">
    <!-- Header Card -->
    <div class="card header-card">
      <div class="header-titles">
        <h2 class="card-title">
          {{ store.t('settings.title') }}
          <span class="card-subtitle-badge">{{ store.t('settings.subtitle') }}</span>
        </h2>
        <span class="card-subtitle">{{ store.t('settings.desc') }}</span>
      </div>
    </div>

    <!-- Main Settings Bento Grid -->
    <section class="grid settings-grid">
      <!-- Section 1: Interface Language -->
      <div class="card c6 settings-card">
        <div class="card-header-row">
          <div class="header-icon-title">
            <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="2" y1="12" x2="22" y2="12" />
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
            </svg>
            <h3 class="section-title">{{ store.t('settings.langTitle') }}</h3>
          </div>
          <span v-if="draftLang !== store.lang" class="status-chip chip-modified">
            {{ store.lang === 'FR' ? 'Modifié' : 'Modified' }}
          </span>
        </div>
        <p class="section-desc">{{ store.t('settings.langDesc') }}</p>

        <div class="lang-toggle-group">
          <button 
            type="button"
            class="lang-choice-btn" 
            :class="{ active: draftLang === 'FR' }"
            @click="draftLang = 'FR'"
            aria-label="Français"
          >
            <span class="lang-tag">FR</span>
            <div class="lang-meta">
              <b class="lang-name">Français</b>
              <span class="lang-sub">Langue du système</span>
            </div>
            <span v-if="draftLang === 'FR'" class="active-check">✓</span>
          </button>

          <button 
            type="button"
            class="lang-choice-btn" 
            :class="{ active: draftLang === 'EN' }"
            @click="draftLang = 'EN'"
            aria-label="English"
          >
            <span class="lang-tag">EN</span>
            <div class="lang-meta">
              <b class="lang-name">English</b>
              <span class="lang-sub">System language</span>
            </div>
            <span v-if="draftLang === 'EN'" class="active-check">✓</span>
          </button>
        </div>
      </div>

      <!-- Section 2: AI Detection Thresholds -->
      <div class="card c6 settings-card">
        <div class="card-header-row">
          <div class="header-icon-title">
            <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 20v-6M6 20V10M18 20V4" />
            </svg>
            <h3 class="section-title">{{ store.t('settings.thresholdsTitle') }}</h3>
          </div>
          <span v-if="isThresholdsModified" class="status-chip chip-modified">
            {{ store.lang === 'FR' ? 'Modifié' : 'Modified' }}
          </span>
        </div>
        <p class="section-desc">{{ store.t('settings.aeHelp') }}</p>

        <div class="thresholds-form">
          <div class="form-group">
            <div class="label-row">
              <label class="form-label" for="aeThresholdInput">
                {{ store.t('settings.aeThresholdLabel') }}
              </label>
              <span class="current-tag mono">Actuel : {{ store.aeThreshold }}</span>
            </div>
            <input 
              id="aeThresholdInput"
              v-model.number="draftAeThreshold" 
              type="number" 
              step="0.0001" 
              min="0.1" 
              max="2.0" 
              class="soc-input"
            />
          </div>

          <div class="form-group">
            <div class="label-row">
              <label class="form-label" for="minConfInput">
                {{ store.t('settings.minConfLabel') }}
              </label>
              <span class="current-tag mono">Actuel : {{ store.filterMinConfidence || 70 }}%</span>
            </div>
            <input 
              id="minConfInput"
              v-model.number="draftMinConf" 
              type="number" 
              min="10" 
              max="99" 
              class="soc-input"
            />
          </div>
        </div>
      </div>

      <!-- Section 3: Database & Node Telemetry (Single unified card) -->
      <div class="card c12 telemetry-maintenance-card">
        <div class="card-header-row">
          <div class="header-icon-title">
            <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <ellipse cx="12" cy="5" rx="9" ry="3" />
              <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
              <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
            </svg>
            <h3 class="section-title">{{ store.t('settings.telemetryTitle') }}</h3>
          </div>
          <span class="node-live-tag">
            <span class="pulse-dot"></span>
            SQLite WAL Mode
          </span>
        </div>

        <div class="database-unified-grid">
          <!-- Left: Telemetry Specs -->
          <div class="telemetry-col">
            <div class="kv">
              <span>{{ store.t('settings.dbFile') }}</span>
              <span class="mono">nids.db</span>
              <span>{{ store.t('settings.indexedCols') }}</span>
              <span class="mono">received_at, pred, anomalie_ae, src_ip, dst_port</span>
              <span>{{ store.t('settings.wsStream') }}</span>
              <span class="mono ok-text">ws://localhost:8000/ws</span>
              <span>{{ store.t('settings.retention') }}</span>
              <span>30 Days Rolling Window</span>
            </div>
          </div>

          <!-- Right: Database Purge / Reset Action -->
          <div class="maintenance-danger-col">
            <div class="danger-box">
              <div class="danger-meta">
                <div class="danger-title-row">
                  <svg class="danger-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                  </svg>
                  <h4>{{ store.t('settings.resetDbTitle') }}</h4>
                </div>
                <p class="danger-desc">{{ store.t('settings.resetDbDesc') }}</p>
              </div>

              <button 
                type="button"
                class="danger-action-btn"
                @click="openResetModal"
                aria-label="Réinitialiser la base de données"
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
                <span>{{ store.t('settings.resetDbBtn') }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Section 4: Multi-Channel Alerts & Notifications (Telegram & SMTP) -->
      <NotificationSettingsCard />

      <!-- Section 5: AI Assistant & LLM Connectors -->
      <AiSettingsCard />
    </section>

    <!-- Floating Dock: Single Unified Bottom Save Bar when changes exist -->
    <transition name="dock-slide">
      <div v-if="hasChanges" class="floating-save-dock" role="region" aria-label="Unsaved settings">
        <div class="dock-content">
          <div class="dock-meta">
            <span class="pulse-indicator"></span>
            <span class="dock-title">{{ store.t('settings.savePending') }}</span>
          </div>
          <div class="dock-actions">
            <button type="button" class="revert-btn" @click="revertChanges">
              {{ store.t('settings.cancelBtn') }}
            </button>
            <button type="button" class="pri dock-save-btn" @click="openSettingsModal">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
              <span>{{ store.t('settings.saveBtn') }}</span>
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Modal 1: Confirmation des Paramètres -->
    <transition name="modal-fade">
      <div 
        v-if="showSettingsModal" 
        class="modal-backdrop" 
        @click.self="closeSettingsModal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="settingsModalTitle"
      >
        <div class="modal-card">
          <div class="modal-header">
            <div class="modal-icon-wrap settings-icon-wrap">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
              </svg>
            </div>
            <div class="modal-title-stack">
              <h3 id="settingsModalTitle" class="modal-title">{{ store.t('settings.confirmSettingsTitle') }}</h3>
              <p class="modal-subtitle">{{ store.t('settings.confirmSettingsDesc') }}</p>
            </div>
            <button class="modal-close-btn" @click="closeSettingsModal" aria-label="Fermer">✕</button>
          </div>

          <div class="modal-body">
            <div class="change-summary-list">
              <div class="change-row">
                <span class="change-label">{{ store.t('settings.langChange') }}</span>
                <div class="change-values">
                  <span class="old-val">{{ store.lang === 'FR' ? 'Français' : 'English' }}</span>
                  <span class="arrow-sep">→</span>
                  <b class="new-val">{{ draftLang === 'FR' ? 'Français' : 'English' }}</b>
                </div>
              </div>

              <div class="change-row">
                <span class="change-label">{{ store.t('settings.aeChange') }}</span>
                <div class="change-values">
                  <span class="old-val mono">{{ store.aeThreshold }}</span>
                  <span class="arrow-sep">→</span>
                  <b class="new-val mono">{{ draftAeThreshold }}</b>
                </div>
              </div>

              <div class="change-row">
                <span class="change-label">{{ store.t('settings.confChange') }}</span>
                <div class="change-values">
                  <span class="old-val mono">{{ store.filterMinConfidence || 70 }}%</span>
                  <span class="arrow-sep">→</span>
                  <b class="new-val mono">{{ draftMinConf }}%</b>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="modal-cancel-btn" @click="closeSettingsModal">
              {{ store.t('settings.cancelBtn') }}
            </button>
            <button type="button" class="pri modal-confirm-btn" @click="confirmApplySettings">
              {{ store.t('settings.confirmSettingsBtn') }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Modal 2: Confirmation de Réinitialisation Critique de la Base -->
    <transition name="modal-fade">
      <div 
        v-if="showResetModal" 
        class="modal-backdrop" 
        @click.self="closeResetModal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="resetModalTitle"
      >
        <div class="modal-card modal-card-danger">
          <div class="modal-header">
            <div class="modal-icon-wrap danger-icon-wrap">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                <line x1="12" y1="9" x2="12" y2="13"></line>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
              </svg>
            </div>
            <div class="modal-title-stack">
              <h3 id="resetModalTitle" class="modal-title danger-text">{{ store.t('settings.confirmResetTitle') }}</h3>
              <p class="modal-subtitle">{{ store.t('settings.confirmResetDesc') }}</p>
            </div>
            <button class="modal-close-btn" @click="closeResetModal" aria-label="Fermer">✕</button>
          </div>

          <div class="modal-body">
            <div class="danger-warning-callout">
              <div class="callout-point">
                <span class="bullet">⚠</span>
                <span>Effacement complet de la table <code>flows</code> (toutes les alertes et flux capturés).</span>
              </div>
              <div class="callout-point">
                <span class="bullet">⚠</span>
                <span>Remise à zéro immédiate du flux en direct et des métriques analytiques.</span>
              </div>
              <div class="callout-point">
                <span class="bullet">⚠</span>
                <span>Exécution de <code>VACUUM</code> pour compacter la base SQLite locale.</span>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="modal-cancel-btn" :disabled="isResetting" @click="closeResetModal">
              {{ store.t('settings.cancelBtn') }}
            </button>
            <button 
              type="button"
              class="danger-confirm-btn" 
              :disabled="isResetting"
              @click="confirmResetDatabase"
            >
              <span v-if="isResetting" class="btn-spinner"></span>
              <span>{{ isResetting ? 'Réinitialisation en cours...' : store.t('settings.confirmResetBtn') }}</span>
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Toast Feedback Notification -->
    <transition name="toast-fade">
      <div v-if="toastMessage" class="feedback-toast" :class="toastType">
        <svg v-if="toastType === 'toast-success'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
        <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        <span>{{ toastMessage }}</span>
      </div>
    </transition>
  </main>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useSocStore } from '@/stores/socStore'
import NotificationSettingsCard from '@/components/settings/NotificationSettingsCard.vue'
import AiSettingsCard from '@/components/settings/AiSettingsCard.vue'

const store = useSocStore()

// Local Draft State (Modifications do NOT apply until confirmed)
const draftLang = ref(store.lang)
const draftAeThreshold = ref(store.aeThreshold)
const draftMinConf = ref(store.filterMinConfidence || 70)

// Modal & Loading States
const showSettingsModal = ref(false)
const showResetModal = ref(false)
const isResetting = ref(false)

// Toast Feedback State
const toastMessage = ref('')
const toastType = ref('toast-success')
let toastTimer = null

const isThresholdsModified = computed(() => {
  const aeChanged = Number(draftAeThreshold.value) !== Number(store.aeThreshold)
  const confChanged = Number(draftMinConf.value) !== Number(store.filterMinConfidence || 70)
  return aeChanged || confChanged
})

const hasChanges = computed(() => {
  return draftLang.value !== store.lang || isThresholdsModified.value
})

function revertChanges() {
  draftLang.value = store.lang
  draftAeThreshold.value = store.aeThreshold
  draftMinConf.value = store.filterMinConfidence || 70
}

function openSettingsModal() {
  showSettingsModal.value = true
}

function closeSettingsModal() {
  showSettingsModal.value = false
}

function openResetModal() {
  showResetModal.value = true
}

function closeResetModal() {
  if (isResetting.value) return
  showResetModal.value = false
}

async function confirmApplySettings() {
  try {
    await store.applySettings({
      lang: draftLang.value,
      aeThreshold: draftAeThreshold.value,
      minConfidence: draftMinConf.value
    })
    closeSettingsModal()
    showToast(store.t('settings.saveSuccess'), 'toast-success')
  } catch (err) {
    console.error('Erreur lors de l\'enregistrement des paramètres:', err)
    showToast('Erreur lors de l\'enregistrement des paramètres', 'toast-error')
  }
}

async function confirmResetDatabase() {
  isResetting.value = true
  try {
    await store.resetDatabase()
    showResetModal.value = false
    showToast(store.t('settings.resetSuccess'), 'toast-success')
  } catch (err) {
    console.error('Erreur lors de la réinitialisation de la base:', err)
    showToast('Échec de la réinitialisation de la base de données', 'toast-error')
  } finally {
    isResetting.value = false
    showResetModal.value = false
  }
}

function showToast(msg, type = 'toast-success') {
  toastMessage.value = msg
  toastType.value = type
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toastMessage.value = ''
  }, 2800)
}

function onKeyDown(e) {
  if (e.key === 'Escape') {
    if (showSettingsModal.value) closeSettingsModal()
    if (showResetModal.value && !isResetting.value) closeResetModal()
  }
}

onMounted(() => {
  store.init()
  window.addEventListener('keydown', onKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
  if (toastTimer) clearTimeout(toastTimer)
})
</script>

<style scoped>
.settings-page {
  position: relative;
  padding-bottom: 60px;
}

/* Header */
.header-card {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
}

.header-titles {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.card-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #fff;
}

.card-subtitle-badge {
  font-size: 11px;
  font-weight: 600;
  background: rgba(88, 101, 242, 0.2);
  color: var(--lo);
  border: 1px solid rgba(88, 101, 242, 0.35);
  padding: 2px 8px;
  border-radius: 12px;
}

.card-subtitle {
  font-size: 12.5px;
  color: var(--mu);
}

/* Settings Bento Grid */
.settings-grid {
  display: grid;
  gap: 16px;
}

.settings-card {
  display: flex;
  flex-direction: column;
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.header-icon-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-icon {
  width: 17px;
  height: 17px;
  color: var(--lo);
}

.section-title {
  margin: 0;
  font-size: 14.5px;
  font-weight: 700;
  color: #fff;
}

.status-chip {
  font-size: 10.5px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 4px;
  letter-spacing: 0.3px;
}

.chip-modified {
  background: rgba(255, 181, 71, 0.16);
  color: var(--md);
  border: 1px solid rgba(255, 181, 71, 0.35);
}

.section-desc {
  color: var(--mu);
  font-size: 12px;
  margin: 0 0 14px 0;
  line-height: 1.45;
}

/* Language Selector */
.lang-toggle-group {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.lang-choice-btn {
  display: inline-flex;
  align-items: center;
  position: relative;
  gap: 12px;
  padding: 12px 16px;
  min-height: 52px;
  background: var(--panel2);
  border: 1px solid var(--line);
  border-radius: 10px;
  color: var(--tx);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  text-align: left;
}

.lang-choice-btn:hover {
  background: rgba(88, 101, 242, 0.12);
  border-color: rgba(88, 101, 242, 0.4);
}

.lang-choice-btn.active {
  background: rgba(88, 101, 242, 0.22);
  border-color: var(--ac);
  color: #fff;
  box-shadow: 0 0 16px rgba(88, 101, 242, 0.3);
}

.lang-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 6px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.5px;
  color: var(--tx);
}

.lang-choice-btn.active .lang-tag {
  background: var(--ac);
  border-color: var(--ac);
  color: #fff;
}

.lang-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
}

.lang-name {
  font-size: 13.5px;
  font-weight: 700;
}

.lang-sub {
  font-size: 11px;
  color: var(--mu);
}

.active-check {
  margin-left: auto;
  color: var(--ok);
  font-weight: 800;
  font-size: 14px;
}

/* Thresholds Form */
.thresholds-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--tx);
}

.current-tag {
  font-size: 11px;
  color: var(--mu);
}

.soc-input {
  width: 100%;
  padding: 8px 12px;
  background: var(--panel2);
  border: 1px solid var(--line);
  border-radius: 6px;
  color: var(--tx);
  font-size: 13px;
  box-sizing: border-box;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.soc-input:focus {
  outline: none;
  border-color: var(--ac);
  box-shadow: 0 0 0 2px rgba(88, 101, 242, 0.25);
}

/* Unified Telemetry & Maintenance Card */
.telemetry-maintenance-card {
  display: flex;
  flex-direction: column;
}

.node-live-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--ok);
  background: rgba(61, 220, 151, 0.1);
  border: 1px solid rgba(61, 220, 151, 0.25);
  padding: 2px 10px;
  border-radius: 12px;
}

.database-unified-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-top: 10px;
  align-items: start;
}

.ok-text {
  color: var(--ok);
}

.maintenance-danger-col {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.danger-box {
  background: rgba(255, 77, 126, 0.06);
  border: 1px solid rgba(255, 77, 126, 0.25);
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 14px;
  height: 100%;
  box-sizing: border-box;
}

.danger-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.danger-title-row h4 {
  margin: 0;
  font-size: 13.5px;
  font-weight: 700;
  color: #fff;
}

.danger-icon {
  width: 16px;
  height: 16px;
  color: var(--cr);
  flex: none;
}

.danger-desc {
  margin: 0;
  font-size: 12px;
  color: var(--mu);
  line-height: 1.45;
}

.danger-action-btn {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 12.5px;
  font-weight: 600;
  background: rgba(255, 77, 126, 0.14);
  border: 1px solid rgba(255, 77, 126, 0.4);
  color: #ff6b8b;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.danger-action-btn:hover {
  background: rgba(255, 77, 126, 0.24);
  border-color: var(--cr);
  color: #fff;
  box-shadow: 0 0 16px rgba(255, 77, 126, 0.35);
}

/* Floating Dock for Save Action (Linear/Vercel-style) */
.floating-save-dock {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 900;
  width: auto;
  min-width: 420px;
  max-width: 90vw;
}

.dock-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-radius: 12px;
  background: rgba(24, 25, 38, 0.94);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(88, 101, 242, 0.45);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.08);
  gap: 20px;
}

.dock-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pulse-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--md);
  box-shadow: 0 0 10px var(--md);
  animation: pulse-dot 1.8s infinite;
}

.dock-title {
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
}

.dock-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.revert-btn {
  background: transparent;
  border: 1px solid var(--line);
  color: var(--mu);
  padding: 7px 14px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.revert-btn:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.2);
}

.dock-save-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 16px;
  font-size: 12.5px;
  font-weight: 600;
  white-space: nowrap;
}

/* Modals Overlay & Card */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(8, 9, 14, 0.8);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.modal-card {
  width: 100%;
  max-width: 480px;
  background: #191a27;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: modal-pop 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}

.modal-card-danger {
  border-color: rgba(255, 77, 126, 0.45);
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.7), 0 0 24px rgba(255, 77, 126, 0.15);
}

@keyframes modal-pop {
  from { opacity: 0; transform: scale(0.96) translateY(8px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.modal-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 18px 20px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  position: relative;
}

.modal-icon-wrap {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: none;
}

.settings-icon-wrap {
  background: rgba(88, 101, 242, 0.18);
  border: 1px solid rgba(88, 101, 242, 0.35);
  color: var(--lo);
}

.danger-icon-wrap {
  background: rgba(255, 77, 126, 0.18);
  border: 1px solid rgba(255, 77, 126, 0.4);
  color: var(--cr);
}

.modal-title-stack {
  flex: 1;
}

.modal-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  line-height: 1.3;
}

.danger-text {
  color: #ff6b8b;
}

.modal-subtitle {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--mu);
  line-height: 1.4;
}

.modal-close-btn {
  background: transparent;
  border: none;
  color: var(--mu);
  font-size: 16px;
  cursor: pointer;
  padding: 4px;
  line-height: 1;
  border-radius: 4px;
  transition: color 0.15s ease;
}

.modal-close-btn:hover {
  color: #fff;
}

.modal-body {
  padding: 18px 20px;
}

.change-summary-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: rgba(0, 0, 0, 0.28);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  padding: 12px 14px;
}

.change-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12.5px;
}

.change-label {
  color: var(--mu);
}

.change-values {
  display: flex;
  align-items: center;
  gap: 8px;
}

.old-val {
  color: var(--mu);
  text-decoration: line-through;
  opacity: 0.7;
}

.arrow-sep {
  color: var(--mu);
  font-size: 11px;
}

.new-val {
  color: #fff;
}

.danger-warning-callout {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: rgba(255, 77, 126, 0.08);
  border: 1px solid rgba(255, 77, 126, 0.25);
  border-radius: 8px;
  padding: 12px 14px;
}

.callout-point {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 12px;
  line-height: 1.4;
  color: #ffd2dc;
}

.callout-point .bullet {
  color: var(--cr);
  font-size: 12px;
  flex: none;
}

.callout-point code {
  background: rgba(0, 0, 0, 0.35);
  padding: 1px 4px;
  border-radius: 3px;
  font-family: ui-monospace, monospace;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(0, 0, 0, 0.15);
}

.modal-cancel-btn {
  background: transparent;
  border: 1px solid var(--line);
  color: var(--mu);
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.modal-cancel-btn:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
}

.modal-confirm-btn {
  padding: 8px 18px;
  font-size: 12.5px;
  font-weight: 600;
}

.danger-confirm-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--cr);
  border: 1px solid var(--cr);
  color: #fff;
  padding: 8px 18px;
  border-radius: 6px;
  font-size: 12.5px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 2px 10px rgba(255, 77, 126, 0.35);
}

.danger-confirm-btn:hover:not(:disabled) {
  background: #ff2f67;
  box-shadow: 0 4px 18px rgba(255, 77, 126, 0.5);
}

.danger-confirm-btn:disabled {
  opacity: 0.6;
  cursor: wait;
}

.btn-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Toast Notification */
.feedback-toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 1200;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: 8px;
  font-size: 12.5px;
  font-weight: 600;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.toast-success {
  background: rgba(20, 36, 28, 0.95);
  border: 1px solid var(--ok);
  color: var(--ok);
}

.toast-error {
  background: rgba(38, 18, 24, 0.95);
  border: 1px solid var(--cr);
  color: var(--cr);
}

/* Transitions */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.dock-slide-enter-active,
.dock-slide-leave-active {
  transition: transform 0.24s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.24s ease;
}

.dock-slide-enter-from,
.dock-slide-leave-to {
  opacity: 0;
  transform: translate(-50%, 20px);
}

.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

/* Responsive */
@media (max-width: 860px) {
  .database-unified-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}

@media (max-width: 600px) {
  .lang-toggle-group {
    grid-template-columns: 1fr;
  }
  .floating-save-dock {
    min-width: calc(100vw - 32px);
    bottom: 74px; /* above mobile bottom nav */
  }
  .dock-content {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  .dock-actions {
    justify-content: flex-end;
  }
}
</style>