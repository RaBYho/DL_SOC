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

      <!-- Clear Button (Only shown when filters are active) -->
      <button 
        v-if="store.hasActiveFilters" 
        type="button" 
        class="clear-btn" 
        @click="store.clearFilters"
      >
        {{ store.t('table.clearFilters') }}
      </button>

      <!-- Consolidated Export Dropdown at right end of toolbar -->
      <div class="export-dropdown-wrapper" ref="exportDropdownRef">
        <button 
          type="button" 
          class="export-dropdown-trigger" 
          :class="{ active: showExportMenu }"
          @click.stop="showExportMenu = !showExportMenu"
          title="Exporter le jeu de données Active Learning (flux qualifiés par l'analyste)"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          <span>Exporter</span>
          <svg class="chevron-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </button>

        <transition name="dropdown-pop">
          <div v-if="showExportMenu" class="export-dropdown-menu" @click.stop>
            <div class="export-menu-header">Dataset Active Learning</div>
            <a 
              href="/api/dashboard/feedback/export?format=json&download=true" 
              download="feedback_flows.json"
              class="export-menu-item"
              @click="showExportMenu = false"
            >
              <span class="fmt-badge json">JSON</span>
              <div class="fmt-details">
                <span class="fmt-title">feedback_flows.json</span>
                <span class="fmt-desc">Format structuré pour Colab &amp; Fine-Tuning</span>
              </div>
            </a>
            <a 
              href="/api/dashboard/feedback/export?format=csv" 
              download="feedback_flows.csv"
              class="export-menu-item"
              @click="showExportMenu = false"
            >
              <span class="fmt-badge csv">CSV</span>
              <div class="fmt-details">
                <span class="fmt-title">feedback_flows.csv</span>
                <span class="fmt-desc">Format tableur pour reporting et analyse</span>
              </div>
            </a>
          </div>
        </transition>
      </div>
    </div>

    <!-- Floating Batch Actions Bar -->
    <transition name="slide-down">
      <div v-if="store.selectedCount > 0" class="batch-floating-bar">
        <div class="batch-info">
          <div class="batch-count-pill">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            <span><b>{{ store.selectedCount }}</b> {{ store.t('batch.flowsSelected') }}</span>
          </div>
          <span v-if="store.selectedZeroDaysCount > 0" class="batch-zd-tag">
            {{ store.selectedZeroDaysCount }} {{ store.t('batch.zeroDaysCount') }}
          </span>
        </div>

        <div class="batch-actions">
          <!-- Button 1: Copy Prompt for LLM -->
          <button class="batch-action-btn copy-prompt-btn" :class="{ 'btn-success': isPromptCopied }" @click="copyBatchPrompt">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
            <span>{{ isPromptCopied ? 'Copié !' : store.t('batch.copyPrompt') }}</span>
          </button>

          <!-- Button 2: Open Pattern Modal -->
          <button class="batch-action-btn triage-modal-btn" @click="store.openBatchPatternModal">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
              <polyline points="2 17 12 22 22 17"></polyline>
              <polyline points="2 12 12 17 22 12"></polyline>
            </svg>
            <span>{{ store.t('batch.detectPattern') }}</span>
          </button>

          <!-- Button 3: Clear Selection -->
          <button class="batch-clear-btn" @click="store.clearSelectedAlerts" title="Tout désélectionner">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </div>
    </transition>

    <!-- Live Incident Table (Separate Source & Destination Columns, No Arrows) -->
    <div class="table-container">
      <table v-if="store.isLoading || store.filteredAlerts.length > 0">
        <thead>
          <tr>
            <th class="th-checkbox">
              <input 
                type="checkbox" 
                class="batch-checkbox" 
                :checked="store.isAllFilteredSelected" 
                @change="store.toggleSelectAllFiltered" 
                :title="store.t('batch.selectAll')" 
              />
            </th>
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
        <tbody v-if="store.isLoading">
          <tr v-for="i in 6" :key="'table-skel-' + i" class="skeleton-table-row">
            <td><div class="skeleton-shimmer skel-cell skel-checkbox"></div></td>
            <td><div class="skeleton-shimmer skel-cell skel-time"></div></td>
            <td><div class="skeleton-shimmer skel-cell skel-sensor"></div></td>
            <td><div class="skeleton-shimmer skel-cell skel-ip"></div></td>
            <td><div class="skeleton-shimmer skel-cell skel-ip"></div></td>
            <td><div class="skeleton-shimmer skel-cell skel-proto"></div></td>
            <td><div class="skeleton-shimmer skel-cell skel-pred"></div></td>
            <td><div class="skeleton-shimmer skel-cell skel-conf"></div></td>
            <td><div class="skeleton-shimmer skel-cell skel-ae"></div></td>
            <td><div class="skeleton-shimmer skel-cell skel-sev"></div></td>
          </tr>
        </tbody>
        <tbody v-else>
          <tr 
            v-for="(alert, idx) in displayedAlerts" 
            :key="alert.id || idx"
            tabindex="0"
            :class="{ 
              'row-new': alert.isNew, 
              'row-selected': store.selectedFlow === alert,
              'row-batch-checked': store.isAlertSelected(alert)
            }"
            @click="store.openFlowDrawer(alert)"
            @keydown.enter="store.openFlowDrawer(alert)"
          >
            <td class="td-checkbox" @click.stop>
              <input 
                type="checkbox" 
                class="batch-checkbox" 
                :checked="store.isAlertSelected(alert)" 
                @change="store.toggleSelectAlert(alert)" 
              />
            </td>
            <td class="mono time-col">{{ formatTime(alert.received_at || alert.timestamp) }}</td>
            <td>
              <span class="sensor-pill">{{ alert.sensor_id || alert.sensor || 'sensor-01' }}</span>
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
              <div class="pred-with-verdict">
                <b class="pred-label">{{ alert.classification || alert.pred || 'BENIGN' }}</b>
                <span v-if="getFeedbackVerdict(alert)" class="table-verdict-tag" :class="getFeedbackClass(alert)">
                  {{ getFeedbackLabel(alert) }}
                </span>
              </div>
            </td>
            <td>
              <div class="conf-cell">
                <div class="conf-bar-bg">
                  <i :style="{ width: `${((alert.confiance !== undefined ? alert.confiance : (alert.confidence ? alert.confidence / 100 : 0.9)) * 100).toFixed(0)}%` }"></i>
                </div>
                <span class="mono">{{ ((alert.confiance !== undefined ? alert.confiance : (alert.confidence ? alert.confidence / 100 : 0.9)) * 100).toFixed(1) }}%</span>
              </div>
            </td>
            <td>
              <div class="ae-cell">
                <span 
                  class="flag-pill" 
                  :class="(alert.anomalie_ae === 1 || alert.is_anomaly) ? 'flag-anomaly' : 'flag-nominal'"
                >
                  {{ (alert.anomalie_ae === 1 || alert.is_anomaly) ? '0-Day' : 'Nominal' }}
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

    <!-- Batch Pattern & Campaign Investigation Modal -->
    <BatchPatternModal />

    <!-- Table Toast Notification -->
    <transition name="fade">
      <div v-if="toastMessage" class="table-toast">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
        <span>{{ toastMessage }}</span>
      </div>
    </transition>
  </section>
