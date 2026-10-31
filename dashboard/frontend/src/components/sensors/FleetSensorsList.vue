<template>
  <div class="card fleet-list-card">
    <div class="fleet-list-header">
      <div class="header-titles-wrap">
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

      <!-- Barre d'outils et Actions -->
      <div class="header-toolbar-actions">
        <!-- Recherche interne -->
        <div class="sensor-search-box">
          <svg class="search-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input 
            v-model="searchQuery" 
            type="text" 
            placeholder="Filtrer (nom, ip, type)..." 
            class="sensor-search-input"
          />
          <span v-if="searchQuery" class="clear-search-btn" @click="searchQuery = ''">✕</span>
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

        <!-- Bouton Déployer un agent -->
        <button 
          type="button" 
          class="btn-deploy-toggle"
          :class="{ 'is-open': isDeployOpen }"
          @click="$emit('toggleDeploy')"
          title="Afficher les commandes de déploiement d'une nouvelle sonde"
        >
          <svg class="deploy-btn-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="12 2 19 21 12 17 5 21 12 2"/>
          </svg>
          <span>{{ isDeployOpen ? 'Fermer le guide' : 'Déployer une sonde' }}</span>
        </button>
      </div>
    </div>

    <!-- État vide animé avec radar -->
    <FleetRadarEmpty 
      v-if="filteredSensors.length === 0" 
      @switchTab="$emit('switchTab', 'replay')"
      @resetFilter="resetFilters"
      @deploy="$emit('toggleDeploy')"
    />

    <!-- Grille Responsive des Cartes de Sondes -->
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
  },
  isDeployOpen: {
    type: Boolean,
    default: false
  }
})

defineEmits(['filterAlerts', 'switchTab', 'toggleDeploy'])

const statusFilter = ref('all')
const searchQuery = ref('')

const resetFilters = () => {
  statusFilter.value = 'all'
  searchQuery.value = ''
}

const filteredSensors = computed(() => {
  let list = props.sensors || []
  if (statusFilter.value === 'online') {
    list = list.filter(s => s.status === 'Online')
  } else if (statusFilter.value === 'offline') {
    list = list.filter(s => s.status !== 'Online')
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(s => 
      (s.name || '').toLowerCase().includes(q) ||
      (s.id || '').toLowerCase().includes(q) ||
      (s.interface || '').toLowerCase().includes(q) ||
      (s.type || '').toLowerCase().includes(q)
    )
  }
  return list
})
</script>

<style scoped>
.fleet-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.header-titles-wrap {
  flex: 1;
  min-width: 260px;
}

.header-title-flex {
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-title-icon {
  width: 20px;
  height: 20px;
  color: #8fa0ff;
  flex-shrink: 0;
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

.header-toolbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

/* Recherche interne */
.sensor-search-box {
  position: relative;
  width: 190px;
}

.search-svg {
  position: absolute;
  left: 9px;
  top: 50%;
  transform: translateY(-50%);
  width: 13px;
  height: 13px;
  color: #7982a9;
  pointer-events: none;
}

.sensor-search-input {
  width: 100%;
  height: 32px;
  padding: 0 24px 0 28px;
  background: #11121d;
  border: 1px solid #282a40;
  border-radius: 8px;
  color: #ffffff;
  font-size: 11.5px;
  outline: none;
  transition: all 0.2s;
}

.sensor-search-input:focus {
  border-color: #5865f2;
  box-shadow: 0 0 0 2px rgba(88, 101, 242, 0.2);
}

.clear-search-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  color: #7982a9;
  font-size: 11px;
  cursor: pointer;
}

.clear-search-btn:hover {
  color: #ffffff;
}

/* Filtres de statut */
.status-filter-pills {
  display: flex;
  gap: 4px;
  background: #121320;
  padding: 3px;
  border-radius: 9px;
  border: 1px solid #282a40;
}

.status-pill-btn {
  height: 26px;
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

/* Bouton Déployer */
.btn-deploy-toggle {
  height: 32px;
  padding: 0 12px;
  font-size: 11.5px;
  font-weight: 700;
  border-radius: 8px;
  background: rgba(88, 101, 242, 0.15);
  border: 1px solid rgba(88, 101, 242, 0.35);
  color: #8fa0ff;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.btn-deploy-toggle:hover {
  background: #5865f2;
  color: #ffffff;
  border-color: #5865f2;
  box-shadow: 0 2px 10px rgba(88, 101, 242, 0.35);
}

.btn-deploy-toggle.is-open {
  background: rgba(255, 77, 126, 0.15);
  border-color: rgba(255, 77, 126, 0.35);
  color: #ff4d7e;
}

.btn-deploy-toggle.is-open:hover {
  background: #ff4d7e;
  color: #ffffff;
  border-color: #ff4d7e;
  box-shadow: 0 2px 10px rgba(255, 77, 126, 0.35);
}

.deploy-btn-svg {
  width: 13px;
  height: 13px;
}

/* Grille Responsive des Cartes de Sondes */
.fleet-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(460px, 1fr));
  gap: 16px;
}

@media (max-width: 640px) {
  .fleet-cards-grid {
    grid-template-columns: 1fr;
  }
}
</style>
