<template>
  <div class="replay-progress-card">
    <div class="progress-top">
      <span class="progress-file-info">
        <span class="progress-glow-dot"></span>
        Rejeu en cours : <b>{{ replayStatus.pcap_name }}</b>
      </span>
      <span class="progress-pct">{{ (replayStatus.progress_pct || 0).toFixed(1) }}%</span>
    </div>

    <div class="progress-track">
      <div class="progress-bar-fill" :style="{ width: `${replayStatus.progress_pct || 0}%` }">
        <span class="progress-laser"></span>
      </div>
    </div>

    <div class="progress-kpi-grid">
      <div class="progress-kpi">
        <span class="kpi-label">Flux Traités</span>
        <b class="kpi-val">{{ replayStatus.processed_flows }} / {{ replayStatus.total_flows }}</b>
      </div>
      <div class="progress-kpi">
        <span class="kpi-label">Vitesse Active</span>
        <b class="kpi-val text-accent">{{ replayStatus.speed }}x</b>
      </div>
      <div class="progress-kpi">
        <span class="kpi-label">Menaces Interceptées</span>
        <b class="kpi-val text-danger">{{ replayStatus.total_alerts || totalAttacks }}</b>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  replayStatus: {
    type: Object,
    required: true
  },
  totalAttacks: {
    type: Number,
    default: 0
  }
})
</script>

<style scoped>
.replay-progress-card {
  background: #121320;
  border: 1px solid #2d3049;
  border-radius: 12px;
  padding: 14px 16px;
}

.progress-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12.5px;
  margin-bottom: 8px;
}

.progress-file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #c4ccff;
}

.progress-glow-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #3ddc97;
  box-shadow: 0 0 8px #3ddc97;
  animation: pulse-dot 1s infinite;
}

@keyframes pulse-dot {
  0% { transform: scale(0.9); opacity: 0.7; }
  50% { transform: scale(1.4); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.7; }
}

.progress-pct {
  font-size: 14px;
  font-weight: 800;
  color: #3ddc97;
}

.progress-track {
  height: 8px;
  background: #1c1d2e;
  border-radius: 999px;
  overflow: hidden;
  position: relative;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #5865f2 0%, #3ddc97 100%);
  border-radius: 999px;
  transition: width 0.3s ease;
  position: relative;
}

.progress-laser {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 12px;
  background: #ffffff;
  box-shadow: 0 0 10px #ffffff;
  opacity: 0.8;
}

.progress-kpi-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.progress-kpi {
  display: flex;
  flex-direction: column;
}

.kpi-label {
  font-size: 10.5px;
  color: #7982a9;
  text-transform: uppercase;
}

.kpi-val {
  font-size: 13px;
  font-weight: 700;
  color: #ffffff;
  margin-top: 2px;
}

.text-accent { color: #5865f2 !important; }
.text-danger { color: #ff4d7e !important; }
</style>
