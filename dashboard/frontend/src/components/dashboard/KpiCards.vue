<template>
  <section class="kpis-container" aria-label="Key performance indicators">
    <!-- Card 1: Total Flows -->
    <div class="kpi-card">
      <div class="kpi-top">
        <span class="kpi-label">{{ store.t('kpi.totalFlows') }}</span>
        <div class="kpi-icon-pill icon-flows">
          <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <ellipse cx="10" cy="5" rx="7" ry="2.5" />
            <path d="M3 5v5c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5V5" />
            <path d="M3 10v5c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5v-5" />
          </svg>
        </div>
      </div>
      <div class="kpi-value">{{ formatNumber(store.kpis.total_flows) }}</div>
    </div>

    <!-- Card 2: Confirmed Cyber Attacks -->
    <div class="kpi-card kpi-attacks">
      <div class="kpi-top">
        <span class="kpi-label">{{ store.t('kpi.confirmedAttacks') }}</span>
        <div class="kpi-icon-pill icon-attacks">
          <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10 2L3 6v6c0 4.5 3.5 7.5 7 8 3.5-.5 7-3.5 7-8V6l-7-4z" />
            <path d="M10 7v4" />
            <circle cx="10" cy="13.5" r="0.75" fill="currentColor" />
          </svg>
        </div>
      </div>
      <div class="kpi-value text-attacks">{{ formatNumber(store.kpis.attacks) }}</div>
    </div>

    <!-- Card 3: Zero-Day / Unknown Anomalies -->
    <div class="kpi-card kpi-anomalies">
      <div class="kpi-top">
        <span class="kpi-label">{{ store.t('kpi.anomalies') }}</span>
        <div class="kpi-icon-pill icon-anomalies">
          <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="10" cy="10" r="7" />
            <path d="M10 7v3l2 2" />
            <path d="M4 10a6 6 0 0 1 1.8-4.2" stroke-dasharray="2 2" />
          </svg>
        </div>
      </div>
      <div class="kpi-value text-anomalies">{{ formatNumber(store.kpis.anomalies) }}</div>
    </div>

    <!-- Card 4: Ingestion Rate -->
    <div class="kpi-card">
      <div class="kpi-top">
        <span class="kpi-label">{{ store.t('kpi.rate') }}</span>
        <div class="kpi-icon-pill icon-rate">
          <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="11 2 4 11 10 11 9 18 16 9 10 9 11 2" />
          </svg>
        </div>
      </div>
      <div class="kpi-value">
        <span>{{ formatNumber(store.kpis.flow_rate_sec) }}</span>
        <small class="kpi-unit">{{ store.t('kpi.flowsSec') }}</small>
      </div>
      <div class="kpi-spark-group">
        <div class="kpi-bandwidth-text">{{ store.kpis.bandwidth_mbps }} Mbps</div>
        <div class="spark-bars" aria-hidden="true">
          <i v-for="(h, idx) in sparkHeights" :key="idx" :style="{ height: `${h}%` }"></i>
        </div>
      </div>
    </div>

    <!-- Card 5: Benign vs Malicious (Spans 2 columns on mobile) -->
    <div class="kpi-card kpi-card-full-mobile">
      <div class="kpi-top">
        <span class="kpi-label">{{ store.t('kpi.trafficDist') }}</span>
        <div class="kpi-icon-pill icon-ratio">
          <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="10" cy="10" r="8" />
            <path d="M10 2v16" />
            <path d="M10 2a8 8 0 0 1 0 16z" fill="currentColor" fill-opacity="0.2" />
          </svg>
        </div>
      </div>
      <div class="kpi-value ratio-text">
        <span style="color:var(--ok);">{{ (store.kpis.benign_pct || 96).toFixed(1) }}%</span>
        <span style="color:var(--mu); font-size: 18px; font-weight:400; margin: 0 4px;">/</span>
        <span style="color:var(--cr);">{{ (store.kpis.attack_pct || 4).toFixed(1) }}%</span>
      </div>
      <div class="ratio-bar-wrapper">
        <div class="ratio-bar-bg" aria-hidden="true">
          <i class="ratio-bar-fill" :style="{ width: `${Math.min(Math.max(store.kpis.attack_pct || 4, 3), 100)}%` }"></i>
        </div>
        <div class="ratio-labels">
          <span>{{ store.t('kpi.benign') }}</span>
          <span style="color:var(--cr);">{{ store.t('kpi.malicious') }}</span>
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
.kpis-container {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
}

