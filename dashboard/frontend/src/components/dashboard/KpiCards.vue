<template>
  <section class="kpis-container" aria-label="Key performance indicators">
    <!-- Card 1: Total Flows -->
    <div class="kpi-card">
      <template v-if="store.isLoading">
        <div class="kpi-top">
          <div class="skeleton-shimmer skeleton-box" style="width: 85px; height: 12px;"></div>
          <div class="skeleton-shimmer skeleton-box" style="width: 32px; height: 32px; border-radius: 8px;"></div>
        </div>
        <div class="kpi-bottom">
          <div class="skeleton-shimmer skeleton-box" style="width: 110px; height: 26px; border-radius: 6px;"></div>
        </div>
      </template>
      <template v-else>
        <div class="kpi-top">
          <span class="kpi-label">{{ store.t('kpi.totalFlows') }}</span>
          <div class="kpi-icon-pill icon-flows" aria-hidden="true">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <ellipse cx="10" cy="5" rx="7" ry="2.5" />
              <path d="M3 5v5c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5V5" />
              <path d="M3 10v5c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5v-5" />
            </svg>
          </div>
        </div>
        <div class="kpi-bottom">
          <div class="kpi-value">{{ formatNumber(store.kpis.total_flows) }}</div>
        </div>
      </template>
    </div>

    <!-- Card 2: Confirmed Cyber Attacks -->
    <div class="kpi-card kpi-attacks">
      <template v-if="store.isLoading">
        <div class="kpi-top">
          <div class="skeleton-shimmer skeleton-box" style="width: 85px; height: 12px;"></div>
          <div class="skeleton-shimmer skeleton-box" style="width: 32px; height: 32px; border-radius: 8px;"></div>
        </div>
        <div class="kpi-bottom">
          <div class="skeleton-shimmer skeleton-box" style="width: 110px; height: 26px; border-radius: 6px;"></div>
        </div>
      </template>
      <template v-else>
        <div class="kpi-top">
          <span class="kpi-label">{{ store.t('kpi.confirmedAttacks') }}</span>
          <div class="kpi-icon-pill icon-attacks" aria-hidden="true">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10 2L3 6v6c0 4.5 3.5 7.5 7 8 3.5-.5 7-3.5 7-8V6l-7-4z" />
              <path d="M10 7v4" />
              <circle cx="10" cy="13.5" r="0.75" fill="currentColor" />
            </svg>
          </div>
        </div>
        <div class="kpi-bottom">
          <div class="kpi-value text-attacks">{{ formatNumber(store.kpis.attacks) }}</div>
        </div>
      </template>
    </div>

    <!-- Card 3: Zero-Day / Unknown Anomalies -->
    <div class="kpi-card kpi-anomalies">
      <template v-if="store.isLoading">
        <div class="kpi-top">
          <div class="skeleton-shimmer skeleton-box" style="width: 85px; height: 12px;"></div>
          <div class="skeleton-shimmer skeleton-box" style="width: 32px; height: 32px; border-radius: 8px;"></div>
        </div>
        <div class="kpi-bottom">
          <div class="skeleton-shimmer skeleton-box" style="width: 110px; height: 26px; border-radius: 6px;"></div>
        </div>
      </template>
      <template v-else>
        <div class="kpi-top">
          <span class="kpi-label">{{ store.t('kpi.anomalies') }}</span>
          <div class="kpi-icon-pill icon-anomalies" aria-hidden="true">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="10" cy="10" r="7" />
              <path d="M10 7v3l2 2" />
              <path d="M4 10a6 6 0 0 1 1.8-4.2" stroke-dasharray="2 2" />
            </svg>
          </div>
        </div>
        <div class="kpi-bottom">
          <div class="kpi-value text-anomalies">{{ formatNumber(store.kpis.anomalies) }}</div>
        </div>
      </template>
    </div>

    <!-- Card 4: Ingestion Rate -->
    <div class="kpi-card kpi-rate-card">
      <template v-if="store.isLoading">
        <div class="kpi-top">
          <div class="skeleton-shimmer skeleton-box" style="width: 85px; height: 12px;"></div>
          <div class="skeleton-shimmer skeleton-box" style="width: 32px; height: 32px; border-radius: 8px;"></div>
        </div>
        <div class="kpi-bottom">
          <div class="rate-value-row">
            <div class="skeleton-shimmer skeleton-box" style="width: 90px; height: 26px; border-radius: 6px;"></div>
            <div class="skeleton-shimmer skeleton-box" style="width: 55px; height: 20px; border-radius: 12px;"></div>
          </div>
          <div class="skeleton-shimmer skeleton-box" style="width: 100%; height: 12px; margin-top: 8px; border-radius: 4px;"></div>
        </div>
      </template>
      <template v-else>
        <div class="kpi-top">
          <span class="kpi-label">{{ store.t('kpi.rate') }}</span>
          <div class="kpi-icon-pill icon-rate" aria-hidden="true">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <polygon points="11 2 4 11 10 11 9 18 16 9 10 9 11 2" />
            </svg>
          </div>
        </div>
        <div class="kpi-bottom">
          <div class="rate-value-row">
            <div class="kpi-value">
              <span>{{ formatNumber(store.kpis.flow_rate_sec) }}</span>
              <small class="kpi-unit">{{ store.t('kpi.flowsSec') }}</small>
            </div>
            <span class="kpi-bandwidth-pill">{{ store.kpis.bandwidth_mbps }} Mbps</span>
          </div>
          <div class="spark-bars" aria-hidden="true">
            <i v-for="(h, idx) in sparkHeights" :key="idx" :style="{ height: `${h}%` }"></i>
          </div>
        </div>
      </template>
    </div>

    <!-- Card 5: Benign vs Malicious Traffic Distribution -->
    <div class="kpi-card kpi-ratio-card">
      <template v-if="store.isLoading">
        <div class="kpi-top">
          <div class="skeleton-shimmer skeleton-box" style="width: 90px; height: 12px;"></div>
          <div class="skeleton-shimmer skeleton-box" style="width: 32px; height: 32px; border-radius: 8px;"></div>
        </div>
        <div class="kpi-bottom">
          <div class="skeleton-shimmer skeleton-box" style="width: 120px; height: 26px; border-radius: 6px;"></div>
          <div class="skeleton-shimmer skeleton-box" style="width: 100%; height: 6px; margin-top: 8px; border-radius: 3px;"></div>
        </div>
      </template>
      <template v-else>
        <div class="kpi-top">
          <span class="kpi-label">{{ store.t('kpi.trafficDist') }}</span>
          <div class="kpi-icon-pill icon-ratio" aria-hidden="true">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="10" cy="10" r="8" />
              <path d="M10 2v16" />
              <path d="M10 2a8 8 0 0 1 0 16z" fill="currentColor" fill-opacity="0.2" />
            </svg>
          </div>
        </div>

        <div class="kpi-bottom">
          <div class="ratio-values-row">
            <div class="kpi-value ratio-text">
              <span class="benign-num" title="Normal">{{ benignPct }}%</span>
              <span class="ratio-slash">/</span>
              <span class="malicious-num" title="Anormal">{{ attackPct }}%</span>
            </div>
          </div>

          <!-- Segmented Dual Progress Bar -->
          <div class="ratio-bar-wrapper">
            <div class="ratio-bar-track" role="progressbar" :aria-valuenow="benignPct" aria-valuemin="0" aria-valuemax="100">
              <div 
                class="bar-seg benign-seg" 
                :style="{ width: `${benignPct}%` }"
              ></div>
              <div 
                class="bar-seg malicious-seg" 
                :style="{ width: `${attackPct}%` }"
              ></div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useSocStore } from '@/stores/socStore'

