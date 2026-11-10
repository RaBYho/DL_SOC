<template>
  <header class="h-13 border-b border-zinc-800/80 bg-zinc-950 px-5 flex items-center justify-between sticky top-0 z-30 select-none">
    <!-- Left: Brand & Engine Health -->
    <div class="flex items-center space-x-5">
      <div class="flex items-center space-x-2.5">
        <span
          class="w-2.5 h-2.5 rounded-full"
          :class="store.isLoading ? 'bg-amber-400 animate-pulse' : store.connected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'"
          :title="store.isLoading ? 'Connecting to backend...' : store.connected ? 'Connected to live stream' : 'Disconnected from backend'"
        ></span>
        <span class="text-xs font-bold tracking-wider text-zinc-100 uppercase">NIDS SOC</span>
        <span class="text-[10px] font-mono text-zinc-500 uppercase px-1.5 py-0.5 rounded border border-zinc-800 bg-zinc-900">v1.0-Cascaded</span>
      </div>

      <div class="h-4 w-px bg-zinc-800"></div>

      <!-- Sensor / Live Interface telemetry -->
      <div class="flex items-center space-x-4 text-xs font-mono text-zinc-400">
        <div class="flex items-center space-x-1.5">
          <Wifi :size="13" class="text-zinc-500" />
          <span class="text-zinc-300 font-medium">{{ store.activeSensor?.interface || 'enx3ecd36af7cdb' }}</span>
        </div>

        <div class="flex items-center space-x-1.5">
          <Activity :size="13" class="text-zinc-500" />
          <span class="text-zinc-200 tabular-nums font-semibold">{{ store.traffic.throughput_flows_sec }}</span>
          <span class="text-zinc-500 text-[10px]">fps</span>
        </div>

        <div class="hidden md:flex items-center space-x-2">
          <Cpu :size="13" class="text-zinc-500" />
          <span class="text-zinc-400">T1:</span>
          <span class="text-zinc-200 tabular-nums font-medium">{{ store.thresholds.t1 }}</span>
          <span class="text-zinc-600">|</span>
          <span class="text-zinc-400">T2:</span>
          <span class="text-zinc-200 tabular-nums font-medium">{{ store.thresholds.t2 }}</span>
          <span class="text-zinc-600">|</span>
          <span class="text-zinc-400">T3:</span>
          <span class="text-zinc-200 tabular-nums font-medium">{{ store.thresholds.t3 }}</span>
        </div>
      </div>
    </div>

    <!-- Center: Global Quick Filter -->
    <div class="flex-1 max-w-md mx-6 hidden lg:block">
      <div class="relative flex items-center">
        <Search :size="14" class="absolute left-3 text-zinc-500 pointer-events-none" />
        <input
          v-model="store.searchQuery"
          type="text"
          placeholder="Filter by IP, Port, Rule (e.g. 192.168.1.105, PortScan)..."
          class="w-full bg-zinc-900/80 border border-zinc-800 rounded px-3 py-1.5 pl-9 text-xs font-mono text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-zinc-700 transition duration-150"
        />
        <button
          v-if="store.searchQuery"
          @click="store.searchQuery = ''"
          class="absolute right-2.5 text-zinc-500 hover:text-zinc-300 text-xs cursor-pointer"
        >
          ✕
        </button>
      </div>
    </div>

    <!-- Right: Stream Controls & Action -->
    <div class="flex items-center space-x-2.5">
      <!-- Group 1: Ergonomics & Views -->
      <div class="flex items-center space-x-1.5">
        <!-- Collapsible Charts Toggle -->
        <button
          @click="store.toggleCharts"
          class="hidden sm:flex items-center space-x-1.5 px-2.5 py-1 text-xs font-mono rounded border transition duration-150 cursor-pointer"
          :class="store.chartsVisible ? 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/80' : 'bg-sky-500/10 border-sky-500/30 text-sky-400'"
          :title="store.chartsVisible ? 'Hide telemetry charts to maximize triage height' : 'Show telemetry charts'"
        >
          <BarChart2 :size="12" />
          <span class="text-[10px] font-semibold uppercase">{{ store.chartsVisible ? 'Charts: On' : 'Charts: Off' }}</span>
        </button>

        <!-- Table Density Toggle -->
        <button
          @click="store.toggleDensity"
          class="hidden md:flex items-center space-x-1.5 px-2.5 py-1 text-xs font-mono rounded border transition duration-150 cursor-pointer"
          :class="store.tableDensity === 'compact' ? 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/80' : 'bg-zinc-800 text-zinc-200 border-zinc-700'"
          :title="store.tableDensity === 'compact' ? 'Row Density: Compact (click to switch to Normal)' : 'Row Density: Normal (click to switch to Compact)'"
        >
          <Rows :size="12" />
          <span class="text-[10px] font-semibold uppercase">{{ store.tableDensity }}</span>
        </button>
      </div>

      <div class="h-4 w-px bg-zinc-800 hidden sm:block"></div>

      <!-- Group 2: Noise Filter & Status -->
      <div class="flex items-center space-x-2">
        <!-- 127.0.0.1 Loopback Noise Toggle -->
        <button
          @click="store.toggleLoopbackFilter"
          class="flex items-center space-x-1.5 px-2.5 py-1 text-xs font-mono rounded border transition duration-150 cursor-pointer"
          :class="store.excludeLoopback ? 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/80' : 'bg-amber-500/10 border-amber-500/30 text-amber-400 hover:bg-amber-500/20'"
          :title="store.excludeLoopback ? 'Loopback (127.0.0.1) noise is hidden. Click to show.' : 'Loopback (127.0.0.1) noise is visible. Click to filter.'"
        >
          <Filter :size="12" />
          <span class="text-[10px] font-semibold uppercase">{{ store.excludeLoopback ? '127.0.0.1 OFF' : '127.0.0.1 ON' }}</span>
        </button>

        <!-- Status Badge -->
        <span
          class="text-[11px] font-mono px-2 py-0.5 rounded border uppercase font-medium"
          :class="statusBadgeClasses"
        >
          {{ store.traffic.status }}
        </span>
      </div>

      <div class="h-4 w-px bg-zinc-800"></div>

      <!-- Group 3: Stream & DB Actions -->
      <div class="flex items-center space-x-1.5">
        <!-- Pause / Resume Stream -->
        <button
          @click="store.togglePause"
          class="flex items-center space-x-1.5 px-3 py-1 text-xs font-medium rounded border transition duration-150 cursor-pointer"
          :class="store.streamPaused ? 'bg-amber-500/10 text-amber-300 border-amber-500/30 hover:bg-amber-500/20' : 'bg-zinc-900 border-zinc-800 text-zinc-300 hover:bg-zinc-800/80'"
          :title="store.streamPaused ? 'Resume live stream updates' : 'Pause live stream updates'"
        >
          <Play v-if="store.streamPaused" :size="12" />
          <Pause v-else :size="12" />
          <span class="text-[11px] font-mono">{{ store.streamPaused ? 'PAUSED' : 'LIVE' }}</span>
        </button>

        <!-- Clear / Reset DB (Busy state handled) -->
        <button
          @click="confirmClear"
          :disabled="store.isPurging"
          class="p-1.5 text-zinc-400 hover:text-red-400 bg-zinc-900 border border-zinc-800 hover:border-red-900/40 rounded transition duration-150 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          :title="store.isPurging ? 'Purging database...' : 'Purge database logs and reset statistics'"
        >
          <Loader2 v-if="store.isPurging" :size="13" class="animate-spin text-red-400" />
          <Trash2 v-else :size="13" />
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from "vue"
import { useSocStore } from "@/stores/socStore"
import { Activity, Pause, Play, Search, Trash2, Wifi, Cpu, Filter, Loader2, BarChart2, Rows } from "lucide-vue-next"

const store = useSocStore()

const statusBadgeClasses = computed(() => {
  switch (store.traffic.status) {
    case "CRITICAL":
      return "bg-red-500/10 text-red-400 border-red-500/30"
    case "ELEVATED":
      return "bg-amber-500/10 text-amber-400 border-amber-500/30"
    default:
      return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
  }
})

function confirmClear() {
  if (window.confirm("Purge all recorded flows, incidents, and statistics from the database?")) {
    store.clearAllData()
  }
}
</script>
