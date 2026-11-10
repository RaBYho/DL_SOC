"""Module d'interface terminale Rich pour le monitoring SOC temps réel du NIDS."""

from contextlib import contextmanager
import os
from pathlib import Path
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from nids.live_guard import ConsolidatedAlert

CRITICAL_CLASSES = {
    "Web Attack – Sql Injection",
    "Web Attack – XSS",
    "Infiltration",
    "Bot",
    "Heartbleed",
}
HIGH_CLASSES = {
    "DDoS",
    "DoS GoldenEye",
    "DoS Slowhttptest",
    "DoS Hulk",
    "DoS slowloris",
}
MEDIUM_CLASSES = {
    "PortScan",
    "Web Attack – Brute Force",
    "FTP-Patator",
    "SSH-Patator",
}


@contextmanager
def suppress_c_stderr():
    """Redirige temporairement le descripteur stderr (fd 2) vers /dev/null."""
    try:
        null_fd = os.open(os.devnull, os.O_RDWR)
        saved_stderr = os.dup(2)
        os.dup2(null_fd, 2)
        yield
    finally:
        try:
            os.dup2(saved_stderr, 2)
            os.close(saved_stderr)
            os.close(null_fd)
        except OSError:
            pass


def get_severity_style(attack_class: str) -> tuple[str, str]:
    """Retourne le style visuel et le badge de sévérité selon la classe d'attaque."""
    if attack_class in CRITICAL_CLASSES:
        return "bold red", "CRITIQUE"
    if attack_class in HIGH_CLASSES:
        return "bold yellow", "ÉLEVÉ"
    if attack_class in MEDIUM_CLASSES:
        return "bold yellow", "MOYEN"
    if attack_class == "ANOMALY_UNKNOWN":
        return "bold magenta", "ANOMALIE INCONNUE"
    return "bold red", "ALERTE"


def _build_banner_table(
    iface: str, duration: int, t1: float, t2: float, t3: float, tool: str, is_pcap: bool, pcap_name: str | None
) -> Table:
    """Construit la table d'informations synthétiques pour la bannière SOC."""
    table = Table(box=box.SIMPLE_HEAD, show_header=False, expand=True, padding=(0, 1))
    table.add_column("Propriété", style="bold cyan", width=22)
    table.add_column("Valeur", style="white")

    mode_text = f"📦 Mode Hors-Ligne (PCAP: {pcap_name})" if is_pcap else f"📡 Temps Réel ({tool} sur {iface}, batch={duration}s)"
    table.add_row("Mode de détection", mode_text)
    table.add_row("Seuils de décision", f"t1={t1:.2f} (S1 Suspicion) │ t2={t2:.2f} (S2 Confiance) │ t3={t3:.4f} (Kitsune)")
    table.add_row(
        "Moteurs actifs",
        "[green]✔ Supervisé (CatBoost+XGB+CNN)[/green] │ [green]✔ Kitsune (Autoencodeur)[/green] │ [green]✔ DPI (Suricata)[/green]",
    )
    return table


def print_banner(
    console: Console,
    iface: str,
    duration: int,
    t1: float,
    t2: float,
    t3: float,
    tool: str,
    is_pcap: bool,
    pcap_name: str | None = None,
) -> None:
    """Affiche la bannière d'accueil du SOC Sentinel NIDS."""
    title = Text("🛡️  SENTINEL NIDS | CAPTURE & ANALYSE RÉSEAU TEMPS RÉEL", style="bold white on blue", justify="center")
    sub_table = _build_banner_table(iface, duration, t1, t2, t3, tool, is_pcap, pcap_name)
    panel = Panel(
        sub_table,
        title=title,
        subtitle="[dim]Surveillance active & détection d'intrusions multicouches[/dim]",
        border_style="bright_blue",
        box=box.ROUNDED,
    )
    console.print()
    console.print(panel)


