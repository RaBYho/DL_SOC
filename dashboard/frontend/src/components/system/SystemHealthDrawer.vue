<template>
  <div v-if="store.systemDrawerOpen" class="drawer-backdrop" @click.self="store.closeSystemDrawer">
    <aside class="system-drawer" aria-label="Diagnostic de santé système">
      <!-- 1. En-tête du Tiroir -->
      <div class="drawer-header">
        <div class="header-left">
          <div class="system-icon-box" :class="'icon-' + (store.systemHealth.status || 'healthy').toLowerCase()">
            <svg class="sys-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
            </svg>
          </div>
          <div>
            <div class="title-with-badge">
              <h3 class="drawer-title">Santé Système &amp; Infrastructure</h3>
              <span class="health-status-badge" :class="'badge-' + (store.systemHealth.status || 'healthy').toLowerCase()">
                {{ statusLabel }}
              </span>
            </div>
            <p class="drawer-subtitle">
              Supervision de la chaîne d'ingestion, du moteur IA, de la base SQLite et de l'hôte Linux Mint.
            </p>
          </div>
        </div>

        <button 
          type="button" 
          class="btn-close-drawer" 
          @click="store.closeSystemDrawer"
          title="Fermer le tiroir"
        >
          ✕
        </button>
      </div>

      <!-- 2. Corps du Diagnostic avec Défilement -->
      <div class="drawer-body-scroll">
        <!-- Barre de Score Global et Uptime -->
        <div class="health-score-banner">
          <div class="score-meta-row">
            <div>
              <span class="score-label">Indice de Santé Opérationnelle</span>
              <div class="score-number-row">
                <b class="score-val" :class="scoreColorClass">{{ store.systemHealth.score || 0 }}%</b>
                <span class="score-caption">disponibilité infrastructure</span>
              </div>
            </div>
            <div class="uptime-badge">
              <svg class="uptime-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
              <span>Uptime : <b>{{ store.systemHealth.uptime_str || '0s' }}</b></span>
            </div>
          </div>

          <div class="score-track">
            <div 
              class="score-fill" 
              :class="scoreBarClass"
              :style="{ width: `${store.systemHealth.score || 0}%` }"
            ></div>
          </div>
        </div>

        <!-- Alertes & Pannes Détectées (si issues > 0) -->
        <div v-if="store.systemHealth.issues && store.systemHealth.issues.length > 0" class="issues-alert-box">
          <div class="issues-header">
            <svg class="alert-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            <b>{{ store.systemHealth.issues.length }} anomalie(s) technique(s) requiert votre attention :</b>
          </div>

          <div class="issues-list">
            <div 
              v-for="(issue, idx) in store.systemHealth.issues" 
              :key="idx" 
              class="issue-card"
              :class="'sev-' + (issue.severity || 'warning').toLowerCase()"
            >
              <div class="issue-source-tag">{{ issue.source }}</div>
              <div class="issue-content">
                <p class="issue-msg">{{ issue.message }}</p>
                <div v-if="issue.fix" class="issue-fix">
                  <span class="fix-label">Conseil de remédiation :</span>
                  <span class="fix-text">{{ issue.fix }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 4 Piliers d'Infrastructure en Grille 2x2 -->
        <div class="pillars-grid">
          <!-- Pilier 1 : Capteurs & Ingestion -->
          <div class="pillar-card">
            <div class="pillar-top">
              <div class="pillar-identity">
                <svg class="pillar-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
                  <rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>
                  <line x1="6" y1="6" x2="6.01" y2="6"/>
                  <line x1="6" y1="18" x2="6.01" y2="18"/>
                </svg>
                <b class="pillar-title">Sondes &amp; Ingestion</b>
              </div>
              <span class="pillar-status-pill" :class="'status-' + (store.systemHealth.components?.sensors?.status || 'offline').toLowerCase()">
                {{ store.systemHealth.components?.sensors?.status || 'OFFLINE' }}
              </span>
            </div>

            <div class="pillar-metrics">
              <div class="metric-row">
                <span class="metric-label">Sondes actives :</span>
                <b class="metric-val">{{ store.systemHealth.components?.sensors?.online_sensors || 0 }} / {{ store.systemHealth.components?.sensors?.total_sensors || 0 }}</b>
              </div>
              <div class="metric-row">
                <span class="metric-label">Dernier flux :</span>
                <span class="metric-val text-accent">
                  {{ store.systemHealth.components?.sensors?.last_flow_sec_ago !== null ? `il y a ${store.systemHealth.components?.sensors?.last_flow_sec_ago}s` : 'Aucun flux' }}
                </span>
              </div>
            </div>
          </div>

          <!-- Pilier 2 : Moteur d'Inférence IA -->
          <div class="pillar-card">
            <div class="pillar-top">
              <div class="pillar-identity">
                <svg class="pillar-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
                <b class="pillar-title">Moteur d'Inférence IA</b>
              </div>
              <span class="pillar-status-pill" :class="'status-' + (store.systemHealth.components?.ai_engine?.status || 'operational').toLowerCase()">
                {{ store.systemHealth.components?.ai_engine?.status || 'OPERATIONAL' }}
              </span>
            </div>

            <div class="pillar-metrics">
              <div class="metric-row">
                <span class="metric-label">Version modèle :</span>
                <b class="metric-val">DNN-{{ store.systemHealth.components?.ai_engine?.dnn_version }} + AE-{{ store.systemHealth.components?.ai_engine?.ae_version }}</b>
              </div>
              <div class="metric-row">
                <span class="metric-label">Latence moyenne :</span>
                <b class="metric-val text-accent">{{ store.systemHealth.components?.ai_engine?.avg_inference_ms }} ms</b>
              </div>
              <div class="metric-row">
                <span class="metric-label">Accélérateur :</span>
                <span class="metric-val">{{ store.systemHealth.components?.ai_engine?.device }}</span>
              </div>
            </div>
          </div>

          <!-- Pilier 3 : Base de Données SQLite -->
          <div class="pillar-card">
            <div class="pillar-top">
              <div class="pillar-identity">
                <svg class="pillar-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <ellipse cx="12" cy="5" rx="9" ry="3"/>
                  <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
                  <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
                </svg>
                <b class="pillar-title">Base de Données SQLite</b>
              </div>
              <span class="pillar-status-pill" :class="'status-' + (store.systemHealth.components?.database?.status || 'healthy').toLowerCase()">
                {{ store.systemHealth.components?.database?.status || 'HEALTHY' }}
              </span>
            </div>

            <div class="pillar-metrics">
              <div class="metric-row">
                <span class="metric-label">Taille nids.db :</span>
                <b class="metric-val">{{ store.systemHealth.components?.database?.file_size_mb }} Mo</b>
              </div>
              <div class="metric-row">
                <span class="metric-label">Latence requête :</span>
                <b class="metric-val text-success">{{ store.systemHealth.components?.database?.latency_ms }} ms</b>
              </div>
              <div class="metric-row">
                <span class="metric-label">Mode journal :</span>
                <span class="metric-val">{{ store.systemHealth.components?.database?.journal_mode }}</span>
              </div>
            </div>
          </div>

          <!-- Pilier 4 : Hôte & Système d'Exploitation -->
          <div class="pillar-card">
            <div class="pillar-top">
              <div class="pillar-identity">
                <svg class="pillar-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
                  <line x1="8" y1="21" x2="16" y2="21"/>
                  <line x1="12" y1="17" x2="12" y2="21"/>
                </svg>
                <b class="pillar-title">Hôte Linux Mint</b>
              </div>
              <span class="pillar-status-pill status-online">ACTIF</span>
            </div>

            <div class="pillar-metrics">
              <div class="metric-row">
                <span class="metric-label">Charge CPU :</span>
                <b class="metric-val">{{ store.systemHealth.components?.host?.cpu_pct }} %</b>
              </div>
              <div class="metric-row">
                <span class="metric-label">Mémoire RAM :</span>
                <b class="metric-val">{{ store.systemHealth.components?.host?.ram_pct }} % ({{ store.systemHealth.components?.host?.ram_used_gb }} Go / {{ store.systemHealth.components?.host?.ram_total_gb }} Go)</b>
              </div>
              <div class="metric-row">
                <span class="metric-label">Disque libre :</span>
                <b class="metric-val text-accent">{{ store.systemHealth.components?.host?.disk_free_gb }} Go</b>
              </div>
            </div>
          </div>
        </div>

        <!-- 5. Console des Logs Techniques d'Infrastructure -->
        <div class="tech-logs-section">
          <div class="tech-logs-header">
            <div class="tech-logs-title-row">
              <svg class="logs-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="4 17 10 11 4 5"/>
                <line x1="12" y1="19" x2="20" y2="19"/>
              </svg>
              <h4>Journal des Événements Techniques (Infrastructure)</h4>
            </div>
            <button 
              type="button" 
              class="btn-refresh-logs"
              @click="store.fetchSystemLogs"
            >
              Actualiser les logs
            </button>
          </div>

          <div class="logs-console-window">
            <div v-if="store.systemLogs.length === 0" class="no-logs-msg">
              Aucun incident technique d'infrastructure enregistré.
            </div>
            <div 
              v-else 
              v-for="(log, idx) in store.systemLogs" 
              :key="idx" 
              class="log-row"
            >
              <span class="log-time">{{ log.time_str }}</span>
              <span class="log-level" :class="'level-' + log.level.toLowerCase()">[{{ log.level }}]</span>
              <span class="log-source">[{{ log.source }}]</span>
              <span class="log-msg">{{ log.message }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 3. Pied d'Actions de Maintenance -->
      <div class="drawer-footer">
        <button 
          type="button" 
          class="btn-action-primary" 
          :disabled="isOptimizing"
          @click="handleOptimizeDb"
        >
          <svg class="action-btn-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
          </svg>
          <span>{{ isOptimizing ? 'Optimisation en cours...' : 'Optimiser Base SQLite' }}</span>
        </button>

        <button 
          type="button" 
          class="btn-action-secondary" 
          @click="store.fetchSystemHealth"
        >
          <svg class="action-btn-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
            <path d="M3 3v5h5"/>
            <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
            <path d="M16 21h5v-5"/>
          </svg>
          <span>Lancer un Audit</span>
        </button>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useSocStore } from '@/stores/socStore'

const store = useSocStore()
const isOptimizing = ref(false)

const statusLabel = computed(() => {
  const s = store.systemHealth.status
  if (s === 'HEALTHY') return 'Système Nominal (100%)'
  if (s === 'DEGRADED') return 'Vigilance / Attention Requise'
  return 'Incident Technique Critique'
})

const scoreColorClass = computed(() => {
  const score = store.systemHealth.score || 0
  if (score >= 85) return 'text-success'
  if (score >= 60) return 'text-warning'
  return 'text-danger'
})

const scoreBarClass = computed(() => {
  const score = store.systemHealth.score || 0
  if (score >= 85) return 'bar-success'
  if (score >= 60) return 'bar-warning'
  return 'bar-danger'
})

const handleOptimizeDb = async () => {
  isOptimizing.value = true
  try {
    await store.optimizeDatabase()
  } finally {
    setTimeout(() => {
      isOptimizing.value = false
    }, 400)
  }
}
</script>

<style scoped>
.drawer-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(5px);
  display: flex;
  justify-content: flex-end;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.system-drawer {
  width: 100%;
  max-width: 720px;
  height: 100vh;
  background: #121320;
  border-left: 1px solid #282a44;
  box-shadow: -10px 0 35px rgba(0, 0, 0, 0.6);
  display: flex;
  flex-direction: column;
  animation: slideLeft 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideLeft {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}

/* 1. Header */
.drawer-header {
  padding: 18px 24px;
  background: #18192a;
  border-bottom: 1px solid #282a42;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.system-icon-box {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.system-icon-box.icon-healthy  { background: rgba(61, 220, 151, 0.15); border: 1px solid rgba(61, 220, 151, 0.3); color: #3ddc97; }
.system-icon-box.icon-degraded { background: rgba(255, 181, 71, 0.15); border: 1px solid rgba(255, 181, 71, 0.3); color: #ffb547; }
.system-icon-box.icon-critical { background: rgba(255, 77, 126, 0.15); border: 1px solid rgba(255, 77, 126, 0.3); color: #ff4d7e; }

.sys-svg { width: 22px; height: 22px; }

.title-with-badge {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.drawer-title {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: #ffffff;
}

.health-status-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 5px;
  text-transform: uppercase;
}

.badge-healthy  { background: rgba(61, 220, 151, 0.2); color: #3ddc97; border: 1px solid rgba(61, 220, 151, 0.35); }
.badge-degraded { background: rgba(255, 181, 71, 0.2); color: #ffb547; border: 1px solid rgba(255, 181, 71, 0.35); }
.badge-critical { background: rgba(255, 77, 126, 0.2); color: #ff4d7e; border: 1px solid rgba(255, 77, 126, 0.35); }

.drawer-subtitle {
  margin: 4px 0 0;
  font-size: 12px;
  color: #8b8ea8;
  line-height: 1.4;
}

.btn-close-drawer {
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

.btn-close-drawer:hover {
  background: rgba(255, 77, 126, 0.15);
  color: #ff4d7e;
}

/* 2. Body Scroll */
.drawer-body-scroll {
  padding: 20px 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex: 1;
}

/* Score banner */
.health-score-banner {
  background: #171829;
  border: 1px solid #282a44;
  border-radius: 12px;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.score-meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.score-label {
  font-size: 11px;
  font-weight: 600;
  color: #8b8ea8;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.score-number-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-top: 2px;
}

.score-val {
  font-size: 26px;
  font-weight: 800;
  letter-spacing: -0.5px;
}

.score-caption {
  font-size: 12px;
  color: #7982a9;
}

.uptime-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #c4ccff;
  background: rgba(88, 101, 242, 0.12);
  border: 1px solid rgba(88, 101, 242, 0.25);
  padding: 4px 10px;
  border-radius: 6px;
}

.uptime-svg { width: 14px; height: 14px; color: #8fa0ff; }

.score-track {
  height: 6px;
  background: #0f101a;
  border-radius: 999px;
  overflow: hidden;
}

.score-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.4s ease-out;
}

.bar-success { background: #3ddc97; box-shadow: 0 0 10px #3ddc97; }
.bar-warning { background: #ffb547; box-shadow: 0 0 10px #ffb547; }
.bar-danger  { background: #ff4d7e; box-shadow: 0 0 10px #ff4d7e; }

/* Alert issues */
.issues-alert-box {
  background: rgba(255, 181, 71, 0.08);
  border: 1px solid rgba(255, 181, 71, 0.25);
  border-radius: 12px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.issues-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #ffd08a;
}

.alert-svg { width: 16px; height: 16px; color: #ffb547; flex-shrink: 0; }

.issues-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.issue-card {
  background: #141524;
  border: 1px solid #282a40;
  border-left: 3px solid #ffb547;
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.issue-card.sev-critical { border-left-color: #ff4d7e; }

.issue-source-tag {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  color: #8fa0ff;
}

.issue-msg {
  margin: 0;
  font-size: 12px;
  color: #ffffff;
  line-height: 1.4;
}

.issue-fix {
  font-size: 11.5px;
  color: #ffb547;
  line-height: 1.35;
}

.fix-label { font-weight: 700; margin-right: 4px; }

/* 4 Piliers Grid */
.pillars-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

@media (max-width: 600px) {
  .pillars-grid { grid-template-columns: 1fr; }
}

.pillar-card {
  background: #161728;
  border: 1px solid #252840;
  border-radius: 12px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.pillar-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pillar-identity {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pillar-svg { width: 16px; height: 16px; color: #8fa0ff; }
.pillar-title { font-size: 13px; color: #ffffff; }

.pillar-status-pill {
  font-size: 10px;
  font-weight: 800;
  padding: 2px 7px;
  border-radius: 5px;
}

.status-online, .status-operational, .status-healthy {
  background: rgba(61, 220, 151, 0.15);
  color: #3ddc97;
  border: 1px solid rgba(61, 220, 151, 0.3);
}

.status-degraded, .status-slow, .status-high_latency {
  background: rgba(255, 181, 71, 0.15);
  color: #ffb547;
  border: 1px solid rgba(255, 181, 71, 0.3);
}

.status-offline, .status-error, .status-corrupt, .status-locked {
  background: rgba(255, 77, 126, 0.15);
  color: #ff4d7e;
  border: 1px solid rgba(255, 77, 126, 0.3);
}

.pillar-metrics {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 12px;
}

.metric-label { color: #7982a9; }
.metric-val { color: #ffffff; }

.text-accent  { color: #8fa0ff !important; }
.text-success { color: #3ddc97 !important; }
.text-warning { color: #ffb547 !important; }
.text-danger  { color: #ff4d7e !important; }

/* Logs techniques */
.tech-logs-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tech-logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tech-logs-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logs-svg { width: 15px; height: 15px; color: #8fa0ff; }
.tech-logs-header h4 { margin: 0; font-size: 13px; font-weight: 700; color: #ffffff; }

.btn-refresh-logs {
  background: transparent;
  border: none;
  font-size: 11px;
  color: #8fa0ff;
  cursor: pointer;
}

.btn-refresh-logs:hover { text-decoration: underline; }

.logs-console-window {
  background: #0b0c14;
  border: 1px solid #1e2033;
  border-radius: 8px;
  padding: 10px 12px;
  max-height: 160px;
  overflow-y: auto;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 11px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.no-logs-msg { color: #585c7b; text-align: center; padding: 10px; }

.log-row {
  display: flex;
  gap: 6px;
  line-height: 1.4;
}

.log-time { color: #636b8e; }
.log-level { font-weight: 700; }
.level-info { color: #3ddc97; }
.level-warning { color: #ffb547; }
.level-error, .level-critical { color: #ff4d7e; }

.log-source { color: #8fa0ff; }
.log-msg { color: #d0d5fa; }

/* 3. Footer */
.drawer-footer {
  padding: 16px 24px;
  background: #171828;
  border-top: 1px solid #282a42;
  display: flex;
  gap: 12px;
}

.btn-action-primary {
  flex: 1;
  height: 38px;
  border-radius: 8px;
  background: #5865f2;
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #ffffff;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s;
}

.btn-action-primary:hover:not(:disabled) {
  background: #4752c4;
}

.btn-action-secondary {
  height: 38px;
  padding: 0 16px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #c4ccff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.btn-action-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.action-btn-svg { width: 14px; height: 14px; }
</style>
