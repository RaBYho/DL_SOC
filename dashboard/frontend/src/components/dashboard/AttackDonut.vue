<template>
  <div class="card c4 attack-donut-card">
    <div class="card-header-row">
      <h2>
        {{ store.t('donut.title') }}
        <span>{{ store.t('donut.subtitle') }}</span>
      </h2>
      <span class="threat-count-pill">{{ formatNumber(totalAttacks) }} {{ store.t('donut.detected') }}</span>
    </div>

    <!-- Concentric Donut SVG -->
    <div class="donut-wrapper">
      <svg viewBox="0 0 130 130" class="donut-svg" role="img" aria-label="Attack family distribution">
        <defs>
          <filter id="glowDonut" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>
        <!-- Background Track -->
        <circle cx="65" cy="65" r="48" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="14" />
        
        <!-- Segments -->
        <circle 
          v-for="(seg, idx) in donutSegments"
          :key="idx"
          cx="65" 
          cy="65" 
          r="48" 
          fill="none" 
          stroke-width="14" 
          :style="{ stroke: seg.color }" 
          :stroke-dasharray="`${Math.max(seg.arcLength - 2.5, 0)} ${CIRCUMFERENCE}`" 
          :stroke-dashoffset="-seg.offset" 
          transform="rotate(-90 65 65)"
        />

        <!-- Center Text -->
        <text x="65" y="61" text-anchor="middle" class="donut-center-val">
          {{ formatNumber(totalAttacks) }}
        </text>
        <text x="65" y="76" text-anchor="middle" class="donut-center-sub">
          {{ store.t('donut.attacks') }}
        </text>
      </svg>
    </div>

    <!-- Legend -->
    <div class="legend-list">
      <div 
        v-for="item in sortedDist" 
        :key="item.name" 
        class="legend-item"
      >
        <i class="legend-dot" :style="{ background: item.color, boxShadow: `0 0 8px ${item.color}` }"></i>
        <span class="legend-name">{{ item.name }}</span>
        <em class="legend-pct">{{ item.pct.toFixed(0) }}%</em>
        <div class="legend-bar-track">
          <b :style="{ width: `${item.barPct}%`, background: item.color }"></b>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSocStore } from '@/stores/socStore'

const store = useSocStore()
const CIRCUMFERENCE = 2 * Math.PI * 48 // ~301.59

const COLOR_MAP = {
  'DDoS': 'var(--cr)',
  'DoS-Hulk': 'var(--hi)',
  'DoS-GoldenEye': 'var(--hi)',
  'DoS-slowloris': 'var(--hi)',
  'DoS-Slowhttptest': 'var(--hi)',
  'PortScan': 'var(--md)',
  'SSH-Patator': 'var(--lo)',
  'FTP-Patator': 'var(--ac)',
  'WebAttack': 'var(--zd)',
  'Bot': 'var(--ok)',
  'Scan-Vista': 'var(--ac2)',
  'Zero-Day Anomaly': 'var(--zd)'
}

const sortedDist = computed(() => {
  let list = store.attackDistribution || []
  if (list.length === 0) {
    list = [
      { name: 'DDoS', count: 680, color: 'var(--cr)' },
      { name: 'PortScan', count: 420, color: 'var(--md)' },
      { name: 'DoS-Hulk', count: 310, color: 'var(--hi)' },
      { name: 'SSH-Patator', count: 180, color: 'var(--lo)' },
      { name: 'WebAttack', count: 160, color: 'var(--zd)' },
      { name: 'FTP-Patator', count: 110, color: 'var(--ac)' },
      { name: 'Bot', count: 76, color: 'var(--ok)' }
    ]
  }

  const tot = list.reduce((acc, curr) => acc + (curr.count || 0), 0) || 1
  const maxVal = Math.max(...list.map(l => l.count || 0)) || 1

  return list
    .filter(i => (i.count || 0) > 0)
    .sort((a, b) => (b.count || 0) - (a.count || 0))
    .slice(0, 7)
    .map(i => {
      const name = i.label || i.name || 'Threat'
      const count = i.count || 0
      return {
        name,
        count,
        pct: (count / tot) * 100,
        barPct: (count / maxVal) * 100,
        color: i.color || COLOR_MAP[name] || 'var(--ac)'
      }
    })
})

const totalAttacks = computed(() => {
  return sortedDist.value.reduce((acc, curr) => acc + curr.count, 0)
})

const donutSegments = computed(() => {
  let cumulative = 0
  return sortedDist.value.map(item => {
    const arcLength = (item.pct / 100) * CIRCUMFERENCE
    const offset = cumulative
    cumulative += arcLength
    return {
      color: item.color,
      arcLength,
      offset
    }
  })
})

function formatNumber(num) {
  if (!num) return '0'
  return Math.round(num).toLocaleString('en-US')
}
</script>

<style scoped>
.attack-donut-card {
  display: flex;
  flex-direction: column;
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 12px;
}

.card-header-row h2 {
  margin: 0;
}

.threat-count-pill {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 6px;
  background: rgba(255, 77, 126, 0.15);
  color: var(--cr);
  border: 1px solid rgba(255, 77, 126, 0.3);
}

.donut-wrapper {
  display: flex;
  justify-content: center;
  margin: 6px 0 14px;
}

.donut-svg {
  width: 175px;
  height: 175px;
}

.donut-center-val {
  font-size: 20px;
  font-weight: 800;
  fill: #fff;
}

.donut-center-sub {
  font-size: 11px;
  fill: var(--mu);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.legend-list {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.legend-item {
  display: grid;
  grid-template-columns: 10px 1fr 38px 60px;
  gap: 10px;
  align-items: center;
  font-size: 12.5px;
}

.legend-dot {
  width: 9px;
  height: 9px;
  border-radius: 3px;
  flex: none;
}

.legend-name {
  color: var(--tx);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.legend-pct {
  font-style: normal;
  color: var(--mu);
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.legend-bar-track {
  height: 5px;
  background: var(--panel2);
  border-radius: 3px;
  overflow: hidden;
}

.legend-bar-track b {
  display: block;
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}
</style>
