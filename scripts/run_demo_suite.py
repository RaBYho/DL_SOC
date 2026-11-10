#!/usr/bin/env python3
"""Script d'orchestration et de démonstration interactive des attaques en conditions réelles.

Ce script simule ou exécute en direct de véritables outils offensifs (Nmap, Hydra, Curl)
contre la machine locale, capture le trafic réseau via dumpcap, et le soumet au NIDS hybride.
"""

import argparse
from dataclasses import dataclass
from pathlib import Path
import socket
import subprocess
import sys
import time
from typing import Callable


@dataclass
class DemoScenario:
    """Scénario de démonstration d'attaque."""

    name: str
    category: str
    expected_class: str
    description: str
    action: Callable[[], None]


def _exec_nmap() -> None:
    """Exécute un scan TCP Connect Nmap sur une plage de ports."""
    cmd = ["nmap", "-sT", "-p", "1-100", "127.0.0.1"]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _exec_hydra() -> None:
    """Exécute une attaque par force brute HTTP avec Hydra."""
    pass_file = Path("/tmp/hydra_demo_pass.txt")
    pass_file.write_text("\n".join([f"test_pwd_{i}" for i in range(10)]))
    cmd = [
        "hydra", "-s", "80", "127.0.0.1", "http-get", "/admin",
        "-l", "admin", "-P", str(pass_file), "-t", "4",
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _exec_sqli() -> None:
    """Injecte une charge utile SQLi classique via Curl."""
    url = "http://127.0.0.1:80/?user=admin%27+UNION+SELECT+1,version(),3--"
    subprocess.run(["curl", "-s", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _exec_xss() -> None:
    """Injecte une charge utile XSS par réflexion via Curl."""
    url = "http://127.0.0.1:80/?q=%3Cscript%3Ealert(%27pwned%27)%3C/script%3E"
    subprocess.run(["curl", "-s", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _exec_log4j() -> None:
    """Envoie un en-tête d'exploitation RCE Log4Shell JNDI via Curl."""
    hdr = "X-Api-Version: ${jndi:ldap://127.0.0.1:1389/Exploit}"
    subprocess.run(["curl", "-s", "-H", hdr, "http://127.0.0.1:80/"], stdout=subprocess.DEVNULL)


def _exec_gobuster() -> None:
    """Simule un fuzzing de répertoires sensibles (Gobuster) via Curl."""
    subprocess.run(
        ["curl", "-s", "-A", "gobuster/3.1.0", "http://127.0.0.1:80/.env"],
        stdout=subprocess.DEVNULL,
    )


def _exec_ddos() -> None:
    """Génère une rafale volumétrique de 40 connexions TCP concurrentes en boucle locale."""
    for _ in range(40):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("127.0.0.1", 80))
            s.sendall(b"GET / HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n")
            s.close()
        except OSError:
            pass


def _exec_benign() -> None:
    """Simule une navigation web normale sans aucune signature malveillante."""
    subprocess.run(["curl", "-s", "http://127.0.0.1:80/"], stdout=subprocess.DEVNULL)
    time.sleep(0.1)
    subprocess.run(["curl", "-s", "http://127.0.0.1:80/index.html"], stdout=subprocess.DEVNULL)


def _capture_and_execute(action: Callable[[], None], pcap_path: Path) -> None:
    """Capture le trafic réseau sur l'interface de bouclage pendant l'action offensive."""
    if pcap_path.exists():
        pcap_path.unlink()
    proc = subprocess.Popen(["dumpcap", "-i", "lo", "-w", str(pcap_path), "-q"])
    time.sleep(0.4)
    action()
    time.sleep(0.5)
    proc.terminate()
    proc.wait()


def _analyze_pcap(pcap_path: Path) -> list[str]:
    """Exécute l'analyse NIDS en mode hors-ligne et extrait les classes d'alertes."""
    cmd = [
        sys.executable,
        "scripts/run_live_capture.py",
        "--pcap",
        str(pcap_path),
        "--allow-loopback",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    detected_classes = []
    for line in res.stdout.splitlines():
        if "Classe:" in line:
            parts = line.split("Classe:")[1].split("|")[0].strip()
            detected_classes.append(parts)
    return detected_classes


def _run_single_demo(s: DemoScenario, work_dir: Path) -> bool:
    """Exécute un scénario de test unique et affiche les résultats SOC."""
    pcap = work_dir / f"demo_{s.name}.pcap"
    print(f"\n▶️  [SCÉNARIO] {s.name.upper()} : {s.description}")
    _capture_and_execute(s.action, pcap)
    alerts = _analyze_pcap(pcap)

    if s.expected_class == "BENIGN":
        success = len(alerts) == 0
        status = "✅ PASS (0 fausse alerte)" if success else f"❌ FAUX POSITIF ({alerts})"
    else:
        success = (s.expected_class in alerts) or ("ANOMALY_UNKNOWN" in alerts)
        status = f"✅ DÉTECTÉ ({', '.join(alerts)})" if success else "❌ NON DÉTECTÉ"

    print(f"    └─ Résultat SOC : {status}")
    return success


def _get_scenarios() -> dict[str, DemoScenario]:
    """Retourne le registre complet des scénarios de démonstration."""
    return {
        "nmap": DemoScenario("nmap", "Reconnaissance", "PortScan", "Scan de 100 ports TCP via Nmap", _exec_nmap),
        "hydra": DemoScenario("hydra", "Brute-Force", "Web Attack – Brute Force", "Attaque par dictionnaire HTTP via Hydra", _exec_hydra),
        "sqli": DemoScenario("sqli", "Injection Web", "Web Attack – Sql Injection", "Injection SQL UNION SELECT via Curl", _exec_sqli),
        "xss": DemoScenario("xss", "Injection Web", "Web Attack – XSS", "Injection XSS réfléchie <script> via Curl", _exec_xss),
        "log4j": DemoScenario("log4j", "Exploit RCE", "Infiltration", "Exploitation RCE Log4Shell JNDI via Curl", _exec_log4j),
        "gobuster": DemoScenario("gobuster", "Fuzzing Web", "Web Attack – Brute Force", "Fuzzing d'endpoints sensibles (.env) via Curl", _exec_gobuster),
        "ddos": DemoScenario("ddos", "Déni de Service", "DDoS", "Inondation volumétrique de 40 connexions concurrentes", _exec_ddos),
        "benign": DemoScenario("benign", "Contrôle", "BENIGN", "Requêtes HTTP légitimes de navigation normale", _exec_benign),
    }


def parse_args() -> argparse.Namespace:
    """Parse les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(description="Suite de démonstration d'attaques réelles (Nmap, Hydra, Curl).")
    parser.add_argument("--attack", choices=list(_get_scenarios().keys()), default=None, help="Scénario unique à lancer.")
    parser.add_argument("--all", action="store_true", help="Exécuter tous les scénarios séquentiellement.")
    parser.add_argument("--work-dir", type=Path, default=Path("/tmp/nids_demo"), help="Dossier temporaire PCAP.")
    return parser.parse_args()


def main() -> None:
    """Point d'entrée principal du script de démonstration."""
    args = parse_args()
    args.work_dir.mkdir(parents=True, exist_ok=True)
    scenarios = _get_scenarios()
    targets = scenarios.values() if (args.all or not args.attack) else [scenarios[args.attack]]

    print("=" * 78 + "\n   🛡️  SUITE DE DÉMONSTRATION DU NIDS TEMPS RÉEL (Attaques Offensives)\n" + "=" * 78)
    passed = 0
    for s in targets:
        if _run_single_demo(s, args.work_dir):
            passed += 1

    print("\n" + "=" * 78)
    print(f"📊 SYNTHÈSE DE LA DÉMONSTRATION : {passed}/{len(targets)} scénarios validés avec succès.")
    print("=" * 78 + "\n")


if __name__ == "__main__":
    main()
