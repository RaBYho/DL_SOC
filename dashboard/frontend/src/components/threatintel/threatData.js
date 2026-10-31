/**
 * Base de Connaissances Threat Intelligence & Taxonomie MITRE ATT&CK
 * Référentiel des menaces détectables par le NIDS (DNN-v4 supervisé + Autoencodeur)
 */

export const THREAT_KNOWLEDGE_BASE = [
  {
    id: 'portscan',
    name: 'PortScan & Reconnaissance Réseau',
    datasetLabel: 'PortScan',
    aliases: ['PortScan', 'Scan-Vista', 'Reconnaissance'],
    severity: 'Medium',
    category: 'Reconnaissance',
    iconType: 'radar',
    mitreId: 'T1046',
    mitreName: 'Network Service Discovery',
    mitreTactic: 'Discovery',
    mitreUrl: 'https://attack.mitre.org/techniques/T1046/',
    description: 'Balayage systématique de plages d\'adresses et de ports TCP/UDP pour cartographier les services exposés, déceler les failles logicielles et préparer une intrusion ciblée.',
    target: 'Ports éphémères & standards (1-65535, TCP/UDP)',
    networkSignature: 'Multiples flux TCP SYN consécutifs sans finalisation du handshake (SYN/ACK sans ACK), durées de flux extrêmement brèves (<10ms) et volume nul de données applicatives sortantes.',
    impactVector: 'Cartographie complète de l\'architecture interne, découverte d\'équipements non patchés et prélude à des attaques de force brute ou d\'exploitation de vulnérabilités.',
    playbook: {
      iptablesRule: '# Blocage temporaire des scans SYN répétés via le module recent\niptables -A INPUT -p tcp --tcp-flags SYN,ACK,FIN,RST SYN -m limit --limit 1/s --limit-burst 3 -j ACCEPT\niptables -A INPUT -p tcp --tcp-flags SYN,ACK,FIN,RST SYN -j DROP',
      suricataRule: 'alert tcp $EXTERNAL_NET any -> $HOME_NET any (msg:"ET SCAN Potential Nmap Port Scan (SYN Sweep)"; flags:S,12; threshold: type both, track by_src, count 20, seconds 5; classtype:attempted-recon; sid:2000001; rev:1;)',
      containmentSteps: [
        'Isoler l\'adresse IP source au niveau du routeur de bordure (BGP / Blackhole).',
        'Vérifier les logs des ports identifiés comme « ouverts » pour confirmer l\'absence de compromission consécutive.',
        'Activer les mécanismes de port-knocking ou de rate-limiting sur le pare-feu externe.'
      ],
      hardeningTips: 'Déployer des honeypots sur les ports inutilisés pour détecter proactivement les phases de repérage et masquer les bannières de versions logicielles.'
    }
  },
  {
    id: 'ddos',
    name: 'DDoS (Déni de Service Distribué)',
    datasetLabel: 'DDoS',
    aliases: ['DDoS', 'LOIC', 'HOIC'],
    severity: 'Critical',
    category: 'Déni de Service',
    iconType: 'zap',
    mitreId: 'T1498',
    mitreName: 'Network Denial of Service',
    mitreTactic: 'Impact',
    mitreUrl: 'https://attack.mitre.org/techniques/T1498/',
    description: 'Inondation volumétrique massive de paquets SYN, UDP ou ICMP générée par un réseau distribué (botnet) conçue pour saturer la bande passante et faire tomber les routeurs et liaisons transit.',
    target: 'Toutes interfaces & ports (TCP/UDP/ICMP)',
    networkSignature: 'Pic fulgurant de paquets par seconde (PPS), ratio paquets entrants/sortants asymétrique (>1000:1), multiplicité d\'adresses IP sources et répétition de tailles de paquets fixes.',
    impactVector: 'Indisponibilité totale des services critiques, paralysie des flux métiers, perte de chiffre d\'affaires et surcharge des équipements de sécurité périmétrique.',
    playbook: {
      iptablesRule: '# Activation des SYN-Cookies et limitation drastique du volume entrant\nsysctl -w net.ipv4.tcp_syncookies=1\niptables -A INPUT -p tcp --syn -m limit --limit 50/s --limit-burst 100 -j ACCEPT\niptables -A INPUT -p tcp --syn -j DROP',
      suricataRule: 'alert tcp $EXTERNAL_NET any -> $HOME_NET any (msg:"HDVR FLOOD SYN Flood Inbound Threshold Exceeded"; flags:S; threshold: type both, track by_dst, count 500, seconds 2; classtype:denial-of-service; sid:2000002; rev:1;)',
      containmentSteps: [
        'Activer le délestage volumétrique chez l\'opérateur de transit (Scrubbing Center ou mitigation BGP Anycast Cloudflare/Akamai).',
        'Basculer les flux critiques vers des interfaces d\'administration hors-bande (OOB).',
        'Bloquer les protocoles de réflexion UDP connus (NTP 123, DNS 53, SNMP 161, SSDP 1900) aux bordures.'
      ],
      hardeningTips: 'Mettre en place un plan de continuité d\'activité (PCA) avec des CDN distribués et souscrire une protection anti-DDoS en amont des liens physiques.'
    }
  },
  {
    id: 'dos-hulk',
    name: 'DoS-Hulk (HTTP Exhaustion)',
    datasetLabel: 'DoS-Hulk',
    aliases: ['DoS-Hulk', 'HULK'],
    severity: 'High',
    category: 'Déni de Service',
    iconType: 'server-crash',
    mitreId: 'T1499',
    mitreName: 'Endpoint Denial of Service',
    mitreTactic: 'Impact',
    mitreUrl: 'https://attack.mitre.org/techniques/T1499/',
    description: 'Génération de milliers de requêtes HTTP GET uniques avec User-Agents forgés et paramètres URL aléatoires visant à contourner les caches et asphyxier le pool de workers du serveur web (CPU/RAM).',
    target: 'Ports 80 (HTTP), 443 (HTTPS), 8080 (APIs)',
    networkSignature: 'Flux HTTP saturés de requêtes avec des en-têtes User-Agent aléatoires et des chaînes de requête générées dynamiquement (ex: ?id=rand...). Absence totale d\'intervalles entre requêtes.',
    impactVector: 'Saturation des processeurs des serveurs applicatifs (Nginx/Apache), dépassement des limites max_children/workers et erreur HTTP 502/504 Bad Gateway pour les utilisateurs légitimes.',
    playbook: {
      iptablesRule: '# Limitation des connexions concurrentes par adresse IP source sur ports web\niptables -A INPUT -p tcp -m multiport --dports 80,443 -m connlimit --connlimit-above 30 -j DROP',
      suricataRule: 'alert http $EXTERNAL_NET any -> $HTTP_SERVERS $HTTP_PORTS (msg:"HDVR DOS Hulk HTTP Flooder Inbound"; flow:established,to_server; content:"GET"; http_method; threshold: type both, track by_src, count 60, seconds 3; sid:2000003; rev:1;)',
      containmentSteps: [
        'Activer le module WAF mod_security ou les règles de rate-limiting Nginx (limit_req_zone).',
        'Activer le challenge JavaScript (Under Attack Mode) sur le reverse-proxy frontal.',
        'Bannir immédiatement les adresses IP sources via Fail2ban ou script d\'automatisation SOC.'
      ],
      hardeningTips: 'Mettre en cache toutes les pages statiques via Varnish ou CDN et optimiser la gestion des threads applicatifs (PHP-FPM, Uvicorn, Gunicorn).'
    }
  },
  {
    id: 'dos-slowloris',
    name: 'DoS-Slowloris (Keep-Alive Starvation)',
    datasetLabel: 'DoS-slowloris',
    aliases: ['DoS-slowloris', 'Slowloris'],
    severity: 'High',
    category: 'Déni de Service',
    iconType: 'hourglass',
    mitreId: 'T1499',
    mitreName: 'Endpoint Denial of Service',
    mitreTactic: 'Impact',
    mitreUrl: 'https://attack.mitre.org/techniques/T1499/',
    description: 'Attaque lente à très faible bande passante envoyant des en-têtes HTTP partiels à intervalles réguliers pour maintenir des centaines de sockets ouvertes jusqu\'à épuisement de la table des connexions.',
    target: 'Ports 80 (HTTP), 443 (HTTPS)',
    networkSignature: 'Connexions TCP d\'une durée anormale (>60s) avec un débit microscopique (<100 octets/min), envoi fragmenté d\'en-têtes HTTP non terminés par le double CRLF réglementaire.',
    impactVector: 'Épuisement silencieux de la capacité de traitement du serveur web sans déclencher les alertes volumétriques classiques de bande passante.',
    playbook: {
      iptablesRule: '# Limitation drastique des sockets ouvertes par IP et timeout agressif\niptables -A INPUT -p tcp --dport 80 -m connlimit --connlimit-above 15 -j REJECT --reject-with tcp-reset',
      suricataRule: 'alert tcp $EXTERNAL_NET any -> $HOME_NET 80 (msg:"HDVR DOS Slowloris Partial Header Inactivity Pattern"; flow:established,to_server; threshold: type both, track by_src, count 10, seconds 20; sid:2000004; rev:1;)',
      containmentSteps: [
        'Réduire drastiquement le timeout de lecture des requêtes HTTP (client_header_timeout 5s sous Nginx).',
        'Terminer les connexions TCP inactives via un proxy inverse asynchrone (HAProxy/Envoy).',
        'Injecter les IPs assaillantes dans la liste noire du pare-feu avec un script d\'éviction.'
      ],
      hardeningTips: 'Remplacer les architectures de serveurs web basées sur les processus (Apache prefork) par des moteurs événementiels asynchrones (Nginx, Caddy).'
    }
  },
  {
    id: 'dos-goldeneye',
    name: 'DoS-GoldenEye (HTTP Keep-Alive & Cache-Control)',
    datasetLabel: 'DoS-GoldenEye',
    aliases: ['DoS-GoldenEye', 'GoldenEye'],
    severity: 'High',
    category: 'Déni de Service',
    iconType: 'flame',
    mitreId: 'T1499',
    mitreName: 'Endpoint Denial of Service',
    mitreTactic: 'Impact',
    mitreUrl: 'https://attack.mitre.org/techniques/T1499/',
    description: 'Arme de déni de service combinant requêtes Keep-Alive persistantes et en-têtes Cache-Control: no-cache pour forcer le serveur à recalculer des requêtes dynamiques lourdes en base de données.',
    target: 'Ports 80 (HTTP), 443 (HTTPS)',
    networkSignature: 'Requêtes HTTP pipelinées avec en-têtes Keep-Alive: max=1000 et Cache-Control: no-cache répétées en boucle rapide sur un même socket TCP.',
    impactVector: 'Saturation instantanée des pools de connexions SQL/PostgreSQL et effondrement des temps de réponse applicatifs.',
    playbook: {
      iptablesRule: '# Coupure des flux HTTP saturants récurrents\niptables -A INPUT -p tcp -m multiport --dports 80,443 -m state --state NEW -m recent --set --name GOLDENEYE\niptables -A INPUT -p tcp -m multiport --dports 80,443 -m state --state NEW -m recent --update --seconds 1 --hitcount 20 --name GOLDENEYE -j DROP',
      suricataRule: 'alert http $EXTERNAL_NET any -> $HTTP_SERVERS $HTTP_PORTS (msg:"HDVR DOS GoldenEye Aggressive No-Cache Pattern"; content:"Cache-Control|3a| no-cache"; http_header; threshold: type both, track by_src, count 40, seconds 2; sid:2000005; rev:1;)',
      containmentSteps: [
        'Activer les limites de connexions persistantes Keep-Alive (keepalive_requests 20; keepalive_timeout 5s;).',
        'Bloquer les User-Agents typiques de GoldenEye au niveau du WAF.',
        'Mettre en place un rate-limiting applicatif par IP et par token de session.'
      ],
      hardeningTips: 'Découpler les requêtes d\'écriture et de lecture et implémenter des disjoncteurs (circuit breakers) pour protéger la base de données.'
    }
  },
  {
    id: 'dos-slowhttptest',
    name: 'DoS-Slowhttptest (R-U-Dead-Yet / Slow POST)',
    datasetLabel: 'DoS-Slowhttptest',
    aliases: ['DoS-Slowhttptest', 'SlowHTTP'],
    severity: 'High',
    category: 'Déni de Service',
    iconType: 'clock',
    mitreId: 'T1499',
    mitreName: 'Endpoint Denial of Service',
    mitreTactic: 'Impact',
    mitreUrl: 'https://attack.mitre.org/techniques/T1499/',
    description: 'Exploitation de la phase d\'envoi du corps des requêtes HTTP POST (Slow POST). L\'attaquant annonce un Content-Length énorme mais transmet les octets 1 par 1 toutes les 10 secondes.',
    target: 'Ports 80, 443 (Formulaires & Endpoints POST)',
    networkSignature: 'En-tête HTTP POST avec Content-Length élevé suivi d\'un flux de paquets TCP minuscules (1 à 2 octets) espacés d\'intervalles réguliers pour tromper les timeouts.',
    impactVector: 'Verrouillage des processus serveurs qui attendent indéfiniment la fin des corps de requêtes avant de libérer les ressources.',
    playbook: {
      iptablesRule: '# Détection et coupure des connexions lentes persistantes\niptables -A INPUT -p tcp --dport 443 -m connlimit --connlimit-above 20 -j DROP',
      suricataRule: 'alert http $EXTERNAL_NET any -> $HTTP_SERVERS $HTTP_PORTS (msg:"HDVR DOS Slowhttptest Abnormally Low Transmission Rate"; flow:established,to_server; content:"POST"; http_method; threshold: type both, track by_src, count 15, seconds 30; sid:2000006; rev:1;)',
      containmentSteps: [
        'Configurer client_body_timeout 10s et client_header_timeout 5s dans Nginx.',
        'Utiliser le module mod_reqtimeout sous Apache pour imposer un débit minimal (ex: minrate=500).',
        'Terminer la session TCP de l\'attaquant.'
      ],
      hardeningTips: 'Rejeter les corps de requêtes excessifs (client_max_body_size) sur les endpoints qui n\'acceptent pas de téléversement de fichiers.'
    }
  },
  {
    id: 'ssh-patator',
    name: 'SSH-Patator (Force Brute d\'Identifiants SSH)',
    datasetLabel: 'SSH-Patator',
    aliases: ['SSH-Patator', 'SSH-BruteForce'],
    severity: 'High',
    category: 'Brute Force',
    iconType: 'terminal',
    mitreId: 'T1110',
    mitreName: 'Brute Force Credentials',
    mitreTactic: 'Credential Access',
    mitreUrl: 'https://attack.mitre.org/techniques/T1110/',
    description: 'Tentatives répétées et automatisées d\'authentification par force brute ou dictionnaire ciblant le démon SSH (port 22) pour dérober des accès privilégiés (root, admin).',
    target: 'Port 22 (SSH OpenSSH daemon)',
    networkSignature: 'Succession dense de handshakes TCP SSH-2.0 suivis de fermeture immédiate (FIN/ACK) après échec de négociation des clés ou de mot de passe. Volume élevé de flux sur le port 22.',
    impactVector: 'Compromission complète du serveur hôte, installation de portes dérobées (rootkits) et pivotement latéral au sein du datacenter.',
    playbook: {
      iptablesRule: '# Blocage automatique des IPs tentant plus de 4 connexions SSH par minute\niptables -A INPUT -p tcp --dport 22 -m state --state NEW -m recent --set --name SSH_ATTACK\niptables -A INPUT -p tcp --dport 22 -m state --state NEW -m recent --update --seconds 60 --hitcount 4 --name SSH_ATTACK -j DROP',
      suricataRule: 'alert tcp $EXTERNAL_NET any -> $HOME_NET 22 (msg:"HDVR AUTH SSH Brute Force Rapid Sequence"; flow:to_server,established; content:"SSH-2.0"; threshold: type both, track by_src, count 5, seconds 60; classtype:attempted-admin; sid:2000007; rev:1;)',
      containmentSteps: [
        'Bannir immédiatement l\'adresse IP assaillante via Fail2ban (`fail2ban-client set sshd banip <IP>`).',
        'Inspecter `/var/log/auth.log` ou `journalctl -u ssh` pour vérifier si une tentative a réussi (Accepted password).',
        'En cas de doute, forcer la révocation des clés SSH et la réinitialisation des mots de passe.'
      ],
      hardeningTips: 'Désactiver totalement l\'authentification par mot de passe (`PasswordAuthentication no`), interdire la connexion root (`PermitRootLogin no`) et changer le port par défaut (ex: 2222).'
    }
  },
  {
    id: 'ftp-patator',
    name: 'FTP-Patator (Force Brute d\'Identifiants FTP)',
    datasetLabel: 'FTP-Patator',
    aliases: ['FTP-Patator', 'FTP-BruteForce'],
    severity: 'High',
    category: 'Brute Force',
    iconType: 'folder-lock',
    mitreId: 'T1110',
    mitreName: 'Brute Force Credentials',
    mitreTactic: 'Credential Access',
    mitreUrl: 'https://attack.mitre.org/techniques/T1110/',
    description: 'Attaque par dictionnaire automatisée contre les démons de transfert de fichiers (vsftpd, ProFTPD) testant des combinaisons d\'utilisateurs (anonymous, admin, backup) et mots de passe.',
    target: 'Port 21 (FTP Control Channel)',
    networkSignature: 'Répétition de commandes FTP USER et PASS dans un flux clair, suivie de codes de réponse 530 Login incorrect émis en boucle rapide par le serveur.',
    impactVector: 'Fuite de données confidentielles hébergées sur le serveur, exfiltration de sauvegardes et écriture de scripts malveillants dans des répertoires web.',
    playbook: {
      iptablesRule: '# Limitation des tentatives de connexion FTP entrantes\niptables -A INPUT -p tcp --dport 21 -m state --state NEW -m recent --set --name FTP_BRUTE\niptables -A INPUT -p tcp --dport 21 -m state --state NEW -m recent --update --seconds 60 --hitcount 5 --name FTP_BRUTE -j DROP',
      suricataRule: 'alert ftp $EXTERNAL_NET any -> $HOME_NET 21 (msg:"HDVR AUTH FTP Rapid Authentication Failure (Patator)"; flow:established,from_server; content:"530"; threshold: type both, track by_dst, count 5, seconds 30; sid:2000008; rev:1;)',
      containmentSteps: [
        'Bloquer l\'IP source sur le pare-feu hôte.',
        'Désactiver immédiatement le compte anonymous si activé.',
        'Vérifier l\'intégrité des fichiers déposés dans la racine FTP (`/srv/ftp` ou `/home/`).'
      ],
      hardeningTips: 'Déprécier FTP non sécurisé au profit de SFTP (SSH File Transfer Protocol) ou FTPS avec certificats TLS obligatoires.'
    }
  },
  {
    id: 'webattack',
    name: 'WebAttack (XSS, SQL Injection & Web Exploits)',
    datasetLabel: 'WebAttack',
    aliases: ['WebAttack', 'Sql Injection', 'XSS'],
    severity: 'High',
    category: 'Application Web',
    iconType: 'code',
    mitreId: 'T1190',
    mitreName: 'Exploit Public-Facing Application',
    mitreTactic: 'Initial Access',
    mitreUrl: 'https://attack.mitre.org/techniques/T1190/',
    description: 'Tentatives d\'injection de code SQL (SQLi), de scripts malveillants intersites (XSS) ou de fuzzing d\'URL visant à extraire la base de données ou compromettre les sessions clients.',
    target: 'Ports 80 (HTTP), 443 (HTTPS), 8080 (APIs REST/GraphQL)',
    networkSignature: 'Présence de caractères suspects dans les requêtes HTTP GET/POST : apostrophes non échappées (\' OR 1=1--), balises de script (<script>alert()), directives UNION SELECT ou chemins de traversée (../etc/passwd).',
    impactVector: 'Exfiltration complète de bases de données (dump SQL), vol de jetons d\'authentification et exécution de commandes arbitraires côté serveur (RCE).',
    playbook: {
      iptablesRule: '# Redirection des flux suspects vers une chaîne d\'inspection WAF ou rejet applicatif\niptables -A INPUT -p tcp -m multiport --dports 80,443 -m string --string "UNION SELECT" --algo bm -j DROP',
      suricataRule: 'alert http $EXTERNAL_NET any -> $HTTP_SERVERS $HTTP_PORTS (msg:"HDVR WEB-ATTACK SQL Injection Attempt Detected"; flow:to_server,established; content:"UNION"; nocase; http_uri; content:"SELECT"; nocase; http_uri; classtype:web-application-attack; sid:2000009; rev:1;)',
      containmentSteps: [
        'Isoler l\'application web concernée et vérifier les requêtes SQL enregistrées dans les logs applicatifs.',
        'Mettre à jour immédiatement les règles de filtrage WAF (Coraza, ModSecurity, Cloudflare OWASP Core Rule Set).',
        'Vérifier les tables de sessions pour révoquer les accès potentiellement usurpés.'
      ],
      hardeningTips: 'Utiliser systématiquement des requêtes préparées (requêtes paramétrées PDO/ORM) et activer les en-têtes HTTP de sécurité (Content-Security-Policy, X-Frame-Options).'
    }
  },
  {
    id: 'bot',
    name: 'Botnet Command & Control (C2 Beaconing)',
    datasetLabel: 'Bot',
    aliases: ['Bot', 'Ares', 'C2'],
    severity: 'Critical',
    category: 'Malware & C2',
    iconType: 'bug',
    mitreId: 'T1071',
    mitreName: 'Application Layer Protocol: Web Protocols',
    mitreTactic: 'Command and Control',
    mitreUrl: 'https://attack.mitre.org/techniques/T1071/',
    description: 'Communication régulière et automatisée (beaconing) entre un agent malveillant implanté sur le réseau local et un serveur de commande et contrôle (C2) externe pour recevoir des instructions ou exfiltrer des données.',
    target: 'Ports 80 (HTTP), 443 (HTTPS), 53 (DNS Tunneling), ports non standards',
    networkSignature: 'Flux réseau périodiques avec gigue (jitter) minimale, échanges de messages de petite taille à intervalles temporels réguliers (heartbeats) vers des domaines suspects ou IPs sans réputation.',
    impactVector: 'Prise de contrôle à distance d\'équipements internes, pivotement vers d\'autres sous-réseaux, déploiement ultérieur de rançongiciels (ransomware).',
    playbook: {
      iptablesRule: '# Blocage immédiat de tout trafic sortant vers l\'infrastructure C2 identifiée\niptables -A OUTPUT -d <IP_C2> -j DROP\niptables -A FORWARD -d <IP_C2> -j DROP',
      suricataRule: 'alert tcp $HOME_NET any -> $EXTERNAL_NET any (msg:"HDVR MALWARE Suspicious Periodic Beaconing Detected"; flow:established,to_server; threshold: type both, track by_src, count 10, seconds 60; classtype:trojan-activity; sid:2000010; rev:1;)',
      containmentSteps: [
        'Isoler physiquement ou logiquement (quarantaine VLAN) la machine compromise du reste du réseau d\'entreprise.',
        'Créer un dump mémoire (RAM) et capturer les artefacts sur l\'hôte infecté pour analyse forensique.',
        'Bloquer les domaines et adresses IP C2 au niveau du résolveur DNS menteur (DNS Sinkhole).'
      ],
      hardeningTips: 'Restreindre drastiquement le trafic sortant via un pare-feu egress (interdire tout flux sortant non expressément autorisé vers Internet).'
    }
  },
  {
    id: 'scan-vista',
    name: 'Scan-Vista & Fingerprinting d\'OS',
    datasetLabel: 'Scan-Vista',
    aliases: ['Scan-Vista', 'OS-Fingerprint'],
    severity: 'Medium',
    category: 'Reconnaissance',
    iconType: 'shield-search',
    mitreId: 'T1046',
    mitreName: 'Network Service Discovery',
    mitreTactic: 'Discovery',
    mitreUrl: 'https://attack.mitre.org/techniques/T1046/',
    description: 'Séquences de paquets TCP aux drapeaux inhabituels (SYN/FIN, NULL, XMAS, ACK) utilisées par des scanners (Nmap, ZMap) pour déduire la pile TCP/IP exacte et le système d\'exploitation sous-jacent.',
    target: 'Tous ports TCP',
    networkSignature: 'Combinaisons de flags TCP illégitimes (FIN sans ACK, URG/PSH/FIN), valeurs de fenêtres TCP (TCP Window Size) fixes et requêtes envoyées sur des ports fermés.',
    impactVector: 'Découverte de l\'OS cible permettant à l\'attaquant de sélectionner des exploits spécifiques (CVE) adaptés à la version exacte du système.',
    playbook: {
      iptablesRule: '# Rejet des paquets TCP aux drapeaux invalides (NULL scan, XMAS scan)\niptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP\niptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP\niptables -A INPUT -p tcp --tcp-flags ALL FIN,PSH,URG -j DROP',
      suricataRule: 'alert tcp $EXTERNAL_NET any -> $HOME_NET any (msg:"HDVR SCAN Nmap OS Detection Probe Sequence"; flags:FPU; classtype:attempted-recon; sid:2000011; rev:1;)',
      containmentSteps: [
        'Vérifier si le scan provient de l\'interne ou de l\'externe.',
        'Ajouter l\'adresse IP source à la liste de surveillance du SOC.',
        'Vérifier que les machines ciblées ont un pare-feu local rejetant silencieusement les paquets non sollicités.'
      ],
      hardeningTips: 'Configurer le pare-feu du système d\'exploitation pour qu\'il ne réponde pas aux paquets TCP anormaux ou malformés.'
    }
  },
  {
    id: 'zero-day',
    name: 'Anomalie Inconnue / Zero-Day (Autoencodeur)',
    datasetLabel: 'Zero-Day / Inconnu',
    aliases: ['Zero-Day', 'Anomaly', 'Autoencoder'],
    severity: 'Critical',
    category: 'Anomalie Comportementale',
    iconType: 'sparkles',
    mitreId: 'T1203',
    mitreName: 'Exploitation for Client Execution',
    mitreTactic: 'Defense Evasion',
    mitreUrl: 'https://attack.mitre.org/techniques/T1203/',
    description: 'Déviation statistique majeure du comportement réseau détectée par l\'Autoencodeur non supervisé (Erreur MSE > Seuil de coupure). Indique une technique inconnue, un canal covert ou une attaque 0-day sans signature connue.',
    target: 'Toute interface ou service réseau',
    networkSignature: 'Reconstruction MSE très élevée sur les 58 caractéristiques de flux (durée, entropie des paquets, inter-arrival time, ratios d\'octets) rompant avec le profil nominal appris.',
    impactVector: 'Menace furtive de haut niveau (APT, exploit zero-day non divulgué, exfiltration de données non documentée).',
    playbook: {
      iptablesRule: '# Journalisation approfondie et isolement du flux incriminé\niptables -A INPUT -s <IP_SUSPECTE> -j LOG --log-prefix "HDVR-ZERO-DAY: "\niptables -A INPUT -s <IP_SUSPECTE> -j DROP',
      suricataRule: 'alert ip $EXTERNAL_NET any -> $HOME_NET any (msg:"HDVR ZERO-DAY High Reconstruction Error Anomaly"; threshold: type both, track by_src, count 1, seconds 10; sid:2000012; rev:1;)',
      containmentSteps: [
        'Déclencher une capture PCAP complète immédiate sur l\'interface réseau concernée.',
        'Extraire le flux brut dans le tiroir d\'inspection pour décortiquer les 58 métriques NFStream.',
        'Soumettre les payloads suspects au bac à sable (sandbox) d\'analyse de malwares.'
      ],
      hardeningTips: 'Re-entraîner périodiquement l\'Autoencodeur avec les flux labellisés pour affiner le seuil de coupure et réduire les faux positifs.'
    }
  }
]

export const MITRE_TACTICS_LIST = [
  { key: 'ALL', label: 'Toutes les tactiques' },
  { key: 'Discovery', label: 'Reconnaissance (Discovery)' },
  { key: 'Impact', label: 'Déni de Service (Impact)' },
  { key: 'Credential Access', label: 'Accès Identifiants (Credential Access)' },
  { key: 'Initial Access', label: 'Accès Initial (Initial Access)' },
  { key: 'Command and Control', label: 'Command & Control (C2)' },
  { key: 'Defense Evasion', label: 'Évasion & Zero-Day' }
]
