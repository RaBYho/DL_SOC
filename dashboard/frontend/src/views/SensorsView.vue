<template>
  <main>
    <!-- ========================================================================= -->
    <!-- EN-TÊTE PRINCIPAL & NAVIGATION PAR ONGLETS                                -->
    <!-- ========================================================================= -->
    <div class="card header-card">
      <div class="header-main-row">
        <div>
          <div class="title-with-badge">
            <h2 class="page-title">Sondes Réseau &amp; Ingestion de Trafic</h2>
            <span class="fleet-status-pill" :class="{ 'is-active': store.sensorsOnline > 0 }">
              <span class="status-pulse-dot"></span>
              {{ store.sensorsOnline }} sonde(s) en direct
            </span>
          </div>
          <p class="page-desc">
            Basculez entre le <b>rejeu de scénarios d'attaques en laboratoire (PCAP)</b> et la <b>supervision de votre parc de sondes réseau réelles (Agents Edge)</b>.
          </p>
        </div>

        <div class="header-quick-actions">
          <button 
            type="button" 
            class="btn-glass" 
            :class="{ 'spinning': isRefreshing }"
            :disabled="isRefreshing" 
            @click="handleManualRefresh"
            title="Rafraîchir les sondes et métriques"
          >
            <svg class="svg-icon refresh-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
              <path d="M3 3v5h5"/>
              <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
              <path d="M16 21h5v-5"/>
            </svg>
            <span>Actualiser</span>
          </button>
        </div>
      </div>

      <!-- Sélecteur d'Onglets Segmenté Haut de Gamme -->
      <div class="mode-tabs-wrapper">
        <button 
          type="button" 
          class="mode-tab-btn" 
          :class="{ active: activeTab === 'replay' }"
          @click="activeTab = 'replay'"
        >
          <svg class="svg-icon tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
          </svg>
          <span class="tab-title">Simulateur &amp; Rejeu PCAP</span>
          <span class="tab-tag mode-lab">Laboratoire</span>
          <span v-if="store.replayStatus.active" class="active-pulse-badge">
            <span class="pulse-ring"></span>
            En cours ({{ store.replayStatus.speed }}x)
          </span>
        </button>

        <button 
          type="button" 
          class="mode-tab-btn" 
          :class="{ active: activeTab === 'fleet' }"
          @click="activeTab = 'fleet'"
        >
          <svg class="svg-icon tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4.93 19.07a10 10 0 0 1 0-14.14"/>
            <path d="M7.76 16.24a6 6 0 0 1 0-8.48"/>
            <circle cx="12" cy="12" r="2"/>
            <path d="M16.24 7.76a6 6 0 0 1 0 8.48"/>
            <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
          </svg>
          <span class="tab-title">Parc de Sondes Réseau</span>
          <span class="tab-tag mode-fleet">Agents Réels</span>
          <span class="count-bubble">{{ store.sensorsList.length }}</span>
        </button>
      </div>
    </div>

    <!-- ========================================================================= -->
    <!-- ONGLET 1 : SIMULATEUR & REJEU PCAP (LABORATOIRE)                          -->
    <!-- ========================================================================= -->
    <div v-if="activeTab === 'replay'" class="tab-pane">
      <div class="grid">
        <!-- Panneau de Contrôle du Rejeu -->
        <div class="card c6 control-panel-card">
          <div class="card-header-row">
            <div>
              <h3 class="section-title">Injection de Scénarios d'Attaques</h3>
              <p class="section-subtitle">
                Simulez des captures réelles pour tester la robustesse et la réactivité du modèle Deep Learning.
              </p>
            </div>
            <span v-if="store.replayStatus.active" class="badge-running" :class="{ 'is-paused': store.replayStatus.is_paused }">
              {{ store.replayStatus.is_paused ? 'Rejeu Suspendu' : 'Rejeu Actif' }}
            </span>
          </div>

          <div class="form-flow">
            <!-- Sélecteur de fichier PCAP -->
            <div class="field-group">
              <label class="field-label">Scénario de Capture Réseau (PCAP)</label>
              <div class="select-wrapper">
                <select v-model="selectedPcap" class="custom-select" :disabled="store.replayStatus.active">
                  <option value="">Sélectionnez un scénario d'attaque...</option>
                  <option v-for="p in store.pcapFiles" :key="p.filename" :value="p.filename">
                    {{ p.title ? p.title : p.filename }} ({{ p.size_mb }} Mo)
                  </option>
                </select>
                <span class="select-arrow">▼</span>
              </div>
            </div>

            <!-- Fiche détaillée du scénario sélectionné -->
            <div v-if="selectedPcapMeta" class="scenario-meta-card">
              <div class="scenario-meta-header">
                <div class="scenario-meta-title">
                  <span class="scenario-bullet"></span>
                  <b>{{ selectedPcapMeta.title }}</b>
                </div>
                <span class="sev-tag" :class="selectedPcapMeta.severity">{{ selectedPcapMeta.category }}</span>
              </div>
              <p class="scenario-desc">{{ selectedPcapMeta.description }}</p>
              <div class="scenario-chips">
                <div class="chip">
                  <span class="chip-label">Fichier :</span>
                  <code class="chip-val">{{ selectedPcapMeta.filename }}</code>
                </div>
                <div class="chip">
                  <span class="chip-label">Taille :</span>
                  <b class="chip-val">{{ selectedPcapMeta.size_mb }} Mo</b>
                </div>
                <div class="chip">
                  <span class="chip-label">Niveau d'impact :</span>
                  <b class="chip-val" :class="'text-' + (selectedPcapMeta.severity || 'Medium').toLowerCase()">{{ selectedPcapMeta.severity }}</b>
                </div>
              </div>
            </div>

            <!-- Sélecteur de Vitesse avec Segmented Control -->
            <div class="field-group">
              <div class="field-header">
                <label class="field-label">Vitesse d'Injection Réseau</label>
                <span class="rate-indicator">{{ (replaySpeed * 25).toFixed(0) }} flux/seconde estimés</span>
              </div>
              <div class="speed-segmented-control">
                <button 
                  v-for="s in [0.5, 1.0, 2.0, 5.0, 10.0]" 
                  :key="s"
                  type="button"
                  class="speed-btn"
                  :class="{ active: replaySpeed === s }"
                  @click="replaySpeed = s"
                  :disabled="store.replayStatus.active"
                >
                  {{ s }}x
                  <span v-if="s === 1.0" class="speed-badge-norm">Normal</span>
                  <span v-else-if="s === 10.0" class="speed-badge-turbo">Turbo</span>
                </button>
              </div>
            </div>

            <!-- Carte de Progression Live -->
            <div v-if="store.replayStatus.active" class="replay-progress-card">
              <div class="progress-top">
                <span class="progress-file-info">
                  <span class="progress-glow-dot"></span>
                  Rejeu en cours : <b>{{ store.replayStatus.pcap_name }}</b>
                </span>
                <span class="progress-pct">{{ (store.replayStatus.progress_pct || 0).toFixed(1) }}%</span>
              </div>

              <div class="progress-track">
                <div class="progress-bar-fill" :style="{ width: `${store.replayStatus.progress_pct || 0}%` }">
                  <span class="progress-laser"></span>
                </div>
              </div>

              <div class="progress-kpi-grid">
                <div class="progress-kpi">
                  <span class="kpi-label">Flux Traités</span>
                  <b class="kpi-val">{{ store.replayStatus.processed_flows }} / {{ store.replayStatus.total_flows }}</b>
                </div>
                <div class="progress-kpi">
                  <span class="kpi-label">Vitesse Active</span>
                  <b class="kpi-val text-accent">{{ store.replayStatus.speed }}x</b>
                </div>
                <div class="progress-kpi">
                  <span class="kpi-label">Menaces Interceptées</span>
                  <b class="kpi-val text-danger">{{ store.replayStatus.total_alerts || store.kpis.attacks }}</b>
                </div>
              </div>
            </div>

            <!-- Commandes du Rejeu -->
            <div class="controls-row">
              <button 
                v-if="!store.replayStatus.active"
                type="button"
                class="btn-primary-action" 
                :disabled="!selectedPcap"
                @click="startReplay"
              >
                <svg class="svg-icon" viewBox="0 0 24 24" fill="currentColor">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
                <span>Lancer le Rejeu PCAP</span>
              </button>

              <template v-else>
                <button 
                  v-if="!store.replayStatus.is_paused"
                  type="button"
                  class="btn-secondary-action" 
                  @click="pauseReplay"
                >
                  <svg class="svg-icon" viewBox="0 0 24 24" fill="currentColor">
                    <rect x="6" y="4" width="4" height="16"/>
                    <rect x="14" y="4" width="4" height="16"/>
                  </svg>
                  <span>Mettre en Pause</span>
                </button>
                <button 
                  v-else
                  type="button"
                  class="btn-secondary-action btn-resume" 
                  @click="resumeReplay"
                >
                  <svg class="svg-icon" viewBox="0 0 24 24" fill="currentColor">
                    <polygon points="5 3 19 12 5 21 5 3"/>
                  </svg>
                  <span>Reprendre le Rejeu</span>
                </button>

                <button 
                  type="button"
                  class="btn-danger-action" 
                  @click="stopReplay"
                >
                  <svg class="svg-icon" viewBox="0 0 24 24" fill="currentColor">
                    <rect x="5" y="5" width="14" height="14"/>
                  </svg>
                  <span>Arrêter le Rejeu</span>
                </button>
              </template>
            </div>

            <!-- Accès au Terminal IA -->
            <router-link to="/models" class="link-to-terminal-card">
              <div class="terminal-card-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="4 17 10 11 4 5"/>
                  <line x1="12" y1="19" x2="20" y2="19"/>
                </svg>
              </div>
              <div class="terminal-card-text">
                <b>Terminal d'Inférence IA en Direct</b>
                <span>Observez chaque batch analysé par le DNN et l'AutoEncodeur avec leur latence</span>
              </div>
              <div class="terminal-card-arrow">&rarr;</div>
            </router-link>
          </div>
        </div>

        <!-- Catalogue des Scénarios Disponibles -->
        <div class="card c6 catalog-panel-card">
          <div class="catalog-header">
            <div>
              <h3 class="section-title">Catalogue des Scénarios d'Attaques</h3>
              <p class="section-subtitle">
                {{ filteredPcaps.length }} capture(s) prête(s) pour validation empirique
              </p>
            </div>
            
            <!-- Barre de recherche interne -->
            <div class="catalog-search-wrap">
              <svg class="search-input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"/>
                <line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
              <input 
                v-model="pcapSearch" 
                type="text" 
                placeholder="Filtrer les captures..." 
                class="catalog-search-input"
              />
              <span v-if="pcapSearch" class="clear-search-btn" @click="pcapSearch = ''">✕</span>
            </div>
          </div>

          <!-- Filtres de Catégories -->
          <div class="catalog-cat-chips">
            <button 
              v-for="cat in pcapCategories" 
              :key="cat.key"
              type="button"
              class="cat-chip-btn"
              :class="{ active: selectedCategoryFilter === cat.key }"
              @click="selectedCategoryFilter = cat.key"
            >
              {{ cat.label }}
            </button>
          </div>

          <!-- Liste des scénarios -->
          <div class="scenario-scroll-list">
            <div 
              v-for="p in filteredPcaps" 
              :key="p.filename"
              class="scenario-card-item"
              :class="{ 
                'is-selected': selectedPcap === p.filename,
                'is-active-running': store.replayStatus.active && store.replayStatus.pcap_name === p.filename
              }"
              @click="selectScenario(p.filename)"
            >
              <div class="card-item-indicator" :class="'ind-' + (p.severity || 'Medium').toLowerCase()"></div>
              <div class="card-item-body">
                <div class="card-item-top">
                  <div class="item-name-wrap">
                    <span class="item-category-icon">
                      <component :is="getScenarioIconComponent(p.category)" />
                    </span>
                    <b class="item-title">{{ p.title || p.filename }}</b>
                  </div>
                  <span class="sev-tag" :class="p.severity || 'Medium'">{{ p.category || 'PCAP' }}</span>
                </div>
                <p class="item-desc">{{ p.description || 'Capture réseau standard pour entraînement et évaluation.' }}</p>
                <div class="item-meta-bar">
                  <span class="meta-filename"><code>{{ p.filename }}</code></span>
                  <span class="meta-size"><b>{{ p.size_mb }} Mo</b></span>
                  <span v-if="selectedPcap === p.filename" class="meta-selected-badge">Sélectionné ✓</span>
                </div>
              </div>
            </div>

            <div v-if="filteredPcaps.length === 0" class="no-pcaps-matched">
              <span>Aucun fichier PCAP ne correspond à votre filtre.</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ========================================================================= -->
    <!-- ONGLET 2 : PARC DE SONDES RÉSEAU (SUPERVISION EDGE & AGENTS RÉELS)       -->
    <!-- ========================================================================= -->
    <div v-else class="tab-pane fleet-tab-pane">
      
      <!-- Bandeau 4 Métriques KPI du Parc -->
      <div class="fleet-kpis-strip">
        <div class="fleet-kpi-card">
          <div class="kpi-icon-wrap icon-blue">
            <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
              <rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>
              <line x1="6" y1="6" x2="6.01" y2="6"/>
              <line x1="6" y1="18" x2="6.01" y2="18"/>
            </svg>
          </div>
          <div class="kpi-content">
            <span class="kpi-card-label">Sondes Enregistrées</span>
            <div class="kpi-card-val-row">
              <b class="kpi-card-num">{{ store.sensorsList.length }}</b>
              <span class="kpi-card-unit">source(s)</span>
            </div>
          </div>
        </div>

        <div class="fleet-kpi-card">
          <div class="kpi-icon-wrap icon-emerald">
            <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <polyline points="9 12 11 14 15 10"/>
            </svg>
          </div>
          <div class="kpi-content">
            <span class="kpi-card-label">Sondes En Ligne (Direct)</span>
            <div class="kpi-card-val-row">
              <b class="kpi-card-num text-success">{{ store.sensorsOnline }}</b>
              <span class="kpi-card-unit">actives</span>
            </div>
          </div>
        </div>

        <div class="fleet-kpi-card">
          <div class="kpi-icon-wrap icon-indigo">
            <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="20" x2="18" y2="10"/>
              <line x1="12" y1="20" x2="12" y2="4"/>
              <line x1="6" y1="20" x2="6" y2="14"/>
            </svg>
          </div>
          <div class="kpi-content">
            <span class="kpi-card-label">Flux Transmis (Parc)</span>
            <div class="kpi-card-val-row">
              <b class="kpi-card-num">{{ totalFleetFlows.toLocaleString() }}</b>
              <span class="kpi-card-unit">flux analysés</span>
            </div>
          </div>
        </div>

        <div class="fleet-kpi-card">
          <div class="kpi-icon-wrap icon-rose">
            <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
          </div>
          <div class="kpi-content">
            <span class="kpi-card-label">Menaces Interceptées</span>
            <div class="kpi-card-val-row">
              <b class="kpi-card-num text-danger">{{ totalFleetAttacks.toLocaleString() }}</b>
              <span class="kpi-card-unit">alertes</span>
            </div>
          </div>
        </div>
      </div>

      <div class="grid">
        <!-- Colonne Gauche : Carte Parc de Sondes Actives & Distantes -->
        <div class="card c7 fleet-list-card">
          <div class="fleet-list-header">
            <div>
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

            <!-- Filtre Rapide de Statut -->
            <div class="status-filter-pills">
              <button 
                type="button" 
                class="status-pill-btn" 
                :class="{ active: fleetStatusFilter === 'all' }"
                @click="fleetStatusFilter = 'all'"
              >
                Toutes ({{ store.sensorsList.length }})
              </button>
              <button 
                type="button" 
                class="status-pill-btn online" 
                :class="{ active: fleetStatusFilter === 'online' }"
                @click="fleetStatusFilter = 'online'"
              >
                <span class="pill-dot green"></span>
                En ligne ({{ store.sensorsOnline }})
              </button>
              <button 
                type="button" 
                class="status-pill-btn offline" 
                :class="{ active: fleetStatusFilter === 'offline' }"
                @click="fleetStatusFilter = 'offline'"
              >
                Inactives ({{ store.sensorsList.length - store.sensorsOnline }})
              </button>
            </div>
          </div>

          <!-- ÉTAT VIDE ÉLÉGANT AVEC RADAR -->
          <div v-if="filteredSensors.length === 0" class="fleet-empty-state">
            <div class="radar-scan-box">
              <div class="radar-circle circle-1"></div>
              <div class="radar-circle circle-2"></div>
              <div class="radar-circle circle-3"></div>
              <div class="radar-sweeper"></div>
              <div class="radar-center-dot"></div>
            </div>
            <h4 class="empty-state-title">Aucune sonde détectée pour ce filtre</h4>
            <p class="empty-state-text">
              Déployez un agent sur une machine distante avec la commande ci-contre ou lancez une simulation de rejeu PCAP pour générer des flux en direct.
            </p>
            <div class="empty-actions">
              <button type="button" class="btn-glass" @click="activeTab = 'replay'">
                <svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                </svg>
                <span>Lancer un Rejeu PCAP</span>
              </button>
              <button type="button" class="btn-glass" @click="fleetStatusFilter = 'all'">
                Réinitialiser le filtre
              </button>
            </div>
          </div>

          <!-- LISTE DES CARTES DE SONDES SOC -->
          <div v-else class="fleet-cards-grid">
            <div 
              v-for="s in filteredSensors" 
              :key="s.id" 
              class="sensor-fleet-card"
              :class="{ 'is-online': s.status === 'Online', 'is-replay': s.type === 'replay' }"
            >
              <!-- En-tête de la sonde -->
              <div class="sensor-card-top">
                <div class="sensor-badge-icon" :class="{ 'icon-replay': s.type === 'replay' }">
                  <!-- Icône Beaker pour simulateur Replay -->
                  <svg v-if="s.type === 'replay'" class="sensor-svg-type" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M10 2v7.31L4.69 19.3A2 2 0 0 0 6.36 22h11.28a2 2 0 0 0 1.67-2.7L14 9.31V2"/>
                    <line x1="8.5" y1="2" x2="15.5" y2="2"/>
                    <line x1="14" y1="9" x2="10" y2="9"/>
                  </svg>
                  <!-- Icône Server / Antenne pour Agent Réseau Réel -->
                  <svg v-else class="sensor-svg-type" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
                    <rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>
                    <line x1="6" y1="6" x2="6.01" y2="6"/>
                    <line x1="6" y1="18" x2="6.01" y2="18"/>
                  </svg>
                </div>

                <div class="sensor-headline">
                  <div class="sensor-title-row">
                    <b class="sensor-title">{{ s.name }}</b>
                    <span 
                      class="sensor-status-tag"
                      :class="'tag-' + s.status.toLowerCase()"
                    >
                      <span class="status-indicator-dot"></span>
                      {{ s.status_label || s.status }}
                    </span>
                  </div>

                  <div class="sensor-ids-row">
                    <span class="sensor-id-pill" @click="copySensorId(s.id)" title="Cliquez pour copier l'identifiant">
                      ID: <code>{{ s.id }}</code>
                      <svg class="copy-small-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                      </svg>
                    </span>
                    <span class="type-pill" :class="s.type">
                      {{ s.type === 'replay' ? 'Simulateur PCAP Interne' : 'Agent Edge Distant' }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Corps Télémétrie Réseau -->
              <div class="sensor-telemetry-box">
                <div class="telemetry-item">
                  <div class="telemetry-lbl-row">
                    <svg class="telemetry-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
                      <line x1="6" y1="6" x2="6.01" y2="6"/>
                    </svg>
                    <span class="telemetry-lbl">Interface d'écoute</span>
                  </div>
                  <b class="telemetry-val">
                    <span class="eth-bullet"></span>
                    {{ s.interface || (s.type === 'replay' ? 'Moteur PCAP' : 'eth0') }}
                  </b>
                </div>

                <div class="telemetry-item">
                  <div class="telemetry-lbl-row">
                    <svg class="telemetry-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <line x1="18" y1="20" x2="18" y2="10"/>
                      <line x1="12" y1="20" x2="12" y2="4"/>
                      <line x1="6" y1="20" x2="6" y2="14"/>
                    </svg>
                    <span class="telemetry-lbl">Flux analysés</span>
                  </div>
                  <b class="telemetry-val">{{ (s.total_flows || 0).toLocaleString() }}</b>
                </div>

                <div class="telemetry-item">
                  <div class="telemetry-lbl-row">
                    <svg class="telemetry-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                    </svg>
                    <span class="telemetry-lbl">Attaques bloquées</span>
                  </div>
                  <b class="telemetry-val" :class="{ 'text-danger': (s.total_attacks || 0) > 0 }">
                    {{ (s.total_attacks || 0).toLocaleString() }}
                  </b>
                </div>

                <div class="telemetry-item">
                  <div class="telemetry-lbl-row">
                    <svg class="telemetry-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <circle cx="12" cy="12" r="10"/>
                      <polyline points="12 6 12 12 16 14"/>
                    </svg>
                    <span class="telemetry-lbl">Dernier Heartbeat</span>
                  </div>
                  <span class="telemetry-val text-muted">
                    {{ s.last_seen || 'En attente' }}
                    <span v-if="s.elapsed_sec" class="elapsed-badge">
                      ({{ formatElapsed(s.elapsed_sec) }})
                    </span>
                  </span>
                </div>
              </div>

              <!-- Jauge de Ratio de Menaces -->
              <div class="sensor-threat-ratio">
                <div class="ratio-labels">
                  <span>Répartition du trafic</span>
                  <b>{{ calculateAttackPct(s) }}% malveillant</b>
                </div>
                <div class="threat-ratio-bar">
                  <div 
                    class="ratio-fill-danger" 
                    :style="{ width: `${calculateAttackPct(s)}%` }"
                  ></div>
                  <div 
                    class="ratio-fill-benign" 
                    :style="{ width: `${100 - calculateAttackPct(s)}%` }"
                  ></div>
                </div>
              </div>

              <!-- Pied de Carte & Actions -->
              <div class="sensor-card-footer">
                <div class="sensor-protocol-tag">
                  <svg class="proto-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                  </svg>
                  <span>Moteur : Scorer IA v4 + AE</span>
                </div>

                <div class="sensor-actions">
                  <button 
                    type="button" 
                    class="btn-sensor-action"
                    @click="filterAlertsBySensor(s.id)"
                    title="Voir toutes les alertes de cette sonde dans la table d'incidents"
                  >
                    <svg class="action-btn-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <circle cx="11" cy="11" r="8"/>
                      <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                    </svg>
                    <span>Voir les alertes</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Colonne Droite : Centre de Déploiement & Onboarding d'Agents -->
        <div class="card c5 deployment-hub-card">
          <div class="deploy-header">
            <div class="deploy-icon-badge">
              <svg class="deploy-header-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="12 2 19 21 12 17 5 21 12 2"/>
              </svg>
            </div>
            <div>
              <h3 class="section-title">Déployer une Nouvelle Sonde</h3>
              <p class="section-subtitle">
                Ajoutez un serveur ou équipement distant au cluster de détection temps réel.
              </p>
            </div>
          </div>

          <!-- Onglets de Méthode de Déploiement -->
          <div class="deploy-method-nav">
            <button 
              type="button" 
              class="deploy-tab-btn" 
              :class="{ active: deployMethod === 'linux' }"
              @click="deployMethod = 'linux'"
            >
              <svg class="method-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
                <line x1="8" y1="21" x2="16" y2="21"/>
                <line x1="12" y1="17" x2="12" y2="21"/>
              </svg>
              <span>Agent Linux</span>
            </button>
            <button 
              type="button" 
              class="deploy-tab-btn" 
              :class="{ active: deployMethod === 'docker' }"
              @click="deployMethod = 'docker'"
            >
              <svg class="method-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
                <line x1="12" y1="22.08" x2="12" y2="12"/>
              </svg>
              <span>Docker</span>
            </button>
            <button 
              type="button" 
              class="deploy-tab-btn" 
              :class="{ active: deployMethod === 'curl' }"
              @click="deployMethod = 'curl'"
            >
              <svg class="method-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
              </svg>
              <span>Test API</span>
            </button>
          </div>

          <!-- Schéma d'Architecture Miniature -->
          <div class="arch-flow-box">
            <div class="flow-step">
              <svg class="flow-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
                <line x1="8" y1="21" x2="16" y2="21"/>
              </svg>
              <span class="flow-label">Sonde Edge</span>
            </div>
            <div class="flow-arrow">&rarr;</div>
            <div class="flow-step">
              <svg class="flow-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              <span class="flow-label">POST /ingest</span>
            </div>
            <div class="flow-arrow">&rarr;</div>
            <div class="flow-step">
              <svg class="flow-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="4" y="4" width="16" height="16" rx="2" ry="2"/>
                <rect x="9" y="9" width="6" height="6"/>
                <line x1="9" y1="1" x2="9" y2="4"/>
                <line x1="15" y1="1" x2="15" y2="4"/>
              </svg>
              <span class="flow-label">Moteur IA</span>
            </div>
            <div class="flow-arrow">&rarr;</div>
            <div class="flow-step">
              <svg class="flow-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
              <span class="flow-label">Alertes SOC</span>
            </div>
          </div>

          <!-- Instructions Méthode 1 : Agent Linux Python -->
          <div v-if="deployMethod === 'linux'" class="deploy-steps-container">
            <div class="deploy-step">
              <div class="step-badge">1</div>
              <div class="step-content">
                <b class="step-title">Dépendances système &amp; bibliothèques</b>
                <p class="step-desc">Installez Python 3.10+ et NFStream pour l'extraction de métriques réseau :</p>
                <div class="code-box-wrapper">
                  <pre class="code-block">pip install nfstream requests pandas</pre>
                  <button type="button" class="btn-copy-code" @click="copyText('pip install nfstream requests pandas')">
                    {{ copiedText === 'pip install nfstream requests pandas' ? 'Copié !' : 'Copier' }}
                  </button>
                </div>
              </div>
            </div>

            <div class="deploy-step">
              <div class="step-badge">2</div>
              <div class="step-content">
                <b class="step-title">Lancer l'agent d'écoute en direct</b>
                <p class="step-desc">Remplacez <code>eth0</code> par votre carte réseau (nécessite les privilèges root) :</p>
                <div class="code-box-wrapper">
                  <pre class="code-block">{{ linuxDeployCommand }}</pre>
                  <button type="button" class="btn-copy-code" @click="copyText(linuxDeployCommand)">
                    {{ copiedText === linuxDeployCommand ? 'Copié !' : 'Copier' }}
                  </button>
                </div>
              </div>
            </div>

            <div class="deploy-step">
              <div class="step-badge">3</div>
              <div class="step-content">
                <b class="step-title">Accréditation &amp; Sécurité</b>
                <p class="step-desc">
                  Clé d'API configurée : <code>dev-secret-key</code> (modifiable dans les paramètres du SOC).
                </p>
              </div>
            </div>
          </div>

          <!-- Instructions Méthode 2 : Conteneur Docker -->
          <div v-else-if="deployMethod === 'docker'" class="deploy-steps-container">
            <div class="deploy-step">
              <div class="step-badge">1</div>
              <div class="step-content">
                <b class="step-title">Exécution dans le réseau de l'hôte</b>
                <p class="step-desc">Pour capturer le trafic réel, le conteneur doit utiliser le mode <code>--net=host</code> :</p>
                <div class="code-box-wrapper">
                  <pre class="code-block">{{ dockerDeployCommand }}</pre>
                  <button type="button" class="btn-copy-code" @click="copyText(dockerDeployCommand)">
                    {{ copiedText === dockerDeployCommand ? 'Copié !' : 'Copier' }}
                  </button>
                </div>
              </div>
            </div>

            <div class="deploy-step">
              <div class="step-badge">2</div>
              <div class="step-content">
                <b class="step-title">Tolérance aux pannes</b>
                <p class="step-desc">L'agent Docker redémarre automatiquement et met en mémoire tampon les flux en cas de micro-coupure réseau.</p>
              </div>
            </div>
          </div>

          <!-- Instructions Méthode 3 : Test API cURL -->
          <div v-else class="deploy-steps-container">
            <div class="deploy-step">
              <div class="step-badge">1</div>
              <div class="step-content">
                <b class="step-title">Tester la connectivité du serveur</b>
                <p class="step-desc">Vérifiez que le serveur SOC répond bien sur le port 8000 :</p>
                <div class="code-box-wrapper">
                  <pre class="code-block">curl -i {{ serverBaseUrl }}/health</pre>
                  <button type="button" class="btn-copy-code" @click="copyText(`curl -i ${serverBaseUrl}/health`)">
                    {{ copiedText === `curl -i ${serverBaseUrl}/health` ? 'Copié !' : 'Copier' }}
                  </button>
                </div>
              </div>
            </div>

            <div class="deploy-step">
              <div class="step-badge">2</div>
              <div class="step-content">
                <b class="step-title">Transmettre un flux de test</b>
                <p class="step-desc">Envoyez une charge utile JSON standard avec l'en-tête d'authentification :</p>
                <div class="code-box-wrapper">
                  <pre class="code-block">{{ curlTestCommand }}</pre>
                  <button type="button" class="btn-copy-code" @click="copyText(curlTestCommand)">
                    {{ copiedText === curlTestCommand ? 'Copié !' : 'Copier' }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Fiche de Bonnes Pratiques -->
          <div class="deploy-tip-box">
            <svg class="tip-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="16" x2="12" y2="12"/>
              <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
            <div class="tip-body">
              <b>Conseil de durcissement en production :</b>
              Activez le mode promiscuité sur le switch (port mirroring / SPAN) afin que la sonde capture tout le trafic du segment réseau.
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { useSocStore } from '@/stores/socStore'

const router = useRouter()
const store = useSocStore()

// Gestion des onglets principaux
const activeTab = ref('replay')

// Rejeu PCAP
const selectedPcap = ref('')
const replaySpeed = ref(1.0)
const pcapSearch = ref('')
const selectedCategoryFilter = ref('ALL')

// Parc de sondes
const fleetStatusFilter = ref('all')
const isRefreshing = ref(false)
const deployMethod = ref('linux')
const copiedText = ref('')

// Catégories de PCAPs
const pcapCategories = [
  { key: 'ALL', label: 'Toutes les captures' },
  { key: 'DDoS', label: 'DDoS & DoS' },
  { key: 'PortScan', label: 'Scans de Ports' },
  { key: 'Bot', label: 'Botnet & C2' },
  { key: 'BruteForce', label: 'Brute Force' },
  { key: 'WebAttack', label: 'Web Attacks' },
  { key: 'BENIGN', label: 'Trafic Nominal' }
]

// URL de base du serveur
const serverBaseUrl = computed(() => {
  if (typeof window !== 'undefined') {
    return `${window.location.protocol}//${window.location.host}`
  }
  return 'http://127.0.0.1:8000'
})

// Commandes de déploiement dynamiques
const linuxDeployCommand = computed(() => {
  return `sudo python nids_sensor.py --source eth0 --server ${serverBaseUrl.value} --api-key dev-secret-key --sensor-id sonde-edge-01`
})

const dockerDeployCommand = computed(() => {
  return `docker run --net=host --cap-add=NET_ADMIN -e SERVER=${serverBaseUrl.value} -e SENSOR_ID=docker-edge-01 hdvr-sensor:latest`
})

const curlTestCommand = computed(() => {
  return `curl -X POST "${serverBaseUrl.value}/ingest" -H "X-API-Key: dev-secret-key" -H "Content-Type: application/json" -d '{"sensor_id":"sonde-test","flows":[]}'`
})

// Métadonnées du PCAP sélectionné
const selectedPcapMeta = computed(() => {
  if (!selectedPcap.value) return null
  return store.pcapFiles.find(p => p.filename === selectedPcap.value) || null
})

// Filtrage des fichiers PCAP
const filteredPcaps = computed(() => {
  let list = store.pcapFiles || []
  if (selectedCategoryFilter.value !== 'ALL') {
    list = list.filter(p => {
      const cat = (p.category || '').toUpperCase()
      const target = selectedCategoryFilter.value.toUpperCase()
      return cat.includes(target) || (target === 'DDOS' && cat.includes('DOS'))
    })
  }
  if (pcapSearch.value.trim()) {
    const q = pcapSearch.value.trim().toLowerCase()
    list = list.filter(p => 
      (p.filename || '').toLowerCase().includes(q) ||
      (p.title || '').toLowerCase().includes(q) ||
      (p.description || '').toLowerCase().includes(q) ||
      (p.category || '').toLowerCase().includes(q)
    )
  }
  return list
})

// Filtrage des sondes
const filteredSensors = computed(() => {
  let list = store.sensorsList || []
  if (fleetStatusFilter.value === 'online') {
    list = list.filter(s => s.status === 'Online')
  } else if (fleetStatusFilter.value === 'offline') {
    list = list.filter(s => s.status !== 'Online')
  }
  return list
})

// Métriques agrégées du parc
const totalFleetFlows = computed(() => {
  return (store.sensorsList || []).reduce((acc, s) => acc + (s.total_flows || 0), 0)
})

const totalFleetAttacks = computed(() => {
  return (store.sensorsList || []).reduce((acc, s) => acc + (s.total_attacks || 0), 0)
})

const calculateAttackPct = (sensor) => {
  if (!sensor.total_flows || sensor.total_flows === 0) return 0
  const pct = ((sensor.total_attacks || 0) / sensor.total_flows) * 100
  return Math.min(100, Math.max(0, Math.round(pct * 10) / 10))
}

const formatElapsed = (sec) => {
  if (!sec && sec !== 0) return ''
  if (sec < 60) return `${Math.round(sec)}s`
  if (sec < 3600) return `${Math.round(sec / 60)} min`
  return `${(sec / 3600).toFixed(1)} h`
}

// Composants Iconographiques Vectoriels
const IconDDoS = () => h('svg', { class: 'svg-icon-mini text-danger', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
  h('polygon', { points: '13 2 3 14 12 14 11 22 21 10 12 10 13 2' })
])

const IconScan = () => h('svg', { class: 'svg-icon-mini text-warning', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
  h('circle', { cx: '11', cy: '11', r: '8' }),
  h('line', { x1: '21', y1: '21', x2: '16.65', y2: '16.65' })
])

const IconBot = () => h('svg', { class: 'svg-icon-mini text-purple', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
  h('rect', { x: '4', y: '4', width: '16', height: '16', rx: '2' }),
  h('circle', { cx: '9', cy: '9', r: '2' }),
  h('circle', { cx: '15', cy: '9', r: '2' }),
  h('line', { x1: '9', y1: '15', x2: '15', y2: '15' })
])

const IconBrute = () => h('svg', { class: 'svg-icon-mini text-orange', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
  h('rect', { x: '3', y: '11', width: '18', height: '11', rx: '2', ry: '2' }),
  h('path', { d: 'M7 11V7a5 5 0 0 1 10 0v4' })
])

const IconWeb = () => h('svg', { class: 'svg-icon-mini text-blue', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
  h('circle', { cx: '12', cy: '12', r: '10' }),
  h('line', { x1: '2', y1: '12', x2: '22', y2: '12' }),
  h('path', { d: 'M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z' })
])

const IconShield = () => h('svg', { class: 'svg-icon-mini text-success', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
  h('path', { d: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z' }),
  h('polyline', { points: '9 12 11 14 15 10' })
])

const IconGeneric = () => h('svg', { class: 'svg-icon-mini text-muted', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
  h('path', { d: 'M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z' })
])

const getScenarioIconComponent = (category) => {
  const cat = (category || '').toLowerCase()
  if (cat.includes('ddos') || cat.includes('dos')) return IconDDoS
  if (cat.includes('scan')) return IconScan
  if (cat.includes('bot')) return IconBot
  if (cat.includes('brute')) return IconBrute
  if (cat.includes('web')) return IconWeb
  if (cat.includes('benign') || cat.includes('normal')) return IconShield
  return IconGeneric
}

const selectScenario = (filename) => {
  if (store.replayStatus.active) return
  selectedPcap.value = filename
}

const startReplay = async () => {
  if (!selectedPcap.value) return
  await store.startPcapReplay(selectedPcap.value, replaySpeed.value)
}

const pauseReplay = async () => {
  await store.pausePcapReplay()
}

const resumeReplay = async () => {
  await store.resumePcapReplay()
}

const stopReplay = async () => {
  await store.stopPcapReplay()
}

const handleManualRefresh = async () => {
  isRefreshing.value = true
  try {
    await store.fetchSensors()
    await store.fetchPcapFiles()
  } finally {
    setTimeout(() => {
      isRefreshing.value = false
    }, 400)
  }
}

const filterAlertsBySensor = (sensorId) => {
  store.filterSearch = sensorId
  router.push('/alerts')
}

const copySensorId = async (id) => {
  await copyText(id)
}

const copyText = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    copiedText.value = text
    setTimeout(() => {
      if (copiedText.value === text) copiedText.value = ''
    }, 2500)
  } catch (err) {
    console.error('Erreur copie presse-papiers:', err)
  }
}

onMounted(async () => {
  await store.fetchSensors()
  await store.fetchPcapFiles()
  if (!selectedPcap.value && store.pcapFiles && store.pcapFiles.length > 0) {
    selectedPcap.value = store.pcapFiles[0].filename
  }
})
</script>

<style scoped>
/* ========================================================================= */
/* SVG ET ICONES VECTORIELLES                                                */
/* ========================================================================= */
.svg-icon {
  width: 16px;
  height: 16px;
  display: inline-block;
  vertical-align: middle;
}

.svg-icon-mini {
  width: 15px;
  height: 15px;
  display: inline-block;
}

.tab-icon {
  width: 18px;
  height: 18px;
}

/* ========================================================================= */
/* EN-TÊTE PRINCIPAL                                                         */
/* ========================================================================= */
.header-card {
  padding: 20px 24px;
  background: linear-gradient(180deg, rgba(28, 30, 48, 0.95) 0%, rgba(20, 21, 34, 0.95) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--r);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
  margin-bottom: 20px;
}

.header-main-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
}

.title-with-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.3px;
}

