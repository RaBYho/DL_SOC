<template>
  <div class="card c4 attack-donut-card">
    <!-- Header: Title and Subtitle strictly stacked -->
    <div class="card-header-row">
      <div class="header-titles">
        <h2 class="card-title">{{ store.t('donut.title') }}</h2>
        <span class="card-subtitle">{{ store.t('donut.subtitle') }}</span>
      </div>
    </div>

    <!-- Skeleton Loading State -->
    <div v-if="store.isLoading" class="donut-content-row">
      <div class="donut-wrapper">
        <div class="skeleton-donut-placeholder skeleton-shimmer">
          <div class="skeleton-donut-hole">
            <div class="skeleton-shimmer skeleton-box" style="width: 45px; height: 9px; margin-bottom: 6px;"></div>
            <div class="skeleton-shimmer skeleton-box" style="width: 60px; height: 18px; border-radius: 4px;"></div>
          </div>
        </div>
      </div>
      <div class="legend-list">
        <div v-for="i in 5" :key="i" class="legend-item">
          <div class="skeleton-shimmer skeleton-box" style="width: 7px; height: 7px; border-radius: 50%; flex: none;"></div>
          <div class="legend-text-col" style="gap: 4px;">
            <div class="skeleton-shimmer skeleton-box" :style="{ width: `${60 + (i * 10)}px`, height: '11px' }"></div>
            <div class="skeleton-shimmer skeleton-box" style="width: 45px; height: 9px;"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loaded Content: Large Donut on Left, Clean Legend List on Right -->
    <div v-else class="donut-content-row">
      <!-- Left: Large Donut Ring with Multi-Level Center Metrics -->
      <div class="donut-wrapper">
        <svg viewBox="0 0 160 160" class="donut-svg" role="img" aria-label="Attack family distribution">
          <defs>
            <filter id="donutGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000" flood-opacity="0.4" />
            </filter>
          </defs>

          <!-- Background Track Arc -->
          <circle 
            cx="80" 
            cy="80" 
            r="56" 
            fill="none" 
            stroke="rgba(255, 255, 255, 0.06)" 
            stroke-width="14" 
          />

          <!-- Colored Segments with Smooth Fluid Interpolation -->
          <circle 
            v-for="(seg, idx) in donutSegments"
            :key="idx"
            class="donut-segment"
            cx="80" 
            cy="80" 
            r="56" 
            fill="none" 
            stroke-width="14" 
            :style="{ 
              stroke: seg.color,
              strokeDasharray: `${Math.max(seg.arcLength - 2.5, 0)} ${CIRCUMFERENCE}`,
              strokeDashoffset: -seg.offset
            }" 
            transform="rotate(-90 80 80)"
            filter="url(#donutGlow)"
          />

          <!-- Donut Center Content -->
          <text x="80" y="58" text-anchor="middle" class="donut-center-label">
            {{ store.t('donut.attacks').toUpperCase() }}
          </text>

          <text x="80" y="80" text-anchor="middle" class="donut-center-val">
            {{ formatNumber(totalAttacks) }}
          </text>

          <!-- Micro Pill Trend Badge -->
          <g transform="translate(56, 89)">
            <rect 
              x="0" 
              y="0" 
              width="48" 
              height="16" 
              rx="8" 
              :fill="totalAttacks > 0 ? 'rgba(255, 77, 126, 0.16)' : 'rgba(61, 220, 151, 0.16)'" 
              :stroke="totalAttacks > 0 ? 'rgba(255, 77, 126, 0.35)' : 'rgba(61, 220, 151, 0.35)'" 
              stroke-width="0.8"
            />
            <text x="24" y="11.5" text-anchor="middle" class="donut-center-trend">
              {{ totalAttacks > 0 ? `↑ ${attackPct}%` : '0.0%' }}
            </text>
          </g>
        </svg>
      </div>

      <!-- Right: Legend List -->
      <div class="legend-list">
        <div v-if="sortedDist.length === 0" class="empty-legend">
          <span class="empty-ok-badge">✓</span>
          <span class="empty-legend-text">{{ store.lang === 'FR' ? 'Aucune menace active' : 'No active threats' }}</span>
        </div>
        <div 
          v-else
          v-for="item in sortedDist" 
          :key="item.name" 
          class="legend-item"
        >
          <span 
            class="legend-dot" 
            :style="{ background: item.color, boxShadow: `0 0 8px ${item.color}66` }"
          ></span>
          <div class="legend-text-col">
            <span class="legend-name" :title="item.name">{{ item.name }}</span>
            <span class="legend-count">{{ formatNumber(item.count) }} flux</span>
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
const CIRCUMFERENCE = 2 * Math.PI * 56 // ~351.86

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
  const list = store.attackDistribution || []
  const tot = list.reduce((acc, curr) => acc + (curr.count || 0), 0) || 1

  return list
    .filter(i => (i.count || 0) > 0)
    .sort((a, b) => (b.count || 0) - (a.count || 0))
    .slice(0, 6)
    .map(i => {
      const name = i.label || i.name || 'Threat'
      const count = i.count || 0
      return {
        name,
        count,
        pct: (count / tot) * 100,
        color: i.color || COLOR_MAP[name] || 'var(--ac)'
      }
    })
})

