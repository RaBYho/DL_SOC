<template>
  <div class="card threat-toolbar-card">
    <div class="toolbar-primary-row">
      <!-- 1. Recherche Plein-Texte -->
      <div class="search-input-wrap">
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input 
          :value="searchQuery" 
          type="text" 
          placeholder="Rechercher une menace (nom, MITRE ID, port, protocole)..." 
          class="threat-search-input"
          @input="$emit('update:searchQuery', $event.target.value)"
        />
        <span v-if="searchQuery" class="clear-search-btn" @click="$emit('update:searchQuery', '')">✕</span>
      </div>

      <!-- 2. Filtres de Sévérité -->
      <div class="severity-pills-wrap">
        <button 
          type="button" 
          class="pill-btn" 
          :class="{ active: selectedSeverity === 'ALL' }"
          @click="$emit('update:selectedSeverity', 'ALL')"
        >
          Toutes ({{ totalThreats }})
        </button>
        <button 
          type="button" 
          class="pill-btn crit" 
          :class="{ active: selectedSeverity === 'Critical' }"
          @click="$emit('update:selectedSeverity', 'Critical')"
        >
          Critique ({{ countsBySeverity.Critical || 0 }})
        </button>
        <button 
          type="button" 
          class="pill-btn high" 
          :class="{ active: selectedSeverity === 'High' }"
          @click="$emit('update:selectedSeverity', 'High')"
        >
          Élevée ({{ countsBySeverity.High || 0 }})
        </button>
        <button 
          type="button" 
          class="pill-btn med" 
          :class="{ active: selectedSeverity === 'Medium' }"
          @click="$emit('update:selectedSeverity', 'Medium')"
        >
          Moyenne ({{ countsBySeverity.Medium || 0 }})
        </button>
      </div>

      <!-- 3. Toggle exclusif : Détectées dans le SOC -->
      <button 
        type="button" 
        class="btn-soc-only"
        :class="{ active: socDetectedOnly }"
        @click="$emit('update:socDetectedOnly', !socDetectedOnly)"
      >
        <span class="soc-pulse-dot" :class="{ 'is-active': activeInSocCount > 0 }"></span>
        <span>Actives dans le SOC ({{ activeInSocCount }})</span>
      </button>

      <!-- 4. Bascule de Vue (Cartes vs Matrice MITRE) -->
      <div class="view-switch-tabs">
        <button 
          type="button" 
          class="view-tab-btn" 
          :class="{ active: activeView === 'cards' }"
          @click="$emit('update:activeView', 'cards')"
          title="Vue en fiches détaillées"
        >
          <svg class="view-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7"/>
            <rect x="14" y="3" width="7" height="7"/>
            <rect x="14" y="14" width="7" height="7"/>
            <rect x="3" y="14" width="7" height="7"/>
          </svg>
          <span>Fiches</span>
        </button>
        <button 
          type="button" 
          class="view-tab-btn" 
          :class="{ active: activeView === 'matrix' }"
          @click="$emit('update:activeView', 'matrix')"
          title="Vue matricielle MITRE ATT&CK"
        >
          <svg class="view-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="8" y1="6" x2="21" y2="6"/>
            <line x1="8" y1="12" x2="21" y2="12"/>
            <line x1="8" y1="18" x2="21" y2="18"/>
            <line x1="3" y1="6" x2="3.01" y2="6"/>
            <line x1="3" y1="12" x2="3.01" y2="12"/>
            <line x1="3" y1="18" x2="3.01" y2="18"/>
          </svg>
          <span>Matrice MITRE</span>
        </button>
      </div>
    </div>

    <!-- 5. Filtres de Tactique MITRE en bande horizontale -->
    <div class="tactics-filter-row">
      <span class="tactics-label">Filtrer par tactique :</span>
      <div class="tactics-chips-scroll">
        <button 
          v-for="t in tactics" 
          :key="t.key"
          type="button"
          class="tactic-chip-btn"
          :class="{ active: selectedTactic === t.key }"
          @click="$emit('update:selectedTactic', t.key)"
        >
          {{ t.label }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  searchQuery: {
    type: String,
    default: ''
  },
  selectedSeverity: {
    type: String,
    default: 'ALL'
  },
  selectedTactic: {
    type: String,
    default: 'ALL'
  },
  socDetectedOnly: {
    type: Boolean,
    default: false
  },
  activeView: {
    type: String,
    default: 'cards'
  },
  totalThreats: {
    type: Number,
    default: 0
  },
  activeInSocCount: {
    type: Number,
    default: 0
  },
  countsBySeverity: {
    type: Object,
    default: () => ({})
  },
  tactics: {
    type: Array,
    default: () => []
  }
})

