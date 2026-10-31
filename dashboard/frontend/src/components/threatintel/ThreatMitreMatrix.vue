<template>
  <div class="card mitre-matrix-card">
    <div class="matrix-header">
      <div>
        <h3 class="section-title">Matrice Tactique MITRE ATT&amp;CK Enterprise</h3>
        <p class="section-subtitle">
          Cartographie des techniques adverses couvertes par les modèles NIDS (DNN-v4 + AE). Les techniques surlignées sont activement détectées dans votre trafic.
        </p>
      </div>

      <div class="matrix-legend">
        <span class="legend-item">
          <span class="legend-box active-in-soc"></span>
          <span>Détecté dans votre réseau</span>
        </span>
        <span class="legend-item">
          <span class="legend-box covered"></span>
          <span>Modèle IA opérationnel</span>
        </span>
      </div>
    </div>

    <!-- Grille des Colonnes Tactiques MITRE -->
    <div class="matrix-grid">
      <div 
        v-for="col in tacticColumns" 
        :key="col.tacticKey"
        class="tactic-column"
      >
        <div class="column-header">
          <span class="tactic-col-title">{{ col.tacticName }}</span>
          <span class="technique-count-pill">{{ col.threats.length }}</span>
        </div>

        <div class="techniques-list">
          <div 
            v-for="t in col.threats" 
            :key="t.id"
            class="technique-cell"
            :class="{ 
              'has-soc-alerts': (socDistributionMap[t.datasetLabel] || 0) > 0,
              ['sev-' + t.severity.toLowerCase()]: true
            }"
            @click="$emit('selectThreat', t)"
          >
            <div class="tech-cell-top">
              <code class="tech-code">{{ t.mitreId }}</code>
              <span class="tech-sev-dot" :class="'dot-' + t.severity.toLowerCase()"></span>
            </div>

            <b class="tech-name">{{ t.name }}</b>

            <div v-if="(socDistributionMap[t.datasetLabel] || 0) > 0" class="tech-active-badge">
              <span class="pulse-dot-red"></span>
              <span>{{ socDistributionMap[t.datasetLabel].toLocaleString() }} détection(s)</span>
            </div>
            <div v-else class="tech-passive-badge">
              <span>Supervisé</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  threats: {
    type: Array,
    default: () => []
  },
  socDistributionMap: {
    type: Object,
    default: () => ({})
  }
})

defineEmits(['selectThreat'])

const tacticsOrder = [
  { key: 'Discovery', name: '1. Reconnaissance (Discovery)' },
  { key: 'Initial Access', name: '2. Accès Initial (Initial Access)' },
  { key: 'Credential Access', name: '3. Accès Identifiants (Credentials)' },
  { key: 'Command and Control', name: '4. Command & Control (C2)' },
  { key: 'Impact', name: '5. Déni de Service (Impact)' },
  { key: 'Defense Evasion', name: '6. Évasion & 0-Day' }
]

const tacticColumns = computed(() => {
  return tacticsOrder.map(tact => {
    return {
      tacticKey: tact.key,
      tacticName: tact.name,
      threats: props.threats.filter(t => t.mitreTactic === tact.key)
    }
  })
})
</script>

<style scoped>
.mitre-matrix-card {
  padding: 18px 20px;
  background: #141524;
  border: 1px solid #24273d;
  border-radius: 14px;
  margin-bottom: 20px;
}

.matrix-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 18px;
  flex-wrap: wrap;
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

.matrix-legend {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 11px;
  color: #8b8ea8;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-box {
  width: 10px;
  height: 10px;
  border-radius: 3px;
}

.legend-box.active-in-soc {
  background: rgba(255, 77, 126, 0.4);
  border: 1px solid #ff4d7e;
  box-shadow: 0 0 6px rgba(255, 77, 126, 0.5);
}

.legend-box.covered {
  background: rgba(88, 101, 242, 0.2);
  border: 1px solid #5865f2;
}

/* Grille des colonnes */
.matrix-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 8px;
}

@media (max-width: 1280px) {
  .matrix-grid { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 768px) {
  .matrix-grid { grid-template-columns: 1fr; }
}

.tactic-column {
  background: #0f1019;
  border: 1px solid #202235;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  min-width: 170px;
}

.column-header {
  padding: 10px 12px;
  background: #171826;
  border-bottom: 1px solid #24263b;
  border-radius: 10px 10px 0 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tactic-col-title {
  font-size: 11px;
  font-weight: 700;
  color: #c4ccff;
}

.technique-count-pill {
  font-size: 10px;
  font-weight: 700;
  background: #25283f;
  color: #8fa0ff;
  padding: 1px 6px;
  border-radius: 999px;
}

.techniques-list {
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.technique-cell {
  background: #151624;
  border: 1px solid #262940;
  border-radius: 8px;
  padding: 10px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: all 0.2s;
}

.technique-cell:hover {
  background: #202338;
  border-color: #5865f2;
  transform: translateY(-1px);
}

.technique-cell.has-soc-alerts {
  background: rgba(255, 77, 126, 0.1);
  border-color: rgba(255, 77, 126, 0.45);
  box-shadow: 0 0 10px rgba(255, 77, 126, 0.15);
}

.tech-cell-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tech-code {
  font-size: 10.5px;
  font-weight: 700;
  color: #8fa0ff;
  background: rgba(88, 101, 242, 0.15);
  padding: 1px 5px;
  border-radius: 4px;
}

.tech-sev-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.dot-critical { background: #ff4d7e; }
.dot-high     { background: #ff7a45; }
.dot-medium   { background: #ffb547; }
.dot-info     { background: #3ddc97; }

.tech-name {
  font-size: 11.5px;
  color: #ffffff;
  line-height: 1.3;
}

.tech-active-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  font-weight: 700;
  color: #ff85a5;
  background: rgba(255, 77, 126, 0.18);
  padding: 2px 6px;
  border-radius: 4px;
}

.pulse-dot-red {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #ff4d7e;
  box-shadow: 0 0 6px #ff4d7e;
  animation: pulse-dot 1.2s infinite;
}

.tech-passive-badge {
  font-size: 9.5px;
  color: #7982a9;
  font-weight: 600;
}
</style>
