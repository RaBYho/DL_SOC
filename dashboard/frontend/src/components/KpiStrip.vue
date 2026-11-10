<template>
  <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3.5 px-5 py-3">
    <!-- KPI 1: Total Flows Analyzed -->
    <div class="obsidian-panel obsidian-panel-interactive p-3.5 flex flex-col justify-between">
      <div class="flex items-center justify-between text-zinc-400">
        <span class="text-[11px] font-semibold uppercase tracking-wider">Total Network Flows</span>
        <Activity :size="14" class="text-zinc-500" />
      </div>
      <div v-if="store.isLoading" class="h-7 w-24 bg-zinc-800/60 rounded animate-pulse my-2"></div>
      <div v-else class="my-1.5">
        <span class="text-2xl font-bold font-mono tabular-nums text-zinc-100">
          {{ formatNumber(store.kpis.total_flows) }}
        </span>
      </div>
      <div class="pt-1.5 border-t border-zinc-800/50 flex items-center justify-between text-[11px] font-mono text-zinc-500">
        <span>Packets: {{ formatNumber(store.traffic.total_packets) }}</span>
        <span :class="store.excludeLoopback ? 'text-sky-400 font-medium' : 'text-zinc-500'">
          {{ store.excludeLoopback ? 'Clean (No 127.0.0.1)' : 'All Flows' }}
        </span>
      </div>
    </div>

    <!-- KPI 2: Top Offender / Criminal IP -->
    <div
      class="obsidian-panel obsidian-panel-interactive p-3.5 flex flex-col justify-between border-l-2 border-l-red-500"
      :class="store.kpis.top_attacker_ip !== '-' ? 'cursor-pointer hover:border-red-500/80 hover:bg-red-500/5' : ''"
      @click="store.kpis.top_attacker_ip !== '-' && store.filterByIp(store.kpis.top_attacker_ip)"
      title="Click to filter triage flows by this attacker IP"
    >
      <div class="flex items-center justify-between text-zinc-400">
        <span class="text-[11px] font-semibold uppercase tracking-wider text-red-400">Top Criminal IP</span>
        <Flame :size="14" class="text-red-400" />
      </div>
      <div v-if="store.isLoading" class="h-6 w-32 bg-zinc-800/60 rounded animate-pulse my-2"></div>
      <div v-else class="my-1.5 truncate">
        <span class="text-xl font-bold font-mono tabular-nums text-red-300 truncate">
          {{ store.kpis.top_attacker_ip || '-' }}
        </span>
      </div>
      <div class="pt-1.5 border-t border-zinc-800/50 flex items-center justify-between text-[11px] font-mono text-zinc-500 truncate">
        <span>Attacks: <span class="text-zinc-300 font-semibold">{{ store.kpis.top_attacker_attacks || 0 }}</span></span>
        <span class="text-red-400/90 truncate ml-1 font-medium">{{ store.kpis.top_attacker_threat || 'None' }}</span>
      </div>
    </div>

    <!-- KPI 3: Most Targeted Victim IP & Port -->
    <div class="obsidian-panel obsidian-panel-interactive p-3.5 flex flex-col justify-between border-l-2 border-l-orange-500 hover:border-orange-500/80 hover:bg-orange-500/5">
      <div class="flex items-center justify-between text-zinc-400">
        <span class="text-[11px] font-semibold uppercase tracking-wider text-orange-400">Target Victim & Port</span>
        <Target :size="14" class="text-orange-400" />
      </div>
      <div v-if="store.isLoading" class="h-6 w-28 bg-zinc-800/60 rounded animate-pulse my-2"></div>
      <div v-else class="my-1.5 truncate">
        <span class="text-lg font-bold font-mono tabular-nums text-orange-300 truncate">
          {{ store.kpis.top_targeted_ip || '-' }}:<span class="text-orange-400 font-extrabold">{{ store.kpis.top_targeted_port || '-' }}</span>
        </span>
      </div>
      <div class="pt-1.5 border-t border-zinc-800/50 flex items-center justify-between text-[11px] font-mono text-zinc-500">
        <span>Service: <span class="text-zinc-300 font-semibold">{{ store.kpis.top_targeted_service || '-' }}</span></span>
        <span class="text-orange-400/90 font-semibold">{{ store.targetedStats?.top_targeted_port_count || 0 }} hits</span>
      </div>
    </div>

    <!-- KPI 4: Critical Alerts & Zero-Days -->
    <div class="obsidian-panel obsidian-panel-interactive p-3.5 flex flex-col justify-between">
      <div class="flex items-center justify-between text-zinc-400">
        <span class="text-[11px] font-semibold uppercase tracking-wider">Critical & 0-Day</span>
        <ShieldAlert :size="14" class="text-red-400" />
      </div>
      <div v-if="store.isLoading" class="h-7 w-28 bg-zinc-800/60 rounded animate-pulse my-2"></div>
      <div v-else class="my-1.5 flex items-baseline space-x-2">
        <span class="text-2xl font-bold font-mono tabular-nums text-red-400">
          {{ formatNumber(store.kpis.critical_alerts) }}
        </span>
        <span class="text-xs font-mono text-amber-400 font-semibold">
          + {{ formatNumber(store.kpis.zero_days) }} 0-Day
        </span>
      </div>
      <div class="pt-1.5 border-t border-zinc-800/50 flex items-center justify-between text-[11px] font-mono text-zinc-500">
        <span>Threat Rate: <span class="text-zinc-300">{{ store.traffic.attack_ratio_pct }}%</span></span>
        <span class="text-zinc-400">Kitsune T3: {{ store.thresholds.t3 }}</span>
      </div>
    </div>

    <!-- KPI 5: Top Attack Vector & Inspection -->
    <div class="obsidian-panel obsidian-panel-interactive p-3.5 flex flex-col justify-between">
      <div class="flex items-center justify-between text-zinc-400">
        <span class="text-[11px] font-semibold uppercase tracking-wider">Top Vector & DPI</span>
        <Crosshair :size="14" class="text-zinc-500" />
      </div>
      <div v-if="store.isLoading" class="h-6 w-24 bg-zinc-800/60 rounded animate-pulse my-2"></div>
      <div v-else class="my-1.5 truncate">
        <span class="text-lg font-bold font-mono tabular-nums text-zinc-200 truncate" :title="store.kpis.top_vector">
          {{ store.kpis.top_vector || 'BENIGN' }}
        </span>
      </div>
      <div class="pt-1.5 border-t border-zinc-800/50 flex items-center justify-between text-[11px] font-mono text-zinc-500">
        <span>DPI Matches: <span class="text-zinc-300 font-semibold">{{ store.kpis.dpi_triggered }}</span></span>
        <span class="text-emerald-400 font-medium">{{ store.kpis.inspection_rate_pct }}% Deep</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useSocStore } from "@/stores/socStore"
import { Activity, ShieldAlert, Target, Crosshair, Flame } from "lucide-vue-next"

const store = useSocStore()

function formatNumber(num) {
  if (num === undefined || num === null) return "0"
  return Number(num).toLocaleString()
}
</script>
