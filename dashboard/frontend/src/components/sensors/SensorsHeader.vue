<template>
  <div class="card header-card">
    <div class="header-main-row">
      <div>
        <div class="title-with-badge">
          <h2 class="page-title">Sondes Réseau &amp; Ingestion de Trafic</h2>
          <span class="fleet-status-pill" :class="{ 'is-active': sensorsOnline > 0 }">
            <span class="status-pulse-dot"></span>
            {{ sensorsOnline }} sonde(s) en direct
          </span>
        </div>
        <p class="page-desc">
          Basculez entre le <b>rejeu de scénarios d'attaques en laboratoire (PCAP)</b> et la <b>supervision de votre parc de sondes réseau réelles (Agents Edge)</b>.
        </p>
      </div>

      <div class="header-quick-actions">
        <button 
          type="button" 
          class="btn-glass" 
          :class="{ 'spinning': isRefreshing }"
          :disabled="isRefreshing" 
          @click="$emit('refresh')"
          title="Rafraîchir les sondes et métriques"
        >
          <svg class="svg-icon refresh-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
            <path d="M3 3v5h5"/>
            <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
            <path d="M16 21h5v-5"/>
          </svg>
          <span>Actualiser</span>
        </button>
      </div>
    </div>

    <!-- Sélecteur d'Onglets Segmenté -->
    <div class="mode-tabs-wrapper">
      <button 
        type="button" 
        class="mode-tab-btn" 
        :class="{ active: activeTab === 'replay' }"
        @click="$emit('update:activeTab', 'replay')"
      >
        <svg class="svg-icon tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
        </svg>
        <span class="tab-title">Simulateur &amp; Rejeu PCAP</span>
        <span class="tab-tag mode-lab">Laboratoire</span>
        <span v-if="replayStatus.active" class="active-pulse-badge">
          <span class="pulse-ring"></span>
          En cours ({{ replayStatus.speed }}x)
        </span>
      </button>

      <button 
        type="button" 
        class="mode-tab-btn" 
        :class="{ active: activeTab === 'fleet' }"
        @click="$emit('update:activeTab', 'fleet')"
      >
        <svg class="svg-icon tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4.93 19.07a10 10 0 0 1 0-14.14"/>
          <path d="M7.76 16.24a6 6 0 0 1 0-8.48"/>
          <circle cx="12" cy="12" r="2"/>
          <path d="M16.24 7.76a6 6 0 0 1 0 8.48"/>
          <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
        </svg>
        <span class="tab-title">Parc de Sondes Réseau</span>
        <span class="tab-tag mode-fleet">Agents Réels</span>
        <span class="count-bubble">{{ sensorsCount }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  activeTab: { type: String, default: 'replay' },
  sensorsOnline: { type: Number, default: 0 },
  sensorsCount: { type: Number, default: 0 },
  replayStatus: { type: Object, default: () => ({ active: false }) },
  isRefreshing: { type: Boolean, default: false }
})

defineEmits(['update:activeTab', 'refresh'])
</script>

<style scoped>
.header-card {
  padding: 20px 24px;
  background: linear-gradient(180deg, rgba(28, 30, 48, 0.95) 0%, rgba(20, 21, 34, 0.95) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--r);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
  margin-bottom: 20px;
}

.header-main-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
}

.title-with-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.3px;
}

.fleet-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 11.5px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 999px;
  background: rgba(143, 160, 255, 0.1);
  color: #9baaff;
  border: 1px solid rgba(143, 160, 255, 0.25);
}

.fleet-status-pill.is-active {
  background: rgba(61, 220, 151, 0.15);
  color: #3ddc97;
  border-color: rgba(61, 220, 151, 0.35);
  box-shadow: 0 0 12px rgba(61, 220, 151, 0.2);
}

.status-pulse-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 6px currentColor;
}

.page-desc {
  margin: 6px 0 0;
  font-size: 13px;
  color: #8b8ea8;
  line-height: 1.45;
}

.page-desc b {
  color: #c4ccff;
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

.btn-glass:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.25);
  transform: translateY(-1px);
}

.btn-glass.spinning .refresh-icon {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

.mode-tabs-wrapper {
  display: flex;
  gap: 12px;
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.07);
}

.mode-tab-btn {
  flex: 1;
  height: 48px;
  padding: 0 20px;
  background: rgba(18, 20, 32, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  color: #9aa5ce;
  font-size: 13.5px;
  font-weight: 600;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.mode-tab-btn:hover {
  background: rgba(30, 34, 54, 0.8);
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.16);
}

.mode-tab-btn.active {
  background: linear-gradient(135deg, rgba(88, 101, 242, 0.22) 0%, rgba(74, 87, 224, 0.12) 100%);
  border-color: #5865f2;
  color: #ffffff;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.15), 0 4px 18px rgba(88, 101, 242, 0.3);
}

.tab-icon { width: 18px; height: 18px; }

.tab-tag {
  font-size: 10.5px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 6px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.tab-tag.mode-lab {
  background: rgba(255, 181, 71, 0.15);
  color: #ffb547;
  border: 1px solid rgba(255, 181, 71, 0.3);
}

.tab-tag.mode-fleet {
  background: rgba(61, 220, 151, 0.15);
  color: #3ddc97;
  border: 1px solid rgba(61, 220, 151, 0.3);
}

.count-bubble {
  margin-left: auto;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

.active-pulse-badge {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  color: #3ddc97;
  background: rgba(61, 220, 151, 0.15);
  border: 1px solid rgba(61, 220, 151, 0.35);
  padding: 3px 8px;
  border-radius: 6px;
}

.pulse-ring {
  width: 6px;
  height: 6px;
  background: #3ddc97;
  border-radius: 50%;
  animation: pulse-dot 1.2s infinite;
}

@keyframes pulse-dot {
  0% { transform: scale(0.9); opacity: 0.7; }
  50% { transform: scale(1.4); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.7; }
}

.svg-icon { width: 16px; height: 16px; }
</style>