def print_batch_status(
    console: Console, batch_num: int, pcap_name: str, n_flows: int, n_alerts: int, is_final: bool = False
) -> None:
    """Affiche une ligne d'état claire pour le micro-batch analysé."""
    prefix = f"[bold cyan]⚡ [Batch {'Final #' if is_final else '#'}{batch_num}][/bold cyan] {pcap_name}"
    flow_info = f"[dim]│[/dim] 📊 [bold white]{n_flows}[/bold white] flux"
    if n_alerts == 0:
        status_info = f"[dim]│[/dim] [green]✔ Trafic sain[/green] [dim](0 alerte)[/dim]"
    else:
        status_info = f"[dim]│[/dim] [bold red]🚨 {n_alerts} alerte(s) détectée(s)[/bold red]"
    console.print(f"{prefix} {flow_info} {status_info}")


def print_alert_card(console: Console, alert: ConsolidatedAlert) -> None:
    """Affiche une carte d'alerte stylisée SOC avec compatibilité machine-readable."""
    color, severity = get_severity_style(alert.attack_class)
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold white", width=18)
    table.add_column(style="white")
    table.add_row("Flux ciblé :", f"[bold cyan]{alert.src_ip}[/bold cyan]  ──▶  [bold yellow]{alert.dst_ip}[/bold yellow]")
    table.add_row("Classe d'attaque :", f"[{color}]{alert.attack_class}[/{color}]  [dim]({severity})[/dim]")
    table.add_row("Score hôte :", f"[{color}]{alert.host_score:.1f}[/{color}]")
    table.add_row(
        "Statistiques :",
        f"[white]{alert.flow_count}[/white] flux malveillants │ [dim]{alert.suppressed_count} supprimés (cooldown)[/dim]",
    )

    panel = Panel(
        table,
        title=f"[{color}]🚨 INCIDENT DE SÉCURITÉ DÉTECTÉ[/{color}]",
        border_style=color.replace("bold ", ""),
        box=box.HEAVY,
    )
    console.print(panel)
    console.print(
        f"[dim]🚨 [ALERTE CONSOLIDÉE] {alert.src_ip} -> {alert.dst_ip} | "
        f"Classe: {alert.attack_class} | Score hôte: {alert.host_score:.1f} | "
        f"Flux: {alert.flow_count} | Supprimés: {alert.suppressed_count}[/dim]",
        soft_wrap=True,
    )


def _build_summary_table(alerts: list[ConsolidatedAlert], total_batches: int) -> Table:
    """Génère la table de statistiques finales pour la session de capture."""
    table = Table(box=box.ROUNDED, expand=True)
    table.add_column("Métrique SOC", style="bold cyan")
    table.add_column("Valeur", justify="right", style="bold white")

    table.add_row("Micro-batches traités", str(total_batches))
    table.add_row("Alertes consolidées générées", str(len(alerts)))
    table.add_row("Total des flux malveillants", str(sum(a.flow_count for a in alerts)))
    table.add_row("Alertes supprimées (cooldown anti-flood)", str(sum(a.suppressed_count for a in alerts)))

    if alerts:
        from collections import Counter
        class_counts = Counter(a.attack_class for a in alerts)
        for cls, count in class_counts.most_common():
            table.add_row(f"  └─ Répartition : {cls}", str(count))
    return table


def print_session_summary(
    console: Console, alerts: list[ConsolidatedAlert], total_batches: int, output_path: Path | None
) -> None:
    """Affiche la synthèse d'exécution et le bilan SOC de la session."""
    table = _build_summary_table(alerts, total_batches)
    console.print()
    console.print(Panel(table, title="[bold white]📊 BILAN DE LA SESSION DE SURVEILLANCE[/bold white]", box=box.ROUNDED))
    if output_path:
        console.print(f"[dim]📁 Rapport d'incidents JSON exporté : [bold]{output_path}[/bold][/dim]")
    console.print(f"\n[bold green]✅ Exécution terminée : {len(alerts)} alerte(s) consolidée(s).[/bold green]\n" + "=" * 78)
