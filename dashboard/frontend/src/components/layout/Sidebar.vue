<template>
  <!-- Mobile Backdrop Overlay -->
  <div 
    v-if="store.mobileNavOpen" 
    class="sidebar-backdrop" 
    @click="store.closeMobileNav"
    aria-hidden="true"
  ></div>

  <nav 
    class="side" 
    :class="{ 'mobile-open': store.mobileNavOpen }" 
    aria-label="Main Navigation"
  >
    <!-- Brand Logo & Mobile Close Button -->
    <div class="sidebar-top-row">
      <router-link to="/" class="logo" @click="store.closeMobileNav">
        <div class="logo-icon-wrapper">
          <svg class="soc-logo-svg" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#5865f2" />
                <stop offset="100%" stop-color="#9b5cf6" />
              </linearGradient>
              <linearGradient id="shieldBorder" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#8a98ff" />
                <stop offset="100%" stop-color="#d08eff" />
              </linearGradient>
            </defs>
            <path d="M16 2L28 8V16C28 23.5 22.8 28.5 16 30C9.2 28.5 4 23.5 4 16V8L16 2Z" fill="url(#logoGrad)" fill-opacity="0.25" stroke="url(#shieldBorder)" stroke-width="2" stroke-linejoin="round"/>
            <circle cx="16" cy="15" r="4" fill="url(#logoGrad)"/>
            <circle cx="16" cy="15" r="8" stroke="rgba(255,255,255,0.4)" stroke-dasharray="2 3" stroke-width="1.5"/>
            <line x1="16" y1="15" x2="22" y2="10" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </div>
        <div class="logo-text-group">
          <div class="logo-title">
            <span>{{ store.appName }}</span>
            <span class="logo-badge">NIDS 2.0</span>
          </div>
          <small class="logo-sub">{{ store.appSubName }}</small>
        </div>
      </router-link>

      <!-- Mobile Close X Button -->
      <button class="mobile-close-btn" @click="store.closeMobileNav" aria-label="Close menu">
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
        </svg>
      </button>
    </div>

    <!-- Navigation Links -->
    <div class="nav-links">
      <router-link to="/" class="nv" :class="{ active: $route.path === '/' }" @click="store.closeMobileNav">
        <svg class="nv-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="6" height="6" rx="1.5" />
          <rect x="11" y="3" width="6" height="6" rx="1.5" />
          <rect x="3" y="11" width="6" height="6" rx="1.5" />
          <rect x="11" y="11" width="6" height="6" rx="1.5" />
        </svg>
        <span>{{ store.t('nav.dashboard') }}</span>
      </router-link>

      <router-link to="/alerts" class="nv" :class="{ active: $route.path === '/alerts' }" @click="store.closeMobileNav">
        <svg class="nv-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <path d="M10 2L3 17h14L10 2z" />
          <path d="M10 8v4" />
          <circle cx="10" cy="14.5" r="0.75" fill="currentColor" />
        </svg>
        <span>{{ store.t('nav.alerts') }}</span>
        <span v-if="store.kpis.attacks > 0" class="nav-counter">{{ store.kpis.attacks }}</span>
      </router-link>

      <router-link to="/threat-intel" class="nv" :class="{ active: $route.path === '/threat-intel' }" @click="store.closeMobileNav">
        <svg class="nv-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="10" cy="10" r="7" />
          <circle cx="10" cy="10" r="3" />
          <line x1="10" y1="2" x2="10" y2="5" />
          <line x1="10" y1="15" x2="10" y2="18" />
          <line x1="2" y1="10" x2="5" y2="10" />
          <line x1="15" y1="10" x2="18" y2="10" />
        </svg>
        <span>{{ store.t('nav.threatIntel') }}</span>
      </router-link>

      <router-link to="/sensors" class="nv" :class="{ active: $route.path === '/sensors' }" @click="store.closeMobileNav">
        <svg class="nv-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="3" width="16" height="5" rx="1.5" />
          <rect x="2" y="12" width="16" height="5" rx="1.5" />
          <circle cx="5" cy="5.5" r="1" fill="currentColor" />
          <circle cx="8" cy="5.5" r="1" fill="currentColor" />
          <circle cx="5" cy="14.5" r="1" fill="currentColor" />
          <circle cx="8" cy="14.5" r="1" fill="currentColor" />
        </svg>
        <span>{{ store.t('nav.sensors') }}</span>
      </router-link>

      <router-link to="/models" class="nv" :class="{ active: $route.path === '/models' }" @click="store.closeMobileNav">
        <svg class="nv-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <rect x="4" y="4" width="12" height="12" rx="2" />
          <path d="M8 8h4v4H8z" />
          <line x1="8" y1="1" x2="8" y2="4" />
          <line x1="12" y1="1" x2="12" y2="4" />
          <line x1="8" y1="16" x2="8" y2="19" />
          <line x1="12" y1="16" x2="12" y2="19" />
          <line x1="1" y1="8" x2="4" y2="8" />
          <line x1="1" y1="12" x2="4" y2="12" />
          <line x1="16" y1="8" x2="19" y2="8" />
          <line x1="16" y1="12" x2="19" y2="12" />
        </svg>
        <span>{{ store.t('nav.models') }}</span>
      </router-link>

      <router-link to="/settings" class="nv" :class="{ active: $route.path === '/settings' }" @click="store.closeMobileNav">
        <svg class="nv-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="10" cy="10" r="3" />
          <path d="M16.5 12a1.5 1.5 0 0 0 .3 1.6l.1.1a1.5 1.5 0 1 1-2.1 2.1l-.1-.1a1.5 1.5 0 0 0-1.6-.3 1.5 1.5 0 0 0-1 1.4v.2a1.5 1.5 0 1 1-3 0v-.2a1.5 1.5 0 0 0-1-1.4 1.5 1.5 0 0 0-1.6.3l-.1.1a1.5 1.5 0 1 1-2.1-2.1l.1-.1a1.5 1.5 0 0 0 .3-1.6 1.5 1.5 0 0 0-1.4-1h-.2a1.5 1.5 0 1 1 0-3h.2a1.5 1.5 0 0 0 1.4-1 1.5 1.5 0 0 0-.3-1.6l-.1-.1a1.5 1.5 0 1 1 2.1-2.1l.1.1a1.5 1.5 0 0 0 1.6.3h.1a1.5 1.5 0 0 0 1-1.4v-.2a1.5 1.5 0 1 1 3 0v.2a1.5 1.5 0 0 0 1 1.4 1.5 1.5 0 0 0 1.6-.3l.1-.1a1.5 1.5 0 1 1 2.1 2.1l-.1.1a1.5 1.5 0 0 0-.3 1.6v.1a1.5 1.5 0 0 0 1.4 1h.2a1.5 1.5 0 1 1 0 3h-.2a1.5 1.5 0 0 0-1.4 1z" />
        </svg>
        <span>{{ store.t('nav.settings') }}</span>
      </router-link>
    </div>

    <!-- Mobile Language Switcher in Drawer -->
    <div class="mobile-lang-row">
      <span style="font-size: 12px; color: var(--mu);">{{ store.t('header.lang') }} :</span>
      <div class="lang-pill-group">
        <button 
          class="lang-choice-btn" 
          :class="{ active: store.lang === 'FR' }" 
          @click="store.setLanguage('FR')"
        >
          🇫🇷 FR
        </button>
        <button 
          class="lang-choice-btn" 
          :class="{ active: store.lang === 'EN' }" 
          @click="store.setLanguage('EN')"
        >
          🇬🇧 EN
        </button>
      </div>
    </div>

    <!-- Sensor Fleet Status Footer -->
    <div class="sf-card">
      <div class="sf-status">
        <span class="dot" :class="{ off: !store.wsConnected }"></span>
        <span class="sf-label">{{ store.sensorsOnline }} {{ store.t('nav.sensorsOnline') }}</span>
      </div>
      <div class="sf-details">
        <span>NFStream v6.6</span>
        <span style="color:var(--ok);">{{ store.t('nav.zeroDrops') }}</span>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { useSocStore } from '@/stores/socStore'
