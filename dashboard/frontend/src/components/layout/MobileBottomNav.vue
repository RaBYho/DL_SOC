<template>
  <nav class="mobile-bottom-nav" aria-label="Mobile Navigation">
    <router-link to="/" class="mob-tab" :class="{ active: $route.path === '/' }">
      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8">
        <rect x="3" y="3" width="6" height="6" rx="1.5" />
        <rect x="11" y="3" width="6" height="6" rx="1.5" />
        <rect x="3" y="11" width="6" height="6" rx="1.5" />
        <rect x="11" y="11" width="6" height="6" rx="1.5" />
      </svg>
      <span>{{ store.t('nav.dashboard') }}</span>
    </router-link>

    <router-link to="/alerts" class="mob-tab" :class="{ active: $route.path === '/alerts' }">
      <div class="icon-with-badge">
        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M10 2L3 17h14L10 2z" />
          <path d="M10 8v4" />
        </svg>
        <span v-if="incidentCount > 0" class="mob-badge">{{ incidentCount > 99 ? '99+' : incidentCount }}</span>
      </div>
      <span>{{ store.t('nav.alerts') }}</span>
    </router-link>

    <router-link to="/sensors" class="mob-tab" :class="{ active: $route.path === '/sensors' }">
      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8">
        <rect x="2" y="3" width="16" height="5" rx="1.5" />
        <rect x="2" y="12" width="16" height="5" rx="1.5" />
      </svg>
      <span>{{ store.t('nav.sensors') }}</span>
    </router-link>

    <button class="mob-tab" @click="store.toggleMobileNav">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="3" y1="6" x2="21" y2="6" />
        <line x1="3" y1="12" x2="21" y2="12" />
        <line x1="3" y1="18" x2="21" y2="18" />
      </svg>
      <span>{{ store.t('nav.more') }}</span>
    </button>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useSocStore } from '@/stores/socStore'

const store = useSocStore()

const incidentCount = computed(() => {
  return store.totalDbIncidents || store.incidents.length || store.openIncidentsCount || 0
})
</script>

<style scoped>
.mobile-bottom-nav {
  display: none;
}

@media (max-width: 900px) {
  .mobile-bottom-nav {
    display: flex;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 56px;
    background: rgba(21, 22, 34, 0.96);
    backdrop-filter: blur(20px);
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    z-index: 100;
    justify-content: space-around;
    align-items: center;
    padding-bottom: env(safe-area-inset-bottom, 0px);
    box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.4);
  }

  .mob-tab {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 3px;
    height: 100%;
    background: none;
    border: 0;
    color: var(--mu);
    text-decoration: none;
    font-size: 10px;
    font-weight: 600;
    cursor: pointer;
    transition: color 0.15s ease;
  }

  .mob-tab svg {
    width: 20px;
    height: 20px;
  }

  .mob-tab.active {
    color: var(--ac);
  }

  .icon-with-badge {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .mob-badge {
    position: absolute;
    top: -5px;
    right: -10px;
    background: var(--cr);
    color: #fff;
    font-size: 9px;
    font-weight: 800;
    padding: 1px 4px;
    border-radius: 8px;
    line-height: 1;
  }
}
</style>