const store = useSocStore()

const benignPct = computed(() => {
  return Number(store.kpis.benign_pct || 96.0).toFixed(1)
})

const attackPct = computed(() => {
  return Number(store.kpis.attack_pct || 4.0).toFixed(1)
})

const sparkHeights = computed(() => {
  const seed = store.kpis.flow_rate_sec || 1000
  return [
    40 + (seed % 30),
    45 + ((seed * 2) % 35),
    35 + ((seed * 3) % 40),
    55 + ((seed * 4) % 30),
    50 + ((seed * 5) % 35),
    65 + ((seed * 6) % 30),
    60 + ((seed * 7) % 35),
    80 + ((seed * 8) % 20),
    75 + ((seed * 9) % 22),
    90 + ((seed * 10) % 10)
  ]
})

function formatNumber(num) {
  if (num === null || num === undefined) return '0'
  return Math.round(num).toLocaleString('en-US')
}
</script>

<style scoped>
.kpis-container {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
  margin-bottom: 8px;
}

/* Base Card Styling */
.kpi-card {
  background: linear-gradient(180deg, rgba(30, 31, 46, 0.96) 0%, rgba(22, 23, 34, 0.96) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 104px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08), 0 8px 24px rgba(0, 0, 0, 0.24);
  transition: transform 0.24s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.24s ease, box-shadow 0.24s ease;
  box-sizing: border-box;
}

.kpi-card:hover {
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.16);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12), 0 12px 30px rgba(0, 0, 0, 0.35);
}

.kpi-attacks {
  background: linear-gradient(180deg, rgba(255, 77, 126, 0.08) 0%, rgba(22, 23, 34, 0.96) 100%);
  border-color: rgba(255, 77, 126, 0.25);
  box-shadow: inset 0 1px 0 rgba(255, 77, 126, 0.2), 0 6px 20px rgba(255, 77, 126, 0.1);
}

