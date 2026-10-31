<template>
  <div class="card c12 notification-settings-card">
    <!-- Header Row -->
    <div class="card-header-row">
      <div class="header-icon-title">
        <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
        <div>
          <h3 class="section-title">Canaux d'Alerte & Notifications Multi-Canal</h3>
          <p class="section-desc">Diffusion instantanée hors-dashboard avec moteur de throttling anti-spam (fenêtre de 60s).</p>
        </div>
      </div>

      <div class="header-status-badge" :class="{ active: config.telegram_enabled || config.email_enabled }">
        <span class="status-indicator-dot"></span>
        <span>{{ (config.telegram_enabled || config.email_enabled) ? 'Actif' : 'Désactivé' }}</span>
      </div>
    </div>

    <!-- Channels Grid (Telegram & Email) -->
    <div class="channels-grid">
      <!-- Canal Telegram -->
      <div class="channel-card" :class="{ 'channel-active': config.telegram_enabled }">
        <div class="channel-header">
          <div class="channel-brand">
            <svg class="brand-icon telegram-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
            <div>
              <h4 class="channel-name">Telegram Bot</h4>
              <span class="channel-hint">Alertes instantanées et rapports digest</span>
            </div>
          </div>
          <label class="switch-toggle" aria-label="Activer Telegram">
            <input type="checkbox" v-model="config.telegram_enabled" @change="markModified" />
            <span class="slider"></span>
          </label>
        </div>

        <div class="channel-body">
          <div class="form-group">
            <label class="field-label" for="tgBotToken">Bot Token Telegram</label>
            <div class="input-with-action">
              <input 
                id="tgBotToken"
                :type="showTgToken ? 'text' : 'password'"
                v-model="config.telegram_bot_token"
                placeholder="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
                class="soc-input mono"
                @input="markModified"
              />
              <button 
                type="button" 
                class="field-icon-btn" 
                @click="showTgToken = !showTgToken" 
                :title="showTgToken ? 'Masquer' : 'Afficher'"
              >
                <svg v-if="showTgToken" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
                <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
              </button>
            </div>
          </div>

          <div class="form-group">
            <label class="field-label" for="tgChatId">Chat ID / Channel ID</label>
            <input 
              id="tgChatId"
              type="text" 
              v-model="config.telegram_chat_id" 
              placeholder="-100123456789 ou @nom_canal" 
              class="soc-input mono"
              @input="markModified"
            />
          </div>

          <div class="channel-actions">
            <button 
              type="button" 
              class="sec-action-btn" 
              :disabled="testingTelegram || !config.telegram_bot_token || !config.telegram_chat_id"
              @click="testTelegram"
            >
              <svg v-if="!testingTelegram" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
              <span v-else class="btn-spinner"></span>
              <span>{{ testingTelegram ? 'Test en cours...' : 'Tester l\'envoi Telegram' }}</span>
            </button>
          </div>

          <div v-if="telegramStatusMsg" class="test-feedback" :class="telegramSuccess ? 'feedback-ok' : 'feedback-err'">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline v-if="telegramSuccess" points="20 6 9 17 4 12"></polyline>
              <line v-else x1="18" y1="6" x2="6" y2="18"></line>
              <line v-if="!telegramSuccess" x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
            <span>{{ telegramStatusMsg }}</span>
          </div>
        </div>
      </div>

      <!-- Canal Email / SMTP -->
      <div class="channel-card" :class="{ 'channel-active': config.email_enabled }">
        <div class="channel-header">
          <div class="channel-brand">
            <svg class="brand-icon email-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
              <polyline points="22,6 12,13 2,6" />
            </svg>
            <div>
              <h4 class="channel-name">Email (SMTP)</h4>
              <span class="channel-hint">Bulletins d'incident détaillés en HTML dark</span>
            </div>
          </div>
          <label class="switch-toggle" aria-label="Activer Email">
            <input type="checkbox" v-model="config.email_enabled" @change="markModified" />
            <span class="slider"></span>
          </label>
        </div>

        <div class="channel-body">
          <div class="form-row-2">
            <div class="form-group flex-2">
              <label class="field-label" for="smtpHost">Serveur SMTP</label>
              <input 
                id="smtpHost"
                type="text" 
                v-model="config.smtp_host" 
                placeholder="smtp.example.com" 
                class="soc-input"
                @input="markModified"
              />
            </div>
            <div class="form-group flex-1">
              <label class="field-label" for="smtpPort">Port</label>
              <input 
                id="smtpPort"
                type="number" 
                v-model.number="config.smtp_port" 
                placeholder="587" 
                class="soc-input mono"
                @input="markModified"
              />
            </div>
          </div>

          <div class="form-row-2">
            <div class="form-group flex-1">
              <label class="field-label" for="smtpUser">Utilisateur SMTP</label>
              <input 
                id="smtpUser"
                type="text" 
                v-model="config.smtp_user" 
                placeholder="soc-alert@example.com" 
                class="soc-input"
                @input="markModified"
              />
            </div>
            <div class="form-group flex-1">
              <label class="field-label" for="smtpPass">Mot de passe</label>
              <div class="input-with-action">
                <input 
                  id="smtpPass"
                  :type="showSmtpPass ? 'text' : 'password'"
                  v-model="config.smtp_password" 
                  placeholder="••••••••" 
                  class="soc-input mono"
                  @input="markModified"
                />
                <button 
                  type="button" 
                  class="field-icon-btn" 
                  @click="showSmtpPass = !showSmtpPass"
                  :title="showSmtpPass ? 'Masquer' : 'Afficher'"
                >
                  <svg v-if="showSmtpPass" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
                  <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                </button>
              </div>
            </div>
          </div>

          <div class="form-row-2">
            <div class="form-group flex-1">
              <label class="field-label" for="emailFrom">Expéditeur (From)</label>
              <input 
                id="emailFrom"
                type="email" 
                v-model="config.email_from" 
                placeholder="nids-soc@entreprise.local" 
                class="soc-input"
                @input="markModified"
              />
            </div>
            <div class="form-group flex-1">
              <label class="field-label" for="emailTo">Destinataire(s) (To)</label>
              <input 
                id="emailTo"
                type="text" 
                v-model="config.email_to" 
                placeholder="analyst1@soc.local, lead@soc.local" 
                class="soc-input"
                @input="markModified"
              />
            </div>
          </div>

          <div class="checkbox-inline">
            <label class="soc-checkbox-label">
              <input type="checkbox" v-model="config.smtp_use_tls" @change="markModified" />
              <span>Activer le chiffrement TLS / STARTTLS sécurisé</span>
            </label>
          </div>

          <div class="channel-actions">
            <button 
              type="button" 
              class="sec-action-btn" 
              :disabled="testingEmail || !config.smtp_host || !config.email_to"
              @click="testEmail"
            >
              <svg v-if="!testingEmail" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
              <span v-else class="btn-spinner"></span>
              <span>{{ testingEmail ? 'Test en cours...' : 'Tester l\'envoi Email' }}</span>
            </button>
          </div>

          <div v-if="emailStatusMsg" class="test-feedback" :class="emailSuccess ? 'feedback-ok' : 'feedback-err'">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline v-if="emailSuccess" points="20 6 9 17 4 12"></polyline>
              <line v-else x1="18" y1="6" x2="6" y2="18"></line>
              <line v-if="!emailSuccess" x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
            <span>{{ emailStatusMsg }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Thresholds & Criteria Strip -->
    <div class="criteria-strip">
      <div class="criteria-header">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        <span class="criteria-title">Conditions de Déclenchement & Filtrage</span>
      </div>

      <div class="criteria-options">
        <label class="soc-checkbox-label">
          <input type="checkbox" v-model="config.notify_critical_only" @change="markModified" />
          <span><b>Alertes Critiques uniquement :</b> DDoS, Infiltration, Botnet, Patator (filtre le bruit mineur)</span>
        </label>
        <label class="soc-checkbox-label">
          <input type="checkbox" v-model="config.notify_zero_day" @change="markModified" />
          <span><b>Anomalies Zero-Day :</b> Alerte immédiate dès détection d'une déviation anormale par l'Autoencodeur</span>
        </label>
        <label class="soc-checkbox-label">
          <input type="checkbox" v-model="config.notify_traffic_burst" @change="markModified" />
          <span><b>Rapports de pic volumétrique :</b> Alerte si le flux réseau dépasse le seuil de 5 000 paquets/sec</span>
        </label>
      </div>

      <div class="anti-spam-callout">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        </svg>
        <span>Moteur anti-spam actif : Les doublons de même type et IP source sont groupés en un bulletin unique toutes les 60 secondes.</span>
      </div>
    </div>

    <!-- Save Bar -->
    <div class="notification-save-bar">
      <div class="save-status-info">
        <span v-if="isModified" class="mod-pill">Modifications non enregistrées</span>
        <span v-else class="synced-pill">Configuration synchronisée</span>
      </div>
      <button 
        type="button" 
        class="pri save-btn" 
        :disabled="saving || !isModified"
        @click="saveConfig"
      >
        <svg v-if="!saving" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
        <span v-else class="btn-spinner"></span>
        <span>{{ saving ? 'Enregistrement...' : 'Enregistrer les Notifications' }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../../services/api'

const config = ref({
  telegram_enabled: false,
  telegram_bot_token: '',
  telegram_chat_id: '',
  email_enabled: false,
  smtp_host: '',
  smtp_port: 587,
  smtp_user: '',
  smtp_password: '',
  smtp_use_tls: true,
  email_from: '',
  email_to: '',
  notify_critical_only: true,
  notify_zero_day: true,
  notify_traffic_burst: false
})

const isModified = ref(false)
const saving = ref(false)
const showTgToken = ref(false)
const showSmtpPass = ref(false)

const testingTelegram = ref(false)
const telegramStatusMsg = ref('')
const telegramSuccess = ref(false)

const testingEmail = ref(false)
const emailStatusMsg = ref('')
const emailSuccess = ref(false)

const markModified = () => {
  isModified.value = true
}

const loadConfig = async () => {
  try {
    const res = await api.getNotificationSettings()
    if (res) {
      config.value = { ...config.value, ...res }
      isModified.value = false
    }
  } catch (e) {
    console.error('Erreur chargement configuration notifications:', e)
  }
}

const saveConfig = async () => {
  saving.value = true
  try {
    const res = await api.updateNotificationSettings(config.value)
    if (res && res.status === 'success') {
      config.value = { ...config.value, ...res.config }
      isModified.value = false
    }
  } catch (e) {
    alert(`Erreur d'enregistrement : ${e.message}`)
  } finally {
    saving.value = false
  }
}

const testTelegram = async () => {
  testingTelegram.value = true
  telegramStatusMsg.value = ''
  try {
    const res = await api.testTelegramNotification({
      bot_token: config.value.telegram_bot_token,
      chat_id: config.value.telegram_chat_id
    })
    telegramSuccess.value = Boolean(res.success)
    telegramStatusMsg.value = res.message || (res.success ? 'Message envoyé' : 'Échec du test')
  } catch (e) {
    telegramSuccess.value = false
    telegramStatusMsg.value = e.message || 'Erreur réseau'
  } finally {
    testingTelegram.value = false
  }
}

const testEmail = async () => {
  testingEmail.value = true
  emailStatusMsg.value = ''
  try {
    const res = await api.testEmailNotification({
      smtp_host: config.value.smtp_host,
      smtp_port: config.value.smtp_port,
      smtp_user: config.value.smtp_user,
      smtp_password: config.value.smtp_password,
      smtp_use_tls: config.value.smtp_use_tls,
      email_from: config.value.email_from,
      email_to: config.value.email_to
    })
    emailSuccess.value = Boolean(res.success)
    emailStatusMsg.value = res.message || (res.success ? 'Email envoyé' : 'Échec du test')
  } catch (e) {
    emailSuccess.value = false
    emailStatusMsg.value = e.message || 'Erreur réseau'
  } finally {
    testingEmail.value = false
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.notification-settings-card {
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
  color: var(--ac);
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
  background: rgba(139, 142, 168, 0.1);
  color: var(--mu);
  font-size: 12px;
  font-weight: 600;
  border: 1px solid rgba(139, 142, 168, 0.2);
}

.header-status-badge.active {
  background: rgba(61, 220, 151, 0.12);
  color: var(--ok);
  border-color: rgba(61, 220, 151, 0.3);
}

.status-indicator-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}

/* Channels Grid */
.channels-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

@media (max-width: 900px) {
  .channels-grid {
    grid-template-columns: 1fr;
  }
}

.channel-card {
  background: var(--panel2);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.channel-card.channel-active {
  border-color: rgba(88, 101, 242, 0.5);
  box-shadow: 0 0 15px rgba(88, 101, 242, 0.08);
}

.channel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.channel-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  width: 22px;
  height: 22px;
}

.telegram-icon {
  color: #38bdf8;
}

.email-icon {
  color: #a78bfa;
}

.channel-name {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--tx);
}

.channel-hint {
  font-size: 12px;
  color: var(--mu);
}

/* Switch Toggle */
.switch-toggle {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
}

.switch-toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--line);
  transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 50%;
}

