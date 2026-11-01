<template>
  <main>
    <div class="card" style="margin-bottom: 16px;">
      <h2>
        Detection Models &amp; AI Explainability
        <span>PyTorch Deep Learning Dual-Engine</span>
      </h2>
      <p style="color:var(--mu); font-size: 13px; margin: 0;">
        Architectural specifications, decision boundaries, reconstruction error thresholds and performance metrics.
      </p>
    </div>

    <section class="grid">
      <!-- Supervised DNN -->
      <div class="card c6">
        <h2>Supervised Deep Neural Network (DNN {{ store.modelMeta?.version || 'v5' }})</h2>
        <div class="kv" style="margin-top: 10px;">
          <span>Framework</span><span>PyTorch 2.11 / CUDA</span>
          <span>Input Features</span><span>58 Bidirectional Flow Features</span>
          <span>Target Classes</span><span>{{ classes.length }} Multi-Class Categories</span>
          <span>Overall Accuracy</span><span style="color:var(--ok);">99.42%</span>
          <span>Mean F1-Score</span><span style="color:var(--ok);">0.9555</span>
          <span>Temperature T</span><span>1.4982 (Softmax Calibrated)</span>
          <span>Inference Latency</span><span>&lt; 0.45 ms / flow batch</span>
        </div>

        <h3 style="margin-top: 16px; font-size: 13px;">Trained Attack Classes</h3>
        <div class="fl" style="margin-top: 8px;">
          <span v-for="c in classes" :key="c" class="on">{{ c }}</span>
        </div>
      </div>

      <!-- Autoencoder AE v2 -->
      <div class="card c6">
        <h2>Unsupervised Autoencoder (AE {{ store.modelMeta?.ae_version || 'v2' }})</h2>
        <div class="kv" style="margin-top: 10px;">
          <span>Architecture</span><span>Deep Symmetric Bottleneck (58 &rarr; 32 &rarr; 16 &rarr; 8 &rarr; 16 &rarr; 32 &rarr; 58)</span>
          <span>Training Baseline</span><span>100% Benign Network Flows (Normal Traffic)</span>
          <span>Reconstruction Metric</span><span>Mean Squared Error (MSE)</span>
          <span>Decision Threshold</span><span style="color:var(--zd);">MSE &gt; {{ store.aeThreshold.toFixed(4) }}</span>
          <span>Separation Ratio</span><span style="color:var(--ok);">29.4x (Attacks / Benign)</span>
          <span>False Positive Rate</span><span>0.10%</span>
        </div>

        <h3 style="margin-top: 16px; font-size: 13px;">Active Learning &amp; Feedback Dataset</h3>
        <p style="color:var(--mu); font-size: 12.5px; margin: 8px 0 10px; line-height: 1.5;">
          Les flux qualifiés par les analystes SOC sont synchronisés en direct sur disque dans <code>feedback_flows.json</code> et <code>feedback_flows.csv</code>.
        </p>
        <div style="display:flex; gap: 8px; flex-wrap: wrap;">
          <a href="/api/dashboard/feedback/export?format=json&download=true" download="feedback_flows.json" class="export-pill-btn" style="background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); color: #38bdf8; padding: 5px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; text-decoration: none;">
            📥 Télécharger feedback_flows.json
          </a>
          <a href="/api/dashboard/feedback/export?format=csv" download="feedback_flows.csv" class="export-pill-btn" style="background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); color: #38bdf8; padding: 5px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; text-decoration: none;">
            📥 Télécharger feedback_flows.csv
          </a>
        </div>
      </div>
    </section>

    <!-- Console d'Inférence Temps Réel pour le Modèle IA -->
    <ModelTerminal />
  </main>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useSocStore } from '@/stores/socStore'
import ModelTerminal from '@/components/models/ModelTerminal.vue'

const store = useSocStore()

const fallbackClasses = [
  'BENIGN', 'DDoS', 'DoS-Hulk', 'DoS-GoldenEye', 'DoS-slowloris', 
  'DoS-Slowhttptest', 'PortScan', 'SSH-Patator', 'FTP-Patator', 
  'WebAttack', 'Bot', 'Scan-Vista'
]

const classes = computed(() => {
  return (store.modelClasses && store.modelClasses.length > 0)
    ? store.modelClasses
    : fallbackClasses
})

onMounted(() => {
  store.fetchModelClasses()
})
</script>
