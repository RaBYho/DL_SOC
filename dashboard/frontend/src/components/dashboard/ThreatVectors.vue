<template>
  <div class="card c9 threat-vectors-card">
    <!-- Header: Title and Subtitle strictly stacked beneath -->
    <div class="card-header-row">
      <div class="header-titles">
        <h2 class="card-title">{{ store.t('vectors.title') }}</h2>
        <span class="card-subtitle">{{ store.t('vectors.subtitle') }}</span>
      </div>
    </div>

    <div class="vectors-two-col">
      <!-- Column 1: Top Attacking Source IPs (Scrollable List) -->
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
              <span class="mono ip-text" :title="ip.ip">{{ ip.ip }}</span>
              <div class="ip-meter-bg">
                <i :style="{ transform: `scaleX(${Math.min(ip.count / maxIpCount, 1)})` }"></i>
              </div>
            </div>
            <b class="row-count">{{ formatNumber(ip.count) }}</b>
          </div>
        </div>
      </div>

      <!-- Column 2: Top Targeted Destination Ports (Scrollable List) -->
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
                <i :style="{ transform: `scaleX(${Math.min(p.count / maxPortCount, 1)})` }"></i>
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
      { ip: '103.145.13.2', count: 140 },
      { ip: '198.51.100.23', count: 115 },
      { ip: '203.0.113.88', count: 88 },
      { ip: '192.0.2.14', count: 64 }
    ]
  }
  return ips
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
      { port: 3389, service: 'RDP', count: 95 },
      { port: 445, service: 'SMB', count: 82 },
      { port: 8080, service: 'HTTP-Alt', count: 64 },
      { port: 53, service: 'DNS', count: 45 }
    ]
  }
  return ports
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
.threat-vectors-card {
  height: 330px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  padding: 16px 18px;
  transition: transform 0.24s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.24s ease, box-shadow 0.24s ease;
}

.threat-vectors-card:hover {
  border-color: rgba(255, 255, 255, 0.14);
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  flex: none;
}

.header-titles {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.card-title {
  margin: 0;
  font-size: 14.5px;
  font-weight: 700;
  letter-spacing: -0.2px;
  color: #fff;
  line-height: 1.2;
}

.card-subtitle {
  font-size: 11px;
  font-weight: 400;
  color: var(--mu);
  line-height: 1.2;
}

.vectors-two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  flex: 1;
  min-height: 0;
}

@media (max-width: 700px) {
  .vectors-two-col {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}

.vector-col {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
}

.vector-col-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex: none;
}

.col-icon {
  width: 14px;
  height: 14px;
  color: var(--mu);
}

.vector-col-header h3 {
  font-size: 11.5px;
  color: var(--mu);
  margin: 0;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

/* Scrollable List for IPs and Ports */
.vector-list {
  display: flex;
  flex-direction: column;
  gap: 7px;
  overflow-y: auto;
  overflow-x: hidden;
  flex: 1;
  min-height: 0;
  padding-right: 4px;
  scroll-behavior: smooth;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.2) transparent;
}

.vector-list::-webkit-scrollbar {
  width: 5px;
}

.vector-list::-webkit-scrollbar-track {
  background: transparent;
}

.vector-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.vector-list::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.35);
}

.vector-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  background: var(--panel2);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.04);
  transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), 
              background-color 0.22s cubic-bezier(0.16, 1, 0.3, 1), 
              border-color 0.22s ease;
  will-change: transform;
  flex: none;
}

.vector-row:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.1);
  transform: translateX(3px);
}

.row-rank {
  font-size: 10.5px;
  font-weight: 700;
  color: var(--mu);
  width: 14px;
  text-align: center;
  flex: none;
}

.row-identity {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.ip-text {
  font-size: 12px;
  font-weight: 600;
  color: var(--tx);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.port-name-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.port-number {
  font-size: 12px;
  font-weight: 600;
  color: var(--tx);
}

.service-pill {
  font-size: 9.5px;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 4px;
  background: rgba(88, 101, 242, 0.2);
  color: var(--lo);
  border: 1px solid rgba(88, 101, 242, 0.35);
}

/* GPU Accelerated ScaleX for fluid bar meters without layout reflows */
.ip-meter-bg, .port-meter-bg {
  height: 3px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 2px;
  overflow: hidden;
}

.ip-meter-bg i {
  display: block;
  width: 100%;
  height: 100%;
  transform-origin: left;
  background: linear-gradient(90deg, var(--ac), var(--cr));
  border-radius: 2px;
  transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
  will-change: transform;
}

.port-meter-bg i {
  display: block;
  width: 100%;
  height: 100%;
  transform-origin: left;
  background: linear-gradient(90deg, var(--lo), var(--ac2));
  border-radius: 2px;
  transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
  will-change: transform;
}

.row-count {
  font-size: 11.5px;
  font-variant-numeric: tabular-nums;
  color: var(--tx);
  flex: none;
}

@media (max-width: 768px) {
  .threat-vectors-card {
    height: auto;
    min-height: auto;
    padding: 14px 16px;
  }

  .vector-list {
    max-height: 220px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .vector-row,
  .ip-meter-bg i,
  .port-meter-bg i {
    transition: none !important;
  }
}
</style>