</template>

<script setup>
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { useSocStore } from '@/stores/socStore'
import { api } from '@/services/api'
import BatchPatternModal from './BatchPatternModal.vue'

const store = useSocStore()
const isPromptCopied = ref(false)
const toastMessage = ref('')
const showExportMenu = ref(false)
const exportDropdownRef = ref(null)

function handleClickOutside(event) {
  if (exportDropdownRef.value && !exportDropdownRef.value.contains(event.target)) {
    showExportMenu.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})

async function copyBatchPrompt() {
  if (!store.selectedCount) return
  const flows = store.selectedAlerts
  try {
    const res = await api.generateCampaignPrompt(flows)
    const promptText = res.prompt
    await navigator.clipboard.writeText(promptText)
    isPromptCopied.value = true
    toastMessage.value = store.t('batch.promptCopied')
    setTimeout(() => {
      isPromptCopied.value = false
      toastMessage.value = ''
    }, 3000)
  } catch (err) {
    console.error('Failed to copy campaign prompt:', err)
  }
}

const attackCategories = computed(() => store.availableAttackCategories)

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

function getFeedbackVerdict(alert) {
  const id = alert.id || `${alert.src_ip}-${alert.dst_port}-${alert.received_at}`
  return store.incidentFeedbackMap[id] || null
}

