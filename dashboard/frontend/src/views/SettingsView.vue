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
      <!-- Interface Language (Only place to change language) -->
      <div class="card c6">
        <h2>{{ store.t('settings.langTitle') }}</h2>
        <p class="section-desc">{{ store.t('settings.langDesc') }}</p>
        <div class="form-container">
          <div class="lang-toggle-group">
            <button 
              class="lang-choice-btn" 
              :class="{ active: store.lang === 'FR' }"
              @click="setLanguage('FR')"
            >
              <span class="lang-tag">FR</span>
              <div class="lang-meta">
                <b class="lang-name">Français</b>
                <span class="lang-sub">Langue du système</span>
              </div>
            </button>
            <button 
              class="lang-choice-btn" 
              :class="{ active: store.lang === 'EN' }"
              @click="setLanguage('EN')"
            >
              <span class="lang-tag">EN</span>
              <div class="lang-meta">
                <b class="lang-name">English</b>
                <span class="lang-sub">System language</span>
              </div>
            </button>
          </div>

          <div v-if="savedFeedback" class="save-toast">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            <span>{{ store.lang === 'FR' ? 'Langue appliquée avec succès' : 'Language updated successfully' }}</span>
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

          <button class="pri" @click="saveThresholds" style="margin-top:4px;">
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
const savedFeedback = ref(false)

function setLanguage(lang) {
  store.setLanguage(lang)
  savedFeedback.value = true
  setTimeout(() => {
    savedFeedback.value = false
  }, 2200)
}

function saveThresholds() {
  savedFeedback.value = true
  setTimeout(() => {
    savedFeedback.value = false
  }, 2200)
}
</script>

<style scoped>
.section-desc {
  color: var(--mu);
  font-size: 12.5px;
  margin: 6px 0 12px;
}

.form-container {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 4px;
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

.lang-toggle-group {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.lang-choice-btn {
  flex: 1;
  min-width: 140px;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  min-height: 48px;
  background: var(--panel2);
  border: 1px solid var(--line);
  border-radius: 9px;
  color: var(--tx);
  cursor: pointer;
  transition: all 0.16s ease;
  text-align: left;
}

.lang-choice-btn:hover {
  background: rgba(88, 101, 242, 0.12);
  border-color: var(--bl);
}

.lang-choice-btn.active {
  background: rgba(88, 101, 242, 0.2);
  border-color: var(--bl);
  color: #fff;
  box-shadow: 0 0 14px rgba(88, 101, 242, 0.25);
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

.save-toast {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: rgba(61, 220, 151, 0.14);
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