@media (max-width: 1350px) {
  .kpis-container {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .kpis-container {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }
  .kpi-card-full-mobile {
    grid-column: span 2;
  }
  .kpi-card {
    padding: 12px 14px !important;
  }
  .kpi-value {
    font-size: 22px !important;
  }
}

@media (max-width: 480px) {
  .kpis-container {
    grid-template-columns: 1fr;
  }
  .kpi-card-full-mobile {
    grid-column: span 1;
  }
}

.kpi-card {
  background: linear-gradient(180deg, rgba(34, 35, 51, 0.95) 0%, rgba(27, 28, 40, 0.95) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08), 0 8px 24px rgba(0, 0, 0, 0.22);
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.2s ease, box-shadow 0.2s ease;
  position: relative;
  overflow: hidden;
}

.kpi-card:hover {
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.16);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12), 0 12px 30px rgba(0, 0, 0, 0.35);
}

.kpi-attacks {
  background: linear-gradient(180deg, rgba(255, 77, 126, 0.08) 0%, rgba(27, 28, 40, 0.95) 100%);
  border-color: rgba(255, 77, 126, 0.28);
}

.kpi-anomalies {
  background: linear-gradient(180deg, rgba(178, 102, 255, 0.08) 0%, rgba(27, 28, 40, 0.95) 100%);
  border-color: rgba(178, 102, 255, 0.28);
}

.kpi-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.kpi-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--mu);
}

.kpi-icon-pill {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: none;
}

.kpi-icon-pill svg {
  width: 16px;
  height: 16px;
}

.icon-flows {
  background: rgba(88, 101, 242, 0.15);
  color: var(--lo);
  border: 1px solid rgba(88, 101, 242, 0.25);
}

.icon-attacks {
  background: rgba(255, 77, 126, 0.15);
  color: var(--cr);
  border: 1px solid rgba(255, 77, 126, 0.3);
}

.icon-anomalies {
  background: rgba(178, 102, 255, 0.15);
  color: var(--zd);
  border: 1px solid rgba(178, 102, 255, 0.3);
}

.icon-rate {
  background: rgba(61, 220, 151, 0.15);
  color: var(--ok);
  border: 1px solid rgba(61, 220, 151, 0.25);
}

.icon-ratio {
  background: rgba(255, 181, 71, 0.15);
  color: var(--md);
  border: 1px solid rgba(255, 181, 71, 0.25);
}

.kpi-value {
  font-size: 28px;
  font-weight: 800;
  letter-spacing: -0.5px;
  font-variant-numeric: tabular-nums;
  margin: 2px 0 6px;
  line-height: 1.15;
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
  text-shadow: 0 0 16px rgba(255, 77, 126, 0.3);
}

.text-anomalies {
  color: var(--zd);
  text-shadow: 0 0 16px rgba(178, 102, 255, 0.3);
}

.ratio-text {
  font-size: 22px;
}

.kpi-sub {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
  color: var(--mu);
}

.kpi-sub-badge {
  font-size: 9.5px;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 4px;
  background: var(--panel2);
  color: var(--tx);
  letter-spacing: 0.3px;
}

.badge-attacks {
  background: rgba(255, 77, 126, 0.2);
  color: var(--cr);
}

.badge-anomalies {
  background: rgba(178, 102, 255, 0.2);
  color: var(--zd);
}

.kpi-spark-group {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 8px;
  margin-top: 4px;
}

.kpi-bandwidth-text {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--mu);
}

.spark-bars {
  display: flex;
  align-items: flex-end;
  gap: 2.5px;
  height: 20px;
  flex: 1;
  max-width: 80px;
}

.spark-bars i {
  flex: 1;
  background: linear-gradient(180deg, var(--ac2), var(--ac));
  border-radius: 2px;
  opacity: 0.55;
  transition: height 0.3s ease;
}

.spark-bars i:last-child {
  opacity: 1;
  background: var(--ok);
}

.ratio-bar-wrapper {
  margin-top: 4px;
}

.ratio-bar-bg {
  height: 6px;
  border-radius: 3px;
  background: var(--ok);
  overflow: hidden;
}

.ratio-bar-fill {
  display: block;
  height: 100%;
  background: var(--cr);
  transition: width 0.3s ease;
}

.ratio-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10.5px;
  color: var(--mu);
  margin-top: 3px;
}
</style>