function getFeedbackClass(alert) {
  const fb = getFeedbackVerdict(alert)
  if (!fb) return ''
  if (fb.human_verdict === 'FALSE_POSITIVE') return 'tag-fp'
  if (fb.human_verdict === 'KNOWN_ATTACK') return 'tag-reclass'
  if (fb.human_verdict === 'CONFIRMED_ZERODAY') return 'tag-zd'
  return ''
}

function getFeedbackLabel(alert) {
  const fb = getFeedbackVerdict(alert)
  if (!fb) return ''
  if (fb.human_verdict === 'FALSE_POSITIVE') return 'Faux Positif'
  if (fb.human_verdict === 'KNOWN_ATTACK') return fb.corrected_attack_type || 'Reclassifié'
  if (fb.human_verdict === 'CONFIRMED_ZERODAY') return fb.corrected_attack_type || 'Zero-Day'
  return ''
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

/* Skeleton Rows for Incident Feed */
.skeleton-table-row {
  pointer-events: none;
}

.skel-cell {
  height: 14px;
  border-radius: 4px;
  margin: 3px 0;
}

.skel-time {
  width: 70px;
}

.skel-sensor {
  width: 60px;
  height: 18px;
  border-radius: 12px;
}

.skel-ip {
  width: 100px;
}

.skel-proto {
  width: 38px;
  height: 18px;
  border-radius: 4px;
}

.skel-pred {
  width: 80px;
}

.skel-conf {
  width: 85px;
  height: 12px;
}

.skel-ae {
  width: 70px;
  height: 18px;
  border-radius: 12px;
}

.skel-sev {
  width: 55px;
  height: 18px;
  border-radius: 12px;
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

.pred-with-verdict {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.table-verdict-tag {
  display: inline-block;
  align-self: flex-start;
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  letter-spacing: 0.02em;
}

.tag-fp {
  background: rgba(61, 220, 151, 0.15);
  color: var(--ok);
  border: 1px solid rgba(61, 220, 151, 0.3);
}

.tag-reclass {
  background: rgba(255, 181, 71, 0.15);
  color: var(--md);
  border: 1px solid rgba(255, 181, 71, 0.3);
}

.tag-zd {
  background: rgba(178, 102, 255, 0.15);
  color: var(--zd);
  border: 1px solid rgba(178, 102, 255, 0.3);
}

/* Consolidated Export Dropdown in Filters Bar */
.export-dropdown-wrapper {
  position: relative;
  margin-left: auto;
}

.export-dropdown-trigger {
  background: rgba(56, 189, 248, 0.08);
  border: 1px solid rgba(56, 189, 248, 0.25);
  color: #38bdf8;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.export-dropdown-trigger:hover,
.export-dropdown-trigger.active {
  background: rgba(56, 189, 248, 0.18);
  border-color: rgba(56, 189, 248, 0.5);
  color: #fff;
}

.export-dropdown-trigger svg {
  width: 14px;
  height: 14px;
}

.chevron-svg {
  width: 12px !important;
  height: 12px !important;
  transition: transform 0.2s ease;
}

.export-dropdown-trigger.active .chevron-svg {
  transform: rotate(180deg);
}

.export-dropdown-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  width: 290px;
  background: #0f172a;
  border: 1px solid rgba(56, 189, 248, 0.3);
  border-radius: 10px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.65), 0 0 12px rgba(56, 189, 248, 0.1);
  padding: 8px;
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.export-menu-header {
  font-size: 10.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #94a3b8;
  padding: 4px 8px 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  margin-bottom: 2px;
}

.export-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 6px;
  text-decoration: none;
  transition: background 0.18s ease;
  cursor: pointer;
}

.export-menu-item:hover {
  background: rgba(56, 189, 248, 0.12);
}

.fmt-badge {
  font-size: 10px;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
}

.fmt-badge.json {
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.35);
}

.fmt-badge.csv {
  background: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.35);
}

