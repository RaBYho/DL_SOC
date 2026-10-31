<template>
  <div class="app">
    <!-- Left Navigation Sidebar -->
    <Sidebar />

    <!-- Main Content Area -->
    <div class="ct">
      <Header />
      <router-view />
    </div>

    <!-- Mobile Bottom Navigation Bar (Phone viewports) -->
    <MobileBottomNav />
  </div>
</template>

<script setup>
import Sidebar from '@/components/layout/Sidebar.vue'
import Header from '@/components/layout/Header.vue'
import MobileBottomNav from '@/components/layout/MobileBottomNav.vue'
</script>

<style>
@media (max-width: 900px) {
  .ct {
    padding-bottom: 64px; /* Space for MobileBottomNav */
  }
}
</style>
