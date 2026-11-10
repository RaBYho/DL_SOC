<template>
  <div class="h-screen w-screen flex flex-col bg-[#09090B] text-zinc-100 overflow-hidden font-sans select-none">
    <!-- Critical Error Banner (Backend down or failed init) -->
    <div
      v-if="store.initError"
      class="bg-red-950/80 border-b border-red-800/80 px-4 py-2 flex items-center justify-between text-xs font-mono text-red-200 z-40 select-text"
    >
      <div class="flex items-center space-x-2">
        <AlertTriangle :size="14" class="text-red-400 flex-shrink-0" />
        <span>{{ store.initError }}</span>
      </div>
      <button
        @click="store.initialize()"
        class="px-2.5 py-0.5 bg-red-900/60 hover:bg-red-800 text-red-100 border border-red-700 rounded transition duration-100 font-semibold"
      >
        Retry Connection
      </button>
    </div>

    <!-- Offline / Reconnecting Strip -->
    <div
      v-else-if="!store.connected && !store.isLoading"
      class="bg-zinc-900/90 border-b border-zinc-800 px-4 py-1.5 flex items-center justify-between text-xs font-mono text-amber-300 z-40"
    >
      <div class="flex items-center space-x-2">
        <WifiOff :size="13" class="text-amber-400 flex-shrink-0" />
        <span>Live stream disconnected. Displaying cached telemetry while reconnecting...</span>
      </div>
      <button
        @click="store.reconnectWs()"
        class="px-2 py-0.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 rounded text-[11px] font-semibold transition duration-100"
      >
        Reconnect Now
      </button>
    </div>

    <!-- Top Status Bar (h-12) -->
    <TopStatusBar />

    <!-- Operational KPI Banner (h-auto) -->
    <KpiStrip />

    <!-- Central Split-View Area (Flex-1) -->
    <main class="flex-1 min-h-0 flex flex-col px-5 pb-5 gap-3.5">
      <!-- Upper Telemetry Split-View (Collapsible & Animated) -->
      <Transition name="collapse-charts">
        <section
          v-show="store.chartsVisible"
          class="grid grid-cols-1 lg:grid-cols-3 gap-3.5 h-52 flex-shrink-0"
        >
          <!-- 2 Cols: Timeline -->
          <div class="lg:col-span-2 h-full">
            <TrafficTimeline />
          </div>

          <!-- 1 Col: Engine Distribution -->
          <div class="h-full">
            <EngineDonut />
          </div>
        </section>
      </Transition>

      <!-- Lower Workhorse: Live Alert & Flow Triage Table -->
      <section class="flex-1 min-h-0 flex flex-col">
        <FlowTriageTable />
      </section>
    </main>

    <!-- Slide-Over Forensics Drawer -->
    <ForensicsDrawer />
  </div>
</template>

<script setup>
import { onMounted } from "vue"
import { useSocStore } from "@/stores/socStore"
import { AlertTriangle, WifiOff } from "lucide-vue-next"
import TopStatusBar from "@/components/TopStatusBar.vue"
import KpiStrip from "@/components/KpiStrip.vue"
import TrafficTimeline from "@/components/TrafficTimeline.vue"
import EngineDonut from "@/components/EngineDonut.vue"
import FlowTriageTable from "@/components/FlowTriageTable.vue"
import ForensicsDrawer from "@/components/ForensicsDrawer.vue"

const store = useSocStore()

onMounted(() => {
  store.initialize()
})
</script>
