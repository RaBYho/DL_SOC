<template>
  <div class="card c3 anomaly-gauge-card">
    <!-- Header: Title & Subtitle strictly stacked on left, Threshold pill on right -->
    <div class="card-header-row">
      <div class="header-titles">
        <h2 class="card-title">{{ store.t('gauge.title') }}</h2>
        <span class="card-subtitle">{{ store.t('gauge.subtitle') }}</span>
      </div>
      <span class="threshold-pill">Seuil: {{ store.aeThreshold.toFixed(2) }}</span>
    </div>

    <!-- Gauge Visual: Inspired by jauge.webp with Fluid Spring Needle -->
    <svg 
      viewBox="0 0 240 145" 
      class="gauge-svg"
      role="img" 
      aria-label="Reconstruction error gauge"
    >
      <defs>
        <!-- Continuous Multi-Stop Gradient (Green -> Amber -> Red) -->
        <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#10b981" />
          <stop offset="50%" stop-color="#f59e0b" />
          <stop offset="100%" stop-color="#ef4444" />
        </linearGradient>

        <!-- Needle Drop Shadow -->
        <filter id="needleShadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#000" flood-opacity="0.6" />
        </filter>

        <!-- Center Hub Drop Shadow -->
        <filter id="hubShadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="1.5" stdDeviation="2" flood-color="#000" flood-opacity="0.5" />
        </filter>
      </defs>

      <!-- Background Semicircular Track with Rounded End Caps -->
      <path 
        :d="arcPath(0, MAX_MSE, R)" 
        stroke="rgba(255, 255, 255, 0.08)" 
        stroke-width="14" 
        stroke-linecap="round"
        fill="none" 
      />

      <!-- Active Gradient Scale Arc with Rounded End Caps -->
      <path 
        :d="arcPath(0, MAX_MSE, R)" 
        stroke="url(#gaugeGrad)" 
        stroke-width="12" 
        stroke-linecap="round"
        fill="none" 
        opacity="0.9"
      />

      <!-- Concentric Tachometer Inner Tick Ring -->
      <path 
        :d="arcPath(0, MAX_MSE, R_INNER)" 
        stroke="rgba(255, 255, 255, 0.22)" 
        stroke-width="2.5" 
        stroke-dasharray="1.5 5" 
        fill="none" 
      />

      <!-- Threshold Tick Marker & Label -->
      <line 
        :x1="threshCoords.outer[0]" 
        :y1="threshCoords.outer[1]" 
        :x2="threshCoords.inner[0]" 
        :y2="threshCoords.inner[1]" 
        stroke="#ffffff" 
        stroke-width="2" 
        stroke-linecap="round"
      />
      <text 
        :x="threshCoords.outer[0] + (threshCoords.outer[0] > CX ? 4 : -4)" 
        :y="threshCoords.outer[1] - 4"
        :text-anchor="threshCoords.outer[0] > CX ? 'start' : 'end'"
        class="threshold-marker-text"
      >
        {{ store.aeThreshold.toFixed(2) }}
      </text>

      <!-- Scale Extremity Labels -->
      <text :x="CX - R - 2" :y="CY + 14" text-anchor="middle" class="scale-label">0.0</text>
      <text :x="CX + R + 2" :y="CY + 14" text-anchor="middle" class="scale-label">{{ MAX_MSE.toFixed(1) }}</text>

      <!-- Hardware Needle with Physics Spring Rotation (GPU Transform) -->
      <g 
        class="gauge-needle-group" 
        :style="{ transform: `rotate(${needleAngleDeg}deg)`, transformOrigin: `${CX}px ${CY}px` }"
      >
        <polygon 
          points="120,36 116,108 120,115 124,108" 
          fill="#ffffff" 
          filter="url(#needleShadow)"
        />
      </g>

      <!-- Center Pivot Hub (Hardware Machined Bezel) -->
      <circle 
        :cx="CX" 
        :cy="CY" 
        r="8" 
        fill="#1e222d" 
        stroke="rgba(255, 255, 255, 0.45)" 
        stroke-width="2"
        filter="url(#hubShadow)"
      />
      <circle 
        :cx="CX" 
        :cy="CY" 
        r="3.5" 
        fill="#ffffff" 
      />
    </svg>

    <!-- Digital Readout & Status Pill Centered Below Gauge -->
    <div class="gauge-center-readout">
      <div 
        class="readout-val" 
        :style="{ color: isAboveThreshold ? 'var(--cr)' : '#ffffff' }"
      >
        {{ store.currentMse.toFixed(2) }}
      </div>
      <div 
        class="readout-badge" 
        :style="{ color: statusColor, background: statusBg, borderColor: statusColor }"
      >
        <span class="status-indicator-dot" :style="{ background: statusColor }"></span>
        {{ statusText }}
      </div>
    </div>

    <!-- Bottom Technical Details Strip -->
    <div class="gauge-details">
      <div class="detail-row">
        <span>{{ store.t('gauge.baselineThreshold') }}</span>
        <b class="mono">{{ store.aeThreshold.toFixed(4) }}</b>
      </div>
      <div class="detail-row">
        <span>{{ store.t('gauge.rollingMean') }}</span>
        <b class="mono" :style="{ color: isAboveThreshold ? 'var(--cr)' : '#ffffff' }">
          {{ store.currentMse.toFixed(4) }}
        </b>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSocStore } from '@/stores/socStore'

