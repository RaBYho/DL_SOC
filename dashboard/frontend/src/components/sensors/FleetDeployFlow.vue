<template>
  <div class="arch-flow-box">
    <div class="flow-step">
      <svg class="flow-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
        <line x1="8" y1="21" x2="16" y2="21"/>
      </svg>
      <span class="flow-label">Sonde Edge</span>
    </div>
    <div class="flow-arrow">&rarr;</div>
    <div class="flow-step">
      <svg class="flow-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
      </svg>
      <span class="flow-label">POST /ingest</span>
    </div>
    <div class="flow-arrow">&rarr;</div>
    <div class="flow-step">
      <svg class="flow-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="4" y="4" width="16" height="16" rx="2" ry="2"/>
        <rect x="9" y="9" width="6" height="6"/>
        <line x1="9" y1="1" x2="9" y2="4"/>
        <line x1="15" y1="1" x2="15" y2="4"/>
      </svg>
      <span class="flow-label">Moteur IA</span>
    </div>
    <div class="flow-arrow">&rarr;</div>
    <div class="flow-step">
      <svg class="flow-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      </svg>
      <span class="flow-label">Alertes SOC</span>
    </div>
  </div>
</template>

<style scoped>
.arch-flow-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #11121d;
  border: 1px solid #232538;
  border-radius: 10px;
  padding: 10px 14px;
  margin-bottom: 16px;
}

.flow-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.flow-svg {
  width: 16px;
  height: 16px;
  color: #8fa0ff;
}

.flow-label {
  font-size: 10px;
  color: #7982a9;
  font-weight: 600;
}

.flow-arrow {
  color: #4a57e0;
  font-size: 14px;
  font-weight: 800;
}
</style>
