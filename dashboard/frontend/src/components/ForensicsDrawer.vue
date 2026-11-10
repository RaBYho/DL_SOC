<template>
  <div v-if="store.isDrawerOpen" class="fixed inset-0 z-50 flex justify-end">
    <!-- Backdrop Transition -->
    <Transition name="drawer-backdrop" appear>
      <div
        v-if="store.isDrawerOpen"
        class="fixed inset-0 bg-black/70 backdrop-blur-sm"
        @click="store.closeForensics"
      ></div>
    </Transition>

    <!-- Slide-Over Panel Transition -->
    <Transition name="drawer-panel" appear>
      <div
        v-if="store.isDrawerOpen"
        class="relative w-full max-w-xl bg-zinc-950 border-l border-zinc-800/80 shadow-2xl z-10 flex flex-col h-full overflow-hidden select-text"
      >
      <!-- Header -->
      <div class="h-14 border-b border-zinc-800/80 px-5 flex items-center justify-between bg-zinc-900/60 flex-shrink-0">
        <div class="flex items-center space-x-3">
          <Terminal :size="16" class="text-zinc-400" />
          <span class="text-xs font-bold uppercase tracking-wider text-zinc-200">Forensic Investigation</span>
          <span v-if="store.selectedForensics" class="text-xs font-mono text-zinc-500">
            #{{ store.selectedForensics.flow_id }}
          </span>
        </div>

        <div class="flex items-center space-x-3">
          <span
            v-if="store.selectedForensics?.ml_scores?.severity"
            class="px-2 py-0.5 text-[10px] font-semibold uppercase rounded border"
            :class="severityBadgeClass(store.selectedForensics.ml_scores.severity)"
          >
            {{ store.selectedForensics.ml_scores.severity }}
          </span>

          <button
            @click="store.closeForensics"
            class="text-zinc-400 hover:text-zinc-100 p-1 rounded hover:bg-zinc-800 transition duration-100"
          >
            <X :size="16" />
          </button>
        </div>
      </div>

      <!-- Loading State: Structured Skeleton -->
      <div v-if="store.forensicsLoading" class="flex-1 overflow-y-auto p-5 space-y-6 text-xs font-mono animate-pulse">
        <div class="space-y-2">
          <div class="h-3.5 bg-zinc-800/60 rounded w-40"></div>
          <div class="grid grid-cols-2 gap-2 bg-zinc-900/80 border border-zinc-800/80 rounded p-3 h-28"></div>
        </div>
        <div class="space-y-2">
          <div class="h-3.5 bg-zinc-800/60 rounded w-48"></div>
          <div class="bg-zinc-900/80 border border-zinc-800/80 rounded p-3 h-32"></div>
        </div>
        <div class="space-y-2">
          <div class="h-3.5 bg-zinc-800/60 rounded w-44"></div>
          <div class="bg-zinc-900/80 border border-zinc-800/80 rounded p-3 h-32"></div>
        </div>
      </div>

      <!-- Content -->
      <div v-else-if="store.selectedForensics" class="flex-1 overflow-y-auto p-5 space-y-6 text-xs font-mono">
        <!-- 1. 5-Tuple Network Identification -->
        <div class="space-y-2">
          <div class="text-[11px] font-semibold uppercase tracking-wider text-zinc-400 flex items-center space-x-1.5">
            <Globe :size="13" class="text-zinc-500" />
            <span>5-Tuple Network Identity</span>
          </div>

          <div class="grid grid-cols-2 gap-3.5 bg-zinc-900/80 border border-zinc-800/80 rounded-lg p-4 text-zinc-300">
            <div>
              <div class="text-[10px] text-zinc-500 uppercase">Source Endpoint</div>
              <div class="text-zinc-100 font-semibold mt-0.5 tabular-nums">
                {{ store.selectedForensics.five_tuple?.src_ip }}:{{ store.selectedForensics.five_tuple?.src_port }}
              </div>
            </div>

            <div>
              <div class="text-[10px] text-zinc-500 uppercase">Target Endpoint</div>
              <div class="text-zinc-100 font-semibold mt-0.5 tabular-nums">
                {{ store.selectedForensics.five_tuple?.dst_ip }}:{{ store.selectedForensics.five_tuple?.dst_port }}
              </div>
            </div>

            <div class="mt-1">
              <div class="text-[10px] text-zinc-500 uppercase">Transport Protocol</div>
              <div class="text-zinc-200 mt-0.5">
                {{ formatProto(store.selectedForensics.five_tuple?.protocol) }}
              </div>
            </div>

            <div class="mt-1">
              <div class="text-[10px] text-zinc-500 uppercase">Decision Engine</div>
              <div class="text-zinc-200 mt-0.5">
                {{ store.selectedForensics.ml_scores?.decision_engine }}
              </div>
            </div>
          </div>
        </div>

        <!-- 2. Multistage ML & Decision Breakdown -->
        <div class="space-y-2">
          <div class="text-[11px] font-semibold uppercase tracking-wider text-zinc-400 flex items-center space-x-1.5">
            <Cpu :size="13" class="text-zinc-500" />
            <span>Cascaded ML & Anomaly Scores</span>
          </div>

          <div class="bg-zinc-900/80 border border-zinc-800/80 rounded-lg p-4 space-y-3.5">
            <!-- Stage 1 -->
            <div>
              <div class="flex items-center justify-between text-[11px]">
                <span class="text-zinc-400">Étage 1: CatBoost / XGBoost (Suspicion)</span>
                <span class="text-zinc-200 font-semibold tabular-nums">
                  {{ formatScore(store.selectedForensics.ml_scores?.stage1_prediction === 'BENIGN' ? 0.05 : 0.92) }}
                  <span class="text-zinc-500 text-[10px]">(t1: 0.50)</span>
                </span>
              </div>
              <div class="w-full bg-zinc-800 h-1.5 rounded mt-1.5 overflow-hidden">
                <div
                  class="bg-sky-400 h-full rounded"
                  :style="{ width: store.selectedForensics.ml_scores?.stage1_prediction === 'BENIGN' ? '10%' : '90%' }"
                ></div>
              </div>
            </div>

            <!-- Stage 2 -->
            <div>
              <div class="flex items-center justify-between text-[11px]">
                <span class="text-zinc-400">Étage 2: DNN-1D Multiclass Confidence</span>
                <span class="text-zinc-200 font-semibold tabular-nums">
                  {{ formatScore(store.selectedForensics.ml_scores?.stage2_confidence) }}
                  <span class="text-zinc-500 text-[10px]">(t2: 0.70)</span>
                </span>
              </div>
              <div class="w-full bg-zinc-800 h-1.5 rounded mt-1.5 overflow-hidden">
                <div
                  class="bg-red-400 h-full rounded"
                  :style="{ width: `${Math.min(100, (store.selectedForensics.ml_scores?.stage2_confidence || 0) * 100)}%` }"
                ></div>
              </div>
            </div>

            <!-- Kitsune RMSE -->
            <div>
              <div class="flex items-center justify-between text-[11px]">
                <span class="text-zinc-400">Parallel Branch: Kitsune Autoencoder RMSE</span>
                <span class="text-zinc-200 font-semibold tabular-nums">
                  {{ formatScore(store.selectedForensics.ml_scores?.kitsune_rmse) }}
                  <span class="text-zinc-500 text-[10px]">(t3: {{ store.thresholds.t3 }})</span>
                </span>
              </div>
              <div class="w-full bg-zinc-800 h-1.5 rounded mt-1.5 overflow-hidden">
                <div
                  class="bg-amber-400 h-full rounded"
                  :style="{ width: `${Math.min(100, (store.selectedForensics.ml_scores?.kitsune_rmse || 0) * 500)}%` }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <!-- 3. DPI Content Matching -->
        <div class="space-y-2">
          <div class="text-[11px] font-semibold uppercase tracking-wider text-zinc-400 flex items-center space-x-1.5">
            <Search :size="13" class="text-zinc-500" />
            <span>Deep Packet Inspection (DPI)</span>
          </div>

          <div class="bg-zinc-900/80 border border-zinc-800/80 rounded-lg p-4 text-zinc-300">
            <div class="flex items-center justify-between">
              <span class="text-[10px] text-zinc-500 uppercase">Triggered Signature</span>
              <span
                class="px-2.5 py-1 rounded text-[10px] font-semibold uppercase"
                :class="store.selectedForensics.raw_metrics?.dpi_rule ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20' : 'text-zinc-500'"
              >
                {{ store.selectedForensics.raw_metrics?.dpi_rule || 'None (Traffic Clean)' }}
              </span>
            </div>
          </div>
        </div>

        <!-- 4. Raw Flow Telemetry (CICFlowMeter) -->
        <div class="space-y-2.5">
          <div class="text-[11px] font-semibold uppercase tracking-wider text-zinc-400 flex items-center justify-between">
            <div class="flex items-center space-x-1.5">
              <FileText :size="13" class="text-zinc-500" />
              <span>Raw Flow Telemetry</span>
            </div>
            <span
              v-if="featureCount > 0"
              class="text-[10px] text-zinc-400 font-mono px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800"
            >
              {{ featureCount }} Features Captured
            </span>
          </div>

          <!-- Top-Level Telemetry Metrics -->
          <div class="bg-zinc-900/80 border border-zinc-800/80 rounded-lg p-4 grid grid-cols-2 gap-3.5 text-zinc-300">
            <div>
              <span class="text-[10px] text-zinc-500 uppercase">Flow Duration:</span>
              <div class="text-zinc-100 tabular-nums">
                {{ formatDuration(store.selectedForensics.raw_metrics?.flow_duration) }}
              </div>
            </div>

            <div>
              <span class="text-[10px] text-zinc-500 uppercase">Total Packets (Fwd / Bwd):</span>
              <div class="text-zinc-100 tabular-nums">
                {{ store.selectedForensics.raw_metrics?.total_fwd_packets ?? 0 }} / {{ store.selectedForensics.raw_metrics?.total_bwd_packets ?? 0 }}
              </div>
            </div>

            <div>
              <span class="text-[10px] text-zinc-500 uppercase">Throughput:</span>
              <div class="text-zinc-100 tabular-nums">
                {{ formatBytesPerSec(store.selectedForensics.raw_metrics?.flow_bytes_s) }}
              </div>
            </div>

            <div>
              <span class="text-[10px] text-zinc-500 uppercase">Avg Packet Size:</span>
              <div class="text-zinc-100 tabular-nums">
                {{ formatBytes(store.selectedForensics.raw_metrics?.avg_packet_size) }}
              </div>
            </div>

            <div>
              <span class="text-[10px] text-zinc-500 uppercase">Flags (SYN / ACK / PSH):</span>
              <div class="text-zinc-100 tabular-nums">
                {{ store.selectedForensics.raw_metrics?.syn_flag_count ?? 0 }} / {{ store.selectedForensics.raw_metrics?.ack_flag_count ?? 0 }} / {{ store.selectedForensics.raw_metrics?.psh_flag_count ?? 0 }}
              </div>
            </div>

            <div>
              <span class="text-[10px] text-zinc-500 uppercase">Down / Up Ratio:</span>
              <div class="text-zinc-100 tabular-nums">
                {{ formatRatio(store.selectedForensics.raw_metrics?.down_up_ratio) }}
              </div>
            </div>
          </div>

          <!-- Expandable 78 Features Forensic Inspector -->
          <div class="border border-zinc-800/80 rounded-lg bg-zinc-900/40 overflow-hidden">
            <button
              @click="showAllFeatures = !showAllFeatures"
              type="button"
              class="w-full px-3.5 py-2.5 flex items-center justify-between hover:bg-zinc-800/40 transition duration-100 text-left"
            >
              <div class="flex items-center space-x-2">
                <ChevronRight
                  :size="13"
                  class="text-zinc-400 transition-transform duration-150"
                  :class="{ 'rotate-90': showAllFeatures }"
                />
                <span class="text-[11px] font-semibold uppercase tracking-wider text-zinc-300">
                  Full Feature Matrix
                </span>
                <span class="text-[10px] text-zinc-500">
                  ({{ featureCount }} indicators)
                </span>
              </div>
              <span class="text-[10px] text-sky-400 font-mono">
                {{ showAllFeatures ? 'Hide' : 'Inspect All' }}
              </span>
            </button>

            <div v-if="showAllFeatures" class="p-3 border-t border-zinc-800/80 space-y-2.5 bg-zinc-950/60">
              <!-- Search filter for features -->
              <input
                v-model="featureSearch"
                type="text"
                placeholder="Filter features (e.g. IAT, Packet, Flag, Length)..."
                class="w-full bg-zinc-900/90 border border-zinc-800 rounded px-2.5 py-1.5 text-[11px] text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-zinc-700 font-mono"
              />

              <!-- Feature Grid -->
              <div v-if="filteredFeatureList.length > 0" class="max-h-60 overflow-y-auto space-y-1 pr-1">
                <div
                  v-for="item in filteredFeatureList"
                  :key="item.name"
                  class="flex items-center justify-between py-1 px-2.5 rounded bg-zinc-900/60 hover:bg-zinc-800/50 text-[11px] border border-zinc-800/40 transition-colors"
                >
                  <span class="text-zinc-400 truncate mr-3 font-mono text-[10px]" :title="item.name">
                    {{ item.name }}
                  </span>
                  <span class="text-zinc-100 font-mono tabular-nums text-[10px] flex-shrink-0">
                    {{ item.value }}
                  </span>
                </div>
              </div>
              <div v-else class="text-center py-4 text-zinc-500 text-[11px] font-mono">
                {{ featureCount === 0 ? 'No extended features captured for this flow' : `No features match "${featureSearch}"` }}
              </div>
            </div>
          </div>
        </div>

        <!-- 5. Threat Recurrence & IP History -->
        <div v-if="store.selectedForensics.ip_history?.length > 0" class="space-y-2">
          <div class="text-[11px] font-semibold uppercase tracking-wider text-zinc-400 flex items-center space-x-1.5">
            <Clock :size="13" class="text-zinc-500" />
            <span>Source IP Activity (Recent Flows)</span>
          </div>

          <div class="bg-zinc-900/80 border border-zinc-800/80 rounded-lg divide-y divide-zinc-800/50">
            <div
              v-for="h in store.selectedForensics.ip_history"
              :key="h.id"
              class="px-3.5 py-2.5 flex items-center justify-between text-[11px]"
            >
              <span class="text-zinc-400">Dst Port: <span class="text-zinc-200">{{ h.dst_port }}</span></span>
              <span class="font-semibold" :class="h.pred !== 'BENIGN' ? 'text-red-400' : 'text-zinc-400'">{{ h.pred }}</span>
              <span class="text-zinc-500 tabular-nums">RMSE: {{ formatScore(h.mse_ae) }}</span>
            </div>
          </div>
        </div>

        <!-- 6. Incident Triage Workflow Action -->
        <div v-if="store.selectedForensics.incident" class="space-y-2 pt-2 border-t border-zinc-800">
          <div class="flex items-center justify-between text-[11px] font-semibold uppercase tracking-wider text-zinc-400">
            <span>SOC Workflow Status:</span>
            <span class="px-2 py-0.5 rounded border text-[10px]" :class="statusPillClass(store.selectedForensics.incident.status)">
              {{ store.selectedForensics.incident.status }}
            </span>
          </div>

          <div class="grid grid-cols-3 gap-2">
            <button
              @click="updateStatus('INVESTIGATING')"
              :disabled="store.isUpdatingIncident"
              class="py-1.5 px-2 bg-amber-500/10 text-amber-300 border border-amber-500/30 hover:bg-amber-500/20 disabled:opacity-50 disabled:cursor-not-allowed rounded text-[11px] uppercase font-semibold transition flex items-center justify-center space-x-1"
            >
              <Loader2 v-if="store.isUpdatingIncident && targetStatus === 'INVESTIGATING'" :size="12" class="animate-spin" />
              <span>Investigate</span>
            </button>
            <button
              @click="updateStatus('RESOLVED')"
              :disabled="store.isUpdatingIncident"
              class="py-1.5 px-2 bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/20 disabled:opacity-50 disabled:cursor-not-allowed rounded text-[11px] uppercase font-semibold transition flex items-center justify-center space-x-1"
            >
              <Loader2 v-if="store.isUpdatingIncident && targetStatus === 'RESOLVED'" :size="12" class="animate-spin" />
              <span>Resolve</span>
            </button>
            <button
              @click="updateStatus('FALSE_POSITIVE')"
              :disabled="store.isUpdatingIncident"
              class="py-1.5 px-2 bg-zinc-800 text-zinc-400 border border-zinc-700 hover:text-zinc-200 disabled:opacity-50 disabled:cursor-not-allowed rounded text-[11px] uppercase font-semibold transition flex items-center justify-center space-x-1"
            >
              <Loader2 v-if="store.isUpdatingIncident && targetStatus === 'FALSE_POSITIVE'" :size="12" class="animate-spin" />
              <span>False Positive</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</div>