const store = useSocStore()

const CX = 120
const CY = 108
const R = 80
const R_INNER = 66
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

function arcPath(fromVal, toVal, radius = R) {
  const p1 = pt(fromVal, radius)
  const p2 = pt(toVal, radius)
  return `M ${p1[0]} ${p1[1]} A ${radius} ${radius} 0 0 1 ${p2[0]} ${p2[1]}`
}

const threshCoords = computed(() => ({
  outer: pt(store.aeThreshold, R + 9),
  inner: pt(store.aeThreshold, R - 9)
}))

// Needle rotation angle (-90deg at 0.0, 0deg at 0.6, +90deg at 1.2)
const needleAngleDeg = computed(() => {
  const clamped = Math.min(Math.max(store.currentMse, 0), MAX_MSE)
  return -90 + (clamped / MAX_MSE) * 180
})

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
  height: 330px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 16px 18px;
  transition: transform 0.24s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.24s ease, box-shadow 0.24s ease;
}

.anomaly-gauge-card:hover {
  border-color: rgba(255, 255, 255, 0.14);
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 4px;
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

.threshold-pill {
  font-size: 10.5px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 6px;
  background: rgba(178, 102, 255, 0.15);
  color: var(--zd);
  border: 1px solid rgba(178, 102, 255, 0.3);
  white-space: nowrap;
  flex: none;
}

.gauge-svg {
  width: 100%;
  max-width: 215px;
  margin: 0 auto;
  flex: none;
  height: 130px;
  display: block;
}

/* Physics-based needle rotation: spring damping with zero jank */
.gauge-needle-group {
  transition: transform 0.65s cubic-bezier(0.34, 1.28, 0.64, 1);
  will-change: transform;
}

.threshold-marker-text {
  fill: #fff;
  font-size: 9.5px;
  font-weight: 700;
  font-family: ui-monospace, monospace;
}

.scale-label {
  fill: var(--mu);
  font-size: 9.5px;
  font-family: ui-monospace, monospace;
}

/* Digital Readout & Status Pill Centered Below Needle */
.gauge-center-readout {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: -6px;
  flex: none;
}

.readout-val {
  font-size: 24px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.5px;
  line-height: 1;
  transition: color 0.3s ease;
}

.readout-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 10.5px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 12px;
  border: 1px solid;
  letter-spacing: 0.2px;
  line-height: 1.2;
  transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
}

.status-indicator-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  transition: background-color 0.3s ease;
}

/* Technical Details Strip */
.gauge-details {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-top: 4px;
  padding-top: 6px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  flex: none;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: var(--mu);
}

@media (max-width: 768px) {
  .anomaly-gauge-card {
    height: auto;
    min-height: auto;
    padding: 14px 16px;
  }

  .gauge-center-readout {
    margin-top: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .gauge-needle-group {
    transition: none;
  }
}
</style>
