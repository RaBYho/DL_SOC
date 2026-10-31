<template>
  <div class="card c5 timeline-card">
    <!-- Header: Title & Subtitle strictly stacked on left, Badges & Controls on right -->
    <div class="card-header-row">
      <div class="header-titles">
        <h2 class="card-title">{{ store.t('timeline.title') }}</h2>
        <span class="card-subtitle">{{ timeLabel }}</span>
      </div>

      <div class="header-right">
        <!-- Live Ingestion Flow Rate Badge -->
        <div class="rate-badge" title="Taux d'ingestion direct">
          <span class="dot-green"></span>
          <span>{{ store.kpis.flow_rate_sec }} {{ store.t('kpi.flowsSec') }}</span>
        </div>

        <!-- Segmented Time Range Selector -->
        <div class="time-range-group" role="group" aria-label="Time range">
          <button 
            v-for="r in ['15m', '1h', '24h']" 
            :key="r"
            :class="{ active: store.activeTimeRange === r }"
            :aria-pressed="store.activeTimeRange === r"
            @click="changeRange(r)"
          >
            {{ r }}
          </button>
        </div>
      </div>
    </div>

    <!-- Chart: Centered L-Axis and Smooth Spline Waves -->
    <svg 
      viewBox="0 0 560 220" 
      class="timeline-svg"
      role="img" 
      aria-label="Flow volume over time"
    >
      <defs>
        <!-- Area Fill Gradient (Indigo to Transparent) -->
        <linearGradient id="areaGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#6366f1" stop-opacity="0.38" />
          <stop offset="60%" stop-color="#6366f1" stop-opacity="0.10" />
          <stop offset="100%" stop-color="#6366f1" stop-opacity="0.0" />
        </linearGradient>

        <!-- Line Stroke Glow Filter -->
        <filter id="lineGlow" x="-10%" y="-20%" width="120%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#6366f1" flood-opacity="0.3" />
        </filter>
      </defs>

      <!-- Horizontal Grid Lines -->
      <g stroke="rgba(255, 255, 255, 0.06)" stroke-dasharray="2 3">
        <line 
          v-for="g in gridLines" 
          :key="g.val"
          :x1="X_START" 
          :x2="X_END" 
          :y1="g.y" 
          :y2="g.y" 
        />
      </g>

      <!-- L-Shaped Axis Frame -->
      <line 
        :x1="X_START" 
        :y1="T" 
        :x2="X_START" 
        :y2="H - B" 
        stroke="rgba(255, 255, 255, 0.16)" 
        stroke-width="1.2" 
      />
      <line 
        :x1="X_START" 
        :y1="H - B" 
        :x2="X_END" 
        :y2="H - B" 
        stroke="rgba(255, 255, 255, 0.16)" 
        stroke-width="1.2" 
      />

      <!-- Y-Axis Ticks & Labels -->
      <g v-for="g in gridLines" :key="`g-${g.val}`">
        <line 
          :x1="X_START - 4" 
          :x2="X_START" 
          :y1="g.y" 
          :y2="g.y" 
          stroke="rgba(255, 255, 255, 0.22)" 
          stroke-width="1.2" 
        />
        <text 
          :x="X_START - 8" 
          :y="g.y + 3.5" 
          text-anchor="end"
          class="axis-label"
        >
          {{ g.label }}
        </text>
      </g>

      <!-- Rolling Baseline Threshold Line -->
      <line 
        :x1="X_START" 
        :x2="X_END" 
        :y1="baselineY" 
        :y2="baselineY" 
        stroke="var(--md)" 
        stroke-dasharray="4 4" 
        stroke-width="1.3"
        class="baseline-line"
      />
      <text :x="X_END" :y="baselineY - 5" text-anchor="end" class="baseline-text">
        {{ store.t('timeline.baseline') }}
      </text>

      <!-- Gradient Area Under Curve -->
      <path 
        :d="areaPath" 
        fill="url(#areaGrad)" 
        class="timeline-area"
      />

      <!-- Main Smooth Activity Spline Curve -->
      <path 
        :d="linePath" 
        fill="none" 
        stroke="#6366f1" 
        stroke-width="2.4" 
        stroke-linecap="round"
        stroke-linejoin="round"
        filter="url(#lineGlow)"
        class="timeline-line"
      />

      <!-- Incident Spike Highlight Circles with Fluid Radar Pulse -->
      <g v-for="pt in spikes" :key="pt.index">
        <circle 
          :cx="pt.x" 
          :cy="pt.y" 
          r="8" 
          fill="var(--cr)" 
          class="spike-halo"
        />
        <circle 
          :cx="pt.x" 
          :cy="pt.y" 
          r="4" 
          fill="var(--cr)" 
          stroke="#fff" 
          stroke-width="1.5"
          class="spike-core"
        >
          <title>Pic d'incident: {{ pt.val }} flux/s</title>
        </circle>
      </g>

      <!-- X-Axis Time Ticks & Labels -->
      <g v-for="(tick, idx) in xTicks" :key="`xt-${idx}`">
        <line 
          :x1="tick.x" 
          :x2="tick.x" 
          :y1="H - B" 
          :y2="H - B + 4" 
          stroke="rgba(255, 255, 255, 0.22)" 
          stroke-width="1.2" 
        />
        <text 
          :x="tick.x" 
          :y="H - 8" 
          :text-anchor="tick.anchor"
          class="axis-label"
        >
          {{ tick.label }}
        </text>
      </g>
    </svg>

    <!-- Footer Summary Strip -->
    <div class="timeline-footer">
      <span>{{ store.t('timeline.footer') }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSocStore } from '@/stores/socStore'

const store = useSocStore()

