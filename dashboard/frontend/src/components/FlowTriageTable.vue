<template>
  <div class="obsidian-panel flex flex-col flex-1 min-h-[320px] overflow-hidden">
    <!-- Table Header & Filter Toolbar -->
    <div class="px-5 py-3 border-b border-zinc-800/80 flex flex-wrap items-center justify-between gap-3.5 bg-zinc-900/60">
      <!-- Tabs -->
      <div class="flex items-center space-x-1.5 bg-zinc-950 p-1 rounded-md border border-zinc-800">
        <button
          @click="store.activeTab = 'triage'"
          class="px-3.5 py-1.5 text-xs font-semibold rounded transition duration-150 flex items-center space-x-2 cursor-pointer"
          :class="store.activeTab === 'triage' ? 'bg-zinc-800 text-zinc-100 shadow-sm' : 'text-zinc-400 hover:text-zinc-200'"
        >
          <span>Security Incidents</span>
          <span class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-zinc-900 border border-zinc-700 text-zinc-300">
            {{ store.filteredAlerts.length }}
          </span>
        </button>

        <!-- TAB CRIMINELS / THREAT ACTORS -->
        <button
          @click="store.activeTab = 'threat-actors'"
          class="px-3.5 py-1.5 text-xs font-semibold rounded transition duration-150 flex items-center space-x-2 cursor-pointer"
          :class="store.activeTab === 'threat-actors' ? 'bg-red-500/20 text-red-300 border border-red-500/30 shadow-sm' : 'text-zinc-400 hover:text-zinc-200'"
        >
          <Flame :size="12" class="text-red-400" />
          <span>Threat Actors (Criminels)</span>
          <span class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-zinc-900 border border-zinc-700 text-red-300 font-bold">
            {{ store.filteredThreatActors.length }}
          </span>
        </button>

        <button
          @click="store.activeTab = 'flows'"
          class="px-3.5 py-1.5 text-xs font-semibold rounded transition duration-150 flex items-center space-x-2 cursor-pointer"
          :class="store.activeTab === 'flows' ? 'bg-zinc-800 text-zinc-100 shadow-sm' : 'text-zinc-400 hover:text-zinc-200'"
        >
          <span>Real-time Flows</span>
          <span class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-zinc-900 border border-zinc-700 text-zinc-300">
            {{ store.filteredFlows.length }}
          </span>
        </button>

        <button
          @click="store.activeTab = 'replay'"
          class="px-3.5 py-1.5 text-xs font-semibold rounded transition duration-150 cursor-pointer"
          :class="store.activeTab === 'replay' ? 'bg-zinc-800 text-zinc-100 shadow-sm' : 'text-zinc-400 hover:text-zinc-200'"
        >
          PCAP Replay Lab
        </button>
      </div>

      <!-- Severity Filter Pills & Loopback status & Ergonomics -->
      <div v-if="store.activeTab !== 'replay'" class="flex items-center space-x-3 text-[11px] font-mono">
        <span v-if="store.excludeLoopback" class="text-zinc-500 text-[10px] hidden sm:inline">
          (Loopback 127.0.0.1 filtered)
        </span>

        <div class="flex items-center space-x-1.5">
          <button
            v-for="sev in ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'BENIGN']"
            :key="sev"
            @click="store.selectedSeverityFilter = sev"
            class="px-2.5 py-1 rounded uppercase border transition duration-150 cursor-pointer font-medium"
            :class="store.selectedSeverityFilter === sev ? activeFilterClass(sev) : 'bg-zinc-950 text-zinc-500 border-zinc-800 hover:text-zinc-300'"
          >
            {{ sev }}
          </button>
        </div>

        <!-- Quick Layout & Density Toggles -->
        <div class="hidden md:flex items-center space-x-1.5 border-l border-zinc-800 pl-3">
          <button
            @click="store.toggleDensity"
            class="p-1.5 rounded text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition duration-150 cursor-pointer"
            :title="'Table Row Density: ' + store.tableDensity"
          >
            <Rows :size="13" />
          </button>
          <button
            @click="store.toggleCharts"
            class="p-1.5 rounded text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition duration-150 cursor-pointer"
            :title="store.chartsVisible ? 'Collapse charts (Maximize Table)' : 'Show charts'"
          >
            <Maximize2 v-if="store.chartsVisible" :size="13" />
            <Minimize2 v-else :size="13" />
          </button>
        </div>
      </div>
    </div>

    <!-- Animated Tab Content Transition -->
    <Transition name="tab-fade" mode="out-in">
      <!-- TAB 1: Consolidated Security Incidents -->
      <div v-if="store.activeTab === 'triage'" key="triage" class="flex-1 overflow-auto">
      <table class="w-full text-left border-collapse">
        <thead class="sticky top-0 bg-zinc-950/95 backdrop-blur border-b border-zinc-800 z-10 select-none">
          <tr class="text-[11px] font-semibold uppercase tracking-wider text-zinc-400">
            <th class="py-2.5 px-4 w-28">Timestamp</th>
            <th class="py-2.5 px-4 w-24">Severity</th>
            <th class="py-2.5 px-4">Attack / Vector</th>
            <th class="py-2.5 px-4">Source IP & Port</th>
            <th class="py-2.5 px-4">Target IP & Ports</th>
            <th class="py-2.5 px-4 text-right">Flows</th>
            <th class="py-2.5 px-4 text-right">Max Conf</th>
            <th class="py-2.5 px-4 text-right">Max RMSE</th>
            <th class="py-2.5 px-4 text-center w-24">Status</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-800/50 text-xs font-mono">
          <!-- Loading Skeleton -->
          <tr v-if="store.isLoading" v-for="n in 5" :key="'skel-inc-' + n" class="animate-pulse">
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-20"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-16"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-32"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-28"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-28"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-10 ml-auto"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-12 ml-auto"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-12 ml-auto"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-16 mx-auto"></div></td>
          </tr>

          <!-- Data Rows -->
          <tr
            v-else
            v-for="inc in store.filteredAlerts"
            :key="inc.id || inc.incident_code"
            @click="openIncidentDetails(inc)"
            class="hover:bg-zinc-800/40 cursor-pointer transition duration-75 group"
            :class="inc.severity === 'CRITICAL' ? 'border-l-2 border-l-red-500' : ''"
          >
            <td :class="padClass" class="text-zinc-400 tabular-nums whitespace-nowrap">
              {{ formatTimestamp(inc.updated_at || inc.created_at) }}
            </td>
            <td :class="padClass">
              <span class="px-2 py-0.5 text-[10px] font-semibold uppercase rounded border inline-block" :class="severityBadgeClass(inc.severity)">
                {{ inc.severity }}
              </span>
            </td>
            <td :class="padClass" class="text-zinc-200 font-medium">
              <div class="flex items-center space-x-2">
                <span>{{ inc.attack_type }}</span>
                <span v-if="inc.is_zero_day" class="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-semibold">
                  0-DAY
                </span>
              </div>
            </td>
            <td :class="padClass" class="text-zinc-300 tabular-nums">
              {{ inc.src_ip }}
            </td>
            <td :class="padClass" class="text-zinc-300 tabular-nums truncate max-w-xs" :title="inc.targeted_ports || inc.ports_summary || ''">
              {{ inc.dst_ip }}:<span class="text-zinc-500">{{ inc.targeted_ports || inc.ports_summary || 'Multi' }}</span>
            </td>
            <td :class="padClass" class="text-right text-zinc-300 tabular-nums">
              {{ inc.flow_count || 1 }}
            </td>
            <td :class="[padClass, inc.max_confidence > 0.8 ? 'text-red-400 font-semibold' : 'text-zinc-400']" class="text-right tabular-nums">
              {{ formatScore(inc.max_confidence) }}
            </td>
            <td :class="padClass" class="text-right tabular-nums text-zinc-400">
              {{ formatScore(inc.max_mse) }}
            </td>
            <td :class="padClass" class="text-center">
              <span class="text-[10px] uppercase px-2 py-0.5 rounded font-mono border" :class="statusPillClass(inc.status)">
                {{ inc.status }}
              </span>
            </td>
          </tr>

          <!-- Clear Contextual Empty State -->
          <tr v-if="!store.isLoading && store.filteredAlerts.length === 0">
            <td colspan="9" class="py-10 text-center text-zinc-400 font-mono text-xs">
              <div class="flex flex-col items-center justify-center space-y-2 max-w-md mx-auto">
                <ShieldAlert :size="22" class="text-zinc-600 mb-0.5" />
                <div v-if="store.searchQuery" class="space-y-1">
                  <div class="font-semibold text-zinc-300">No security incidents match "{{ store.searchQuery }}"</div>
                  <div class="text-[11px] text-zinc-500">Broaden your query or search by victim IP or attack signature.</div>
                  <button
                    @click="store.searchQuery = ''"
                    class="mt-2 px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-700 rounded text-xs transition duration-100"
                  >
                    Clear Search Filter
                  </button>
                </div>
                <div v-else-if="store.selectedSeverityFilter !== 'ALL'" class="space-y-1">
                  <div class="font-semibold text-zinc-300">No security incidents with severity "{{ store.selectedSeverityFilter }}"</div>
                  <div class="text-[11px] text-zinc-500">There are currently no active incidents at this severity grade.</div>
                  <button
                    @click="store.selectedSeverityFilter = 'ALL'"
                    class="mt-2 px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-700 rounded text-xs transition duration-100"
                  >
                    Show All Severities
                  </button>
                </div>
                <div v-else-if="store.excludeLoopback && store.alerts.length > 0" class="space-y-1">
                  <div class="font-semibold text-zinc-300">Local loopback (127.0.0.1) incidents are hidden</div>
                  <div class="text-[11px] text-zinc-500">{{ store.alerts.length }} local simulation events are filtered by the anti-noise rule.</div>
                  <button
                    @click="store.toggleLoopbackFilter()"
                    class="mt-2 px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-700 rounded text-xs transition duration-100"
                  >
                    Include Local 127.0.0.1 Events
                  </button>
                </div>
                <div v-else class="space-y-1">
                  <div class="font-semibold text-zinc-300">Perimeter Clean &bull; Zero Active Incidents</div>
                  <div class="text-[11px] text-zinc-500">The NIDS pipeline is active. No hostile vector has breached detection thresholds.</div>
                  <button
                    @click="store.activeTab = 'replay'"
                    class="mt-2 px-3 py-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-700 rounded text-xs transition duration-100 flex items-center space-x-1.5 mx-auto"
                  >
                    <Play :size="12" />
                    <span>Launch Attack Simulation in PCAP Lab</span>
                  </button>
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- TAB 2: Threat Actors (Liste des Criminels) -->
    <div v-else-if="store.activeTab === 'threat-actors'" key="threat-actors" class="flex-1 overflow-auto">
      <table class="w-full text-left border-collapse">
        <thead class="sticky top-0 bg-zinc-950/95 backdrop-blur border-b border-zinc-800 z-10 select-none">
          <tr class="text-[11px] font-semibold uppercase tracking-wider text-zinc-400">
            <th class="py-2.5 px-4 w-20">Rank</th>
            <th class="py-2.5 px-4">Offender Source IP</th>
            <th class="py-2.5 px-4 text-right">Total Attacks</th>
            <th class="py-2.5 px-4">Threat Signatures Triggered</th>
            <th class="py-2.5 px-4">Targeted Victim Hosts & Ports</th>
            <th class="py-2.5 px-4 text-right">Max Conf</th>
            <th class="py-2.5 px-4 text-right">Kitsune RMSE</th>
            <th class="py-2.5 px-4 text-center w-28">Threat Level</th>
            <th class="py-2.5 px-4 text-center w-28">SOC Action</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-800/50 text-xs font-mono">
          <!-- Loading Skeleton -->
          <tr v-if="store.isLoading" v-for="n in 5" :key="'skel-actor-' + n" class="animate-pulse">
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-8"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-28"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-12 ml-auto"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-36"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-32"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-12 ml-auto"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-12 ml-auto"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-16 mx-auto"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-14 mx-auto"></div></td>
          </tr>

          <!-- Data Rows -->
          <tr
            v-else
            v-for="actor in store.filteredThreatActors"
            :key="actor.src_ip"
            class="hover:bg-zinc-800/40 transition duration-75 group"
            :class="actor.severity === 'CRITICAL' ? 'border-l-2 border-l-red-500' : ''"
          >
            <!-- Rank -->
            <td :class="padClass" class="text-zinc-500 font-bold tabular-nums">
              #{{ actor.rank }}
            </td>

            <!-- Criminal IP -->
            <td :class="padClass">
              <div class="flex items-center space-x-2.5">
                <span class="font-bold text-red-300 tabular-nums">{{ actor.src_ip }}</span>
                <span
                  class="text-[9px] px-1.5 py-0.2 rounded uppercase border font-semibold"
                  :class="actor.is_loopback ? 'bg-zinc-800 text-zinc-400 border-zinc-700' : 'bg-red-500/20 text-red-300 border-red-500/30'"
                >
                  {{ actor.is_loopback ? 'Local Simulation' : 'Threat Actor' }}
                </span>
              </div>
            </td>

            <!-- Attack Count -->
            <td :class="padClass" class="text-right tabular-nums">
              <span class="text-base font-extrabold text-red-400">{{ actor.total_attacks }}</span>
              <span class="text-[10px] text-zinc-500 block">flows</span>
            </td>

            <!-- Threat Signatures -->
            <td :class="padClass">
              <div class="flex flex-wrap gap-1.5 max-w-xs">
                <span
                  v-for="threat in actor.threat_classes"
                  :key="threat"
                  class="text-[10px] px-2 py-0.5 rounded border uppercase"
                  :class="threat === 'BENIGN' ? 'bg-zinc-800 text-zinc-400 border-zinc-700' : 'bg-red-500/10 text-red-300 border-red-500/30 font-semibold'"
                  :title="threat"
                >
                  {{ threat }}
                </span>
              </div>
            </td>

            <!-- Target Victim Endpoint -->
            <td :class="padClass" class="text-zinc-300 tabular-nums">
              <span class="text-zinc-200 font-medium">{{ actor.victim_count }} victim(s)</span>
              <div class="text-[11px] text-zinc-500 truncate max-w-xs mt-0.5" :title="actor.targeted_ports?.join(', ') || ''">
                Ports: <span class="text-orange-400 font-medium">{{ actor.targeted_ports_summary }}</span>
              </div>
            </td>

            <!-- Max Confidence -->
            <td :class="padClass" class="text-right tabular-nums text-zinc-300">
              {{ formatScore(actor.max_confidence) }}
            </td>

            <!-- Kitsune RMSE -->
            <td :class="padClass" class="text-right tabular-nums text-zinc-400">
              {{ formatScore(actor.max_mse) }}
            </td>

            <!-- Severity -->
            <td :class="padClass" class="text-center">
              <span class="px-2.5 py-0.5 text-[10px] font-semibold uppercase rounded border inline-block" :class="severityBadgeClass(actor.severity)">
                {{ actor.severity }}
              </span>
            </td>

            <!-- Action -->
            <td :class="padClass" class="text-center">
              <button
                @click="store.filterByIp(actor.src_ip)"
                class="px-2.5 py-1 text-[11px] font-semibold rounded bg-zinc-900 border border-zinc-700 text-zinc-200 hover:bg-zinc-800 hover:text-white transition duration-150 flex items-center space-x-1 mx-auto cursor-pointer"
                title="Filter all recent flows by this attacker IP"
              >
                <Search :size="11" />
                <span>Filter</span>
              </button>
            </td>
          </tr>

          <!-- Contextual Empty State for Threat Actors -->
          <tr v-if="!store.isLoading && store.filteredThreatActors.length === 0">
            <td colspan="9" class="py-10 text-center text-zinc-400 font-mono text-xs">
              <div class="flex flex-col items-center justify-center space-y-2 max-w-md mx-auto">
                <Flame :size="22" class="text-zinc-600 mb-0.5" />
                <div v-if="store.searchQuery" class="space-y-1">
                  <div class="font-semibold text-zinc-300">No threat actors match "{{ store.searchQuery }}"</div>
                  <div class="text-[11px] text-zinc-500">Check IP address spelling or clear the active query.</div>
                  <button
                    @click="store.searchQuery = ''"
                    class="mt-2 px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-700 rounded text-xs transition duration-100"
                  >
                    Clear Search Filter
                  </button>
                </div>
                <div v-else class="space-y-1">
                  <div class="font-semibold text-zinc-300">No Hostile Threat Actors Identified</div>
                  <div class="text-[11px] text-zinc-500">All observed source endpoints conform to normal traffic baselines.</div>
                  <button
                    @click="store.activeTab = 'replay'"
                    class="mt-2 px-3 py-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-700 rounded text-xs transition duration-100 flex items-center space-x-1.5 mx-auto"
                  >
                    <Play :size="12" />
                    <span>Replay Attack PCAP to Populate Threat Actors</span>
                  </button>
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- TAB 3: Real-Time Flow Stream -->
    <div v-else-if="store.activeTab === 'flows'" key="flows" class="flex-1 overflow-auto">
      <table class="w-full text-left border-collapse">
        <thead class="sticky top-0 bg-zinc-950/95 backdrop-blur border-b border-zinc-800 z-10 select-none">
          <tr class="text-[11px] font-semibold uppercase tracking-wider text-zinc-400">
            <th class="py-2.5 px-4 w-24">Time</th>
            <th class="py-2.5 px-4 w-20">Severity</th>
            <th class="py-2.5 px-4">5-Tuple (Src &rarr; Dst:Port)</th>
            <th class="py-2.5 px-4 w-16">Proto</th>
            <th class="py-2.5 px-4">Engine</th>
            <th class="py-2.5 px-4">Verdict</th>
            <th class="py-2.5 px-4 text-right">Confidence</th>
            <th class="py-2.5 px-4 text-right">Kitsune RMSE</th>
            <th class="py-2.5 px-4 text-right">Packets</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-zinc-800/50 text-xs font-mono">
          <!-- Loading Skeleton -->
          <tr v-if="store.isLoading" v-for="n in 5" :key="'skel-flow-' + n" class="animate-pulse">
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-16"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-14"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-36"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-8"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-16"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-20"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-12 ml-auto"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-12 ml-auto"></div></td>
            <td :class="padClass"><div class="h-3.5 bg-zinc-800/60 rounded w-8 ml-auto"></div></td>
          </tr>

          <!-- Data Rows -->
          <tr
            v-else
            v-for="flow in store.filteredFlows"
            :key="flow.id"
            @click="store.openForensics(flow.id)"
            class="hover:bg-zinc-800/40 cursor-pointer transition duration-75"
            :class="flow.severity === 'CRITICAL' ? 'border-l-2 border-l-red-500' : ''"
          >
            <td :class="padClass" class="text-zinc-400 tabular-nums whitespace-nowrap">
              {{ formatTimestamp(flow.received_at) }}
            </td>
            <td :class="padClass">
              <span class="px-2 py-0.5 text-[10px] font-semibold uppercase rounded border inline-block" :class="severityBadgeClass(flow.severity)">
                {{ flow.severity }}
              </span>
            </td>
            <td :class="padClass" class="text-zinc-300 tabular-nums">
              {{ flow.src_ip }}:{{ flow.src_port }} &rarr; {{ flow.dst_ip }}:<span class="text-zinc-100 font-semibold">{{ flow.dst_port }}</span>
            </td>
            <td :class="padClass" class="text-zinc-400">
              {{ formatProto(flow.protocol || flow.proto) }}
            </td>
            <td :class="padClass" class="text-zinc-400">
              {{ flow.engine || 'DNN-1D' }}
            </td>
            <td :class="[padClass, flow.pred !== 'BENIGN' ? 'text-red-400' : 'text-zinc-400']" class="font-medium">
              {{ flow.pred }}
            </td>
            <td :class="padClass" class="text-right tabular-nums text-zinc-300">
              {{ formatScore(flow.confiance) }}
            </td>
            <td :class="padClass" class="text-right tabular-nums text-zinc-400">
              {{ formatScore(flow.mse_ae) }}
            </td>
            <td :class="padClass" class="text-right tabular-nums text-zinc-400">
              {{ flow.packet_count || 1 }}
            </td>
          </tr>

          <!-- Contextual Empty State for Flows -->
          <tr v-if="!store.isLoading && store.filteredFlows.length === 0">
            <td colspan="9" class="py-10 text-center text-zinc-400 font-mono text-xs">
              <div class="flex flex-col items-center justify-center space-y-2 max-w-md mx-auto">
                <Radio :size="22" class="text-zinc-600 mb-0.5" />
                <div v-if="store.searchQuery" class="space-y-1">
                  <div class="font-semibold text-zinc-300">No flows match filter "{{ store.searchQuery }}"</div>
                  <div class="text-[11px] text-zinc-500">Check IP address or port number.</div>
                  <button
                    @click="store.searchQuery = ''"
                    class="mt-2 px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-700 rounded text-xs transition duration-100"
                  >
                    Clear Filter
                  </button>
                </div>
                <div v-else-if="store.selectedSeverityFilter !== 'ALL'" class="space-y-1">
                  <div class="font-semibold text-zinc-300">No flows with severity "{{ store.selectedSeverityFilter }}"</div>
                  <button
                    @click="store.selectedSeverityFilter = 'ALL'"
                    class="mt-2 px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-700 rounded text-xs transition duration-100"
                  >
                    Show All Severities
                  </button>
                </div>
                <div v-else-if="store.excludeLoopback && store.flows.length > 0" class="space-y-1">
                  <div class="font-semibold text-zinc-300">Loopback (127.0.0.1) flows are filtered out</div>
                  <div class="text-[11px] text-zinc-500">{{ store.flows.length }} loopback packets are hidden to reduce noise.</div>
                  <button
                    @click="store.toggleLoopbackFilter()"
                    class="mt-2 px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-700 rounded text-xs transition duration-100"
                  >
                    Include 127.0.0.1 Flows
                  </button>
                </div>
                <div v-else class="space-y-1">
                  <div class="font-semibold text-zinc-300">Awaiting Inbound Network Packets</div>
                  <div class="text-[11px] text-zinc-500">Live sensor is active on interface {{ store.activeSensor?.interface || 'eth0' }}.</div>
                  <button
                    @click="store.activeTab = 'replay'"
                    class="mt-2 px-3 py-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-700 rounded text-xs transition duration-100 flex items-center space-x-1.5 mx-auto"
                  >
                    <Play :size="12" />
                    <span>Run PCAP Replay Lab</span>
                  </button>
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- TAB 4: PCAP Replay Lab -->
    <div v-else-if="store.activeTab === 'replay'" key="replay" class="flex-1 p-4 overflow-auto">
      <div class="max-w-3xl space-y-4">
        <div class="text-xs text-zinc-400 leading-relaxed">
          Simulate real offensive traffic flows through the full Cascaded NIDS Pipeline (Stage 1 CatBoost/XGBoost, Stage 2 DNN-1D, Kitsune KitNET Anomaly, and DPI Content Inspector). Select any generated attack PCAP below:
        </div>

        <div v-if="store.replayStatus" class="p-2.5 rounded bg-zinc-900 border border-zinc-800 text-xs font-mono text-emerald-400 flex items-center justify-between">
          <span>{{ store.replayStatus }}</span>
          <span v-if="store.isReplaying" class="animate-pulse">Replaying packets...</span>
        </div>

        <div class="space-y-2">
          <div
            v-for="pcap in store.availablePcaps"
            :key="pcap.filename"
            class="p-3 obsidian-panel flex items-center justify-between hover:bg-zinc-800/40 transition duration-100"
          >
            <div>
              <div class="text-xs font-mono font-semibold text-zinc-200">{{ pcap.filename }}</div>
              <div class="text-[11px] font-mono text-zinc-500 mt-0.5">
                Size: {{ pcap.size_kb }} KB &bull; Path: {{ pcap.path }}
              </div>
            </div>

            <div class="flex items-center space-x-2">
              <button
                @click="store.triggerReplay(pcap.path, 1.0)"
                :disabled="store.isReplaying"
                class="px-3 py-1.5 text-xs font-semibold rounded border border-zinc-700 bg-zinc-800 text-zinc-100 hover:bg-zinc-700 disabled:opacity-50 transition duration-100 flex items-center space-x-1.5"
              >
                <Play :size="12" />
                <span>Replay 1x</span>
              </button>
            </div>
          </div>

          <div v-if="store.availablePcaps.length === 0" class="py-6 text-center text-zinc-500 font-mono text-xs">
            No PCAP files detected in pcap/ or data/samples/. Run `python scripts/run_demo_suite.py` to generate attack PCAPs.
          </div>
        </div>
      </div>
    </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed } from "vue"
