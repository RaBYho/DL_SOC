<template>
  <section class="card incident-card" aria-label="Incident feed">
    <div class="card-header-row">
      <h2>
        {{ store.t('table.title') }}
        <span>{{ store.filteredAlerts.length }} of {{ store.alerts.length }} alerts</span>
      </h2>
      <div class="live-counter-pill">
        <span class="live-dot"></span>
        <span>{{ store.t('table.autoUpdating') }}</span>
      </div>
    </div>

    <!-- Filters Bar -->
    <div class="filters-bar">
      <!-- Search Input with Icon -->
      <div class="search-box">
        <svg class="search-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8">
          <circle cx="9" cy="9" r="6" />
          <line x1="14" y1="14" x2="18" y2="18" />
        </svg>
        <input 
          v-model="store.filterSearch"
          type="search" 
          :placeholder="store.t('table.searchPlaceholder')" 
          aria-label="Search IP" 
        />
      </div>

      <!-- Category Filter -->
      <select v-model="store.filterCategory" aria-label="Attack category">
        <option value="">{{ store.t('table.allCategories') }}</option>
        <option 
          v-for="cat in attackCategories" 
          :key="cat" 
          :value="cat"
        >
          {{ cat }}
        </option>
      </select>

      <!-- Min Confidence Slider -->
      <div class="slider-control">
        <span class="slider-label">{{ store.t('table.minConfidence') }}</span>
        <input 
          v-model.number="store.filterMinConfidence" 
          type="range" 
          min="0" 
          max="99" 
        />
        <b class="slider-val">{{ store.filterMinConfidence }}%</b>
      </div>

      <!-- Autoencoder Checkbox -->
      <label class="checkbox-control">
        <input 
          v-model="store.filterAutoencoderOnly" 
          type="checkbox" 
        />
        <span>{{ store.t('table.zeroDayOnly') }}</span>
      </label>

      <!-- Clear Button -->
      <button class="clear-btn" @click="store.clearFilters">
        {{ store.t('table.clearFilters') }}
      </button>
    </div>

    <!-- Live Incident Table -->
    <div class="table-container">
      <table v-if="store.filteredAlerts.length > 0">
        <thead>
          <tr>
            <th>{{ store.t('table.timestamp') }}</th>
            <th>{{ store.t('table.sensor') }}</th>
            <th v-html="store.t('table.route')"></th>
            <th>{{ store.t('table.protocol') }}</th>
            <th>{{ store.t('table.classification') }}</th>
            <th>{{ store.t('table.confidence') }}</th>
            <th>{{ store.t('table.autoencoder') }}</th>
            <th>{{ store.t('table.severity') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="(alert, idx) in displayedAlerts" 
            :key="alert.id || idx"
            tabindex="0"
            :class="{ 
              'row-new': alert.isNew, 
              'row-selected': store.selectedFlow === alert 
            }"
            @click="store.openFlowDrawer(alert)"
            @keydown.enter="store.openFlowDrawer(alert)"
          >
            <td class="mono time-col">{{ formatTime(alert.received_at) }}</td>
            <td>
              <span class="sensor-pill">{{ alert.sensor_id || 'sensor-01' }}</span>
            </td>
            <td class="mono ip-route-col">
              <span class="src-ip">{{ alert.src_ip }}</span>
              <span class="port-sub">:{{ alert.src_port || '–' }}</span>
              <span class="route-arrow">&rarr;</span>
              <span class="dst-ip">{{ alert.dst_ip }}</span>
              <span class="port-sub">:{{ alert.dst_port }}</span>
            </td>
            <td>
              <span class="proto-badge">{{ resolveProto(alert.protocol) }}</span>
            </td>
            <td>
              <b class="pred-label">{{ alert.pred }}</b>
            </td>
            <td>
              <div class="conf-cell">
                <div class="conf-bar-bg">
                  <i :style="{ width: `${((alert.confiance || 0.9) * 100).toFixed(0)}%` }"></i>
                </div>
                <span class="mono">{{ ((alert.confiance || 0.9) * 100).toFixed(1) }}%</span>
              </div>
            </td>
            <td>
              <div class="ae-cell">
                <span 
                  class="flag-pill" 
                  :class="alert.anomalie_ae === 1 ? 'flag-anomaly' : 'flag-nominal'"
                >
                  {{ alert.anomalie_ae === 1 ? '0-Day' : 'Nominal' }}
                </span>
                <span class="mono mse-num">
                  {{ alert.mse_ae !== null && alert.mse_ae !== undefined ? alert.mse_ae.toFixed(2) : '–' }}
                </span>
              </div>
            </td>
            <td>
              <span class="sev" :class="alert.severity">
                {{ alert.severity }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Empty State -->
      <div v-else class="empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <p>{{ store.t('table.emptyMessage') }}</p>
        <button class="clear-btn" @click="store.clearFilters">{{ store.t('table.resetFilters') }}</button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useSocStore } from '@/stores/socStore'

const store = useSocStore()

const attackCategories = [
  'DDoS',
  'DoS-Hulk',
  'DoS-GoldenEye',
  'DoS-slowloris',
  'DoS-Slowhttptest',
  'PortScan',
  'SSH-Patator',
  'FTP-Patator',
  'WebAttack',
  'Bot',
  'Scan-Vista',
  'Unknown (anomaly)'
]

const displayedAlerts = computed(() => {
  return store.filteredAlerts.slice(0, 80)
})

function formatTime(val) {
  if (!val) return new Date().toTimeString().slice(0, 8)
  if (typeof val === 'string' && val.includes(':')) return val
  try {
    const d = new Date(val)
    return isNaN(d.getTime()) ? String(val).slice(-8) : d.toTimeString().slice(0, 8)
  } catch {
    return '–'
  }
}

function resolveProto(proto) {
  if (proto === 6 || proto === '6' || proto === 'TCP') return 'TCP'
  if (proto === 17 || proto === '17' || proto === 'UDP') return 'UDP'
  if (proto === 1 || proto === '1' || proto === 'ICMP') return 'ICMP'
  return proto || 'IP'
}
</script>

<style scoped>
.incident-card {
  display: flex;
  flex-direction: column;
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.card-header-row h2 {
  margin: 0;
}

.live-counter-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--ok);
  background: rgba(61, 220, 151, 0.1);
  padding: 3px 10px;
  border-radius: 20px;
  border: 1px solid rgba(61, 220, 151, 0.2);
}

