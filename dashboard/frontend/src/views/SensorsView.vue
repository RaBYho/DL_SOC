<template>
  <main>
    <!-- En-tête Principal & Navigation par Onglets -->
    <SensorsHeader 
      v-model:active-tab="activeTab"
      :sensors-online="store.sensorsOnline"
      :sensors-count="store.sensorsList.length"
      :replay-status="store.replayStatus"
      :is-refreshing="isRefreshing"
      @refresh="handleManualRefresh"
    />

    <!-- Onglet 1 : Simulateur & Rejeu PCAP (Laboratoire) -->
    <div v-if="activeTab === 'replay'" class="tab-pane">
      <div class="grid">
        <ReplayControlPanel
          class="c6"
          v-model:selectedPcap="selectedPcap"
          v-model:replaySpeed="replaySpeed"
          :selectedPcapMeta="selectedPcapMeta"
          :pcapFiles="store.pcapFiles"
          :replayStatus="store.replayStatus"
          :totalAttacks="store.kpis.attacks"
          @start="startReplay"
          @pause="pauseReplay"
          @resume="resumeReplay"
          @stop="stopReplay"
        />

        <ReplayScenarioCatalog
          class="c6"
          :pcapFiles="store.pcapFiles"
          :selectedPcap="selectedPcap"
          :isRunning="store.replayStatus.active"
          :activePcapName="store.replayStatus.pcap_name"
          @select="selectScenario"
        />
      </div>
    </div>

    <!-- Onglet 2 : Parc de Sondes Réseau (Supervision Edge & Agents Réels) -->
    <div v-else class="tab-pane fleet-tab-pane">
      <FleetKpiStrip
        :sensorsCount="store.sensorsList.length"
        :sensorsOnline="store.sensorsOnline"
        :totalFlows="totalFleetFlows"
        :totalAttacks="totalFleetAttacks"
      />

      <div class="grid">
        <FleetSensorsList
          class="c7"
          :sensors="store.sensorsList"
          :onlineCount="store.sensorsOnline"
          @filterAlerts="filterAlertsBySensor"
          @switchTab="activeTab = $event"
        />

        <FleetDeployHub class="c5" />
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSocStore } from '@/stores/socStore'

import SensorsHeader from '@/components/sensors/SensorsHeader.vue'
import FleetKpiStrip from '@/components/sensors/FleetKpiStrip.vue'
import FleetSensorsList from '@/components/sensors/FleetSensorsList.vue'
import FleetDeployHub from '@/components/sensors/FleetDeployHub.vue'
import ReplayControlPanel from '@/components/sensors/ReplayControlPanel.vue'
import ReplayScenarioCatalog from '@/components/sensors/ReplayScenarioCatalog.vue'

const router = useRouter()
const store = useSocStore()

const activeTab = ref('replay')
const selectedPcap = ref('')
const replaySpeed = ref(1.0)
const isRefreshing = ref(false)

const selectedPcapMeta = computed(() => {
  if (!selectedPcap.value) return null
  return (store.pcapFiles || []).find(p => p.filename === selectedPcap.value) || null
})

const totalFleetFlows = computed(() => {
  return (store.sensorsList || []).reduce((acc, s) => acc + (s.total_flows || 0), 0)
})

const totalFleetAttacks = computed(() => {
  return (store.sensorsList || []).reduce((acc, s) => acc + (s.total_attacks || 0), 0)
})

const selectScenario = (filename) => {
  if (store.replayStatus.active) return
  selectedPcap.value = filename
}

const startReplay = async () => {
  if (!selectedPcap.value) return
  await store.startPcapReplay(selectedPcap.value, replaySpeed.value)
}

const pauseReplay = async () => {
  await store.pausePcapReplay()
}

const resumeReplay = async () => {
  await store.resumePcapReplay()
}

const stopReplay = async () => {
  await store.stopPcapReplay()
}

const handleManualRefresh = async () => {
  isRefreshing.value = true
  try {
    await store.fetchSensors()
    await store.fetchPcapFiles()
  } finally {
    setTimeout(() => {
      isRefreshing.value = false
    }, 400)
  }
}

const filterAlertsBySensor = (sensorId) => {
  store.filterSearch = sensorId
  router.push('/alerts')
}

onMounted(async () => {
  await store.fetchSensors()
  await store.fetchPcapFiles()
  if (!selectedPcap.value && store.pcapFiles && store.pcapFiles.length > 0) {
    selectedPcap.value = store.pcapFiles[0].filename
  }
})
</script>
