<template>
  <div class="fleet-empty-state">
    <div class="radar-scan-box">
      <div class="radar-circle circle-1"></div>
      <div class="radar-circle circle-2"></div>
      <div class="radar-circle circle-3"></div>
      <div class="radar-sweeper"></div>
      <div class="radar-center-dot"></div>
    </div>
    <h4 class="empty-state-title">Aucune sonde détectée pour ce filtre</h4>
    <p class="empty-state-text">
      Déployez un agent sur une machine distante avec la commande ci-contre ou lancez une simulation de rejeu PCAP pour générer des flux en direct.
    </p>
    <div class="empty-actions">
      <button type="button" class="btn-glass" @click="$emit('switchTab', 'replay')">
        <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
        </svg>
        <span>Lancer un Rejeu PCAP</span>
      </button>
      <button type="button" class="btn-glass" @click="$emit('resetFilter')">
        Réinitialiser le filtre
      </button>
    </div>
  </div>
</template>

<script setup>
defineEmits(['switchTab', 'resetFilter'])
</script>

<style scoped>
.fleet-empty-state {
  text-align: center;
  padding: 48px 24px;
  background: #131422;
  border: 1px dashed #2d3049;
  border-radius: 14px;
  margin-top: 10px;
}

.radar-scan-box {
  position: relative;
  width: 90px;
  height: 90px;
  margin: 0 auto 16px;
  border-radius: 50%;
  border: 1px solid rgba(88, 101, 242, 0.4);
  background: radial-gradient(circle, rgba(88, 101, 242, 0.08) 0%, rgba(15, 16, 23, 0) 70%);
}

.radar-circle {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  border: 1px solid rgba(88, 101, 242, 0.25);
}

.circle-1 { width: 30px; height: 30px; }
.circle-2 { width: 60px; height: 60px; }
.circle-3 { width: 90px; height: 90px; }

.radar-center-dot {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #5865f2;
  box-shadow: 0 0 8px #5865f2;
}

.radar-sweeper {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: conic-gradient(from 0deg, rgba(88, 101, 242, 0.35) 0deg, transparent 60deg, transparent 360deg);
  animation: radar-sweep 3s linear infinite;
}

@keyframes radar-sweep {
  100% { transform: rotate(360deg); }
}

.empty-state-title {
  margin: 0 0 8px;
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
}

.empty-state-text {
  font-size: 12.5px;
  color: #7982a9;
  max-width: 440px;
  margin: 0 auto 18px;
  line-height: 1.5;
}

.empty-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.btn-glass {
  height: 36px;
  padding: 0 14px;
  font-size: 12.5px;
  font-weight: 600;
  color: #d1d6f5;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 9px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.btn-glass:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.25);
  transform: translateY(-1px);
}

.svg-icon {
  width: 15px;
  height: 15px;
}
</style>
