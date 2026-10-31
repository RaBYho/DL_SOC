<template>
  <main>
    <div class="card" style="margin-bottom: 16px;">
      <h2>
        Incident Investigation &amp; Historical Alerts
        <span>Full SQLite telemetry record search</span>
      </h2>
      <p style="color:var(--mu); margin: 0 0 12px; font-size: 13px;">
        Filter, investigate, and analyze detected attack vectors and zero-day deviations across all network sensors.
      </p>
    </div>

    <IncidentTable />
    <FlowDrawer />
  </main>
</template>

<script setup>
import IncidentTable from '@/components/dashboard/IncidentTable.vue'
import FlowDrawer from '@/components/dashboard/FlowDrawer.vue'
</script>
