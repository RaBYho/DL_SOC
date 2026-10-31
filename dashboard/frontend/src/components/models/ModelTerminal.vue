<template>
  <div class="card model-terminal-card">
    <div class="terminal-header">
      <div class="terminal-title">
        <span class="live-pulse"></span>
        <span class="title-text">Console d'Inférence IA (Terminal Temps Réel)</span>
        <span class="badge-device">PyTorch 2.11 / {{ activeDevice }}</span>
      </div>

      <div class="terminal-actions">
        <button 
          type="button" 
          class="btn-term" 
          :class="{ active: autoScroll }" 
          @click="autoScroll = !autoScroll"
          title="Faire défiler automatiquement vers les derniers logs"
        >
          📜 Auto-scroll: {{ autoScroll ? 'ON' : 'OFF' }}
        </button>

        <button 
          type="button" 
          class="btn-term" 
          @click="clearLogs"
          title="Effacer les logs du terminal et réinitialiser le fichier .log"
        >
          🗑️ Vider
        </button>

        <a 
          href="/api/dashboard/models/logs/raw" 
          target="_blank" 
          class="btn-term btn-download"
          title="Ouvrir le fichier physique logs/model_inference.log"
        >
          📥 Fichier .log
        </a>
      </div>
    </div>

    <!-- Corps du Terminal -->
    <div ref="terminalBody" class="terminal-body" @scroll="handleManualScroll">
      <!-- État d'attente si aucun log -->
      <div v-if="store.modelLogs.length === 0" class="terminal-empty">
        <div class="term-line term-sys">
          <span class="term-ts">[{{ currentTimestamp }}]</span> 
          <span class="term-lvl-info">[SYSTEM]</span> 
          <span>Service d'écoute d'inférence démarré sur <code>logs/model_inference.log</code>.</span>
        </div>
        <div class="term-line term-info">
          <span class="term-ts">[{{ currentTimestamp }}]</span> 
          <span class="term-lvl-info">[INFO  ]</span> 
          <span>En attente de paquets réseau injectés par les capteurs ou le rejeu PCAP...</span>
        </div>
        <div class="term-line term-tip">
          <span class="term-prompt">&gt;</span> 
          <span>Astuce : Lancez un rejeu PCAP depuis l'onglet <b>Capteurs</b> pour observer les flux analysés en direct par le modèle.</span>
        </div>
      </div>

      <!-- Liste des logs d'inférence réels -->
      <div v-for="log in store.modelLogs" :key="log.id || log.timestamp" class="log-entry" :class="'log-' + log.level.toLowerCase()">
        <div class="log-main-line">
          <span class="term-ts">[{{ log.timestamp }}]</span>
          <span :class="'term-lvl-' + log.level.toLowerCase()">[{{ log.level.padEnd(7) }}]</span>
          <span class="term-model">[DNN-v4 on {{ log.device || 'cpu' }}]</span>
          <span class="term-batch">Batch: <b>{{ log.batch_size }}</b> flux</span>
          <span class="term-latency">⏱️ {{ log.latency_ms }}ms</span>
          
          <!-- Classes prédites -->
          <span class="term-preds">
            Preds: <span class="pred-tag" v-for="(count, cls) in log.predictions" :key="cls" :class="{ 'pred-malicious': cls !== 'BENIGN' }">
              {{ cls }}:<b>{{ count }}</b>
            </span>
          </span>

          <!-- MSE Autoencodeur -->
          <span v-if="log.max_mse !== null" class="term-mse" :class="{ 'mse-alert': log.anomalies_count > 0 }">
            AE MSE Max: <b>{{ log.max_mse.toFixed(4) }}</b>
          </span>
          <span v-if="log.anomalies_count > 0" class="term-anom-badge">
            ⚠️ {{ log.anomalies_count }} anomalie(s)
          </span>
        </div>

        <!-- Lignes de détails des attaques identifiées -->
        <div v-if="log.details && log.details.length" class="log-details-block">
          <div v-for="(detail, dIdx) in log.details" :key="dIdx" class="log-detail-line">
            {{ detail }}
          </div>
        </div>
      </div>
    </div>

    <!-- Barre d'état inférieure -->
    <div class="terminal-footer">
      <div class="footer-left">
        <span>Fichier actif : <code>logs/model_inference.log</code></span>
        <span class="separator">&bull;</span>
        <span>Événements reçus : <b>{{ store.modelLogs.length }}</b></span>
      </div>
      <div class="footer-right">
        <span>Seuil Zero-Day (Autoencoder) : <code>MSE &gt; {{ store.aeThreshold.toFixed(4) }}</code></span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useSocStore } from '@/stores/socStore'

const store = useSocStore()
const terminalBody = ref(null)
const autoScroll = ref(true)

const currentTimestamp = computed(() => {
  const d = new Date()
  return d.toTimeString().split(' ')[0]
})

const activeDevice = computed(() => {
  if (store.modelLogs.length > 0) {
    return store.modelLogs[store.modelLogs.length - 1].device || 'cpu'
  }
  return 'cpu'
})

// Défilement automatique vers le bas lors de l'arrivée d'un nouveau log
const scrollToBottom = () => {
  if (!autoScroll.value || !terminalBody.value) return
  nextTick(() => {
    terminalBody.value.scrollTop = terminalBody.value.scrollHeight
  })
}