import { useSocStore } from "@/stores/socStore"
import { Play, Flame, Search, ShieldAlert, RotateCcw, Radio, Rows, Maximize2, Minimize2 } from "lucide-vue-next"

const store = useSocStore()

const padClass = computed(() => (store.tableDensity === "compact" ? "py-2 px-4" : "py-3 px-4"))

function formatTimestamp(ts) {
  if (!ts) return "--:--:--"
  const date = new Date(ts > 1e11 ? ts : ts * 1000)
  return date.toTimeString().split(" ")[0]
}

function formatScore(score) {
  if (score === undefined || score === null || isNaN(score)) return "0.000"
  return Number(score).toFixed(3)
}

function formatProto(p) {
  if (p === 6 || p === "6" || p === "TCP") return "TCP"
  if (p === 17 || p === "17" || p === "UDP") return "UDP"
  if (p === 1 || p === "1" || p === "ICMP") return "ICMP"
  return p || "IP"
}

function severityBadgeClass(sev) {
  switch (sev) {
    case "CRITICAL":
      return "badge-critical"
    case "HIGH":
      return "badge-high"
    case "MEDIUM":
      return "badge-medium"
    case "LOW":
      return "badge-low"
    default:
      return "badge-benign"
  }
}

function statusPillClass(status) {
  switch (status) {
    case "OPEN":
      return "bg-red-500/10 text-red-400 border-red-500/30"
    case "INVESTIGATING":
      return "bg-amber-500/10 text-amber-400 border-amber-500/30"
    case "RESOLVED":
      return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
    default:
      return "bg-zinc-800 text-zinc-400 border-zinc-700"
  }
}

function activeFilterClass(sev) {
  switch (sev) {
    case "CRITICAL":
      return "bg-red-500/20 text-red-300 border-red-500/40"
    case "HIGH":
      return "bg-orange-500/20 text-orange-300 border-orange-500/40"
    case "MEDIUM":
      return "bg-amber-500/20 text-amber-300 border-amber-500/40"
    case "LOW":
      return "bg-sky-500/20 text-sky-300 border-sky-500/40"
    case "BENIGN":
      return "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
    default:
      return "bg-zinc-700 text-zinc-100 border-zinc-600"
  }
}

function openIncidentDetails(inc) {
  const flowId = inc.flow_id || (inc.associated_flows && inc.associated_flows[0]?.id)
  if (flowId) {
    store.openForensics(flowId)
  }
}
</script>