.kpi-anomalies {
  background: linear-gradient(180deg, rgba(178, 102, 255, 0.08) 0%, rgba(22, 23, 34, 0.96) 100%);
  border-color: rgba(178, 102, 255, 0.25);
  box-shadow: inset 0 1px 0 rgba(178, 102, 255, 0.2), 0 6px 20px rgba(178, 102, 255, 0.1);
}

.kpi-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.kpi-label {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--mu);
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

.kpi-icon-pill {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: none;
  border: 1px solid transparent;
}

.kpi-icon-pill svg {
  width: 15px;
  height: 15px;
}

.icon-flows {
  background: rgba(88, 101, 242, 0.12);
  color: var(--ac);
  border-color: rgba(88, 101, 242, 0.25);
}

.icon-attacks {
  background: rgba(255, 77, 126, 0.12);
  color: var(--cr);
  border-color: rgba(255, 77, 126, 0.25);
}

.icon-anomalies {
  background: rgba(178, 102, 255, 0.12);
  color: var(--zd);
  border-color: rgba(178, 102, 255, 0.25);
}

.icon-rate {
  background: rgba(46, 204, 113, 0.12);
  color: var(--ok);
  border-color: rgba(46, 204, 113, 0.25);
}

.icon-ratio {
  background: rgba(255, 181, 71, 0.12);
  color: var(--md);
  border-color: rgba(255, 181, 71, 0.25);
}

.kpi-bottom {
  display: flex;
  flex-direction: column;
}

.kpi-value {
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.5px;
  line-height: 1.1;
  color: #fff;
  font-variant-numeric: tabular-nums;
}

.text-attacks {
  color: var(--cr);
}

.text-anomalies {
  color: var(--zd);
}

/* Rate Card Specifics */
.rate-value-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
}

.kpi-unit {
  font-size: 11px;
  font-weight: 500;
  color: var(--mu);
  margin-left: 4px;
}

.kpi-bandwidth-pill {
  font-size: 10px;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.06);
  color: var(--tx);
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.spark-bars {
  display: flex;
  align-items: flex-end;
  gap: 2.5px;
  height: 14px;
  margin-top: 6px;
}

.spark-bars i {
  flex: 1;
  background: linear-gradient(180deg, var(--ac2), var(--ac));
  border-radius: 2px;
  opacity: 0.5;
  transition: height 0.45s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.25s ease;
  will-change: height;
}

.spark-bars i:last-child {
  opacity: 1;
  background: var(--ok);
}

/* Ratio Card Spec */
.ratio-values-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  min-height: 28px;
}

.ratio-text {
  font-size: 22px;
  font-weight: 800;
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  white-space: nowrap !important;
  letter-spacing: -0.4px;
  line-height: 1.1;
}

.benign-num {
  color: var(--ok);
  font-variant-numeric: tabular-nums;
  cursor: default;
  transition: opacity 0.15s ease;
}

.benign-num:hover {
  opacity: 0.85;
}

.ratio-slash {
  color: var(--mu);
  font-size: 15px;
  font-weight: 400;
  margin: 0 1px;
  opacity: 0.5;
}

.malicious-num {
  color: var(--cr);
  font-variant-numeric: tabular-nums;
  cursor: default;
  transition: opacity 0.15s ease;
}

.malicious-num:hover {
  opacity: 0.85;
}

/* Dual Segment Progress Bar */
.ratio-bar-wrapper {
  margin-top: 6px;
}

.ratio-bar-track {
  height: 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.06);
  display: flex;
  overflow: hidden;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.3);
}

.bar-seg {
  height: 100%;
  transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
  will-change: width;
  cursor: default;
}

.bar-seg.benign-seg {
  background: var(--ok);
  box-shadow: 0 0 6px rgba(61, 220, 151, 0.25);
}

.bar-seg.malicious-seg {
  background: var(--cr);
  box-shadow: 0 0 6px rgba(255, 77, 126, 0.3);
}

/* Tablet Layout */
@media (max-width: 1200px) and (min-width: 769px) {
  .kpis-container {
    grid-template-columns: repeat(3, 1fr);
  }
  .kpi-ratio-card {
    grid-column: span 2;
  }
}

/* Mobile Layout */
@media (max-width: 768px) {
  .kpis-container {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    margin-bottom: 4px;
  }

  .kpi-card {
    padding: 12px 14px;
    min-height: 88px;
    border-radius: 12px;
  }

  .kpi-label {
    font-size: 10.5px;
  }

  .kpi-icon-pill {
    width: 24px;
    height: 24px;
    border-radius: 6px;
  }

  .kpi-icon-pill svg {
    width: 13px;
    height: 13px;
  }

  .kpi-value {
    font-size: 19px;
  }

  .kpi-ratio-card {
    grid-column: 1 / -1;
    min-height: 82px;
  }

  .ratio-text {
    font-size: 18px;
  }
}
</style>
