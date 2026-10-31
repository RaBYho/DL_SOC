<template>
  <div 
    class="scenario-card-item"
    :class="{ 
      'is-selected': isSelected,
      'is-active-running': isRunning
    }"
    @click="$emit('select', scenario.filename)"
  >
    <div class="card-item-indicator" :class="'ind-' + (scenario.severity || 'Medium').toLowerCase()"></div>
    <div class="card-item-body">
      <div class="card-item-top">
        <div class="item-name-wrap">
          <span class="item-category-icon">
            <component :is="getScenarioIconComponent(scenario.category)" />
          </span>
          <b class="item-title">{{ scenario.title || scenario.filename }}</b>
        </div>
        <span class="sev-tag" :class="scenario.severity || 'Medium'">{{ scenario.category || 'PCAP' }}</span>
      </div>
      <p class="item-desc">{{ scenario.description || 'Capture réseau standard pour entraînement et évaluation.' }}</p>
      <div class="item-meta-bar">
        <span class="meta-filename"><code>{{ scenario.filename }}</code></span>
        <span class="meta-size"><b>{{ scenario.size_mb }} Mo</b></span>
        <span v-if="isSelected" class="meta-selected-badge">Sélectionné ✓</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { h } from 'vue'

defineProps({
  scenario: {
    type: Object,
    required: true
  },
  isSelected: {
    type: Boolean,
    default: false
  },
  isRunning: {
    type: Boolean,
    default: false
  }
})

defineEmits(['select'])

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

.item-title { font-size: 13.5px; color: #ffffff; }
.item-desc { font-size: 12px; color: #8b8ea8; margin: 0; line-height: 1.4; }

.item-meta-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  color: #7982a9;
  margin-top: 4px;
}

.meta-filename code { color: #c4ccff; }
.meta-size b { color: #eceefa; }
.meta-selected-badge { color: #8fa0ff; font-weight: 700; }

.svg-icon-mini { width: 15px; height: 15px; display: inline-block; }

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
