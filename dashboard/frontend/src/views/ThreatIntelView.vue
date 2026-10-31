<template>
  <main class="threat-intel-page">
    <!-- 1. En-tête de la Page & Statut Global -->
    <ThreatIntelHeader 
      :activeThreatsCount="activeThreatsInSocCount"
      :aeThreshold="store.aeThreshold"
    />

    <!-- 2. Bandeau des KPIs de Threat Intelligence -->
    <ThreatKpiStrip
      :totalThreatsCount="THREAT_KNOWLEDGE_BASE.length"
      :activeAttacksTotal="totalActiveAttacks"
      :globalThreatLevel="store.globalThreatLevel"
    />

    <!-- 3. Barre d'outils, Recherche & Filtres -->
    <ThreatFilterToolbar 
      v-model:searchQuery="searchQuery"
      v-model:selectedSeverity="selectedSeverity"
      v-model:selectedTactic="selectedTactic"
      v-model:socDetectedOnly="socDetectedOnly"
      v-model:activeView="activeView"
      :totalThreats="THREAT_KNOWLEDGE_BASE.length"
      :activeInSocCount="activeThreatsInSocCount"
      :countsBySeverity="countsBySeverity"
      :tactics="MITRE_TACTICS_LIST"
    />

    <!-- 4.A Vue 1 : Grille des Fiches de Menaces Détaillées -->
    <div v-if="activeView === 'cards'" class="threats-cards-grid">
      <ThreatCard
        v-for="threat in filteredThreats"
        :key="threat.id"
        :threat="threat"
        :detectedCount="getDetectedCount(threat)"
        :detectedPct="getDetectedPct(threat)"
        :associatedTopIp="getAssociatedTopIp(threat)"
        @openPlaybook="selectedPlaybookThreat = $event"
        @filterAlerts="navigateToAlertsWithFilter"
      />

      <!-- État vide si la recherche ne renvoie rien -->
      <div v-if="filteredThreats.length === 0" class="threats-empty-box">
        <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <h4>Aucune signature de menace ne correspond à vos filtres</h4>
        <p>Modifiez votre requête de recherche ou réinitialisez les sélecteurs de sévérité et de tactique.</p>
        <button type="button" class="btn-reset-filters" @click="resetFilters">
          Réinitialiser tous les filtres
        </button>
      </div>
    </div>

    <!-- 4.B Vue 2 : Matrice Tactique MITRE ATT&CK -->
    <div v-else class="mitre-matrix-view">
      <ThreatMitreMatrix
        :threats="filteredThreats"
        :socDistributionMap="socDistributionMap"
        @selectThreat="selectedPlaybookThreat = $event"
      />
    </div>

    <!-- 5. Modal Interactif de Remédiation & Playbook -->
    <ThreatPlaybookModal 
      v-if="selectedPlaybookThreat"
      :threat="selectedPlaybookThreat"
      @close="selectedPlaybookThreat = null"
      @filterAlerts="navigateToAlertsWithFilter"
    />
  </main>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSocStore } from '@/stores/socStore'

import { THREAT_KNOWLEDGE_BASE, MITRE_TACTICS_LIST } from '@/components/threatintel/threatData'
import ThreatIntelHeader from '@/components/threatintel/ThreatIntelHeader.vue'
import ThreatKpiStrip from '@/components/threatintel/ThreatKpiStrip.vue'
import ThreatFilterToolbar from '@/components/threatintel/ThreatFilterToolbar.vue'
import ThreatCard from '@/components/threatintel/ThreatCard.vue'
import ThreatMitreMatrix from '@/components/threatintel/ThreatMitreMatrix.vue'
import ThreatPlaybookModal from '@/components/threatintel/ThreatPlaybookModal.vue'

const router = useRouter()
const store = useSocStore()

// Filtres et Vues
const searchQuery = ref('')
const selectedSeverity = ref('ALL')
const selectedTactic = ref('ALL')
const socDetectedOnly = ref(false)
const activeView = ref('cards') // 'cards' ou 'matrix'
const selectedPlaybookThreat = ref(null)

// Dictionnaire de distribution des attaques actives dans le SOC
const socDistributionMap = computed(() => {
  const map = {}
  const dist = store.attackDistribution || []
  dist.forEach(item => {
    const key = item.label || item.name
    if (key) {
      map[key] = (map[key] || 0) + (item.count || 0)
    }
  })
  return map
})

