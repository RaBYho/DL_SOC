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
      <div 
        v-for="p in filteredPcaps" 
        :key="p.filename"
        class="scenario-card-item"
        :class="{ 
          'is-selected': selectedPcap === p.filename,
          'is-active-running': isRunning && activePcapName === p.filename
        }"
        @click="$emit('select', p.filename)"
      >
        <div class="card-item-indicator" :class="'ind-' + (p.severity || 'Medium').toLowerCase()"></div>
        <div class="card-item-body">
          <div class="card-item-top">
            <div class="item-name-wrap">
              <span class="item-category-icon">
                <component :is="getScenarioIconComponent(p.category)" />
              </span>
              <b class="item-title">{{ p.title || p.filename }}</b>
            </div>
            <span class="sev-tag" :class="p.severity || 'Medium'">{{ p.category || 'PCAP' }}</span>
          </div>
          <p class="item-desc">{{ p.description || 'Capture réseau standard pour entraînement et évaluation.' }}</p>
          <div class="item-meta-bar">
            <span class="meta-filename"><code>{{ p.filename }}</code></span>
            <span class="meta-size"><b>{{ p.size_mb }} Mo</b></span>
            <span v-if="selectedPcap === p.filename" class="meta-selected-badge">Sélectionné ✓</span>
          </div>
        </div>
      </div>

      <div v-if="filteredPcaps.length === 0" class="no-pcaps-matched">
        <span>Aucun fichier PCAP ne correspond à votre filtre.</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, h } from 'vue'

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

// Composants Iconographiques Vectoriels
const IconDDoS = () => h('svg', { class: 'svg-icon-mini text-danger', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
  h('polygon', { points: '13 2 3 14 12 14 11 22 21 10 12 10 13 2' })
])

const IconScan = () => h('svg', { class: 'svg-icon-mini text-warning', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
  h('circle', { cx: '11', cy: '11', r: '8' }),
  h('line', { x1: '21', y1: '21', x2: '16.65', y2: '16.65' })
])

const IconBot = () => h('svg', { class: 'svg-icon-mini text-purple', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
  h('rect', { x: '4', y: '4', width: '16', height: '16', rx: '2' }),
  h('circle', { cx: '9', cy: '9', r: '2' }),
  h('circle', { cx: '15', cy: '9', r: '2' }),
  h('line', { x1: '9', y1: '15', x2: '15', y2: '15' })
])

const IconBrute = () => h('svg', { class: 'svg-icon-mini text-orange', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
  h('rect', { x: '3', y: '11', width: '18', height: '11', rx: '2', ry: '2' }),
  h('path', { d: 'M7 11V7a5 5 0 0 1 10 0v4' })
])

const IconWeb = () => h('svg', { class: 'svg-icon-mini text-blue', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
  h('circle', { cx: '12', cy: '12', r: '10' }),
  h('line', { x1: '2', y1: '12', x2: '22', y2: '12' }),
  h('path', { d: 'M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z' })
])

const IconShield = () => h('svg', { class: 'svg-icon-mini text-success', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
  h('path', { d: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z' }),
  h('polyline', { points: '9 12 11 14 15 10' })
])

const IconGeneric = () => h('svg', { class: 'svg-icon-mini text-muted', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
  h('path', { d: 'M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z' })
])

const getScenarioIconComponent = (category) => {
  const cat = (category || '').toLowerCase()
  if (cat.includes('ddos') || cat.includes('dos')) return IconDDoS
  if (cat.includes('scan')) return IconScan
  if (cat.includes('bot')) return IconBot
  if (cat.includes('brute')) return IconBrute
  if (cat.includes('web')) return IconWeb
  if (cat.includes('benign') || cat.includes('normal')) return IconShield
  return IconGeneric
}
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

.scenario-card-item {
  display: flex;
  background: #151624;
  border: 1px solid #26293f;
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.scenario-card-item:hover {
  background: #1a1c2e;
  border-color: #3b4060;
  transform: translateX(2px);
}

.scenario-card-item.is-selected {
  background: rgba(88, 101, 242, 0.12);
  border-color: #5865f2;
  box-shadow: 0 4px 14px rgba(88, 101, 242, 0.2);
}

.scenario-card-item.is-active-running {
  border-color: #3ddc97;
  box-shadow: 0 0 14px rgba(61, 220, 151, 0.25);
}

.card-item-indicator {
  width: 4px;
  flex-shrink: 0;
}

.card-item-indicator.ind-critical { background: #ff4d7e; }
.card-item-indicator.ind-high     { background: #ff7a45; }
.card-item-indicator.ind-medium   { background: #ffb547; }
.card-item-indicator.ind-info     { background: #3ddc97; }

.card-item-body {
  padding: 12px 14px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.card-item-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.item-name-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.item-title {
  font-size: 13.5px;
  color: #ffffff;
}

.item-desc {
  font-size: 12px;
  color: #8b8ea8;
  margin: 0;
  line-height: 1.4;
}

.item-meta-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  color: #7982a9;
  margin-top: 4px;
}

.meta-filename code {
  color: #c4ccff;
}

.meta-size b {
  color: #eceefa;
}

.meta-selected-badge {
  color: #8fa0ff;
  font-weight: 700;
}

.no-pcaps-matched {
  text-align: center;
  padding: 30px;
  color: #7982a9;
  font-size: 12.5px;
}

.svg-icon-mini {
  width: 15px;
  height: 15px;
  display: inline-block;
}

.text-danger  { color: #ff4d7e !important; }
.text-warning { color: #ffb547 !important; }
.text-orange  { color: #ff7a45 !important; }
.text-purple  { color: #b266ff !important; }
.text-blue    { color: #6c8cff !important; }
.text-success { color: #3ddc97 !important; }
.text-muted   { color: #7982a9 !important; }

.sev-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 5px;
  text-transform: uppercase;
}

.sev-tag.Critical { background: rgba(255, 77, 126, 0.2); color: #ff4d7e; border: 1px solid rgba(255, 77, 126, 0.4); }
.sev-tag.High     { background: rgba(255, 122, 69, 0.2); color: #ff7a45; border: 1px solid rgba(255, 122, 69, 0.4); }
.sev-tag.Medium   { background: rgba(255, 181, 71, 0.2); color: #ffb547; border: 1px solid rgba(255, 181, 71, 0.4); }
.sev-tag.Info     { background: rgba(61, 220, 151, 0.2); color: #3ddc97; border: 1px solid rgba(61, 220, 151, 0.4); }
</style>