const totalAttacks = computed(() => {
  return sortedDist.value.reduce((acc, curr) => acc + curr.count, 0)
})

const attackPct = computed(() => {
  if (store.kpis && store.kpis.attack_pct !== undefined) {
    return Number(store.kpis.attack_pct).toFixed(1)
  }
  return '0.0'
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
  height: 330px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  padding: 16px 18px;
  transition: transform 0.24s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.24s ease, box-shadow 0.24s ease;
}

.attack-donut-card:hover {
  border-color: rgba(255, 255, 255, 0.14);
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
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

/* Side-by-side content row */
.donut-content-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
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
  width: 215px;
  height: 215px;
  display: block;
}

/* Skeleton Donut Shimmer Placeholder */
.skeleton-donut-placeholder {
  width: 175px;
  height: 175px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.skeleton-donut-hole {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: #171825;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

/* Fluid segment resizing */
.donut-segment {
  transition: stroke-dasharray 0.65s cubic-bezier(0.16, 1, 0.3, 1),
              stroke-dashoffset 0.65s cubic-bezier(0.16, 1, 0.3, 1),
              opacity 0.25s ease;
  will-change: stroke-dasharray, stroke-dashoffset;
}

.donut-center-label {
  font-size: 9px;
  fill: var(--mu);
  font-weight: 700;
  letter-spacing: 0.8px;
}

.donut-center-val {
  font-size: 23px;
  font-weight: 800;
  fill: #ffffff;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.5px;
}

.donut-center-trend {
  font-size: 9.5px;
  font-weight: 700;
  fill: #ff4d7e;
  letter-spacing: 0.2px;
}

/* Right: Clean Attack Families List */
.legend-list {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
  padding-left: 2px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 3px 6px;
  border-radius: 6px;
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), 
              background-color 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  will-change: transform;
}

.legend-item:hover {
  background: rgba(255, 255, 255, 0.06);
  transform: translateX(3px);
}

.legend-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex: none;
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.legend-item:hover .legend-dot {
  transform: scale(1.25);
}

.legend-text-col {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.legend-name {
  color: #fff;
  font-size: 11.5px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: 0.1px;
  line-height: 1.2;
}

.legend-count {
  color: var(--mu);
  font-size: 10px;
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}

.empty-legend {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: rgba(61, 220, 151, 0.08);
  border: 1px solid rgba(61, 220, 151, 0.25);
  border-radius: 8px;
}

.empty-ok-badge {
  color: var(--ok);
  font-weight: 800;
  font-size: 12px;
}

.empty-legend-text {
  font-size: 11px;
  color: var(--ok);
  font-weight: 600;
}

/* Tablet (769px to 1200px) */
@media (max-width: 1200px) and (min-width: 769px) {
  .attack-donut-card {
    height: 330px;
  }
  .donut-svg,
  .skeleton-donut-placeholder {
    width: 220px;
    height: 220px;
  }
  .donut-content-row {
    gap: 36px;
    justify-content: flex-start;
  }
  .legend-list {
    max-width: 320px;
  }
}

/* Mobile (< 768px) */
@media (max-width: 768px) {
  .attack-donut-card {
    height: auto;
    min-height: auto;
    padding: 14px 16px;
  }

  .donut-content-row {
    gap: 12px;
  }

  .donut-svg,
  .skeleton-donut-placeholder {
    width: 160px;
    height: 160px;
  }

  .donut-center-val {
    font-size: 18px;
  }

  .card-title {
    font-size: 13.5px;
  }

  .card-subtitle {
    font-size: 10.5px;
  }

  .legend-item {
    padding: 2px 4px;
    gap: 7px;
  }

  .legend-name {
    font-size: 11px;
  }

  .legend-count {
    font-size: 9.5px;
  }
}

/* Small mobile (<= 375px) */
@media (max-width: 375px) {
  .donut-svg,
  .skeleton-donut-placeholder {
    width: 130px;
    height: 130px;
  }

  .donut-content-row {
    gap: 8px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .donut-segment,
  .legend-item,
  .legend-dot {
    transition: none !important;
  }
}
</style>