defineEmits([
  'update:searchQuery',
  'update:selectedSeverity',
  'update:selectedTactic',
  'update:socDetectedOnly',
  'update:activeView'
])
</script>

<style scoped>
.threat-toolbar-card {
  padding: 14px 18px;
  background: #151624;
  border: 1px solid #24273d;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 18px;
}

.toolbar-primary-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

/* 1. Recherche */
.search-input-wrap {
  position: relative;
  flex: 1;
  min-width: 240px;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 14px;
  height: 14px;
  color: #7982a9;
  pointer-events: none;
}

.threat-search-input {
  width: 100%;
  height: 34px;
  padding: 0 28px 0 32px;
  background: #0f1019;
  border: 1px solid #262940;
  border-radius: 8px;
  color: #ffffff;
  font-size: 12px;
  outline: none;
  transition: all 0.2s;
}

.threat-search-input:focus {
  border-color: #5865f2;
  box-shadow: 0 0 0 2px rgba(88, 101, 242, 0.2);
}

.clear-search-btn {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #7982a9;
  font-size: 11px;
  cursor: pointer;
}

.clear-search-btn:hover {
  color: #ffffff;
}

/* 2. Sévérité */
.severity-pills-wrap {
  display: flex;
  gap: 4px;
  background: #0e0f18;
  padding: 3px;
  border-radius: 9px;
  border: 1px solid #24273d;
}

.pill-btn {
  height: 28px;
  padding: 0 10px;
  border-radius: 6px;
  background: transparent;
  border: none;
  font-size: 11px;
  font-weight: 600;
  color: #8b8ea8;
  cursor: pointer;
  transition: all 0.2s;
}

.pill-btn:hover { color: #ffffff; }
.pill-btn.active { background: #262942; color: #ffffff; }
.pill-btn.crit.active { background: rgba(255, 77, 126, 0.2); color: #ff4d7e; }
.pill-btn.high.active { background: rgba(255, 122, 69, 0.2); color: #ff7a45; }
.pill-btn.med.active  { background: rgba(255, 181, 71, 0.2); color: #ffb547; }

/* 3. Bouton Actives dans le SOC */
.btn-soc-only {
  height: 34px;
  padding: 0 12px;
  font-size: 11.5px;
  font-weight: 700;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #8b8ea8;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  transition: all 0.2s;
}

.btn-soc-only:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

.btn-soc-only.active {
  background: rgba(255, 77, 126, 0.16);
  border-color: rgba(255, 77, 126, 0.4);
  color: #ff85a5;
}

.soc-pulse-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #7982a9;
}

.soc-pulse-dot.is-active {
  background: #ff4d7e;
  box-shadow: 0 0 6px #ff4d7e;
  animation: pulse-dot 1.2s infinite;
}

@keyframes pulse-dot {
  0% { transform: scale(0.9); opacity: 0.7; }
  50% { transform: scale(1.4); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.7; }
}

/* 4. Bascule de vue */
.view-switch-tabs {
  display: flex;
  gap: 4px;
  background: #0e0f18;
  padding: 3px;
  border-radius: 8px;
  border: 1px solid #24273d;
}

.view-tab-btn {
  height: 28px;
  padding: 0 10px;
  border-radius: 6px;
  background: transparent;
  border: none;
  font-size: 11px;
  font-weight: 600;
  color: #8b8ea8;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.view-tab-btn:hover { color: #ffffff; }
.view-tab-btn.active {
  background: #5865f2;
  color: #ffffff;
}

.view-svg {
  width: 13px;
  height: 13px;
}

/* 5. Tactiques MITRE */
.tactics-filter-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  overflow-x: auto;
}

.tactics-label {
  font-size: 11px;
  font-weight: 600;
  color: #7982a9;
  white-space: nowrap;
}

.tactics-chips-scroll {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 2px;
}

.tactic-chip-btn {
  height: 24px;
  padding: 0 10px;
  border-radius: 6px;
  background: #11121d;
  border: 1px solid #24273b;
  font-size: 10.5px;
  font-weight: 600;
  color: #8b8ea8;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.tactic-chip-btn:hover {
  background: #1b1d2e;
  color: #ffffff;
}

.tactic-chip-btn.active {
  background: #252840;
  border-color: #5865f2;
  color: #9baaff;
}
</style>