.live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--ok);
  animation: pulse-ring 1.6s infinite;
}

.filters-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  margin-bottom: 14px;
  padding: 10px 14px;
  background: var(--panel2);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 220px;
}

.search-icon {
  position: absolute;
  left: 10px;
  width: 15px;
  height: 15px;
  color: var(--mu);
  pointer-events: none;
}

.search-box input {
  width: 100%;
  padding-left: 32px;
  background: var(--panel);
}

.slider-control {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--mu);
}

.slider-val {
  min-width: 32px;
  color: var(--tx);
  font-variant-numeric: tabular-nums;
}

.checkbox-control {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  color: var(--tx);
  cursor: pointer;
}

.clear-btn {
  font-size: 12px;
  padding: 6px 12px;
  background: transparent;
  color: var(--mu);
  border: 1px solid var(--line);
  border-radius: 8px;
}

.clear-btn:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--tx);
}

.table-container {
  overflow-x: auto;
  max-height: 440px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: var(--panel2);
  -webkit-overflow-scrolling: touch;
}

table {
  width: 100%;
  min-width: 640px;
  border-collapse: collapse;
}

th {
  position: sticky;
  top: 0;
  background: #1b1c28;
  color: var(--mu);
  font-size: 11.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 11px 12px;
  text-align: left;
  border-bottom: 1px solid var(--line);
  z-index: 2;
}

td {
  padding: 10px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  font-size: 13px;
}

tbody tr {
  cursor: pointer;
  transition: background 0.12s ease;
}

tbody tr:hover {
  background: rgba(88, 101, 242, 0.12);
}

tbody tr.row-selected {
  background: rgba(88, 101, 242, 0.22);
}

tbody tr.row-new {
  animation: flash-row 1.2s ease-out;
}

@keyframes flash-row {
  from { background: rgba(88, 101, 242, 0.4); }
}

.time-col {
  color: var(--mu);
}

.sensor-pill {
  font-size: 11px;
  color: var(--mu);
  background: rgba(255, 255, 255, 0.05);
  padding: 2px 7px;
  border-radius: 4px;
}

.ip-route-col {
  display: flex;
  align-items: center;
  gap: 3px;
}

.src-ip {
  color: #fff;
  font-weight: 600;
}

.dst-ip {
  color: var(--tx);
}

.port-sub {
  color: var(--mu);
  font-size: 11px;
}

.route-arrow {
  color: var(--ac);
  margin: 0 4px;
}

.proto-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--panel);
  color: var(--tx);
  border: 1px solid var(--line);
}

.pred-label {
  color: #fff;
  font-weight: 700;
}

.conf-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.conf-bar-bg {
  width: 44px;
  height: 5px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.conf-bar-bg i {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, var(--lo), var(--ac));
}

.ae-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.flag-pill {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
}

.flag-anomaly {
  background: rgba(178, 102, 255, 0.2);
  color: var(--zd);
  border: 1px solid rgba(178, 102, 255, 0.4);
}

.flag-nominal {
  color: var(--mu);
  font-weight: 500;
}

.mse-num {
  font-size: 11px;
  color: var(--mu);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--mu);
}

.empty-state svg {
  width: 32px;
  height: 32px;
  margin-bottom: 8px;
  opacity: 0.5;
}
</style>