// Décompte total d'alertes confirmées
const totalActiveAttacks = computed(() => {
  return store.kpis.attacks || 0
})

// Nombre de familles de menaces distinctes actuellement actives
const activeThreatsInSocCount = computed(() => {
  return Object.values(socDistributionMap.value).filter(c => c > 0).length
})

// Comptage par sévérité
const countsBySeverity = computed(() => {
  const counts = { Critical: 0, High: 0, Medium: 0, Info: 0 }
  THREAT_KNOWLEDGE_BASE.forEach(t => {
    if (counts[t.severity] !== undefined) {
      counts[t.severity]++
    }
  })
  return counts
})

// Calcul du nombre de détections pour une menace donnée
const getDetectedCount = (threat) => {
  // Vérifie le label exact ou ses alias
  let count = socDistributionMap.value[threat.datasetLabel] || 0
  if (!count && threat.aliases) {
    for (const a of threat.aliases) {
      if (socDistributionMap.value[a]) {
        count += socDistributionMap.value[a]
      }
    }
  }
  return count
}

// Calcul du pourcentage du trafic d'attaque
const getDetectedPct = (threat) => {
  const count = getDetectedCount(threat)
  if (!count || !totalActiveAttacks.value) return 0
  return Math.min(100, (count / totalActiveAttacks.value) * 100)
}

// Top IP attaquante associée à la menace si active
const getAssociatedTopIp = (threat) => {
  const count = getDetectedCount(threat)
  if (count > 0 && store.threatVectors?.top_source_ips?.length > 0) {
    return store.threatVectors.top_source_ips[0].ip || ''
  }
  return ''
}

// Filtrage multi-critères
const filteredThreats = computed(() => {
  let list = [...THREAT_KNOWLEDGE_BASE]

  // Filtre sévérité
  if (selectedSeverity.value !== 'ALL') {
    list = list.filter(t => t.severity === selectedSeverity.value)
  }

  // Filtre tactique MITRE
  if (selectedTactic.value !== 'ALL') {
    list = list.filter(t => t.mitreTactic === selectedTactic.value)
  }

  // Filtre uniquement les attaques actives dans le SOC
  if (socDetectedOnly.value) {
    list = list.filter(t => getDetectedCount(t) > 0)
  }

  // Recherche plein texte
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(t => 
      t.name.toLowerCase().includes(q) ||
      t.datasetLabel.toLowerCase().includes(q) ||
      t.mitreId.toLowerCase().includes(q) ||
      t.mitreName.toLowerCase().includes(q) ||
      t.mitreTactic.toLowerCase().includes(q) ||
      t.description.toLowerCase().includes(q) ||
      t.target.toLowerCase().includes(q) ||
      t.category.toLowerCase().includes(q)
    )
  }

  return list
})

const resetFilters = () => {
  searchQuery.value = ''
  selectedSeverity.value = 'ALL'
  selectedTactic.value = 'ALL'
  socDetectedOnly.value = false
}

const navigateToAlertsWithFilter = (attackClass) => {
  selectedPlaybookThreat.value = null
  store.filterCategory = attackClass
  store.filterSearch = attackClass
  router.push('/alerts')
}

onMounted(() => {
  store.init()
})
</script>

<style scoped>
.threat-intel-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Grille Responsive Multi-Colonnes des Fiches de Menaces */
.threats-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(480px, 1fr));
  gap: 16px;
}

@media (max-width: 640px) {
  .threats-cards-grid {
    grid-template-columns: 1fr;
  }
}

.threats-empty-box {
  grid-column: 1 / -1;
  text-align: center;
  padding: 48px 24px;
  background: #131422;
  border: 1px dashed #282a40;
  border-radius: 14px;
}

.empty-icon {
  width: 36px;
  height: 36px;
  color: #5865f2;
  margin-bottom: 12px;
}

.threats-empty-box h4 {
  margin: 0 0 6px;
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
}

.threats-empty-box p {
  margin: 0 0 16px;
  font-size: 12.5px;
  color: #8b8ea8;
}

.btn-reset-filters {
  height: 34px;
  padding: 0 16px;
  font-size: 12px;
  font-weight: 700;
  background: #25283f;
  color: #8fa0ff;
  border: 1px solid #3c4266;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-reset-filters:hover {
  background: #5865f2;
  color: #ffffff;
}
</style>
