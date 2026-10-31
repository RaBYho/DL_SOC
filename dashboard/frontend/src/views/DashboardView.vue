<template>
  <main>
    <!-- KPIs Section -->
    <KpiCards />

    <!-- Visualizations Grid -->
    <section class="grid">
      <!-- Donut Attack Distribution -->
      <AttackDonut />

      <!-- Activity Timeline -->
      <TimelineChart />

      <!-- Anomaly MSE Gauge -->
      <AnomalyGauge />

      <!-- Threat Vectors (Top IPs & Ports) -->
      <ThreatVectors />

      <!-- Critical Incident Banner -->
      <CriticalBanner />
    </section>

    <!-- Incident Live Feed Table -->
    <IncidentTable />

    <!-- Drawer for Deep Flow Inspection -->
    <FlowDrawer />
  </main>
</template>

<script setup>
import { onMounted } from 'vue'
import { useSocStore } from '@/stores/socStore'

import KpiCards from '@/components/dashboard/KpiCards.vue'
import AttackDonut from '@/components/dashboard/AttackDonut.vue'
import TimelineChart from '@/components/dashboard/TimelineChart.vue'
import AnomalyGauge from '@/components/dashboard/AnomalyGauge.vue'
import ThreatVectors from '@/components/dashboard/ThreatVectors.vue'
import CriticalBanner from '@/components/dashboard/CriticalBanner.vue'
import IncidentTable from '@/components/dashboard/IncidentTable.vue'
import FlowDrawer from '@/components/dashboard/FlowDrawer.vue'

const store = useSocStore()

onMounted(() => {
  store.init()
})
</script>
