<template>
  <section class="card incident-card" aria-label="Incident feed">
    <!-- Header: Title and Subtitle strictly stacked beneath -->
    <div class="card-header-row">
      <div class="header-titles">
        <h2 class="card-title">{{ store.t('table.title') }}</h2>
        <span class="card-subtitle">
          {{ store.t('table.subtitle') }} &middot; {{ store.filteredAlerts.length }} / {{ store.alerts.length }} alertes
        </span>
      </div>
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

    <!-- Live Incident Table (Separate Source & Destination Columns, No Arrows) -->
    <div class="table-container">
      <table v-if="store.filteredAlerts.length > 0">
        <thead>
          <tr>
            <th>{{ store.t('table.timestamp') }}</th>
            <th>{{ store.t('table.sensor') }}</th>
            <th>{{ store.t('table.source') }}</th>
            <th>{{ store.t('table.destination') }}</th>
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

            <!-- Source Column (Distinct column, no arrows) -->
            <td class="mono ip-cell src-cell">
              <span class="ip-addr" :title="alert.src_ip">{{ alert.src_ip }}</span>
              <span v-if="alert.src_port" class="port-tag">:{{ alert.src_port }}</span>
            </td>

            <!-- Destination Column (Distinct column, no arrows) -->
            <td class="mono ip-cell dst-cell">
              <span class="ip-addr" :title="alert.dst_ip">{{ alert.dst_ip }}</span>
              <span class="port-tag">:{{ alert.dst_port }}</span>
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
  transition: transform 0.24s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.24s ease, box-shadow 0.24s ease;
}

.incident-card:hover {
  border-color: rgba(255, 255, 255, 0.14);
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 14px;
}

.header-titles {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.card-title {
  margin: 0;
  font-size: 15px;
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

.live-counter-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  color: var(--ok);
  background: rgba(61, 220, 151, 0.1);
  padding: 3px 10px;
  border-radius: 20px;
  border: 1px solid rgba(61, 220, 151, 0.22);
}

.live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--ok);
  box-shadow: 0 0 6px rgba(61, 220, 151, 0.6);
  animation: pulse-ring 1.8s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse-ring {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.85); }
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
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--panel);
  border: 1px solid var(--line);
  padding: 6px 12px;
  border-radius: 8px;
  flex: 1;
  min-width: 220px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.search-box:focus-within {
  border-color: var(--ac);
  box-shadow: 0 0 0 2px rgba(88, 101, 242, 0.2);
}

.search-icon {
  width: 15px;
  height: 15px;
  color: var(--mu);
}

.search-box input {
  border: 0;
  background: none;
  color: var(--tx);
  outline: none;
  font-size: 13px;
  width: 100%;
}

select {
  background: var(--panel);
  border: 1px solid var(--line);
  color: var(--tx);
  padding: 7px 12px;
  border-radius: 8px;
  font-size: 12.5px;
  outline: none;
  cursor: pointer;
  transition: border-color 0.2s ease;
}

select:focus {
  border-color: var(--ac);
}

.slider-control {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--panel);
  border: 1px solid var(--line);
  padding: 4px 12px;
  border-radius: 8px;
}

.slider-label {
  font-size: 11.5px;
  color: var(--mu);
}

.slider-val {
  font-size: 12px;
  min-width: 30px;
  color: var(--tx);
  font-variant-numeric: tabular-nums;
}

.checkbox-control {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12.5px;
  color: var(--tx);
  cursor: pointer;
  user-select: none;
}

.checkbox-control input {
  accent-color: var(--zd);
  cursor: pointer;
}

.clear-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--line);
  color: var(--mu);
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.clear-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--tx);
  border-color: rgba(255, 255, 255, 0.2);
}

.table-container {
  height: 440px;
  max-height: 440px;
  overflow-y: auto;
  overflow-x: auto;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(0, 0, 0, 0.12);
  position: relative;
  scroll-behavior: smooth;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.22) transparent;
}

.table-container::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.table-container::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
}

.table-container::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.table-container::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.35);
}

table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

th {
  position: sticky;
  top: 0;
  z-index: 2;
  padding: 11px 12px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--mu);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  background: #171825;
  white-space: nowrap;
}

td {
  padding: 10px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  font-size: 12.5px;
}

tbody tr {
  cursor: pointer;
  transition: background-color 0.18s cubic-bezier(0.16, 1, 0.3, 1);
}

tbody tr:hover {
  background: rgba(88, 101, 242, 0.12);
}

tbody tr.row-selected {
  background: rgba(88, 101, 242, 0.22);
}

tbody tr.row-new {
  animation: flash-row 1.4s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes flash-row {
  0% { background: rgba(99, 102, 241, 0.35); }
  100% { background: transparent; }
}

.time-col {
  color: var(--mu);
  font-size: 12px;
  white-space: nowrap;
}

.sensor-pill {
  font-size: 10.5px;
  color: var(--mu);
  background: rgba(255, 255, 255, 0.05);
  padding: 2px 7px;
  border-radius: 4px;
  white-space: nowrap;
}

/* Distinct Source & Destination Cells (No arrows) */
.ip-cell {
  white-space: nowrap;
}

.ip-addr {
  font-size: 12.5px;
  font-weight: 600;
  color: #fff;
}

.dst-cell .ip-addr {
  color: var(--tx);
}

.port-tag {
  color: var(--mu);
  font-size: 11px;
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
  white-space: nowrap;
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
  border-radius: 3px;
  transition: width 0.4s cubic-bezier(0.16, 1, 0.3, 1);
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

@media (max-width: 768px) {
  .filters-bar {
    flex-direction: column;
    align-items: stretch;
  }
  .table-container {
    height: 380px;
    max-height: 380px;
  }
}
</style>
