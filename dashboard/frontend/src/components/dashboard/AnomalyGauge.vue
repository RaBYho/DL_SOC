<template>
  <div class="card c3 anomaly-gauge-card">
    <div class="card-header-row">
      <h2>
        {{ store.t('gauge.title') }}
        <span>{{ store.t('gauge.subtitle') }}</span>
      </h2>
      <span class="threshold-pill">{{ store.t('gauge.threshold') }} {{ store.aeThreshold.toFixed(2) }}</span>
    </div>

    <svg 
      viewBox="0 0 240 145" 
      class="gauge-svg"
      role="img" 
      aria-label="Reconstruction error gauge"
    >
      <defs>
        <filter id="needleGlow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="1" stdDeviation="2" flood-color="#000" flood-opacity="0.5" />
        </filter>
      </defs>

      <!-- Background Track Arc -->
      <path 
        :d="arcPath(0, MAX_MSE)" 
        stroke="rgba(255,255,255,0.06)" 
        stroke-width="15" 
        fill="none" 
      />

      <!-- Green Normal Arc -->
      <path 
        :d="arcPath(0, store.aeThreshold)" 
        stroke="var(--ok)" 
        stroke-width="13" 
        fill="none" 
      />

      <!-- Orange Elevated Arc -->
      <path 
        :d="arcPath(store.aeThreshold, 0.85)" 
        stroke="var(--md)" 
        stroke-width="13" 
        fill="none" 
      />

      <!-- Red Anomaly Arc -->
      <path 
        :d="arcPath(0.85, MAX_MSE)" 
        stroke="var(--cr)" 
        stroke-width="13" 
        fill="none" 
      />

      <!-- Threshold Tick Mark -->
      <line 
        :x1="threshCoords.outer[0]" 
        :y1="threshCoords.outer[1]" 
        :x2="threshCoords.inner[0]" 
        :y2="threshCoords.inner[1]" 
        stroke="#fff" 
        stroke-width="2.5" 
        stroke-linecap="round"
      />
      <text 
        :x="threshCoords.outer[0] + 5" 
        :y="threshCoords.outer[1] - 4"
        class="threshold-label"
      >
        0.60
      </text>

      <!-- Needle -->
      <line 
        :x1="CX" 
        :y1="CY" 
        :x2="needleCoords[0]" 
        :y2="needleCoords[1]" 
        stroke="#fff" 
        stroke-width="3" 
        stroke-linecap="round" 
        filter="url(#needleGlow)"
      />
      <circle 
        :cx="CX" 
        :cy="CY" 
        r="6" 
        fill="#fff" 
      />

      <!-- Scale Labels -->
      <text :x="CX - R" :y="CY + 15" text-anchor="middle" class="scale-label">0.0</text>
      <text :x="CX + R" :y="CY + 15" text-anchor="middle" class="scale-label">{{ MAX_MSE.toFixed(1) }}</text>

      <!-- Center Value Readout -->
      <text 
        :x="CX" 
        :y="CY - 34" 
        text-anchor="middle" 
        class="center-mse-val"
        :style="{ fill: isAboveThreshold ? 'var(--cr)' : '#fff' }"
      >
        {{ store.currentMse.toFixed(2) }}
      </text>
      <text :x="CX" :y="CY - 18" text-anchor="middle" class="center-mse-sub">
        Reconstruction MSE
      </text>
    </svg>

    <!-- Key-Value Information Panel -->
    <div class="gauge-details">
      <div class="detail-row">
        <span>{{ store.t('gauge.baselineThreshold') }}</span>
        <b class="mono">{{ store.aeThreshold.toFixed(4) }}</b>
      </div>
      <div class="detail-row">
        <span>{{ store.t('gauge.rollingMean') }}</span>
        <b class="mono" :style="{ color: isAboveThreshold ? 'var(--cr)' : 'var(--tx)' }">
          {{ store.currentMse.toFixed(4) }}
        </b>
      </div>
      <div class="detail-row">
        <span>{{ store.t('gauge.status') }}</span>
        <span class="status-pill" :style="{ color: statusColor, background: statusBg, borderColor: statusColor }">
          {{ statusText }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSocStore } from '@/stores/socStore'

const store = useSocStore()

const CX = 120
const CY = 120
const R = 90
const MAX_MSE = 1.2

const isAboveThreshold = computed(() => store.currentMse > store.aeThreshold)

function pt(val, radius = R) {
  const clamped = Math.min(Math.max(val, 0), MAX_MSE)
  const angle = Math.PI * (1 - clamped / MAX_MSE)
  return [
    CX + radius * Math.cos(angle),
    CY - radius * Math.sin(angle)
  ]
}

function arcPath(fromVal, toVal) {
  const p1 = pt(fromVal)
  const p2 = pt(toVal)
  return `M ${p1[0]} ${p1[1]} A ${R} ${R} 0 0 1 ${p2[0]} ${p2[1]}`
}

const threshCoords = computed(() => ({
  outer: pt(store.aeThreshold, R + 11),
  inner: pt(store.aeThreshold, R - 11)
}))

const needleCoords = computed(() => pt(store.currentMse, R - 18))

const statusText = computed(() => {
  if (store.currentMse > store.aeThreshold) return store.t('gauge.statusAnomaly')
  if (store.currentMse > 0.45) return store.t('gauge.statusElevated')
  return store.t('gauge.statusNominal')
})

const statusColor = computed(() => {
  if (store.currentMse > store.aeThreshold) return 'var(--cr)'
  if (store.currentMse > 0.45) return 'var(--md)'
  return 'var(--ok)'
})

const statusBg = computed(() => {
  if (store.currentMse > store.aeThreshold) return 'rgba(255, 77, 126, 0.15)'
  if (store.currentMse > 0.45) return 'rgba(255, 181, 71, 0.15)'
  return 'rgba(61, 220, 151, 0.15)'
})
</script>

<style scoped>
.anomaly-gauge-card {
  display: flex;
  flex-direction: column;
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 8px;
}

.card-header-row h2 {
  margin: 0;
}

.threshold-pill {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 6px;
  background: rgba(178, 102, 255, 0.15);
  color: var(--zd);
  border: 1px solid rgba(178, 102, 255, 0.3);
}

.gauge-svg {
  width: 100%;
  max-width: 220px;
  margin: 0 auto;
}

.threshold-label {
  fill: #fff;
  font-size: 10px;
  font-weight: 700;
  font-family: ui-monospace, monospace;
}

.scale-label {
  fill: var(--mu);
  font-size: 10px;
  font-family: ui-monospace, monospace;
}

.center-mse-val {
  font-size: 24px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.5px;
}

.center-mse-sub {
  font-size: 9.5px;
  fill: var(--mu);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.gauge-details {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 6px;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12.5px;
  color: var(--mu);
}

.status-pill {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 6px;
  border: 1px solid;
}
</style>
