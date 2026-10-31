<template>
  <main>
    <div class="card alerts-header-card">
      <div class="header-titles">
        <h2 class="card-title">{{ store.t('alertsPage.title') }}</h2>
        <span class="card-subtitle">{{ store.t('alertsPage.subtitle') }}</span>
      </div>
      <p class="alerts-desc">
        {{ store.t('alertsPage.desc') }}
      </p>
    </div>

    <IncidentTable />
    <FlowDrawer />
  </main>
</template>

<script setup>
import { onMounted } from 'vue'
import { useSocStore } from '@/stores/socStore'
import IncidentTable from '@/components/dashboard/IncidentTable.vue'
import FlowDrawer from '@/components/dashboard/FlowDrawer.vue'

const store = useSocStore()

onMounted(() => {
  store.init()
})
</script>

<style scoped>
.alerts-header-card {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.header-titles {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.card-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.2px;
  color: #fff;
  line-height: 1.2;
}

.card-subtitle {
  font-size: 11.5px;
  font-weight: 400;
  color: var(--mu);
  line-height: 1.2;
}

.alerts-desc {
  color: var(--mu);
  margin: 0;
  font-size: 13px;
  line-height: 1.45;
}
</style>
