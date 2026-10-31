<template>
  <div v-if="scenario" class="scenario-meta-card">
    <div class="scenario-meta-header">
      <div class="scenario-meta-title">
        <span class="scenario-bullet"></span>
        <b>{{ scenario.title }}</b>
      </div>
      <span class="sev-tag" :class="scenario.severity">{{ scenario.category }}</span>
    </div>
    <p class="scenario-desc">{{ scenario.description }}</p>
    <div class="scenario-chips">
      <div class="chip">
        <span class="chip-label">Fichier :</span>
        <code class="chip-val">{{ scenario.filename }}</code>
      </div>
      <div class="chip">
        <span class="chip-label">Taille :</span>
        <b class="chip-val">{{ scenario.size_mb }} Mo</b>
      </div>
      <div class="chip">
        <span class="chip-label">Niveau d'impact :</span>
        <b class="chip-val" :class="'text-' + (scenario.severity || 'Medium').toLowerCase()">{{ scenario.severity }}</b>
      </div>
    </div>
  </div>
  <div v-else class="scenario-empty-placeholder">
    <svg class="placeholder-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
    </svg>
    <span>Sélectionnez un scénario dans le catalogue pour afficher les détails et configurer le rejeu.</span>
  </div>
</template>

<script setup>
defineProps({
  scenario: {
    type: Object,
    default: null
  }
})
</script>

<style scoped>
.scenario-meta-card {
  background: #131422;
  border: 1px solid #282a40;
  border-left: 3px solid #5865f2;
  border-radius: 10px;
  padding: 14px;
}

.scenario-meta-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.scenario-meta-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13.5px;
  color: #ffffff;
}

.scenario-bullet {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #5865f2;
}

.scenario-desc {
  font-size: 12.5px;
  color: #9aa5ce;
  margin: 0 0 12px;
  line-height: 1.45;
}

.scenario-chips {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
  background: rgba(255, 255, 255, 0.04);
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.chip-label { color: #7982a9; }
.chip-val { color: #ffffff; }

.sev-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 5px;
  text-transform: uppercase;
}

.sev-tag.Critical { background: rgba(255, 77, 126, 0.2); color: #ff4d7e; border: 1px solid rgba(255, 77, 126, 0.4); }
.sev-tag.High     { background: rgba(255, 122, 69, 0.2); color: #ff7a45; border: 1px solid rgba(255, 122, 69, 0.4); }
.sev-tag.Medium   { background: rgba(255, 181, 71, 0.2); color: #ffb547; border: 1px solid rgba(255, 181, 71, 0.4); }
.sev-tag.Info     { background: rgba(61, 220, 151, 0.2); color: #3ddc97; border: 1px solid rgba(61, 220, 151, 0.4); }

.text-critical { color: #ff4d7e !important; }
.text-high     { color: #ff7a45 !important; }
.text-medium   { color: #ffb547 !important; }
.text-info     { color: #3ddc97 !important; }

.scenario-empty-placeholder {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #11121d;
  border: 1px dashed #282a40;
  border-radius: 10px;
  padding: 16px;
  font-size: 12px;
  color: #8b8ea8;
  line-height: 1.4;
}

.placeholder-icon {
  width: 22px;
  height: 22px;
  color: #5865f2;
  flex-shrink: 0;
}
</style>
