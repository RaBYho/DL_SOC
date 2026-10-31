<template>
  <main>
    <div class="card" style="margin-bottom: 16px;">
      <h2>
        {{ store.t('settings.title') }}
        <span>{{ store.t('settings.subtitle') }}</span>
      </h2>
      <p style="color:var(--mu); font-size: 13px; margin: 0;">
        {{ store.t('settings.desc') }}
      </p>
    </div>

    <section class="grid">
      <!-- Identity & Language -->
      <div class="card c6">
        <h2>{{ store.t('settings.brandingTitle') }}</h2>
        <div class="form-container">
          <div class="form-group">
            <label class="form-label">{{ store.t('settings.appNameLabel') }}</label>
            <div class="input-with-icon">
              <input 
                v-model="customName" 
                type="text" 
                :placeholder="store.t('settings.appNamePlaceholder')"
                class="soc-input"
                @input="onNameChange"
              />
              <button 
                v-if="customName !== 'DL_SOC'"
                @click="resetName" 
                class="mini-btn" 
                title="Reset to default"
              >
                Reset
              </button>
            </div>
            <small class="form-help">{{ store.t('settings.appNameHelp') }}</small>
          </div>

          <div class="form-group">
            <label class="form-label">{{ store.t('settings.langLabel') }}</label>
            <div class="lang-toggle-group">
              <button 
                class="lang-choice-btn" 
                :class="{ active: store.lang === 'FR' }"
                @click="store.setLanguage('FR')"
              >
                <span class="flag-icon">🇫🇷</span>
                <span>Français (FR)</span>
              </button>
              <button 
                class="lang-choice-btn" 
                :class="{ active: store.lang === 'EN' }"
                @click="store.setLanguage('EN')"
              >
                <span class="flag-icon">🇬🇧</span>
                <span>English (EN)</span>
              </button>
            </div>
          </div>

          <div v-if="savedFeedback" class="save-toast">
            ✓ {{ store.lang === 'FR' ? 'Paramètres appliqués avec succès !' : 'Settings applied successfully!' }}
          </div>
        </div>
      </div>

      <!-- Detection Thresholds -->
      <div class="card c6">
        <h2>{{ store.t('settings.thresholdsTitle') }}</h2>
        <div class="form-container">
          <div class="form-group">
            <label class="form-label">{{ store.t('settings.aeThresholdLabel') }}</label>
            <input 
              v-model.number="store.aeThreshold" 
              type="number" 
              step="0.0001" 
              min="0.1" 
              max="2.0" 
              class="soc-input"
            />
            <small class="form-help">{{ store.t('settings.aeHelp') }}</small>
          </div>

          <div class="form-group">
            <label class="form-label">{{ store.t('settings.minConfLabel') }}</label>
            <input 
              v-model.number="minConf" 
              type="number" 
              min="10" 
              max="99" 
              class="soc-input"
            />
          </div>

          <button class="pri" @click="saveSettings" style="margin-top:4px;">
            {{ store.t('settings.saveBtn') }}
          </button>
        </div>
      </div>

      <!-- Storage & Ingest -->
      <div class="card c12">
        <h2>{{ store.t('settings.telemetryTitle') }}</h2>
        <div class="kv" style="margin-top:10px;">
          <span>{{ store.t('settings.dbFile') }}</span><span class="mono">nids.db</span>
          <span>{{ store.t('settings.indexedCols') }}</span><span>received_at, pred, anomalie_ae, src_ip, dst_port</span>
          <span>{{ store.t('settings.storageEngine') }}</span><span>SQLite WAL Mode (Write-Ahead-Log)</span>
          <span>{{ store.t('settings.wsStream') }}</span><span style="color:var(--ok);">ws://localhost:8000/ws</span>
          <span>{{ store.t('settings.retention') }}</span><span>30 Days Rolling Window</span>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup>
import { ref } from 'vue'
import { useSocStore } from '@/stores/socStore'

const store = useSocStore()
const minConf = ref(70)
const customName = ref(store.appName)
const savedFeedback = ref(false)

function onNameChange() {
  if (customName.value && customName.value.trim().length > 0) {
    store.setAppName(customName.value.trim())
  }
}

function resetName() {
  customName.value = 'DL_SOC'
  store.setAppName('DL_SOC')
}

function saveSettings() {
  if (customName.value && customName.value.trim().length > 0) {
    store.setAppName(customName.value.trim())
  }
  savedFeedback.value = true
  setTimeout(() => {
    savedFeedback.value = false
  }, 2500)
}
</script>

<style scoped>
.form-container {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 12px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--tx);
}

.form-help {
  color: var(--mu);
  font-size: 11px;
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
  transition: border-color 0.15s ease;
}

.soc-input:focus {
  outline: none;
  border-color: var(--bl);
}

.input-with-icon {
  display: flex;
  gap: 8px;
}

.mini-btn {
  padding: 0 12px;
  font-size: 11px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--line);
  color: var(--mu);
  border-radius: 6px;
  cursor: pointer;
  white-space: nowrap;
}

.mini-btn:hover {
  color: var(--tx);
  background: rgba(255, 255, 255, 0.12);
}

.lang-toggle-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.lang-choice-btn {
  flex: 1;
  min-width: 130px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 14px;
  min-height: 42px;
  background: var(--panel2);
  border: 1px solid var(--line);
  border-radius: 7px;
  color: var(--tx);
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.lang-choice-btn:hover {
  background: rgba(88, 101, 242, 0.12);
  border-color: var(--bl);
}

.lang-choice-btn.active {
  background: rgba(88, 101, 242, 0.22);
  border-color: var(--bl);
  color: #fff;
  box-shadow: 0 0 12px rgba(88, 101, 242, 0.25);
}

.flag-icon {
  font-size: 16px;
}

.save-toast {
  padding: 8px 12px;
  background: rgba(61, 220, 151, 0.15);
  border: 1px solid var(--ok);
  border-radius: 6px;
  color: var(--ok);
  font-size: 12px;
  font-weight: 600;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