</template>

<script setup>
import { ref, computed } from "vue"
import { useSocStore } from "@/stores/socStore"
import { Terminal, X, Globe, Cpu, Search, FileText, Clock, Loader2, ChevronRight } from "lucide-vue-next"

const store = useSocStore()
const targetStatus = ref(null)
const showAllFeatures = ref(false)
const featureSearch = ref("")

const allFeaturesObj = computed(() => {
  return store.selectedForensics?.raw_metrics?.all_features || {}
})

const featureCount = computed(() => {
  return Object.keys(allFeaturesObj.value).length
})

const filteredFeatureList = computed(() => {
  const q = featureSearch.value.trim().toLowerCase()
  const entries = Object.entries(allFeaturesObj.value)
  if (!q) {
    return entries.map(([name, value]) => ({ name, value }))
  }
  return entries
    .filter(([name]) => name.toLowerCase().includes(q))
    .map(([name, value]) => ({ name, value }))
})

function statusPillClass(status) {
  switch (status) {
    case "OPEN":
      return "bg-red-500/10 text-red-400 border-red-500/30"
    case "INVESTIGATING":
      return "bg-amber-500/10 text-amber-400 border-amber-500/30"
    case "RESOLVED":
      return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
    default:
      return "bg-zinc-800 text-zinc-400 border-zinc-700"
  }
}