.fmt-details {
  display: flex;
  flex-direction: column;
}

.fmt-title {
  font-size: 12px;
  font-weight: 600;
  color: #f1f5f9;
}

.fmt-desc {
  font-size: 10.5px;
  color: #94a3b8;
  line-height: 1.3;
}

.dropdown-pop-enter-active,
.dropdown-pop-leave-active {
  transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
}

.dropdown-pop-enter-from,
.dropdown-pop-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.97);
}

/* Floating Batch Action Bar */
.batch-floating-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 8px 14px;
  background: rgba(15, 23, 42, 0.95);
  border: 1px solid rgba(0, 229, 255, 0.3);
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4), 0 0 16px rgba(0, 229, 255, 0.12);
}

.batch-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.batch-count-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  color: #f8fafc;
}

.batch-count-pill svg {
  width: 16px;
  height: 16px;
  color: var(--ac, #00e5ff);
}

.batch-zd-tag {
  background: rgba(244, 63, 94, 0.18);
  border: 1px solid rgba(244, 63, 94, 0.35);
  color: #fb7185;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 20px;
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.batch-action-btn {
  font-size: 12px;
  font-weight: 700;
  padding: 6px 12px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
}

.copy-prompt-btn {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.16);
  color: #f8fafc;
}

.copy-prompt-btn:hover {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.28);
}

.copy-prompt-btn.btn-success {
  background: rgba(16, 185, 129, 0.2);
  border-color: rgba(16, 185, 129, 0.4);
  color: #34d399;
}

.triage-modal-btn {
  background: var(--ac, #00e5ff);
  color: #040810;
}

.triage-modal-btn:hover {
  filter: brightness(1.15);
  box-shadow: 0 0 12px rgba(0, 229, 255, 0.4);
}

.batch-action-btn svg {
  width: 14px;
  height: 14px;
}

.batch-clear-btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94a3b8;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.batch-clear-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.batch-clear-btn svg {
  width: 14px;
  height: 14px;
}

/* Checkbox Column Styling */
.th-checkbox, .td-checkbox {
  width: 38px;
  text-align: center;
  padding: 0 8px !important;
}

.batch-checkbox {
  cursor: pointer;
  width: 15px;
  height: 15px;
  accent-color: var(--ac, #00e5ff);
  vertical-align: middle;
}

.row-batch-checked {
  background: rgba(0, 229, 255, 0.05) !important;
}

.skel-checkbox {
  width: 16px;
  height: 16px;
  margin: 0 auto;
}

/* Table Toast */
.table-toast {
  position: absolute;
  bottom: 20px;
  right: 20px;
  background: #0f172a;
  border: 1px solid var(--ok, #10b981);
  color: #e2e8f0;
  padding: 8px 14px;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  z-index: 50;
}

.table-toast svg {
  width: 16px;
  height: 16px;
  color: var(--ok, #10b981);
}

.slide-down-enter-active, .slide-down-leave-active {
  transition: all 0.2s ease;
}

.slide-down-enter-from, .slide-down-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