input:checked + .slider {
  background-color: var(--ac);
}

input:checked + .slider:before {
  transform: translateX(20px);
}

/* Form Styles */
.channel-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-row-2 {
  display: flex;
  gap: 12px;
}

.flex-1 {
  flex: 1;
}

.flex-2 {
  flex: 2;
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
  transition: border-color 0.2s;
}

.soc-input:focus {
  border-color: var(--ac);
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
  border-radius: 4px;
}

.field-icon-btn:hover {
  color: var(--tx);
}

.checkbox-inline {
  margin-top: 4px;
}

.soc-checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--tx);
  cursor: pointer;
}

.soc-checkbox-label input[type="checkbox"] {
  accent-color: var(--ac);
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.channel-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 4px;
}

.sec-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 14px;
  background: rgba(88, 101, 242, 0.1);
  border: 1px solid rgba(88, 101, 242, 0.25);
  border-radius: 8px;
  color: var(--tx);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sec-action-btn:hover:not(:disabled) {
  background: rgba(88, 101, 242, 0.2);
  border-color: var(--ac);
}

.sec-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-spinner {
  width: 13px;
  height: 13px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-top-color: var(--tx);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.test-feedback {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
}

.feedback-ok {
  background: rgba(61, 220, 151, 0.1);
  color: var(--ok);
  border: 1px solid rgba(61, 220, 151, 0.25);
}

.feedback-err {
  background: rgba(255, 77, 126, 0.1);
  color: var(--cr);
  border: 1px solid rgba(255, 77, 126, 0.25);
}

/* Criteria Strip */
.criteria-strip {
  background: var(--panel2);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.criteria-header {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--ac2);
}

.criteria-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--tx);
}

.criteria-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.anti-spam-callout {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: rgba(155, 92, 246, 0.08);
  border: 1px solid rgba(155, 92, 246, 0.2);
  border-radius: 8px;
  font-size: 12.5px;
  color: #c4b5fd;
}

.anti-spam-callout svg {
  flex-shrink: 0;
  color: var(--ac2);
}

/* Save Bar */
.notification-save-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--line);
}

.mod-pill {
  font-size: 12px;
  font-weight: 600;
  color: var(--md);
}

.synced-pill {
  font-size: 12px;
  color: var(--mu);
}

.save-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 20px;
  background: var(--ac);
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
</style>