function formatNumber(num) {
  if (num === undefined || num === null || isNaN(num)) return "0"
  return Number(num).toLocaleString()
}

function formatDuration(val) {
  if (val === undefined || val === null || isNaN(val)) return "0 ms"
  const n = Number(val)
  if (n === 0) return "0 ms"
  if (n > 10000) {
    if (n < 1000000) return `${(n / 1000).toFixed(2)} ms`
    return `${(n / 1000000).toFixed(2)} s`
  }
  if (n < 0.001) return `${(n * 1000000).toFixed(0)} µs`
  if (n < 1.0) return `${(n * 1000).toFixed(1)} ms`
  return `${n.toFixed(2)} s`
}

function formatBytes(val) {
  if (val === undefined || val === null || isNaN(val)) return "0 B"
  const n = Number(val)
  if (n === 0) return "0 B"
  if (n < 1024) return `${n.toFixed(0)} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / (1024 * 1024)).toFixed(2)} MB`
}

function formatBytesPerSec(val) {
  if (val === undefined || val === null || isNaN(val)) return "0 B/s"
  const n = Number(val)
  if (n === 0) return "0 B/s"
  if (n < 1024) return `${n.toFixed(1)} B/s`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB/s`
  return `${(n / (1024 * 1024)).toFixed(2)} MB/s`
}

function formatRatio(val) {
  if (val === undefined || val === null || isNaN(val)) return "0.0"
  return Number(val).toFixed(2)
}

function formatScore(score) {
  if (score === undefined || score === null || isNaN(score)) return "0.000"
  return Number(score).toFixed(3)
}

function formatProto(p) {
  if (p === 6 || p === "6" || p === "TCP" || p === "tcp") return "TCP (Transmission Control Protocol)"
  if (p === 17 || p === "17" || p === "UDP" || p === "udp") return "UDP (User Datagram Protocol)"
  if (p === 1 || p === "1" || p === "ICMP" || p === "icmp") return "ICMP (Internet Control Message)"
  return p ? `IP Proto ${p}` : "TCP"
}

function severityBadgeClass(sev) {
  switch (sev) {
    case "CRITICAL":
      return "badge-critical"
    case "HIGH":
      return "badge-high"
    case "MEDIUM":
      return "badge-medium"
    case "LOW":
      return "badge-low"
    default:
      return "badge-benign"
  }
}

async function updateStatus(newStatus) {
  if (!store.selectedForensics?.incident?.id) return
  targetStatus.value = newStatus
  try {
    await store.changeIncidentStatus(
      store.selectedForensics.incident.id,
      newStatus,
      `Status updated to ${newStatus} via Forensics Drawer`
    )
    if (store.selectedForensics.incident) {
      store.selectedForensics.incident.status = newStatus
    }
  } finally {
    targetStatus.value = null
  }
}
</script>
