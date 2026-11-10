<template>
  <div class="obsidian-panel hover:border-zinc-700/80 transition duration-150 p-4 h-full flex flex-col">
    <div class="flex items-center justify-between pb-2.5 border-b border-zinc-800/80 mb-3">
      <div class="flex items-center space-x-2">
        <PieChart :size="14" class="text-zinc-400" />
        <span class="text-xs font-semibold uppercase tracking-wider text-zinc-300">Engine Distribution</span>
      </div>
      <span class="text-[10px] font-mono text-zinc-500 uppercase">Hybrid Pipeline</span>
    </div>

    <div class="flex-1 flex items-center justify-between px-2">
      <div class="w-32 h-32 relative flex-shrink-0">
        <canvas ref="donutRef"></canvas>
      </div>

      <!-- Legend -->
      <div class="flex-1 pl-6 space-y-2 text-xs font-mono">
        <div class="flex items-center justify-between hover:bg-zinc-800/40 px-2 py-1 rounded transition duration-100">
          <span class="flex items-center space-x-2">
            <span class="w-2 h-2 rounded-full bg-red-400"></span>
            <span class="text-zinc-400 text-[11px]">Supervised ML</span>
          </span>
          <span class="text-zinc-200 tabular-nums font-semibold">{{ mlCount }}</span>
        </div>

        <div class="flex items-center justify-between hover:bg-zinc-800/40 px-2 py-1 rounded transition duration-100">
          <span class="flex items-center space-x-2">
            <span class="w-2 h-2 rounded-full bg-sky-400"></span>
            <span class="text-zinc-400 text-[11px]">DPI Regex</span>
          </span>
          <span class="text-zinc-200 tabular-nums font-semibold">{{ dpiCount }}</span>
        </div>

        <div class="flex items-center justify-between hover:bg-zinc-800/40 px-2 py-1 rounded transition duration-100">
          <span class="flex items-center space-x-2">
            <span class="w-2 h-2 rounded-full bg-amber-400"></span>
            <span class="text-zinc-400 text-[11px]">Kitsune (0-Day)</span>
          </span>
          <span class="text-zinc-200 tabular-nums font-semibold">{{ kitsuneCount }}</span>
        </div>

        <div class="flex items-center justify-between hover:bg-zinc-800/40 px-2 py-1 rounded transition duration-100">
          <span class="flex items-center space-x-2">
            <span class="w-2 h-2 rounded-full bg-zinc-600"></span>
            <span class="text-zinc-400 text-[11px]">Benign Filter</span>
          </span>
          <span class="text-zinc-400 tabular-nums">{{ benignCount }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onBeforeUnmount } from "vue"
import { useSocStore } from "@/stores/socStore"
import { PieChart } from "lucide-vue-next"
import {
  Chart,
  DoughnutController,
  ArcElement,
  Tooltip,
} from "chart.js"

Chart.register(DoughnutController, ArcElement, Tooltip)

const store = useSocStore()
const donutRef = ref(null)
let chartInstance = null

// Handles both array or dict from backend
const mlCount = computed(() => {
  if (Array.isArray(store.engineDistribution)) {
    const item = store.engineDistribution.find((e) => e.engine?.includes("ML") || e.engine?.includes("Supervisé"))
    return item ? item.count : 0
  }
  return store.engineDistribution?.ml || 0
})

const dpiCount = computed(() => {
  if (Array.isArray(store.engineDistribution)) {
    const item = store.engineDistribution.find((e) => e.engine?.includes("DPI"))
    return item ? item.count : 0
  }
  return store.engineDistribution?.dpi || 0
})

const kitsuneCount = computed(() => {
  if (Array.isArray(store.engineDistribution)) {
    const item = store.engineDistribution.find((e) => e.engine?.includes("Kitsune") || e.engine?.includes("0-Day"))
    return item ? item.count : 0
  }
  return store.engineDistribution?.kitsune || 0
})

const benignCount = computed(() => {
  if (Array.isArray(store.engineDistribution)) {
    const item = store.engineDistribution.find((e) => e.engine?.includes("Benign") || e.engine?.includes("Filtrage"))
    return item ? item.count : 0
  }
  return store.engineDistribution?.benign || 0
})

function renderChart() {
  if (!donutRef.value) return
  if (chartInstance) chartInstance.destroy()

  const dataValues = [mlCount.value, dpiCount.value, kitsuneCount.value, benignCount.value]
  const allZero = dataValues.every((v) => v === 0)

  chartInstance = new Chart(donutRef.value, {
    type: "doughnut",
    data: {
      labels: ["Supervised ML", "DPI Regex", "Kitsune (0-Day)", "Benign Filter"],
      datasets: [
        {
          data: allZero ? [0, 0, 0, 1] : dataValues,
          backgroundColor: allZero
            ? ["#27272A", "#27272A", "#27272A", "#27272A"]
            : ["#F87171", "#38BDF8", "#FBBF24", "#52525B"],
          borderColor: "#09090B",
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "75%",
      animation: {
        animateRotate: false,
        animateScale: false,
        duration: 350,
        easing: "easeOutCubic",
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          enabled: !allZero,
          backgroundColor: "#18181B",
          borderColor: "#27272A",
          borderWidth: 1,
          bodyFont: { family: "JetBrains Mono", size: 11 },
          padding: 8,
          cornerRadius: 4,
        },
      },
    },
  })
}

function updateChart() {
  if (!donutRef.value) return
  if (!chartInstance) {
    renderChart()
    return
  }

  const dataValues = [mlCount.value, dpiCount.value, kitsuneCount.value, benignCount.value]
  const allZero = dataValues.every((v) => v === 0)

  chartInstance.data.datasets[0].data = allZero ? [0, 0, 0, 1] : dataValues
  chartInstance.data.datasets[0].backgroundColor = allZero
    ? ["#27272A", "#27272A", "#27272A", "#27272A"]
    : ["#F87171", "#38BDF8", "#FBBF24", "#52525B"]
  chartInstance.options.plugins.tooltip.enabled = !allZero
  chartInstance.update()
}

onMounted(() => {
  renderChart()
})

watch(
  () => [mlCount.value, dpiCount.value, kitsuneCount.value, benignCount.value, store.engineDistribution],
  () => {
    updateChart()
  },
  { deep: true }
)

onBeforeUnmount(() => {
  if (chartInstance) chartInstance.destroy()
})
</script>