const store = useSocStore()
</script>

<style scoped>
.sidebar-backdrop {
  display: none;
}

@media (max-width: 900px) {
  .sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(8px);
    z-index: 998;
  }

  .side {
    position: fixed !important;
    top: 0;
    left: 0;
    bottom: 0;
    width: 280px;
    height: 100vh !important;
    transform: translateX(-100%);
    transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1);
    z-index: 999;
    box-shadow: 12px 0 36px rgba(0, 0, 0, 0.6);
  }

  .side.mobile-open {
    transform: translateX(0);
  }
}

.sidebar-top-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  padding-bottom: 14px;
  margin-bottom: 12px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: var(--tx);
}

.mobile-close-btn {
  display: none;
  background: var(--panel2);
  border: 1px solid var(--line);
  color: var(--mu);
  width: 32px;
  height: 32px;
  border-radius: 8px;
  padding: 0;
  align-items: center;
  justify-content: center;
}

.mobile-close-btn svg {
  width: 16px;
  height: 16px;
}

@media (max-width: 900px) {
  .mobile-close-btn {
    display: flex;
  }
}

.logo-icon-wrapper {
  width: 36px;
  height: 36px;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  filter: drop-shadow(0 2px 8px rgba(88, 101, 242, 0.35));
}

.soc-logo-svg {
  width: 100%;
  height: 100%;
}

