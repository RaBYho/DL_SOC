#!/usr/bin/env python3
"""Unified CLI entrypoint for NIDS (Live Capture, PCAP Analysis, and SOC Command Dashboard)."""

import argparse
import subprocess
import sys
import time
from pathlib import Path

# Add project root to sys.path
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sentinel NIDS | Multistage Intrusion Detection & Enterprise SOC Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation :
  1. Lancer uniquement le Dashboard SOC Web :
     python main.py --dashboard-only --port 8000

  2. Lancer la capture réseau en direct avec Dashboard SOC couplé :
     python main.py -i enx3ecd36af7cdb -b 5 --dashboard

  3. Analyser un fichier PCAP hors-ligne avec Dashboard SOC :
     python main.py --pcap pcap/demo_nmap.pcap --dashboard --allow-loopback
        """,
    )

    # Dashboard options
    parser.add_argument("--dashboard-only", action="store_true", help="Démarre uniquement le serveur Web SOC Dashboard.")
    parser.add_argument("--dashboard", action="store_true", help="Active le couplage temps réel avec le SOC Dashboard.")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Adresse d'écoute du serveur Dashboard (défaut: 0.0.0.0).")
    parser.add_argument("--port", type=int, default=8000, help="Port d'écoute du serveur Dashboard (défaut: 8000).")

    # Capture / Pipeline options forwarded to run_live_capture
    parser.add_argument("-i", "--interface", type=str, default=None, help="Interface réseau (auto-détectée si omis).")
    parser.add_argument("-b", "--duration", type=int, default=15, help="Durée de chaque micro-batch en secondes (défaut: 15s).")
    parser.add_argument("--pcap", type=Path, default=None, help="Fichier PCAP hors-ligne pour analyse immédiate.")
    parser.add_argument("--tool", choices=["dumpcap", "tcpdump"], default="dumpcap", help="Outil de capture sous-jacent.")
    parser.add_argument("--allow-loopback", action="store_true", help="Autorise le trafic sur l'interface locale (127.0.0.1).")
    parser.add_argument("--max-chunks", type=int, default=None, help="Arrête après N micro-batches.")
    parser.add_argument("--output", type=Path, default=None, help="Fichier JSON d'export des alertes.")
    parser.add_argument("--no-kitsune", action="store_true", help="Désactive la branche d'anomalies Kitsune.")
    parser.add_argument("--no-dpi", action="store_true", help="Désactive l'inspection de contenu applicatif (DPI).")
    parser.add_argument("--cooldown", type=float, default=None, help="Durée anti-flood de cooldown en secondes.")

    return parser.parse_args()


def main():
    args = parse_args()

    # Mode 1: Dashboard Only
    if args.dashboard_only:
        import uvicorn
        print(f"\n🚀 Démarrage du NIDS SOC Command Dashboard sur http://{args.host}:{args.port}")
        print(f"📖 Documentation interactive de l'API : http://{args.host}:{args.port}/docs\n")
        uvicorn.run("dashboard.backend.server:app", host=args.host, port=args.port)
        return

    dashboard_proc = None
    dashboard_url = f"http://127.0.0.1:{args.port}/api/dashboard"

    # Mode 2 & 3: Live / PCAP Analysis with optional integrated Dashboard
    if args.dashboard:
        print(f"\n📡 Lancement en tâche de fond du Dashboard SOC sur http://{args.host}:{args.port}...")
        srv_cmd = [sys.executable, str(REPO_ROOT / "scripts" / "run_dashboard.py"), "--host", args.host, "--port", str(args.port)]
        dashboard_proc = subprocess.Popen(srv_cmd)
        time.sleep(1.0)
        print(f"✅ Dashboard SOC actif. Accès : http://localhost:{args.port}\n")

    capture_cmd = [sys.executable, str(REPO_ROOT / "scripts" / "run_live_capture.py")]
    if args.interface:
        capture_cmd.extend(["-i", args.interface])
    if args.duration != 15:
        capture_cmd.extend(["-b", str(args.duration)])
    if args.pcap:
        capture_cmd.extend(["--pcap", str(args.pcap)])
    if args.tool != "dumpcap":
        capture_cmd.extend(["--tool", args.tool])
    if args.allow_loopback:
        capture_cmd.append("--allow-loopback")
    if args.max_chunks:
        capture_cmd.extend(["--max-chunks", str(args.max_chunks)])
    if args.output:
        capture_cmd.extend(["--output", str(args.output)])
    if args.no_kitsune:
        capture_cmd.append("--no-kitsune")
    if args.no_dpi:
        capture_cmd.append("--no-dpi")
    if args.cooldown is not None:
        capture_cmd.extend(["--cooldown", str(args.cooldown)])
    if args.dashboard:
        capture_cmd.extend(["--dashboard", "--dashboard-url", dashboard_url])

    try:
        subprocess.run(capture_cmd)
    finally:
        if dashboard_proc and dashboard_proc.poll() is None:
            print("\nArrêt du serveur SOC Dashboard...")
            dashboard_proc.terminate()
            try:
                dashboard_proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                dashboard_proc.kill()


if __name__ == "__main__":
    main()
