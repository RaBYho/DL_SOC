<template>
  <section class="kpis-container" aria-label="Key performance indicators">
    <!-- Card 1: Total Flows -->
    <div class="kpi-card">
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
    </div>

    <!-- Card 2: Confirmed Cyber Attacks -->
    <div class="kpi-card kpi-attacks">
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
    </div>

    <!-- Card 3: Zero-Day / Unknown Anomalies -->
    <div class="kpi-card kpi-anomalies">
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
    </div>

    <!-- Card 4: Ingestion Rate -->
    <div class="kpi-card kpi-rate-card">
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
    </div>

    <!-- Card 5: Benign vs Malicious Traffic Distribution -->
    <div class="kpi-card kpi-ratio-card">
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
          <div class="ratio-bar-track" aria-hidden="true">
            <div
              class="bar-seg benign-seg"
              :style="{ width: `${benignBarWidth}%` }"
              title="Normal"
            ></div>
            <div
              class="bar-seg malicious-seg"
              :style="{ width: `${maliciousBarWidth}%` }"
              title="Anormal"
            ></div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useSocStore } from '@/stores/socStore'

const store = useSocStore()

function formatNumber(num) {
  if (num === null || num === undefined) return '0'
  return Math.round(num).toLocaleString('en-US')
}

const attackPct = computed(() => {
  const p = store.kpis.attack_pct !== undefined && store.kpis.attack_pct !== null ? store.kpis.attack_pct : 4.0
  return Number(p).toFixed(1)
})

const benignPct = computed(() => {
  const att = Number(attackPct.value)
  return Math.max(0, 100 - att).toFixed(1)
})

const maliciousBarWidth = computed(() => {
  const p = Number(attackPct.value)
  if (p <= 0) return 0
  if (p >= 100) return 100
  return Math.min(Math.max(p, 4), 96)
})

const benignBarWidth = computed(() => {
  return 100 - maliciousBarWidth.value
})

const sparkHeights = computed(() => {
  const rate = store.kpis.flow_rate_sec || 1000
  const normalized = Math.min(Math.max((rate / 2400) * 100, 25), 100)
  return [
    Math.round(normalized * 0.45),
    Math.round(normalized * 0.70),
    Math.round(normalized * 0.55),
    Math.round(normalized * 0.85),
    Math.round(normalized * 0.65),
    Math.round(normalized * 0.90),
    Math.round(normalized * 0.75),
    Math.round(normalized * 0.95),
    Math.round(normalized * 0.80),
    Math.round(normalized * 0.92),
    Math.round(normalized * 0.88),
    100
  ]
})
</script>

<style scoped>
/* Base Desktop Container (5 equal columns) */
.kpis-container {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
  width: 100%;
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
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.2s ease, box-shadow 0.2s ease;
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
  gap: 8px;
  margin-bottom: 6px;
}

.kpi-label {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--mu);
  letter-spacing: 0.2px;
  line-height: 1.25;
}

.kpi-icon-pill {
  width: 28px;
  height: 28px;
  border-radius: 7px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: none;
}

.kpi-icon-pill svg {
  width: 15px;
  height: 15px;
}

.icon-flows {
  background: rgba(88, 101, 242, 0.16);
  color: var(--lo);
  border: 1px solid rgba(88, 101, 242, 0.28);
}

.icon-attacks {
  background: rgba(255, 77, 126, 0.16);
  color: var(--cr);
  border: 1px solid rgba(255, 77, 126, 0.32);
}

.icon-anomalies {
  background: rgba(178, 102, 255, 0.16);
  color: var(--zd);
  border: 1px solid rgba(178, 102, 255, 0.32);
}

.icon-rate {
  background: rgba(61, 220, 151, 0.16);
  color: var(--ok);
  border: 1px solid rgba(61, 220, 151, 0.28);
}

.icon-ratio {
  background: rgba(255, 181, 71, 0.16);
  color: var(--md);
  border: 1px solid rgba(255, 181, 71, 0.28);
}

.kpi-bottom {
  display: flex;
  flex-direction: column;
}

.kpi-value {
  font-size: 26px;
  font-weight: 800;
  letter-spacing: -0.5px;
  font-variant-numeric: tabular-nums;
  line-height: 1.1;
  color: #fff;
}

.kpi-unit {
  font-size: 12px;
  font-weight: 500;
  color: var(--mu);
  margin-left: 4px;
}

.text-attacks {
  color: var(--cr);
  text-shadow: 0 0 14px rgba(255, 77, 126, 0.32);
}

.text-anomalies {
  color: var(--zd);
  text-shadow: 0 0 14px rgba(178, 102, 255, 0.32);
}

.rate-value-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 6px;
}

.kpi-bandwidth-pill {
  font-size: 10.5px;
  font-weight: 700;
  color: var(--mu);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  padding: 1px 6px;
  font-variant-numeric: tabular-nums;
}

.spark-bars {
  display: flex;
  align-items: flex-end;
  gap: 2px;
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

/* Ratio Card (Card 5) Spec */
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

/* Tablet Layout (2x2 + 1 span or 3 columns) */
@media (max-width: 1200px) and (min-width: 769px) {
  .kpis-container {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
  }
  .kpi-ratio-card {
    grid-column: span 2;
  }
}

/* Mobile Layout (< 768px down to 320px) */
/* Elegant 2x2 Grid + Full Width Ratio Banner (No 1-column stacking) */
@media (max-width: 768px) {
  .kpis-container {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
    gap: 8px;
  }

  .kpi-ratio-card {
    grid-column: span 2 !important;
    min-height: auto;
    padding: 10px 14px;
  }

  .kpi-card {
    min-height: 86px;
    padding: 10px 12px;
    border-radius: 12px;
  }

  .kpi-top {
    margin-bottom: 4px;
    gap: 4px;
  }

  .kpi-label {
    font-size: 11px;
    line-height: 1.2;
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
    font-size: 21px;
  }

  .kpi-unit {
    font-size: 11px;
  }

  .rate-value-row {
    flex-wrap: wrap;
    align-items: center;
  }

  .kpi-bandwidth-pill {
    font-size: 9.5px;
    padding: 0 4px;
  }

  .spark-bars {
    height: 10px;
    margin-top: 4px;
  }

  .ratio-text {
    font-size: 18px !important;
  }
}

/* Extra small devices (iPhone SE, 320-375px) */
@media (max-width: 375px) {
  .kpis-container {
    gap: 6px;
  }

  .kpi-card {
    padding: 8px 10px;
    min-height: 82px;
  }

  .kpi-value {
    font-size: 19px;
  }

  .kpi-label {
    font-size: 10px;
  }

  .kpi-icon-pill {
    display: none; /* Hide icon on ultra-narrow 320px to give full width to label */
  }

  .ratio-text {
    font-size: 16px !important;
  }
}
</style>
