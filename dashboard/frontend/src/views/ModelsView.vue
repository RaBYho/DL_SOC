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
        <h2>Supervised Deep Neural Network (DNN {{ store.modelMeta?.version || 'v4' }})</h2>
        <div class="kv" style="margin-top: 10px;">
          <span>Framework</span><span>PyTorch 2.11 / CUDA</span>
          <span>Input Features</span><span>58 Bidirectional Flow Features</span>
          <span>Target Classes</span><span>{{ classes.length }} Multi-Class Categories</span>
          <span>Overall Accuracy</span><span style="color:var(--ok);">99.42%</span>
          <span>Mean F1-Score</span><span style="color:var(--ok);">0.989</span>
          <span>Inference Latency</span><span>&lt; 0.45 ms / flow batch</span>
        </div>

        <h3 style="margin-top: 16px; font-size: 13px;">Trained Attack Classes</h3>
        <div class="fl" style="margin-top: 8px;">
          <span v-for="c in classes" :key="c" class="on">{{ c }}</span>
        </div>
      </div>

      <!-- Autoencoder AE v1 -->
      <div class="card c6">
        <h2>Unsupervised Autoencoder (AE {{ store.modelMeta?.ae_version || 'v1' }})</h2>
        <div class="kv" style="margin-top: 10px;">
          <span>Architecture</span><span>Deep Symmetric Bottleneck (58 &rarr; 32 &rarr; 16 &rarr; 32 &rarr; 58)</span>
          <span>Training Baseline</span><span>100% Benign Network Flows (Normal Traffic)</span>
          <span>Reconstruction Metric</span><span>Mean Squared Error (MSE)</span>
          <span>Decision Threshold</span><span style="color:var(--zd);">MSE &gt; {{ store.aeThreshold.toFixed(4) }}</span>
          <span>Zero-Day Recall</span><span style="color:var(--ok);">97.8%</span>
          <span>False Positive Rate</span><span>0.41%</span>
        </div>

        <h3 style="margin-top: 16px; font-size: 13px;">Detection Mechanism</h3>
        <p style="color:var(--mu); font-size: 12.5px; margin: 8px 0 0; line-height: 1.5;">
          The Autoencoder compresses normal network patterns into a compact latent representation. When anomalous or zero-day attack patterns (such as unknown exploits or unusual packet timing) pass through the network, the model fails to faithfully reconstruct them, triggering an instant MSE anomaly alert.
        </p>
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