.logo-text-group {
  display: flex;
  flex-direction: column;
}

.logo-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 17px;
  font-weight: 800;
  letter-spacing: -0.3px;
  line-height: 1.1;
}

.logo-badge {
  font-size: 9px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--ac), var(--ac2));
  color: #fff;
  padding: 1px 5px;
  border-radius: 4px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.logo-sub {
  font-size: 11px;
  color: var(--mu);
  font-weight: 500;
}

.nav-links {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nv {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 12px;
  color: var(--mu);
  font-size: 13.5px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative;
  min-height: 42px;
}

.nv-icon {
  width: 18px;
  height: 18px;
  flex: none;
  transition: transform 0.18s ease;
}

.nv:hover {
  background: var(--panel2);
  color: var(--tx);
  transform: translateX(2px);
}

.nv.active {
  background: linear-gradient(135deg, rgba(88, 101, 242, 0.25) 0%, rgba(155, 92, 246, 0.25) 100%);
  color: #fff;
  font-weight: 600;
  border: 1px solid rgba(88, 101, 242, 0.45);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.15), 0 4px 12px rgba(88, 101, 242, 0.2);
}

.nv.active .nv-icon {
  color: var(--ac);
  filter: drop-shadow(0 0 6px var(--ac));
}

.nav-counter {
  margin-left: auto;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 10px;
  background: rgba(255, 77, 126, 0.2);
  color: var(--cr);
  border: 1px solid rgba(255, 77, 126, 0.35);
  font-variant-numeric: tabular-nums;
}

.mobile-lang-row {
  display: none;
  align-items: center;
  justify-content: space-between;
  margin-top: 14px;
  padding: 10px 0;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

@media (max-width: 900px) {
  .mobile-lang-row {
    display: flex;
  }
}

.lang-pill-group {
  display: flex;
  background: var(--panel2);
  border-radius: 8px;
  padding: 2px;
  border: 1px solid var(--line);
}

.lang-choice-btn {
  background: transparent;
  border: 0;
  color: var(--mu);
  font-size: 11px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 6px;
}

.lang-choice-btn.active {
  background: var(--ac);
  color: #fff;
}

.sf-card {
  margin-top: auto;
  padding: 12px 14px;
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(44, 45, 66, 0.6) 0%, rgba(34, 35, 51, 0.9) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.sf-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--tx);
}

.sf-details {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--mu);
  margin-top: 4px;
  padding-top: 4px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}
</style>
