<template>
  <div class="obsidian-panel hover:border-zinc-700/80 transition duration-150 p-4 h-full flex flex-col">
    <div class="flex items-center justify-between pb-2.5 border-b border-zinc-800/80 mb-3">
      <div class="flex items-center space-x-2">
        <TrendingUp :size="14" class="text-zinc-400" />
        <span class="text-xs font-semibold uppercase tracking-wider text-zinc-300">Traffic & Threat Timeline</span>
        <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
      </div>
      <div class="flex items-center space-x-4 text-[11px] font-mono">
        <span class="flex items-center space-x-1.5">
          <span class="w-2 h-2 rounded-full bg-zinc-600"></span>
          <span class="text-zinc-400">Normal</span>
        </span>
        <span class="flex items-center space-x-1.5">
          <span class="w-2 h-2 rounded-full bg-red-400"></span>
          <span class="text-zinc-400">Attacks</span>
        </span>
        <span class="flex items-center space-x-1.5">
          <span class="w-2 h-2 rounded-full bg-amber-400"></span>
          <span class="text-zinc-400">Zero-Day</span>
        </span>
      </div>
    </div>

    <div class="flex-1 relative min-h-[160px]">
      <canvas ref="canvasRef"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from "vue"
import { useSocStore } from "@/stores/socStore"
import { TrendingUp } from "lucide-vue-next"
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Filler,
  Tooltip,
} from "chart.js"

Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Filler,
  Tooltip
)

const store = useSocStore()
const canvasRef = ref(null)
let chartInstance = null

function renderChart() {
  if (!canvasRef.value) return
  if (chartInstance) chartInstance.destroy()

  const labels = store.timeline.map((p) => p.label || "")
  const normalData = store.timeline.map((p) => p.normal || 0)
  const attackData = store.timeline.map((p) => p.attacks || 0)
  const anomalyData = store.timeline.map((p) => p.anomalies || 0)

  chartInstance = new Chart(canvasRef.value, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Attacks (Supervised)",
          data: attackData,
          borderColor: "#F87171",
          backgroundColor: "rgba(248, 113, 113, 0.15)",
          borderWidth: 1.5,
          tension: 0.2,
          pointRadius: 2,
          pointHoverRadius: 4,
          fill: true,
        },
        {
          label: "Zero-Day (Kitsune)",
          data: anomalyData,
          borderColor: "#FBBF24",
          backgroundColor: "rgba(251, 191, 36, 0.1)",
          borderWidth: 1.5,
          tension: 0.2,
          pointRadius: 2,
          pointHoverRadius: 4,
          fill: true,
        },
        {
          label: "Normal Traffic",
          data: normalData,
          borderColor: "#52525B",
          backgroundColor: "rgba(82, 82, 91, 0.08)",
          borderWidth: 1,
          tension: 0.2,
          pointRadius: 1,
          pointHoverRadius: 3,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 350,
        easing: "easeOutCubic",
      },
      transitions: {
        active: {
          animation: {
            duration: 150,
          },
        },
      },
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#18181B",
          borderColor: "#27272A",
          borderWidth: 1,
          titleFont: { family: "JetBrains Mono", size: 11 },
          bodyFont: { family: "JetBrains Mono", size: 11 },
          padding: 8,
          cornerRadius: 4,
        },
      },
      scales: {
        x: {
          grid: { color: "rgba(39, 39, 42, 0.5)" },
          ticks: { color: "#71717A", font: { family: "JetBrains Mono", size: 9 }, maxTicksLimit: 8 },
        },
        y: {
          beginAtZero: true,
          grid: { color: "rgba(39, 39, 42, 0.5)" },
          ticks: { color: "#71717A", font: { family: "JetBrains Mono", size: 9 }, precision: 0 },
        },
      },
    },
  })
}

function updateChart() {
  if (!canvasRef.value) return
  if (!chartInstance) {
    renderChart()
    return
  }

  const labels = store.timeline.map((p) => p.label || "")
  const normalData = store.timeline.map((p) => p.normal || 0)
  const attackData = store.timeline.map((p) => p.attacks || 0)
  const anomalyData = store.timeline.map((p) => p.anomalies || 0)

  // Only update labels if bucket keys have shifted to preserve CategoryScale continuity
  const currentLabels = chartInstance.data.labels || []
  const labelsChanged =
    currentLabels.length !== labels.length ||
    labels.some((l, idx) => l !== currentLabels[idx])

  if (labelsChanged) {
    chartInstance.data.labels = labels
  }

  chartInstance.data.datasets[0].data = attackData
  chartInstance.data.datasets[1].data = anomalyData
  chartInstance.data.datasets[2].data = normalData

  // Smooth easing update (350ms)
  chartInstance.update()
}

onMounted(() => {
  renderChart()
})

watch(
  () => store.timeline,
  () => {
    updateChart()
  },
  { deep: true }
)

onBeforeUnmount(() => {
  if (chartInstance) chartInstance.destroy()
})
</script>
