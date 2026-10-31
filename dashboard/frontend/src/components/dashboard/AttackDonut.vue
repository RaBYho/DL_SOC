<template>
  <div class="card c4 attack-donut-card">
    <div class="card-header-row">
      <div class="header-titles">
        <h2 class="card-title">{{ store.t('donut.title') }}</h2>
        <span class="card-subtitle">{{ store.t('donut.subtitle') }}</span>
      </div>
      <span class="threat-count-pill">{{ formatNumber(totalAttacks) }} {{ store.t('donut.detected') }}</span>
    </div>

    <!-- Side-by-side Content: Large Donut on Left, Compact Info on Right -->
    <div class="donut-content-row">
      <!-- Left: Large Donut Ring -->
      <div class="donut-wrapper">
        <svg viewBox="0 0 130 130" class="donut-svg" role="img" aria-label="Attack family distribution">
          <defs>
            <filter id="glowDonut" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2.5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>
          <!-- Background Track -->
          <circle cx="65" cy="65" r="48" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="13" />
          
          <!-- Segments -->
          <circle 
            v-for="(seg, idx) in donutSegments"
            :key="idx"
            cx="65" 
            cy="65" 
            r="48" 
            fill="none" 
            stroke-width="13" 
            :style="{ stroke: seg.color }" 
            :stroke-dasharray="`${Math.max(seg.arcLength - 2.5, 0)} ${CIRCUMFERENCE}`" 
            :stroke-dashoffset="-seg.offset" 
            transform="rotate(-90 65 65)"
          />

          <!-- Center Text -->
          <text x="65" y="60" text-anchor="middle" class="donut-center-val">
            {{ formatNumber(totalAttacks) }}
          </text>
          <text x="65" y="74" text-anchor="middle" class="donut-center-sub">
            {{ store.t('donut.attacks') }}
          </text>
        </svg>
      </div>

      <!-- Right: Compact Information on Each Color -->
      <div class="legend-list">
        <div 
          v-for="item in sortedDist" 
          :key="item.name" 
          class="legend-item"
          :title="`${item.name}: ${formatNumber(item.count)} (${item.pct.toFixed(1)}%)`"
        >
          <i class="legend-dot" :style="{ background: item.color, boxShadow: `0 0 6px ${item.color}` }"></i>
          <span class="legend-name">{{ item.name }}</span>
          <em class="legend-pct">{{ item.pct.toFixed(0) }}%</em>
          <div class="legend-bar-track">
            <b :style="{ width: `${item.barPct}%`, background: item.color }"></b>
          </div>
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
  height: 320px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  padding: 16px 18px;
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
  flex: none;
}

.header-titles {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.card-title {
  margin: 0;
  font-size: 14.5px;
  font-weight: 700;
  letter-spacing: -0.2px;
  color: #fff;
  line-height: 1.2;
}

.card-subtitle {
  font-size: 11px;
  font-weight: 400;
  color: var(--mu);
  line-height: 1.2;
}

.threat-count-pill {
  font-size: 10.5px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 6px;
  background: rgba(255, 77, 126, 0.14);
  color: var(--cr);
  border: 1px solid rgba(255, 77, 126, 0.28);
  white-space: nowrap;
  flex: none;
}

/* Side-by-side content row */
.donut-content-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  flex: 1;
  min-height: 0;
}

/* Left: Large Donut Ring */
.donut-wrapper {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
}

.donut-svg {
  width: 195px;
  height: 195px;
  display: block;
  filter: drop-shadow(0 6px 16px rgba(0, 0, 0, 0.35));
}

.donut-center-val {
  font-size: 20px;
  font-weight: 800;
  fill: #fff;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.5px;
}

.donut-center-sub {
  font-size: 9.5px;
  fill: var(--mu);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.6px;
}

/* Right: Compact Information on Each Color */
.legend-list {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 7px;
  flex: 1;
  min-width: 0;
}

.legend-item {
  display: grid;
  grid-template-columns: 7px 1fr 28px 36px;
  gap: 7px;
  align-items: center;
  font-size: 11px;
  padding: 2px 4px;
  border-radius: 4px;
  transition: background 0.15s ease;
}

.legend-item:hover {
  background: rgba(255, 255, 255, 0.04);
}

.legend-dot {
  width: 7px;
  height: 7px;
  border-radius: 2px;
  flex: none;
}

.legend-name {
  color: var(--tx);
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: 0.1px;
}

.legend-pct {
  font-style: normal;
  color: var(--mu);
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  font-size: 10.5px;
}

.legend-bar-track {
  height: 4px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 2px;
  overflow: hidden;
  width: 100%;
}

.legend-bar-track b {
  display: block;
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}

/* Tablet (769px to 1200px) */
@media (max-width: 1200px) and (min-width: 769px) {
  .attack-donut-card {
    height: 310px;
  }
  .donut-svg {
    width: 205px;
    height: 205px;
  }
  .donut-content-row {
    gap: 32px;
    justify-content: flex-start;
  }
  .legend-list {
    max-width: 380px;
  }
}

/* Mobile (< 768px) - can shrink as requested */
@media (max-width: 768px) {
  .attack-donut-card {
    height: auto;
    min-height: auto;
    padding: 14px 16px;
  }

  .donut-content-row {
    gap: 12px;
  }

  .donut-svg {
    width: 150px;
    height: 150px;
  }

  .card-title {
    font-size: 13.5px;
  }

  .card-subtitle {
    font-size: 10.5px;
  }

  .legend-item {
    grid-template-columns: 6px 1fr 26px 30px;
    gap: 5px;
    font-size: 10.5px;
  }

  .legend-name {
    font-size: 10.5px;
  }

  .legend-pct {
    font-size: 10px;
  }
}

/* Extra small mobile (<= 375px) */
@media (max-width: 375px) {
  .donut-svg {
    width: 130px;
    height: 130px;
  }

  .donut-content-row {
    gap: 8px;
  }

  .legend-bar-track {
    display: none;
  }

  .legend-item {
    grid-template-columns: 6px 1fr 26px;
    gap: 5px;
  }
}
</style>
