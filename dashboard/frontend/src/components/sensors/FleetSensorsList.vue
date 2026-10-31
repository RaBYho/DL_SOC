<template>
  <div class="card fleet-list-card">
    <div class="fleet-list-header">
      <div>
        <div class="header-title-flex">
          <svg class="section-title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
            <rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>
            <line x1="6" y1="6" x2="6.01" y2="6"/>
            <line x1="6" y1="18" x2="6.01" y2="18"/>
          </svg>
          <h3 class="section-title">Parc de Sondes Actives &amp; Distantes</h3>
        </div>
        <p class="section-subtitle">
          Supervision des sondes matérielles, virtuelles et agents edge transmettant des flux au serveur NIDS.
        </p>
      </div>

      <!-- Filtres de Statut -->
      <div class="status-filter-pills">
        <button 
          type="button" 
          class="status-pill-btn" 
          :class="{ active: statusFilter === 'all' }"
          @click="statusFilter = 'all'"
        >
          Toutes ({{ sensors.length }})
        </button>
        <button 
          type="button" 
          class="status-pill-btn online" 
          :class="{ active: statusFilter === 'online' }"
          @click="statusFilter = 'online'"
        >
          <span class="pill-dot green"></span>
          En ligne ({{ onlineCount }})
        </button>
        <button 
          type="button" 
          class="status-pill-btn offline" 
          :class="{ active: statusFilter === 'offline' }"
          @click="statusFilter = 'offline'"
        >
          Inactives ({{ sensors.length - onlineCount }})
        </button>
      </div>
    </div>

    <!-- État vide animé avec radar -->
    <FleetRadarEmpty 
      v-if="filteredSensors.length === 0" 
      @switchTab="$emit('switchTab', 'replay')"
      @resetFilter="statusFilter = 'all'"
    />

    <!-- Liste des cartes de sondes -->
    <div v-else class="fleet-cards-grid">
      <FleetSensorCard 
        v-for="s in filteredSensors" 
        :key="s.id" 
        :sensor="s"
        @filterAlerts="$emit('filterAlerts', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import FleetRadarEmpty from './FleetRadarEmpty.vue'
import FleetSensorCard from './FleetSensorCard.vue'

const props = defineProps({
  sensors: {
    type: Array,
    default: () => []
  },
  onlineCount: {
    type: Number,
    default: 0
  }
})

defineEmits(['filterAlerts', 'switchTab'])

const statusFilter = ref('all')

const filteredSensors = computed(() => {
  let list = props.sensors || []
  if (statusFilter.value === 'online') {
    return list.filter(s => s.status === 'Online')
  }
  if (statusFilter.value === 'offline') {
    return list.filter(s => s.status !== 'Online')
  }
  return list
})
</script>

<style scoped>
.fleet-list-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 18px;
}

.header-title-flex {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title-icon {
  width: 18px;
  height: 18px;
  color: #8fa0ff;
}

.section-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.2px;
}

.section-subtitle {
  margin: 4px 0 0;
  font-size: 12px;
  color: #8b8ea8;
  line-height: 1.4;
}

.status-filter-pills {
  display: flex;
  gap: 6px;
  background: #121320;
  padding: 4px;
  border-radius: 9px;
  border: 1px solid #282a40;
}

.status-pill-btn {
  height: 28px;
  padding: 0 10px;
  border-radius: 6px;
  background: transparent;
  border: none;
  font-size: 11px;
  font-weight: 600;
  color: #8b8ea8;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.status-pill-btn:hover { color: #ffffff; }
.status-pill-btn.active { background: #25283f; color: #ffffff; }
.status-pill-btn.online.active { background: rgba(61, 220, 151, 0.2); color: #3ddc97; }
.status-pill-btn.offline.active { background: rgba(99, 107, 142, 0.3); color: #c4ccff; }

.pill-dot { width: 6px; height: 6px; border-radius: 50%; }
.pill-dot.green { background: #3ddc97; box-shadow: 0 0 6px #3ddc97; }

.fleet-cards-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
