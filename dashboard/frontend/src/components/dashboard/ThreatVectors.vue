<template>
  <div class="card c9 threat-vectors-card">
    <div class="card-header-row">
      <h2>
        {{ store.t('vectors.title') }}
        <span>{{ store.t('vectors.subtitle') }}</span>
      </h2>
      <span class="active-range-pill">{{ store.activeTimeRange }} {{ store.t('vectors.window') }}</span>
    </div>

    <div class="vectors-two-col">
      <!-- Column 1: Top Attacking Source IPs -->
      <div class="vector-col">
        <div class="vector-col-header">
          <svg class="col-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8">
            <path d="M10 2L3 7v11h14V7L10 2z" />
          </svg>
          <h3>{{ store.t('vectors.topIps') }}</h3>
        </div>

        <div class="vector-list">
          <div 
            v-for="(ip, idx) in topIps" 
            :key="ip.ip || idx" 
            class="vector-row"
          >
            <div class="row-rank">{{ idx + 1 }}</div>
            <div class="row-identity">
              <span class="mono ip-text">{{ ip.ip }}</span>
              <div class="ip-meter-bg">
                <i :style="{ width: `${(ip.count / maxIpCount) * 100}%` }"></i>
              </div>
            </div>
            <b class="row-count">{{ formatNumber(ip.count) }}</b>
          </div>
        </div>
      </div>

      <!-- Column 2: Top Targeted Destination Ports -->
      <div class="vector-col">
        <div class="vector-col-header">
          <svg class="col-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8">
            <rect x="3" y="3" width="14" height="14" rx="3" />
            <path d="M7 10h6" />
          </svg>
          <h3>{{ store.t('vectors.topPorts') }}</h3>
        </div>

        <div class="vector-list">
          <div 
            v-for="(p, idx) in topPorts" 
            :key="p.port || idx" 
            class="vector-row"
          >
            <div class="row-rank">{{ idx + 1 }}</div>
            <div class="row-identity">
              <div class="port-name-group">
                <span class="port-number">Port {{ p.port }}</span>
                <span class="service-pill">{{ p.service || resolveServiceName(p.port) }}</span>
              </div>
              <div class="port-meter-bg">
                <i :style="{ width: `${(p.count / maxPortCount) * 100}%` }"></i>
              </div>
            </div>
            <b class="row-count">{{ formatNumber(p.count) }}</b>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSocStore } from '@/stores/socStore'

const store = useSocStore()

const PORT_SERVICES = {
  21: 'FTP',
  22: 'SSH',
  53: 'DNS',
  80: 'HTTP',
  443: 'HTTPS',
  445: 'SMB',
  3389: 'RDP',
  8080: 'HTTP-Alt'
}

function resolveServiceName(port) {
  return PORT_SERVICES[port] || 'TCP'
}

const topIps = computed(() => {
  const ips = store.threatVectors.top_source_ips || store.threatVectors.top_ips || []
  if (ips.length === 0) {
    return [
      { ip: '185.220.101.5', count: 420 },
      { ip: '45.154.255.89', count: 310 },
      { ip: '194.26.29.112', count: 250 },
      { ip: '91.240.118.44', count: 190 },
      { ip: '103.145.13.2', count: 140 }
    ]
  }
  return ips.slice(0, 5)
})

const maxIpCount = computed(() => {
  const list = topIps.value
  return list.length > 0 ? Math.max(...list.map(i => i.count || 1)) : 1
})

const topPorts = computed(() => {
  const ports = store.threatVectors.top_dest_ports || store.threatVectors.top_ports || []
  if (ports.length === 0) {
    return [
      { port: 80, service: 'HTTP', count: 520 },
      { port: 443, service: 'HTTPS', count: 380 },
      { port: 22, service: 'SSH', count: 290 },
      { port: 21, service: 'FTP', count: 160 },
      { port: 3389, service: 'RDP', count: 95 }
    ]
  }
  return ports.slice(0, 5)
})

const maxPortCount = computed(() => {
  const list = topPorts.value
  return list.length > 0 ? Math.max(...list.map(p => p.count || 1)) : 1
})

function formatNumber(num) {
  if (!num) return '0'
  return Math.round(num).toLocaleString('en-US')
}
</script>

<style scoped>
.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 14px;
}

.card-header-row h2 {
  margin: 0;
}

.active-range-pill {
  font-size: 11px;
  font-weight: 600;
  color: var(--mu);
  background: var(--panel2);
  padding: 2px 8px;
  border-radius: 6px;
  border: 1px solid var(--line);
}

.vectors-two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

@media (max-width: 700px) {
  .vectors-two-col {
    grid-template-columns: 1fr;
  }
}

.vector-col-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.col-icon {
  width: 15px;
  height: 15px;
  color: var(--mu);
}

.vector-col-header h3 {
  font-size: 12.5px;
  color: var(--mu);
  margin: 0;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

.vector-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.vector-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: var(--panel2);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.04);
  transition: background 0.15s ease, transform 0.15s ease;
}

.vector-row:hover {
  background: rgba(255, 255, 255, 0.06);
  transform: translateX(2px);
}

.row-rank {
  font-size: 11px;
  font-weight: 700;
  color: var(--mu);
  width: 16px;
  text-align: center;
}

.row-identity {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ip-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--tx);
}

.port-name-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.port-number {
  font-size: 13px;
  font-weight: 600;
  color: var(--tx);
}

.service-pill {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(88, 101, 242, 0.2);
  color: var(--lo);
  border: 1px solid rgba(88, 101, 242, 0.35);
}

.ip-meter-bg, .port-meter-bg {
  height: 4px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 2px;
  overflow: hidden;
}

.ip-meter-bg i {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, var(--ac), var(--cr));
  border-radius: 2px;
  transition: width 0.3s ease;
}

.port-meter-bg i {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, var(--lo), var(--ac2));
  border-radius: 2px;
  transition: width 0.3s ease;
}

.row-count {
  font-size: 13px;
  font-variant-numeric: tabular-nums;
  color: var(--tx);
}
</style>
