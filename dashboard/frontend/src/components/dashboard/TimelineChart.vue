<template>
  <div class="card c5 timeline-card">
    <div class="card-header-row">
      <h2>
        {{ store.t('timeline.title') }}
        <span>{{ timeLabel }}</span>
      </h2>
      <div class="rate-badge">
        <span class="dot-green"></span>
        <span>{{ store.kpis.flow_rate_sec }} {{ store.t('kpi.flowsSec') }}</span>
      </div>
    </div>

    <svg 
      viewBox="0 0 560 230" 
      class="timeline-svg"
      role="img" 
      aria-label="Flow volume over time"
    >
      <defs>
        <linearGradient id="areaGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#5865f2" stop-opacity="0.35" />
          <stop offset="100%" stop-color="#5865f2" stop-opacity="0.0" />
        </linearGradient>
      </defs>

      <!-- Background Grid Lines -->
      <g stroke="rgba(255, 255, 255, 0.06)" stroke-dasharray="2 3">
        <line 
          v-for="y in gridLines" 
          :key="y.val"
          x1="44" 
          x2="554" 
          :y1="y.y" 
          :y2="y.y" 
        />
      </g>
      <!-- Y Axis Labels -->
      <text 
        v-for="y in gridLines" 
        :key="`lbl-${y.val}`"
        x="38" 
        :y="y.y + 4" 
        text-anchor="end"
        class="axis-label"
      >
        {{ y.label }}
      </text>

      <!-- Rolling Baseline Threshold Line -->
      <line 
        x1="44" 
        x2="554" 
        :y1="baselineY" 
        :y2="baselineY" 
        stroke="var(--md)" 
        stroke-dasharray="4 4" 
        stroke-width="1.2"
      />
      <text x="548" :y="baselineY - 5" text-anchor="end" class="baseline-text">
        {{ store.t('timeline.baseline') }}
      </text>

      <!-- Area Path with Gradient -->
      <path 
        :d="areaPath" 
        fill="url(#areaGrad)" 
      />

      <!-- Main Activity Line -->
      <path 
        :d="linePath" 
        fill="none" 
        stroke="var(--ac)" 
        stroke-width="2.2" 
        stroke-linejoin="round"
        stroke-linecap="round"
      />

      <!-- Spike Highlight Circles -->
      <g v-for="pt in spikes" :key="pt.index">
        <circle 
          :cx="pt.x" 
          :cy="pt.y" 
          r="8" 
          fill="var(--cr)" 
          opacity="0.3"
        />
        <circle 
          :cx="pt.x" 
          :cy="pt.y" 
          r="4" 
          fill="var(--cr)" 
          stroke="#fff" 
          stroke-width="1.5"
        >
          <title>Incident spike: {{ pt.val }} flows/s</title>
        </circle>
      </g>

      <!-- X Axis Time Ticks -->
      <text 
        v-for="(tick, idx) in xTicks" 
        :key="idx"
        :x="tick.x" 
        y="224" 
        :text-anchor="tick.anchor"
        class="axis-label"
      >
        {{ tick.label }}
      </text>
    </svg>

    <div class="timeline-footer">
      <span>{{ store.t('timeline.footer') }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSocStore } from '@/stores/socStore'

const store = useSocStore()

const W = 560
const H = 230
const L = 44
const B = 24
const T = 16

const timeLabel = computed(() => {
  if (store.activeTimeRange === '1h') return store.t('timeline.window1h')
  if (store.activeTimeRange === '24h') return store.t('timeline.window24h')
  return store.t('timeline.window15m')
})

const series = computed(() => {
  if (store.timelineSeries && store.timelineSeries.length > 5) {
    return store.timelineSeries.map(item => item.count || 0)
  }
  return [
    820, 890, 840, 920, 860, 910, 870, 930, 890, 960,
    910, 880, 940, 1120, 1450, 1780, 1340, 960, 910, 890,
    930, 950, 910, 890, 920, 940, 900, 920, 960, 980,
    940, 910, 890, 930, 1380, 1890, 1520, 980, 920, 950
  ]
})

const maxVal = computed(() => {
  const m = Math.max(...series.value, 1400)
  return m * 1.15
})

const xs = (i, total) => L + i * ((W - L - 8) / Math.max(total - 1, 1))
const ys = (val) => H - B - (val / maxVal.value) * (H - B - T)

const baselineVal = computed(() => {
  const sorted = [...series.value].sort((a, b) => a - b)
  const median = sorted[Math.floor(sorted.length / 2)] || 900
  return median * 1.35
})

const baselineY = computed(() => ys(baselineVal.value))

const gridLines = computed(() => {
  const m = maxVal.value / 1.15
  return [0, 0.5, 1.0].map(f => {
    const val = Math.round(m * f)
    return {
      val,
      y: ys(val),
      label: val >= 1000 ? `${(val / 1000).toFixed(1)}k` : String(val)
    }
  })
})

const linePath = computed(() => {
  const pts = series.value
  return pts.map((v, i) => (i ? 'L' : 'M') + `${xs(i, pts.length).toFixed(1)} ${ys(v).toFixed(1)}`).join(' ')
})

const areaPath = computed(() => {
  const pts = series.value
  if (pts.length === 0) return ''
  const line = linePath.value
  const lastX = xs(pts.length - 1, pts.length).toFixed(1)
  const baseY = (H - B).toFixed(1)
  return `${line} L${lastX} ${baseY} L${L} ${baseY} Z`
})

const spikes = computed(() => {
  const pts = series.value
  const thresh = baselineVal.value
  const list = []
  pts.forEach((v, i) => {
    if (v > thresh) {
      list.push({
        index: i,
        val: Math.round(v),
        x: xs(i, pts.length),
        y: ys(v)
      })
    }
  })
  return list
})

const xTicks = computed(() => {
  const nowLabel = store.t('timeline.liveNow')
  const labels = {
    '15m': ['-15m', '-10m', '-5m', nowLabel],
    '1h': ['-60m', '-40m', '-20m', nowLabel],
    '24h': ['-24h', '-16h', '-8h', nowLabel]
  }[store.activeTimeRange] || ['-15m', '-10m', '-5m', nowLabel]

  return labels.map((label, idx) => ({
    label,
    x: L + idx * ((W - L - 8) / 3),
    anchor: idx === 0 ? 'start' : idx === 3 ? 'end' : 'middle'
  }))
})
</script>

<style scoped>
.timeline-card {
  display: flex;
  flex-direction: column;
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 10px;
}

.card-header-row h2 {
  margin: 0;
}

.rate-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
  font-weight: 700;
  color: var(--ok);
  background: rgba(61, 220, 151, 0.12);
  padding: 2px 8px;
  border-radius: 6px;
  border: 1px solid rgba(61, 220, 151, 0.25);
  font-variant-numeric: tabular-nums;
}

.dot-green {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--ok);
}

.timeline-svg {
  width: 100%;
  height: auto;
}

.axis-label {
  fill: var(--mu);
  font-size: 10px;
  font-family: ui-monospace, monospace;
}

.baseline-text {
  fill: var(--md);
  font-size: 9.5px;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.timeline-footer {
  font-size: 11.5px;
  color: var(--mu);
  margin-top: 6px;
}
</style>
