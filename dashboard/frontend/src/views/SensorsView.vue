<template>
  <main>
    <div class="card" style="margin-bottom: 16px;">
      <h2>
        Sensor Fleet &amp; Traffic Capture Management
        <span>{{ store.sensorsOnline }} Sensors Active</span>
      </h2>
      <p style="color:var(--mu); font-size: 13px; margin: 0;">
        Orchestrate edge sensors, ingest bidirectional network flows, and run offline PCAP traffic replays.
      </p>
    </div>

    <section class="grid">
      <!-- PCAP Replay Manager -->
      <div class="card c6">
        <h2>Traffic Replay Engine (PCAP)</h2>
        <div style="display:flex; flex-direction:column; gap: 12px; margin-top: 8px;">
          <div>
            <label style="display:block; font-size:12px; color:var(--mu); margin-bottom:4px;">Capture File</label>
            <select v-model="selectedPcap" style="width:100%;" :disabled="store.replayStatus.active">
              <option value="">Select a PCAP capture...</option>
              <option v-for="p in store.pcapFiles" :key="p.filename" :value="p.filename">
                {{ p.filename }} ({{ p.size_mb }} MB)
              </option>
            </select>
          </div>

          <div>
            <label style="display:block; font-size:12px; color:var(--mu); margin-bottom:4px;">Replay Speed</label>
            <div class="rng">
              <button 
                v-for="s in [0.5, 1.0, 2.0, 5.0]" 
                :key="s"
                :class="{ active: replaySpeed === s }"
                @click="replaySpeed = s"
                :disabled="store.replayStatus.active"
              >
                {{ s }}x
              </button>
            </div>
          </div>

          <!-- Progress -->
          <div v-if="store.replayStatus.active" style="margin-top: 8px;">
            <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">
              <span>Progress: {{ store.replayStatus.pcap_name }}</span>
              <b>{{ store.replayStatus.progress_pct.toFixed(1) }}%</b>
            </div>
            <div class="bar2"><i :style="{ width: `${store.replayStatus.progress_pct}%` }"></i></div>
            <div style="display:flex; justify-content:space-between; font-size:12px; color:var(--mu); margin-top:6px;">
              <span>Processed flows: {{ store.replayStatus.processed_flows }}</span>
              <span>Speed: {{ store.replayStatus.speed }}x</span>
            </div>
          </div>

          <div style="margin-top: 10px;">
            <button 
              v-if="!store.replayStatus.active"
              class="pri" 
              style="width:100%;" 
              :disabled="!selectedPcap"
              @click="store.startPcapReplay(selectedPcap, replaySpeed)"
            >
              Start Replay
            </button>
            <button 
              v-else
              class="sec" 
              style="width:100%; border-color:var(--cr); color:var(--cr);"
              @click="store.stopPcapReplay"
            >
              Stop Replay
            </button>
          </div>
        </div>
      </div>

      <!-- Sensor Fleet List -->
      <div class="card c6">
        <h2>Active Sensor Fleet</h2>
        <div style="display:flex; flex-direction:column; gap: 8px; margin-top: 8px;">
          <div v-for="s in sensors" :key="s.id" class="li" style="padding: 10px 0;">
            <div>
              <div style="display:flex; align-items:center; gap:8px;">
                <span class="dot"></span>
                <b>{{ s.id }}</b>
              </div>
              <small style="color:var(--mu);">{{ s.interface }} &bull; {{ s.ip }}</small>
            </div>
            <div style="text-align:right;">
              <span class="sev Low">{{ s.status }}</span>
              <div style="font-size:11px; color:var(--mu); margin-top:2px;">{{ s.flows }} flows/s</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup>
import { ref } from 'vue'
import { useSocStore } from '@/stores/socStore'

const store = useSocStore()
const selectedPcap = ref('')
const replaySpeed = ref(1.0)

const sensors = [
  { id: 'sensor-edge-01', interface: 'eth0 (10 GbE)', ip: '10.0.1.10', status: 'Online', flows: 540 },
  { id: 'sensor-edge-02', interface: 'eth1 (10 GbE)', ip: '10.0.1.11', status: 'Online', flows: 410 },
  { id: 'sensor-dmz-01',  interface: 'ens3 (1 GbE)',  ip: '10.0.2.5',  status: 'Online', flows: 230 },
  { id: 'sensor-core-01', interface: 'ens4 (10 GbE)', ip: '10.0.0.1',  status: 'Online', flows: 890 }
]
</script>