.fleet-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 11.5px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 999px;
  background: rgba(143, 160, 255, 0.1);
  color: #9baaff;
  border: 1px solid rgba(143, 160, 255, 0.25);
}

.fleet-status-pill.is-active {
  background: rgba(61, 220, 151, 0.15);
  color: #3ddc97;
  border-color: rgba(61, 220, 151, 0.35);
  box-shadow: 0 0 12px rgba(61, 220, 151, 0.2);
}

.status-pulse-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 6px currentColor;
}

.page-desc {
  margin: 6px 0 0;
  font-size: 13px;
  color: #8b8ea8;
  line-height: 1.45;
}

.page-desc b {
  color: #c4ccff;
}

.btn-glass {
  height: 36px;
  padding: 0 14px;
  font-size: 12.5px;
  font-weight: 600;
  color: #d1d6f5;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 9px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.btn-glass:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.25);
  transform: translateY(-1px);
}

.btn-glass.spinning .refresh-icon {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

/* ========================================================================= */
/* SÉLECTEUR D'ONGLETS DE MODE                                               */
/* ========================================================================= */
.mode-tabs-wrapper {
  display: flex;
  gap: 12px;
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.07);
}

.mode-tab-btn {
  flex: 1;
  height: 48px;
  padding: 0 20px;
  background: rgba(18, 20, 32, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  color: #9aa5ce;
  font-size: 13.5px;
  font-weight: 600;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.mode-tab-btn:hover {
  background: rgba(30, 34, 54, 0.8);
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.16);
}

.mode-tab-btn.active {
  background: linear-gradient(135deg, rgba(88, 101, 242, 0.22) 0%, rgba(74, 87, 224, 0.12) 100%);
  border-color: #5865f2;
  color: #ffffff;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.15), 0 4px 18px rgba(88, 101, 242, 0.3);
}

.tab-tag {
  font-size: 10.5px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 6px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.tab-tag.mode-lab {
  background: rgba(255, 181, 71, 0.15);
  color: #ffb547;
  border: 1px solid rgba(255, 181, 71, 0.3);
}

.tab-tag.mode-fleet {
  background: rgba(61, 220, 151, 0.15);
  color: #3ddc97;
  border: 1px solid rgba(61, 220, 151, 0.3);
}

.count-bubble {
  margin-left: auto;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

.active-pulse-badge {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  color: #3ddc97;
  background: rgba(61, 220, 151, 0.15);
  border: 1px solid rgba(61, 220, 151, 0.35);
  padding: 3px 8px;
  border-radius: 6px;
}

.pulse-ring {
  width: 6px;
  height: 6px;
  background: #3ddc97;
  border-radius: 50%;
  animation: pulse-dot 1.2s infinite;
}

@keyframes pulse-dot {
  0% { transform: scale(0.9); opacity: 0.7; }
  50% { transform: scale(1.4); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.7; }
}

/* ========================================================================= */
/* BANDEAU KPIS DE LA FLOTTE                                                 */
/* ========================================================================= */
.fleet-kpis-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}

@media (max-width: 1024px) {
  .fleet-kpis-strip {
    grid-template-columns: repeat(2, 1fr);
  }
}

.fleet-kpi-card {
  background: linear-gradient(180deg, rgba(26, 28, 44, 0.95) 0%, rgba(18, 19, 30, 0.95) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 16px 18px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.22);
  transition: transform 0.2s, border-color 0.2s;
}

.fleet-kpi-card:hover {
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.18);
}

.kpi-icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.kpi-icon-wrap .svg-icon {
  width: 22px;
  height: 22px;
}

.kpi-icon-wrap.icon-blue { background: rgba(88, 101, 242, 0.15); border: 1px solid rgba(88, 101, 242, 0.3); color: #8fa0ff; }
.kpi-icon-wrap.icon-emerald { background: rgba(61, 220, 151, 0.15); border: 1px solid rgba(61, 220, 151, 0.3); color: #3ddc97; }
.kpi-icon-wrap.icon-indigo { background: rgba(155, 92, 246, 0.15); border: 1px solid rgba(155, 92, 246, 0.3); color: #c4b5fd; }
.kpi-icon-wrap.icon-rose { background: rgba(255, 77, 126, 0.15); border: 1px solid rgba(255, 77, 126, 0.3); color: #ff85a5; }

.kpi-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.kpi-card-label {
  font-size: 11.5px;
  font-weight: 600;
  color: #8b8ea8;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.kpi-card-val-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.kpi-card-num {
  font-size: 22px;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: -0.5px;
  line-height: 1.1;
}

.kpi-card-unit {
  font-size: 11.5px;
  color: #7982a9;
}

/* ========================================================================= */
/* PANNEAUX ET CARTES DU SOC                                                 */
/* ========================================================================= */
.header-title-flex {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title-icon {
  width: 18px;
  height: 18px;
  color: #8fa0ff;
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

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.badge-running {
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 7px;
  background: rgba(61, 220, 151, 0.15);
  color: #3ddc97;
  border: 1px solid rgba(61, 220, 151, 0.35);
}

.badge-running.is-paused {
  background: rgba(255, 181, 71, 0.15);
  color: #ffb547;
  border-color: rgba(255, 181, 71, 0.35);
}

/* ========================================================================= */
/* REJEU PCAP : FORMULAIRE ET CONTRÔLES                                      */
/* ========================================================================= */
.form-flow {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

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

.select-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.custom-select {
  width: 100%;
  height: 44px;
  background: #141524;
  color: #ffffff;
  border: 1px solid #2e3047;
  border-radius: 10px;
  padding: 0 36px 0 14px;
  font-size: 13px;
  font-weight: 500;
  outline: none;
  cursor: pointer;
  appearance: none;
  transition: all 0.2s;
}

.custom-select:focus {
  border-color: #5865f2;
  box-shadow: 0 0 0 3px rgba(88, 101, 242, 0.25);
}

.select-arrow {
  position: absolute;
  right: 14px;
  font-size: 10px;
  color: #8b8ea8;
  pointer-events: none;
}

/* Fiche détaillée du scénario */
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

.chip-label {
  color: #7982a9;
}

.chip-val {
  color: #ffffff;
}

/* Sélecteur Segmenté de Vitesse */
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

/* Carte de Progression */
.replay-progress-card {
  background: #121320;
  border: 1px solid #2d3049;
  border-radius: 12px;
  padding: 14px 16px;
}

.progress-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12.5px;
  margin-bottom: 8px;
}

.progress-file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #c4ccff;
}

.progress-glow-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #3ddc97;
  box-shadow: 0 0 8px #3ddc97;
  animation: pulse-dot 1s infinite;
}

.progress-pct {
  font-size: 14px;
  font-weight: 800;
  color: #3ddc97;
}

.progress-track {
  height: 8px;
  background: #1c1d2e;
  border-radius: 999px;
  overflow: hidden;
  position: relative;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #5865f2 0%, #3ddc97 100%);
  border-radius: 999px;
  transition: width 0.3s ease;
  position: relative;
}

.progress-laser {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 12px;
  background: #ffffff;
  box-shadow: 0 0 10px #ffffff;
  opacity: 0.8;
}

.progress-kpi-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.progress-kpi {
  display: flex;
  flex-direction: column;
}

.kpi-label {
  font-size: 10.5px;
  color: #7982a9;
  text-transform: uppercase;
}

.kpi-val {
  font-size: 13px;
  font-weight: 700;
  color: #ffffff;
  margin-top: 2px;
}

/* Commandes */
.controls-row {
  display: flex;
  gap: 10px;
}

.btn-primary-action, .btn-secondary-action, .btn-danger-action {
  height: 44px;
  padding: 0 20px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.btn-primary-action {
  width: 100%;
  background: linear-gradient(135deg, #5865f2 0%, #4a57e0 100%);
  color: #ffffff;
  border: 1px solid #6b77ff;
  box-shadow: 0 4px 16px rgba(88, 101, 242, 0.35);
}

.btn-primary-action:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 22px rgba(88, 101, 242, 0.5);
}

.btn-primary-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary-action {
  flex: 1;
  background: #202235;
  color: #d1d6f5;
  border: 1px solid #363a56;
}

.btn-secondary-action:hover {
  background: #282b44;
  color: #ffffff;
}

.btn-secondary-action.btn-resume {
  background: rgba(61, 220, 151, 0.15);
  color: #3ddc97;
  border-color: rgba(61, 220, 151, 0.35);
}

.btn-danger-action {
  flex: 1;
  background: rgba(255, 77, 126, 0.12);
  color: #ff4d7e;
  border: 1px solid rgba(255, 77, 126, 0.35);
}

.btn-danger-action:hover {
  background: rgba(255, 77, 126, 0.22);
}

/* Lien Terminal IA */
.link-to-terminal-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  border-radius: 10px;
  background: rgba(88, 101, 242, 0.08);
  border: 1px solid rgba(88, 101, 242, 0.22);
  text-decoration: none;
  transition: all 0.2s;
}

.link-to-terminal-card:hover {
  background: rgba(88, 101, 242, 0.16);
  border-color: rgba(88, 101, 242, 0.4);
  transform: translateX(2px);
}

.terminal-card-icon {
  width: 24px;
  height: 24px;
  color: #8fa0ff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.terminal-card-icon svg {
  width: 22px;
  height: 22px;
}

.terminal-card-text {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.terminal-card-text b {
  font-size: 13px;
  color: #ffffff;
}

.terminal-card-text span {
  font-size: 11.5px;
  color: #8b8ea8;
  margin-top: 2px;
}

.terminal-card-arrow {
  font-size: 18px;
  color: #8fa0ff;
}

/* ========================================================================= */
/* CATALOGUE DES SCÉNARIOS                                                   */
/* ========================================================================= */
.catalog-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 12px;
}

.catalog-search-wrap {
  position: relative;
  width: 240px;
}

.search-input-icon {
  position: absolute;
  left: 10px;
  top: 10px;
  width: 14px;
  height: 14px;
  color: #7982a9;
  pointer-events: none;
}

.catalog-search-input {
  width: 100%;
  height: 36px;
  background: #141524;
  border: 1px solid #2e3047;
  border-radius: 8px;
  padding: 0 28px 0 32px;
  font-size: 12px;
  color: #ffffff;
  outline: none;
}

.catalog-search-input:focus {
  border-color: #5865f2;
}

.clear-search-btn {
  position: absolute;
  right: 10px;
  top: 9px;
  font-size: 11px;
  color: #7982a9;
  cursor: pointer;
}

.catalog-cat-chips {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 8px;
  margin-bottom: 12px;
}

.cat-chip-btn {
  height: 28px;
  padding: 0 12px;
  font-size: 11px;
  font-weight: 600;
  border-radius: 6px;
  background: #151726;
  border: 1px solid #292d44;
  color: #8b8ea8;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.cat-chip-btn:hover {
  background: #202337;
  color: #ffffff;
}

.cat-chip-btn.active {
  background: #4a57e0;
  color: #ffffff;
  border-color: #5865f2;
}

.scenario-scroll-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 520px;
  overflow-y: auto;
  padding-right: 4px;
}

.scenario-card-item {
  display: flex;
  background: #151624;
  border: 1px solid #26293f;
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.scenario-card-item:hover {
  background: #1a1c2e;
  border-color: #3b4060;
  transform: translateX(2px);
}

.scenario-card-item.is-selected {
  background: rgba(88, 101, 242, 0.12);
  border-color: #5865f2;
  box-shadow: 0 4px 14px rgba(88, 101, 242, 0.2);
}

.scenario-card-item.is-active-running {
  border-color: #3ddc97;
  box-shadow: 0 0 14px rgba(61, 220, 151, 0.25);
}

.card-item-indicator {
  width: 4px;
  flex-shrink: 0;
}

.card-item-indicator.ind-critical { background: #ff4d7e; }
.card-item-indicator.ind-high     { background: #ff7a45; }
.card-item-indicator.ind-medium   { background: #ffb547; }
.card-item-indicator.ind-info     { background: #3ddc97; }

.card-item-body {
  padding: 12px 14px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.card-item-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.item-name-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.item-title {
  font-size: 13.5px;
  color: #ffffff;
}

.item-desc {
  font-size: 12px;
  color: #8b8ea8;
  margin: 0;
  line-height: 1.4;
}

.item-meta-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  color: #7982a9;
  margin-top: 4px;
}

.meta-filename code {
  color: #c4ccff;
}

.meta-size b {
  color: #eceefa;
}

.meta-selected-badge {
  color: #8fa0ff;
  font-weight: 700;
}

.no-pcaps-matched {
  text-align: center;
  padding: 30px;
  color: #7982a9;
  font-size: 12.5px;
}

/* ========================================================================= */
/* ONGLET 2 : PARC DE SONDES RÉSEAU (SUPERVISION EDGE)                       */
/* ========================================================================= */
.fleet-list-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 18px;
}

.status-filter-pills {
  display: flex;
  gap: 6px;
  background: #121320;
  padding: 4px;
  border-radius: 9px;
  border: 1px solid #282a40;
}

.status-pill-btn {
  height: 28px;
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

.status-pill-btn:hover {
  color: #ffffff;
}

.status-pill-btn.active {
  background: #25283f;
  color: #ffffff;
}

.status-pill-btn.online.active {
  background: rgba(61, 220, 151, 0.2);
  color: #3ddc97;
}

.status-pill-btn.offline.active {
  background: rgba(99, 107, 142, 0.3);
  color: #c4ccff;
}

.pill-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.pill-dot.green {
  background: #3ddc97;
  box-shadow: 0 0 6px #3ddc97;
}

/* État vide avec radar */
.fleet-empty-state {
  text-align: center;
  padding: 48px 24px;
  background: #131422;
  border: 1px dashed #2d3049;
  border-radius: 14px;
  margin-top: 10px;
}

.radar-scan-box {
  position: relative;
  width: 90px;
  height: 90px;
  margin: 0 auto 16px;
  border-radius: 50%;
  border: 1px solid rgba(88, 101, 242, 0.4);
  background: radial-gradient(circle, rgba(88, 101, 242, 0.08) 0%, rgba(15, 16, 23, 0) 70%);
}

.radar-circle {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  border: 1px solid rgba(88, 101, 242, 0.25);
}

.circle-1 { width: 30px; height: 30px; }
.circle-2 { width: 60px; height: 60px; }
.circle-3 { width: 90px; height: 90px; }

.radar-center-dot {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #5865f2;
  box-shadow: 0 0 8px #5865f2;
}

.radar-sweeper {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: conic-gradient(from 0deg, rgba(88, 101, 242, 0.35) 0deg, transparent 60deg, transparent 360deg);
  animation: radar-sweep 3s linear infinite;
}

@keyframes radar-sweep {
  100% { transform: rotate(360deg); }
}

.empty-state-title {
  margin: 0 0 8px;
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
}

.empty-state-text {
  font-size: 12.5px;
  color: #7982a9;
  max-width: 440px;
  margin: 0 auto 18px;
  line-height: 1.5;
}

.empty-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}

/* Cartes de sondes */
.fleet-cards-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sensor-fleet-card {
  background: linear-gradient(180deg, rgba(22, 24, 38, 0.95) 0%, rgba(16, 17, 28, 0.95) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 16px 18px;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.sensor-fleet-card:hover {
  border-color: rgba(255, 255, 255, 0.18);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  transform: translateY(-1px);
}

.sensor-fleet-card.is-online {
  border-left: 3px solid #3ddc97;
}

.sensor-fleet-card.is-replay {
  border-left: 3px solid #5865f2;
}

.sensor-card-top {
  display: flex;
  align-items: center;
  gap: 14px;
}

.sensor-badge-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  background: #1b1d2e;
  border: 1px solid #2e314a;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8fa0ff;
  flex-shrink: 0;
}

.sensor-badge-icon.icon-replay {
  color: #c4b5fd;
  border-color: rgba(155, 92, 246, 0.3);
  background: rgba(155, 92, 246, 0.1);
}

.sensor-svg-type {
  width: 22px;
  height: 22px;
}

.sensor-headline {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sensor-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sensor-title {
  font-size: 15px;
  color: #ffffff;
}

.sensor-status-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 6px;
}

.sensor-status-tag.tag-online {
  background: rgba(61, 220, 151, 0.15);
  color: #3ddc97;
  border: 1px solid rgba(61, 220, 151, 0.35);
}

.sensor-status-tag.tag-idle {
  background: rgba(255, 181, 71, 0.15);
  color: #ffb547;
  border: 1px solid rgba(255, 181, 71, 0.35);
}

.sensor-status-tag.tag-offline {
  background: rgba(99, 107, 142, 0.2);
  color: #8b8ea8;
  border: 1px solid rgba(99, 107, 142, 0.3);
}

.status-indicator-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.tag-online .status-indicator-dot {
  box-shadow: 0 0 6px #3ddc97;
  animation: pulse-dot 1.2s infinite;
}

.sensor-ids-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 11.5px;
}

.sensor-id-pill {
  color: #c4ccff;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.04);
  padding: 2px 8px;
  border-radius: 5px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: all 0.2s;
}

.sensor-id-pill:hover {
  background: rgba(88, 101, 242, 0.2);
  border-color: #5865f2;
}

.copy-small-svg {
  width: 12px;
  height: 12px;
  color: #8fa0ff;
}

.type-pill {
  font-size: 11px;
  color: #7982a9;
}

/* Télémétrie */
.sensor-telemetry-box {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  background: #11121d;
  border: 1px solid #232538;
  border-radius: 9px;
  padding: 10px 14px;
}

@media (max-width: 900px) {
  .sensor-telemetry-box {
    grid-template-columns: repeat(2, 1fr);
  }
}

.telemetry-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.telemetry-lbl-row {
  display: flex;
  align-items: center;
  gap: 5px;
}

.telemetry-icon {
  width: 12px;
  height: 12px;
  color: #7982a9;
}

.telemetry-lbl {
  font-size: 10.5px;
  color: #7982a9;
  text-transform: uppercase;
}

.telemetry-val {
  font-size: 13px;
  font-weight: 700;
  color: #ffffff;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.eth-bullet {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #5865f2;
}

.elapsed-badge {
  font-size: 10.5px;
  color: #8b8ea8;
  font-weight: normal;
}

/* Jauge de ratio */
.sensor-threat-ratio {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ratio-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #7982a9;
}

.ratio-labels b {
  color: #ff4d7e;
}

.threat-ratio-bar {
  height: 5px;
  background: #1c1d2c;
  border-radius: 999px;
  overflow: hidden;
  display: flex;
}

.ratio-fill-danger {
  height: 100%;
  background: #ff4d7e;
  transition: width 0.3s;
}

.ratio-fill-benign {
  height: 100%;
  background: #3ddc97;
  transition: width 0.3s;
}

/* Pied de carte */
.sensor-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.sensor-protocol-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #7982a9;
}

.proto-svg {
  width: 13px;
  height: 13px;
  color: #3ddc97;
}

.btn-sensor-action {
  height: 30px;
  padding: 0 12px;
  font-size: 11.5px;
  font-weight: 600;
  border-radius: 6px;
  background: rgba(88, 101, 242, 0.12);
  border: 1px solid rgba(88, 101, 242, 0.3);
  color: #8fa0ff;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.btn-sensor-action:hover {
  background: #5865f2;
  color: #ffffff;
}

.action-btn-svg {
  width: 12px;
  height: 12px;
}

/* ========================================================================= */
/* CENTRE DE DÉPLOIEMENT (HUB)                                               */
/* ========================================================================= */
.deploy-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.deploy-icon-badge {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: rgba(88, 101, 242, 0.15);
  border: 1px solid rgba(88, 101, 242, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8fa0ff;
}

.deploy-header-svg {
  width: 20px;
  height: 20px;
}

.deploy-method-nav {
  display: flex;
  gap: 8px;
  background: #121320;
  padding: 4px;
  border-radius: 10px;
  border: 1px solid #282a40;
  margin-bottom: 16px;
}

.deploy-tab-btn {
  flex: 1;
  height: 34px;
  border-radius: 7px;
  background: transparent;
  border: none;
  font-size: 12px;
  font-weight: 600;
  color: #8b8ea8;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.2s;
}

.deploy-tab-btn:hover {
  color: #ffffff;
}

.deploy-tab-btn.active {
  background: #5865f2;
  color: #ffffff;
  box-shadow: 0 2px 10px rgba(88, 101, 242, 0.35);
}

.method-svg {
  width: 14px;
  height: 14px;
}

.arch-flow-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #11121d;
  border: 1px solid #232538;
  border-radius: 10px;
  padding: 10px 14px;
  margin-bottom: 16px;
}

.flow-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.flow-svg {
  width: 16px;
  height: 16px;
  color: #8fa0ff;
}

.flow-label {
  font-size: 10px;
  color: #7982a9;
  font-weight: 600;
}

.flow-arrow {
  color: #4a57e0;
  font-size: 14px;
  font-weight: 800;
}

.deploy-steps-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.deploy-step {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.step-badge {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #5865f2;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
  flex-shrink: 0;
  margin-top: 1px;
}

.step-content {
  flex: 1;
}

.step-title {
  display: block;
  font-size: 13px;
  color: #ffffff;
}

.step-desc {
  margin: 3px 0 6px;
  font-size: 11.5px;
  color: #8b8ea8;
  line-height: 1.4;
}

.code-box-wrapper {
  position: relative;
  background: #0d0e16;
  border: 1px solid #23253b;
  border-radius: 8px;
  overflow: hidden;
}

.code-block {
  margin: 0;
  padding: 10px 12px;
  padding-right: 64px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 11.5px;
  color: #c4ccff;
  line-height: 1.45;
  white-space: pre-wrap;
  word-break: break-all;
}

.btn-copy-code {
  position: absolute;
  top: 6px;
  right: 6px;
  height: 24px;
  padding: 0 8px;
  font-size: 10.5px;
  font-weight: 700;
  background: #25283f;
  color: #eceefa;
  border: 1px solid #3c4266;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-copy-code:hover {
  background: #5865f2;
  color: #ffffff;
}

.deploy-tip-box {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: rgba(255, 181, 71, 0.08);
  border: 1px solid rgba(255, 181, 71, 0.2);
  border-radius: 8px;
  padding: 10px 12px;
  margin-top: 18px;
}

.tip-svg {
  width: 18px;
  height: 18px;
  color: #ffb547;
  flex-shrink: 0;
  margin-top: 2px;
}

.tip-body {
  font-size: 11.5px;
  color: #ffb547;
  line-height: 1.4;
}

.tip-body b {
  color: #ffd08a;
  display: block;
  margin-bottom: 2px;
}

/* ========================================================================= */
/* CLASSES UTILITAIRES DE COULEURS & BADGES                                  */
/* ========================================================================= */
.text-accent  { color: #5865f2 !important; }
.text-success { color: #3ddc97 !important; }
.text-danger  { color: #ff4d7e !important; }
.text-warning { color: #ffb547 !important; }
.text-orange  { color: #ff7a45 !important; }
.text-purple  { color: #b266ff !important; }
.text-blue    { color: #6c8cff !important; }
.text-muted   { color: #7982a9 !important; }

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
</style>