// Symmetrical margins for balanced centering inside 560px SVG
const W = 560
const H = 220
const X_START = 40
const X_END = 520
const B = 24
const T = 16

const timeLabel = computed(() => {
  if (store.activeTimeRange === '1h') return store.t('timeline.window1h')
  if (store.activeTimeRange === '24h') return store.t('timeline.window24h')
  return store.t('timeline.window15m')
})

function changeRange(range) {
  if (store.activeTimeRange !== range) {
    store.loadDashboardData(range)
  }
}

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

const xs = (i, total) => X_START + i * ((X_END - X_START) / Math.max(total - 1, 1))
const ys = (val) => H - B - (val / maxVal.value) * (H - B - T)

const pointCoords = computed(() => {
  const pts = series.value
  return pts.map((v, i) => ({
    val: v,
    x: xs(i, pts.length),
    y: ys(v)
  }))
})

// Catmull-Rom to Cubic Bézier Spline Interpolation for silky smooth waves
function getSmoothSplinePath(points, tension = 0.18) {
  if (!points || points.length === 0) return ''
  if (points.length === 1) return `M ${points[0].x.toFixed(1)} ${points[0].y.toFixed(1)}`

  let d = `M ${points[0].x.toFixed(1)} ${points[0].y.toFixed(1)}`
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i === 0 ? 0 : i - 1]
    const p1 = points[i]
    const p2 = points[i + 1]
    const p3 = points[i + 2 >= points.length ? points.length - 1 : i + 2]

    const cp1x = p1.x + (p2.x - p0.x) * tension
    const cp1y = p1.y + (p2.y - p0.y) * tension
    const cp2x = p2.x - (p3.x - p1.x) * tension
    const cp2y = p2.y - (p3.y - p1.y) * tension

    d += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`
  }
  return d
}

const linePath = computed(() => {
  return getSmoothSplinePath(pointCoords.value, 0.18)
})

const areaPath = computed(() => {
  const pts = pointCoords.value
  if (pts.length === 0) return ''
  const spline = linePath.value
  const lastX = pts[pts.length - 1].x.toFixed(1)
  const firstX = pts[0].x.toFixed(1)
  const baseY = (H - B).toFixed(1)
  return `${spline} L ${lastX} ${baseY} L ${firstX} ${baseY} Z`
})

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

const spikes = computed(() => {
  const thresh = baselineVal.value
  return pointCoords.value
    .map((pt, i) => ({ ...pt, index: i }))
    .filter(pt => pt.val > thresh)
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
    x: X_START + idx * ((X_END - X_START) / (labels.length - 1)),
    anchor: idx === 0 ? 'start' : idx === labels.length - 1 ? 'end' : 'middle'
  }))
})
</script>

<style scoped>
.timeline-card {
  height: 330px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 16px 18px;
  transition: transform 0.24s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.24s ease, box-shadow 0.24s ease;
}

.timeline-card:hover {
  border-color: rgba(255, 255, 255, 0.14);
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 6px;
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

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.rate-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  color: var(--ok);
  background: rgba(61, 220, 151, 0.12);
  padding: 3px 8px;
  border-radius: 6px;
  border: 1px solid rgba(61, 220, 151, 0.25);
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.dot-green {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--ok);
  box-shadow: 0 0 6px rgba(61, 220, 151, 0.6);
  animation: pulse-live-dot 2s infinite ease-in-out;
}

@keyframes pulse-live-dot {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(0.85); opacity: 0.6; }
}

.time-range-group {
  display: inline-flex;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 8px;
  padding: 2px;
  align-items: center;
}

.time-range-group button {
  border: 0;
  background: none;
  padding: 3px 9px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--mu);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  line-height: 1.2;
}

.time-range-group button:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.06);
}

.time-range-group button:active {
  transform: scale(0.95);
}

.time-range-group button.active {
  background: #6366f1;
  color: #fff;
  box-shadow: 0 1px 6px rgba(99, 102, 241, 0.4);
}

.timeline-svg {
  width: 100%;
  flex: 1;
  min-height: 0;
  max-height: 200px;
}

.timeline-line,
.timeline-area {
  transition: d 0.55s cubic-bezier(0.16, 1, 0.3, 1);
  will-change: d;
}

.baseline-line {
  transition: y1 0.55s cubic-bezier(0.16, 1, 0.3, 1), y2 0.55s cubic-bezier(0.16, 1, 0.3, 1);
}

/* Fluid radar pulse for incident spikes */
.spike-halo {
  animation: pulse-spike 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  transform-origin: center;
}

@keyframes pulse-spike {
  0% { opacity: 0.45; transform: scale(0.9); }
  50% { opacity: 0.15; transform: scale(1.35); }
  100% { opacity: 0.45; transform: scale(0.9); }
}

.spike-core {
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.spike-core:hover {
  transform: scale(1.4);
}

.axis-label {
  fill: var(--mu);
  font-size: 9.5px;
  font-family: ui-monospace, monospace;
}

.baseline-text {
  fill: var(--md);
  font-size: 9.5px;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.timeline-footer {
  font-size: 11px;
  color: var(--mu);
  margin-top: 4px;
  flex: none;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 768px) {
  .timeline-card {
    height: auto;
    min-height: auto;
    padding: 14px 16px;
  }

  .timeline-footer {
    white-space: normal;
  }
}

@media (max-width: 640px) {
  .card-header-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  .header-right {
    width: 100%;
    justify-content: space-between;
  }
}

@media (prefers-reduced-motion: reduce) {
  .timeline-line,
  .timeline-area,
  .baseline-line,
  .dot-green,
  .spike-halo {
    transition: none !important;
    animation: none !important;
  }
}
</style>
