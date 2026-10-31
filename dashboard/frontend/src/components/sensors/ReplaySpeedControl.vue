<template>
  <div class="field-group">
    <div class="field-header">
      <label class="field-label">Vitesse d'Injection Réseau</label>
      <span class="rate-indicator">{{ (speed * 25).toFixed(0) }} flux/seconde estimés</span>
    </div>
    <div class="speed-segmented-control">
      <button 
        v-for="s in [0.5, 1.0, 2.0, 5.0, 10.0]" 
        :key="s"
        type="button"
        class="speed-btn"
        :class="{ active: speed === s }"
        :disabled="disabled"
        @click="$emit('update:speed', s)"
      >
        {{ s }}x
        <span v-if="s === 1.0" class="speed-badge-norm">Normal</span>
        <span v-else-if="s === 10.0" class="speed-badge-turbo">Turbo</span>
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  speed: {
    type: Number,
    default: 1.0
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

defineEmits(['update:speed'])
</script>

<style scoped>
.field-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.field-label {
  font-size: 12px;
  font-weight: 600;
  color: #c4ccff;
}

.rate-indicator {
  font-size: 11.5px;
  color: #8fa0ff;
  font-weight: 600;
}

.speed-segmented-control {
  display: flex;
  background: #121320;
  padding: 4px;
  border-radius: 10px;
  border: 1px solid #26283d;
  gap: 4px;
}

.speed-btn {
  flex: 1;
  height: 36px;
  background: transparent;
  border: none;
  border-radius: 7px;
  color: #8b8ea8;
  font-size: 12.5px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: all 0.2s;
}

.speed-btn:hover:not(:disabled) {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.05);
}

.speed-btn.active {
  background: #5865f2;
  color: #ffffff;
  box-shadow: 0 2px 10px rgba(88, 101, 242, 0.4);
}

.speed-badge-norm, .speed-badge-turbo {
  font-size: 9px;
  padding: 1px 4px;
  border-radius: 4px;
}

.speed-badge-norm { background: rgba(255, 255, 255, 0.2); }
.speed-badge-turbo { background: rgba(255, 77, 126, 0.3); color: #ff85a5; }
</style>
