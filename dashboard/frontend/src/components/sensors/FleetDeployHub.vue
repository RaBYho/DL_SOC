<template>
  <div class="card deployment-hub-card">
    <div class="deploy-header">
      <div class="deploy-header-left">
        <div class="deploy-icon-badge">
          <svg class="deploy-header-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="12 2 19 21 12 17 5 21 12 2"/>
          </svg>
        </div>
        <div>
          <div class="title-with-tag">
            <h3 class="section-title">Guide de Déploiement d'une Sonde</h3>
            <span class="deploy-badge-tag">Intégration &amp; Onboarding</span>
          </div>
          <p class="section-subtitle">
            Connectez une machine physique, virtuelle ou conteneur edge au moteur d'analyse temps réel.
          </p>
        </div>
      </div>

      <button 
        type="button" 
        class="btn-close-deploy" 
        @click="$emit('close')"
        title="Fermer le guide de déploiement"
      >
        <svg class="close-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
        <span>Fermer</span>
      </button>
    </div>

    <!-- Onglets de Méthode -->
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

    <!-- Mini-Schéma d'Architecture -->
    <FleetDeployFlow />

    <!-- Instructions Linux -->
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
          <p class="step-desc">Remplacez <code>eth0</code> par votre carte réseau (privilèges root requis) :</p>
          <div class="code-box-wrapper">
            <pre class="code-block">{{ linuxDeployCommand }}</pre>
            <button type="button" class="btn-copy-code" @click="copyText(linuxDeployCommand)">
              {{ copiedText === linuxDeployCommand ? 'Copié !' : 'Copier' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Instructions Docker -->
    <div v-else-if="deployMethod === 'docker'" class="deploy-steps-container">
      <div class="deploy-step">
        <div class="step-badge">1</div>
        <div class="step-content">
          <b class="step-title">Exécution dans le réseau de l'hôte</b>
          <p class="step-desc">Pour capturer le trafic réel, le conteneur utilise le mode <code>--net=host</code> :</p>
          <div class="code-box-wrapper">
            <pre class="code-block">{{ dockerDeployCommand }}</pre>
            <button type="button" class="btn-copy-code" @click="copyText(dockerDeployCommand)">
              {{ copiedText === dockerDeployCommand ? 'Copié !' : 'Copier' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Instructions cURL API -->
    <div v-else class="deploy-steps-container">
      <div class="deploy-step">
        <div class="step-badge">1</div>
        <div class="step-content">
          <b class="step-title">Tester la connectivité du serveur</b>
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
          <div class="code-box-wrapper">
            <pre class="code-block">{{ curlTestCommand }}</pre>
            <button type="button" class="btn-copy-code" @click="copyText(curlTestCommand)">
              {{ copiedText === curlTestCommand ? 'Copié !' : 'Copier' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Conseil de Durcissement -->
    <div class="deploy-tip-box">
      <svg class="tip-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="16" x2="12" y2="12"/>
        <line x1="12" y1="8" x2="12.01" y2="8"/>
      </svg>
      <div class="tip-body">
        <b>Conseil en production :</b>
        Activez le mode promiscuité sur le switch (port mirroring / SPAN) afin de capturer tout le trafic du segment.
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import FleetDeployFlow from './FleetDeployFlow.vue'

defineEmits(['close'])

const deployMethod = ref('linux')
const copiedText = ref('')

const serverBaseUrl = computed(() => {
  if (typeof window !== 'undefined') {
    return `${window.location.protocol}//${window.location.host}`
  }
  return 'http://127.0.0.1:8000'
})

const linuxDeployCommand = computed(() => {
  return `sudo python nids_sensor.py --source eth0 --server ${serverBaseUrl.value} --api-key dev-secret-key --sensor-id sonde-edge-01`
})

const dockerDeployCommand = computed(() => {
  return `docker run --net=host --cap-add=NET_ADMIN -e SERVER=${serverBaseUrl.value} -e SENSOR_ID=docker-edge-01 hdvr-sensor:latest`
})

const curlTestCommand = computed(() => {
  return `curl -X POST "${serverBaseUrl.value}/ingest" -H "X-API-Key: dev-secret-key" -H "Content-Type: application/json" -d '{"sensor_id":"sonde-test","flows":[]}'`
})

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
</script>

<style scoped>
.deploy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 18px;
  flex-wrap: wrap;
}

.deploy-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-with-tag {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.deploy-badge-tag {
  font-size: 10.5px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 5px;
  background: rgba(88, 101, 242, 0.18);
  color: #9baaff;
  border: 1px solid rgba(88, 101, 242, 0.35);
}

.btn-close-deploy {
  height: 30px;
  padding: 0 12px;
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #8b8ea8;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.btn-close-deploy:hover {
  background: rgba(255, 77, 126, 0.15);
  border-color: rgba(255, 77, 126, 0.4);
  color: #ff4d7e;
}

.close-svg {
  width: 14px;
  height: 14px;
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

.deploy-header-svg { width: 20px; height: 20px; }

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

.deploy-tab-btn:hover { color: #ffffff; }
.deploy-tab-btn.active {
  background: #5865f2;
  color: #ffffff;
  box-shadow: 0 2px 10px rgba(88, 101, 242, 0.35);
}

.method-svg { width: 14px; height: 14px; }

.deploy-steps-container {
  display: flex;
  flex-direction: column;
  gap: 14px;
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

.step-content { flex: 1; }
.step-title { display: block; font-size: 13px; color: #ffffff; }
.step-desc { margin: 3px 0 6px; font-size: 11.5px; color: #8b8ea8; line-height: 1.4; }

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

.btn-copy-code:hover { background: #5865f2; color: #ffffff; }

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

.tip-svg { width: 18px; height: 18px; color: #ffb547; flex-shrink: 0; margin-top: 2px; }
.tip-body { font-size: 11.5px; color: #ffb547; line-height: 1.4; }
.tip-body b { color: #ffd08a; display: block; margin-bottom: 2px; }
</style>