// Surveillance des nouveaux logs
watch(
  () => store.modelLogs.length,
  () => {
    scrollToBottom()
  }
)

const handleManualScroll = () => {
  if (!terminalBody.value) return
  const { scrollTop, scrollHeight, clientHeight } = terminalBody.value
  // Si l'utilisateur remonte manuellement de plus de 40px, on désactive l'autoscroll
  if (scrollHeight - scrollTop - clientHeight > 40) {
    autoScroll.value = false
  } else {
    autoScroll.value = true
  }
}

const clearLogs = async () => {
  await store.clearModelLogs()
}

onMounted(async () => {
  if (store.modelLogs.length === 0) {
    await store.fetchModelLogs(100)
  }
  scrollToBottom()
})
</script>

<style scoped>
.model-terminal-card {
  margin-top: 20px;
  padding: 0;
  overflow: hidden;
  border: 1px solid #25283a;
  background: #0d0e17;
  border-radius: 14px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
}

.terminal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 18px;
  background: #151724;
  border-bottom: 1px solid #23263b;
}

.terminal-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.live-pulse {
  width: 9px;
  height: 9px;
  background: #3ddc97;
  border-radius: 50%;
  box-shadow: 0 0 10px #3ddc97;
  animation: pulse 1.8s infinite;
}

@keyframes pulse {
  0% { transform: scale(0.9); opacity: 0.7; }
  50% { transform: scale(1.3); opacity: 1; box-shadow: 0 0 14px #3ddc97; }
  100% { transform: scale(0.9); opacity: 0.7; }
}

.title-text {
  font-size: 13.5px;
  font-weight: 700;
  letter-spacing: 0.3px;
  color: #eceefa;
}

.badge-device {
  font-size: 11px;
  font-weight: 600;
  background: rgba(143, 160, 255, 0.12);
  color: #8fa0ff;
  border: 1px solid rgba(143, 160, 255, 0.3);
  padding: 2px 8px;
  border-radius: 6px;
  font-family: ui-monospace, Menlo, Consolas, monospace;
}

.terminal-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-term {
  height: 30px;
  padding: 0 12px;
  font-size: 11.5px;
  font-weight: 600;
  background: #1f2235;
  color: #c4ccff;
  border: 1px solid #333752;
  border-radius: 7px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  text-decoration: none;
  transition: all 0.2s ease;
}

.btn-term:hover {
  background: #2b2f48;
  color: #ffffff;
}

.btn-term.active {
  background: rgba(61, 220, 151, 0.15);
  border-color: rgba(61, 220, 151, 0.4);
  color: #3ddc97;
}

.btn-download {
  color: #ffb547;
  border-color: rgba(255, 181, 71, 0.3);
}

.btn-download:hover {
  background: rgba(255, 181, 71, 0.15);
  color: #ffc977;
}

/* Corps du terminal */
.terminal-body {
  height: 360px;
  overflow-y: auto;
  padding: 14px 18px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
  line-height: 1.6;
  color: #a9b1d6;
  background: #090a12;
}

.terminal-empty {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #7982a9;
}

.term-ts {
  color: #636b8e;
  margin-right: 6px;
}

.term-lvl-info {
  color: #3ddc97;
  font-weight: 700;
  margin-right: 6px;
}

.term-lvl-alert {
  color: #ff4d7e;
  font-weight: 700;
  margin-right: 6px;
}

.term-lvl-anomaly {
  color: #c084fc;
  font-weight: 700;
  margin-right: 6px;
}

.term-prompt {
  color: #ffb547;
  font-weight: 800;
  margin-right: 8px;
}

.term-tip {
  margin-top: 10px;
  color: #8f96b3;
}

.term-tip code, .term-empty code {
  color: #c4ccff;
  background: #171826;
  padding: 1px 5px;
  border-radius: 4px;
}

/* Lignes de logs */
.log-entry {
  padding: 3px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.02);
}

.log-main-line {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.term-model {
  color: #8fa0ff;
}

.term-batch {
  color: #eceefa;
}

.term-latency {
  color: #ffb547;
  background: rgba(255, 181, 71, 0.08);
  padding: 0 4px;
  border-radius: 3px;
}

.pred-tag {
  color: #9aa5ce;
  background: #181a29;
  padding: 1px 5px;
  border-radius: 4px;
  margin-right: 4px;
}

.pred-tag.pred-malicious {
  color: #ff5c8a;
  background: rgba(255, 77, 126, 0.15);
  font-weight: 700;
  border: 1px solid rgba(255, 77, 126, 0.3);
}

.term-mse {
  color: #38bdf8;
}

.term-mse.mse-alert {
  color: #f43f5e;
  font-weight: 700;
}

.term-anom-badge {
  background: rgba(192, 132, 252, 0.18);
  color: #c084fc;
  border: 1px solid rgba(192, 132, 252, 0.35);
  padding: 0 6px;
  border-radius: 4px;
  font-weight: 700;
}

.log-details-block {
  margin: 2px 0 4px 18px;
  color: #ff94b4;
  font-size: 11.5px;
}

.log-detail-line {
  line-height: 1.4;
}

/* Barre de pied de terminal */
.terminal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 18px;
  background: #10121d;
  border-top: 1px solid #1e2133;
  font-size: 11.5px;
  color: #7982a9;
}

.terminal-footer code {
  color: #c4ccff;
  font-weight: 600;
}

.separator {
  margin: 0 6px;
  opacity: 0.5;
}
</style>
