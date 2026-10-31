<template>
  <div class="card catalog-panel-card">
    <div class="catalog-header">
      <div>
        <h3 class="section-title">Catalogue des Scénarios d'Attaques</h3>
        <p class="section-subtitle">
          {{ filteredPcaps.length }} capture(s) prête(s) pour validation empirique
        </p>
      </div>
      
      <!-- Barre de recherche interne -->
      <div class="catalog-search-wrap">
        <svg class="search-input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input 
          v-model="pcapSearch" 
          type="text" 
          placeholder="Filtrer les captures..." 
          class="catalog-search-input"
        />
        <span v-if="pcapSearch" class="clear-search-btn" @click="pcapSearch = ''">✕</span>
      </div>
    </div>

    <!-- Filtres de Catégories -->
    <div class="catalog-cat-chips">
      <button 
        v-for="cat in pcapCategories" 
        :key="cat.key"
        type="button"
        class="cat-chip-btn"
        :class="{ active: selectedCategoryFilter === cat.key }"
        @click="selectedCategoryFilter = cat.key"
      >
        {{ cat.label }}
      </button>
    </div>

    <!-- Liste des scénarios -->
    <div class="scenario-scroll-list">
      <ReplayScenarioItem
        v-for="p in filteredPcaps"
        :key="p.filename"
        :scenario="p"
        :is-selected="selectedPcap === p.filename"
        :is-running="isRunning && activePcapName === p.filename"
        @select="$emit('select', $event)"
      />

      <div v-if="filteredPcaps.length === 0" class="no-pcaps-matched">
        <span>Aucun fichier PCAP ne correspond à votre filtre.</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import ReplayScenarioItem from './ReplayScenarioItem.vue'

const props = defineProps({
  pcapFiles: {
    type: Array,
    default: () => []
  },
  selectedPcap: {
    type: String,
    default: ''
  },
  isRunning: {
    type: Boolean,
    default: false
  },
  activePcapName: {
    type: String,
    default: ''
  }
})

defineEmits(['select'])

const pcapSearch = ref('')
const selectedCategoryFilter = ref('ALL')

const pcapCategories = [
  { key: 'ALL', label: 'Toutes les captures' },
  { key: 'DDoS', label: 'DDoS & DoS' },
  { key: 'PortScan', label: 'Scans de Ports' },
  { key: 'Bot', label: 'Botnet & C2' },
  { key: 'BruteForce', label: 'Brute Force' },
  { key: 'WebAttack', label: 'Web Attacks' },
  { key: 'BENIGN', label: 'Trafic Nominal' }
]

const filteredPcaps = computed(() => {
  let list = props.pcapFiles || []
  if (selectedCategoryFilter.value !== 'ALL') {
    list = list.filter(p => {
      const cat = (p.category || '').toUpperCase()
      const target = selectedCategoryFilter.value.toUpperCase()
      return cat.includes(target) || (target === 'DDOS' && cat.includes('DOS'))
    })
  }
  if (pcapSearch.value.trim()) {
    const q = pcapSearch.value.trim().toLowerCase()
    list = list.filter(p => 
      (p.filename || '').toLowerCase().includes(q) ||
      (p.title || '').toLowerCase().includes(q) ||
      (p.description || '').toLowerCase().includes(q) ||
      (p.category || '').toLowerCase().includes(q)
    )
  }
  return list
})
</script>

<style scoped>
.section-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.2px;
}

.section-subtitle {
  margin: 4px 0 0;
  font-size: 12px;
  color: #8b8ea8;
  line-height: 1.4;
}

.catalog-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 12px;
}

.catalog-search-wrap {
  position: relative;
  width: 240px;
}

.search-input-icon {
  position: absolute;
  left: 10px;
  top: 10px;
  width: 14px;
  height: 14px;
  color: #7982a9;
  pointer-events: none;
}

.catalog-search-input {
  width: 100%;
  height: 36px;
  background: #141524;
  border: 1px solid #2e3047;
  border-radius: 8px;
  padding: 0 28px 0 32px;
  font-size: 12px;
  color: #ffffff;
  outline: none;
}

.catalog-search-input:focus {
  border-color: #5865f2;
}

.clear-search-btn {
  position: absolute;
  right: 10px;
  top: 9px;
  font-size: 11px;
  color: #7982a9;
  cursor: pointer;
}

.catalog-cat-chips {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 8px;
  margin-bottom: 12px;
}

.cat-chip-btn {
  height: 28px;
  padding: 0 12px;
  font-size: 11px;
  font-weight: 600;
  border-radius: 6px;
  background: #151726;
  border: 1px solid #292d44;
  color: #8b8ea8;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.cat-chip-btn:hover {
  background: #202337;
  color: #ffffff;
}

.cat-chip-btn.active {
  background: #4a57e0;
  color: #ffffff;
  border-color: #5865f2;
}

.scenario-scroll-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 520px;
  overflow-y: auto;
  padding-right: 4px;
}

.no-pcaps-matched {
  text-align: center;
  padding: 30px;
  color: #7982a9;
  font-size: 12.5px;
}
</style>
