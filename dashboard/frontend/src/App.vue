<template>
  <div class="app">
    <!-- Left Navigation Sidebar -->
    <Sidebar />

    <!-- Main Content Area -->
    <div class="ct">
      <Header />
      <router-view v-slot="{ Component, route }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" :key="route.path" />
        </transition>
      </router-view>
    </div>

    <!-- Mobile Bottom Navigation Bar (Phone viewports) -->
    <MobileBottomNav />

    <!-- Tiroir Latéral de Diagnostic Système & Infrastructure (Plan 1) -->
    <SystemHealthDrawer />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useSocStore } from '@/stores/socStore'
import Sidebar from '@/components/layout/Sidebar.vue'
import Header from '@/components/layout/Header.vue'
import MobileBottomNav from '@/components/layout/MobileBottomNav.vue'
import SystemHealthDrawer from '@/components/system/SystemHealthDrawer.vue'

const store = useSocStore()

onMounted(() => {
  store.init()
})
</script>

<style>
/* Page Transition: High-End Agency Fluid Navigation (Apple/Linear Easing) */
.page-fade-enter-active {
  transition: opacity 0.22s cubic-bezier(0.16, 1, 0.3, 1),
              transform 0.22s cubic-bezier(0.16, 1, 0.3, 1);
  will-change: opacity, transform;
}

.page-fade-leave-active {
  transition: opacity 0.14s cubic-bezier(0.4, 0, 1, 1),
              transform 0.14s cubic-bezier(0.4, 0, 1, 1);
  will-change: opacity, transform;
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@media (max-width: 900px) {
  .ct {
    padding-bottom: 64px; /* Space for MobileBottomNav */
  }
}

@media (prefers-reduced-motion: reduce) {
  .page-fade-enter-active,
  .page-fade-leave-active {
    transition: none !important;
  }
}
</style>
