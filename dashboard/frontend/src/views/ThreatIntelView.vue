<template>
  <main>
    <div class="card" style="margin-bottom: 16px;">
      <h2>
        Threat Intelligence &amp; Attack Taxonomy
        <span>CIC-IDS2017 &amp; MITRE ATT&amp;CK Mapping</span>
      </h2>
      <p style="color:var(--mu); font-size: 13px; margin: 0;">
        Detailed signature profiles, targeted services, and mitigation strategies for all detectable attack classes.
      </p>
    </div>

    <section class="grid">
      <div 
        v-for="t in threats" 
        :key="t.name" 
        class="card c6"
      >
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;">
          <h2 style="margin:0;">{{ t.name }}</h2>
          <span class="sev" :class="t.severity">{{ t.severity }}</span>
        </div>
        <p style="color:var(--mu); font-size:13px; margin: 0 0 10px;">{{ t.description }}</p>
        <div class="kv">
          <span>Targeted Protocol/Port</span><span>{{ t.target }}</span>
          <span>MITRE Technique</span><span class="mono">{{ t.mitre }}</span>
          <span>Recommended Response</span><span>{{ t.mitigation }}</span>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup>
const threats = [
  {
    name: 'DDoS (Distributed Denial of Service)',
    severity: 'Critical',
    description: 'High-volume distributed SYN floods and UDP reflection saturating network capacity.',
    target: 'All Ports (TCP/UDP)',
    mitre: 'T1498 (Network Denial of Service)',
    mitigation: 'BGP Anycast diversion, upstream rate limiting, SYN proxying'
  },
  {
    name: 'DoS-Hulk & Slowloris',
    severity: 'High',
    description: 'Application layer exhaustion through keep-alive connection starvation or randomized HTTP GET floods.',
    target: 'Ports 80 (HTTP), 443 (HTTPS)',
    mitre: 'T1499 (Endpoint Denial of Service)',
    mitigation: 'WAF rate limiting, aggressive connection timeout tuning'
  },
  {
    name: 'PortScan & Reconnaissance',
    severity: 'Medium',
    description: 'Systematic TCP SYN/FIN scanning to map open ports and discover exposed services.',
    target: 'Ephemeral & Standard Ports',
    mitre: 'T1046 (Network Service Discovery)',
    mitigation: 'Dynamic firewall blacklisting, honeypot port diversion'
  },
  {
    name: 'SSH & FTP Patator',
    severity: 'High',
    description: 'High-frequency credential brute-force attacks against management daemon endpoints.',
    target: 'Port 22 (SSH), Port 21 (FTP)',
    mitre: 'T1110 (Brute Force Credentials)',
    mitigation: 'Fail2ban auto-jail, enforce public-key authentication only'
  },
  {
    name: 'WebAttack (XSS / SQLi)',
    severity: 'High',
    description: 'Exploitation attempts targeting web applications and backend databases.',
    target: 'Port 80, 443, 8080',
    mitre: 'T1190 (Exploit Public-Facing Application)',
    mitigation: 'WAF inspection rules, input sanitization, database parameterized queries'
  },
  {
    name: 'Botnet Command & Control',
    severity: 'Critical',
    description: 'Periodic beaconing and telemetry exfiltration to remote C2 infrastructure.',
    target: 'DNS (53), Custom HTTPS (443)',
    mitre: 'T1071 (Application Layer Protocol)',
    mitigation: 'DNS sinkholing, TLS fingerprinting, perimeter isolation'
  }
]
</script>
