import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'

const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: DashboardView
  },
  {
    path: '/alerts',
    name: 'alerts',
    component: () => import('@/views/AlertsView.vue')
  },
  {
    path: '/threat-intel',
    name: 'threat-intel',
    component: () => import('@/views/ThreatIntelView.vue')
  },
  {
    path: '/sensors',
    name: 'sensors',
    component: () => import('@/views/SensorsView.vue')
  },
  {
    path: '/models',
    name: 'models',
    component: () => import('@/views/ModelsView.vue')
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/views/SettingsView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
