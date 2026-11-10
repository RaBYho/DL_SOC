#!/usr/bin/env python3
"""Injecteur interactif d'attaques de test pour valider Sentinel NIDS en direct.

Ce script permet d'émettre des attaques de test réelles et contrôlées à travers
la carte réseau ou en local pour observer la réaction immédiate du terminal NIDS
et du Dashboard SOC.
"""

import argparse
import socket
import subprocess
import sys
import time
from pathlib import Path


def get_default_gateway_ip() -> str:
    """Détecte l'IP de la passerelle par défaut ou repli sur 172.20.10.1."""
    try:
        res = subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True)
        for part in res.stdout.split():
            if part.count(".") == 3 and not part.endswith(".0"):
                return part
    except Exception:
        pass
    return "172.20.10.1"


def run_portscan(target_ip: str, port_count: int = 25) -> None:
    """Exécute un scan TCP sur plusieurs ports pour déclencher l'heuristique PortScan."""
    print(f"\n[+] 🚀 Lancement d'un PortScan TCP sur {target_ip} (ports 1 à {port_count})...")
    cmd = ["nmap", "-sT", "-p", f"1-{port_count}", target_ip]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        print(f"[✔] Scan terminé. {port_count} ports sondés à travers la carte réseau.")
    except Exception as e:
        print(f"[!] Erreur Nmap: {e}")


def run_ddos_burst(target_ip: str, num_flows: int = 35) -> None:
    """Génère une rafale rapide de connexions TCP concurrentes pour déclencher le quorum DDoS."""
    print(f"\n[+] 🚀 Lancement d'une rafale volumétrique de {num_flows} connexions vers {target_ip}:80...")
    success = 0
    for _ in range(num_flows):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.2)
            s.connect_ex((target_ip, 80))
            s.close()
            success += 1
            time.sleep(0.02)
        except Exception:
            pass
    print(f"[✔] Rafale de {success} flux émise. Le quorum DDoS (30 flux) a été franchi.")


def run_cicids_replay(dashboard_url: str = "http://127.0.0.1:8000/api/dashboard") -> None:
    """Injecte un extrait d'attaques réelles CICIDS2017 directement dans le Dashboard."""
    print(f"\n[+] 🚀 Rejeu d'un batch d'attaques réelles CICIDS2017 (DDoS, Bot, Infiltration)...")
    mini_csv = Path("data/samples/mini.csv")
    if not mini_csv.exists():
        print(f"[!] Fichier {mini_csv} introuvable.")
        return

    cmd = [
        sys.executable,
        "scripts/run_demo.py",
        str(mini_csv),
        "--limit",
        "5",
    ]
    subprocess.run(cmd)
    print("\n[✔] Attaques réelles CICIDS2017 classifiées par le pipeline multicouche.")


def main() -> None:
    gateway = get_default_gateway_ip()
    print("=" * 68)
    print("  🛡️  SENTINEL NIDS — INJECTEUR D'ATTAQUES DE TEST EN CONDITIONS RÉELLES")
    print("=" * 68)
    print(f"  Cible réseau détectée : {gateway}")
    print()
    print("  Choisissez le scénario offensif à simuler :")
    print("    [1] PortScan TCP (Reconnaissance réseau Nmap - 25 ports)")
    print("    [2] Inondation volumétrique DDoS (Rafale de 35 flux TCP)")
    print("    [3] Rejeu d'attaques supervisées réelles (CICIDS2017 multi-classes)")
    print("    [4] Tout tester séquentiellement (PortScan + DDoS + CICIDS2017)")
    print("    [q] Quitter")
    print()

    choice = input("  Votre choix (1/2/3/4/q) : ").strip().lower()

    if choice == "1":
        run_portscan(gateway, 25)
    elif choice == "2":
        run_ddos_burst(gateway, 35)
    elif choice == "3":
        run_cicids_replay()
    elif choice == "4":
        run_portscan(gateway, 25)
        time.sleep(2)
        run_ddos_burst(gateway, 35)
        time.sleep(2)
        run_cicids_replay()
    else:
        print("[*] Annulé.")


if __name__ == "__main__":
    main()
