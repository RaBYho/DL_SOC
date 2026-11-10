"""Tests unitaires pour le corrélateur et réducteur de fausses alertes (live_guard.py)."""

import numpy as np
import pandas as pd
import pytest

from nids.live_guard import LiveAlertGuard, ConsolidatedAlert


@pytest.fixture
def guard_config() -> dict:
    """Configuration représentative de live_guard.yaml."""
    return {
        "threat_scoring": {
            "alert_threshold": 100.0,
            "half_life_sec": 60.0,
            "weights": {
                "BENIGN": 0.0,
                "SUSPECT_UNCERTAIN": 15.0,
                "ANOMALY_UNKNOWN": 20.0,
                "KNOWN_ATTACK": 40.0,
                "KNOWN_ATTACK_HIGH_CONF": 100.0,
                "UNKNOWN_ATTACK_LIKELY": 60.0,
            },
        },
        "quorum_rules": {
            "volumetric_classes": [
                "DDoS",
                "DoS Hulk",
                "DoS GoldenEye",
                "DoS Slowloris",
                "DoS Slowhttptest",
                "PortScan",
            ],
            "volumetric_min_flows": 15,
            "volumetric_window_sec": 10.0,
        },
        "cooldown": {
            "ttl_sec": 300.0,
        },
    }


def make_single_flow_df(
    src_ip: str, dst_ip: str = "172.16.0.1", timestamp: float = 1000.0
) -> pd.DataFrame:
    """Helper pour fabriquer un batch d'un flux."""
    return pd.DataFrame({
        "Source IP": [src_ip],
        "Destination IP": [dst_ip],
        "Timestamp": [timestamp],
    })


def test_isolated_false_positive_no_alert(guard_config: dict):
    """Vérifie qu'un faux positif isolé (score < 100) n'émet aucune alerte."""
    guard = LiveAlertGuard(guard_config)
    df = make_single_flow_df("192.168.1.50")
    verdicts = pd.Series(["SUSPECT_UNCERTAIN"])  # +15 points

    alerts = guard.process_batch(
        flows_df=df,
        verdicts=verdicts,
        s1_scores=np.array([0.5]),
        s2_confs=np.array([0.4]),
        timestamps=np.array([1000.0]),
    )

    assert len(alerts) == 0


def test_volumetric_quorum(guard_config: dict):
    """Vérifie qu'un PortScan n'alerte qu'au 15e flux en moins de 10s."""
    guard = LiveAlertGuard(guard_config)
    src = "192.168.1.50"

    # 14 flux de PortScan envoyés entre t=0 et t=5s
    t_14 = np.linspace(0.0, 5.0, 14)
    df_14 = pd.DataFrame({
        "Source IP": [src] * 14,
        "Destination IP": ["172.16.0.1"] * 14,
    })
    verdicts_14 = pd.Series(["PortScan"] * 14)

    alerts_14 = guard.process_batch(
        flows_df=df_14,
        verdicts=verdicts_14,
        s1_scores=np.ones(14) * 0.9,
        s2_confs=np.ones(14) * 0.95,
        timestamps=t_14,
    )
    assert len(alerts_14) == 0  # Quorum de 15 non atteint !

    # 15e flux à t=6s
    df_15 = make_single_flow_df(src)
    verdicts_15 = pd.Series(["PortScan"])
    alerts_15 = guard.process_batch(
        flows_df=df_15,
        verdicts=verdicts_15,
        s1_scores=np.array([0.9]),
        s2_confs=np.array([0.95]),
        timestamps=np.array([6.0]),
    )

    assert len(alerts_15) == 1
    assert alerts_15[0].attack_class == "PortScan"
    assert alerts_15[0].flow_count >= 15


def test_multi_signal_accumulation(guard_config: dict):
    """Vérifie l'accumulation multi-indices (2x UNKNOWN_ATTACK_LIKELY = 120 >= 100)."""
    guard = LiveAlertGuard(guard_config)
    src = "192.168.1.77"

    df_2 = pd.DataFrame({
        "Source IP": [src, src],
        "Destination IP": ["172.16.0.2", "172.16.0.2"],
    })
    verdicts_2 = pd.Series(["UNKNOWN_ATTACK_LIKELY", "UNKNOWN_ATTACK_LIKELY"])

    alerts = guard.process_batch(
        flows_df=df_2,
        verdicts=verdicts_2,
        s1_scores=np.array([0.8, 0.8]),
        s2_confs=np.array([0.5, 0.5]),
        timestamps=np.array([100.0, 102.0]),
    )

    assert len(alerts) == 1
    assert alerts[0].attack_class == "UNKNOWN_ATTACK_LIKELY"
    assert alerts[0].host_score >= 100.0


def test_half_life_temporal_decay(guard_config: dict):
    """Vérifie la décroissance exponentielle du score après 120 secondes."""
    guard = LiveAlertGuard(guard_config)
    src = "192.168.1.88"

    # t=0s : 1 flux UNKNOWN_ATTACK_LIKELY (+60 points) -> score = 60 (< 100)
    df_1 = make_single_flow_df(src)
    alerts_1 = guard.process_batch(
        flows_df=df_1,
        verdicts=pd.Series(["UNKNOWN_ATTACK_LIKELY"]),
        s1_scores=np.array([0.8]),
        s2_confs=np.array([0.5]),
        timestamps=np.array([0.0]),
    )
    assert len(alerts_1) == 0

    # À t=120s (deux demi-vies de 60s, score tombé à 60 / 4 = 15 points)
    # Nouvel impact de +60 points -> score total = 15 + 60 = 75 (< 100) -> Pas d'alerte !
    df_2 = make_single_flow_df(src)
    alerts_2 = guard.process_batch(
        flows_df=df_2,
        verdicts=pd.Series(["UNKNOWN_ATTACK_LIKELY"]),
        s1_scores=np.array([0.8]),
        s2_confs=np.array([0.5]),
        timestamps=np.array([120.0]),
    )
    assert len(alerts_2) == 0


def test_anti_flood_cooldown_and_wake_up(guard_config: dict):
    """Vérifie le cooldown anti-flood (1 seule alerte pour 500 flux) puis réveil post-TTL."""
    guard = LiveAlertGuard(guard_config)
    src = "192.168.1.99"

    # 500 flux de DDoS sur 30 secondes
    t_500 = np.linspace(0.0, 30.0, 500)
    df_500 = pd.DataFrame({
        "Source IP": [src] * 500,
        "Destination IP": ["172.16.0.1"] * 500,
    })
    verdicts_500 = pd.Series(["DDoS"] * 500)

    alerts_initial = guard.process_batch(
        flows_df=df_500,
        verdicts=verdicts_500,
        s1_scores=np.ones(500) * 0.99,
        s2_confs=np.ones(500) * 0.99,
        timestamps=t_500,
    )

    # 1 seule alerte consolidée émise pendant le pic
    assert len(alerts_initial) == 1
    assert alerts_initial[0].attack_class == "DDoS"

    # Nouvelle attaque après expiration du cooldown (t = 301s > 300s TTL)
    df_post = make_single_flow_df(src)
    # Plusieurs flux à t=301s pour franchir le quorum volumétrique
    t_post = np.ones(15) * 301.0
    df_post_15 = pd.DataFrame({
        "Source IP": [src] * 15,
        "Destination IP": ["172.16.0.1"] * 15,
    })
    alerts_post = guard.process_batch(
        flows_df=df_post_15,
        verdicts=pd.Series(["DDoS"] * 15),
        s1_scores=np.ones(15) * 0.99,
        s2_confs=np.ones(15) * 0.99,
        timestamps=t_post,
    )

    # Réveil post-cooldown : nouvelle alerte émise
    assert len(alerts_post) == 1
    assert alerts_post[0].suppressed_count > 0


def test_ip_isolation(guard_config: dict):
    """Vérifie que l'accumulation de score sur IP A n'impacte pas IP B."""
    guard = LiveAlertGuard(guard_config)
    ip_a = "192.168.1.10"
    ip_b = "192.168.1.11"

    df = pd.DataFrame({
        "Source IP": [ip_a, ip_b],
        "Destination IP": ["172.16.0.1", "172.16.0.1"],
    })
    verdicts = pd.Series(["UNKNOWN_ATTACK_LIKELY", "BENIGN"])

    _ = guard.process_batch(
        flows_df=df,
        verdicts=verdicts,
        s1_scores=np.array([0.8, 0.01]),
        s2_confs=np.array([0.5, 0.0]),
        timestamps=np.array([0.0, 0.0]),
    )

    score_a = guard.get_host_score(ip_a, current_time=0.0)
    score_b = guard.get_host_score(ip_b, current_time=0.0)

    assert score_a >= 60.0
    assert score_b == 0.0


def test_slow_portscan_detection_via_distinct_ports(guard_config: dict):
    """Vérifie qu'un scan lent (<15 flux/10s mais >=10 ports distincts) déclenche bien une alerte PortScan."""
    guard = LiveAlertGuard(guard_config)
    src = "192.168.1.50"

    # 12 flux espacés de 2 secondes (durée: 24s) vers 12 ports distincts
    t_12 = np.linspace(0.0, 24.0, 12)
    df_12 = pd.DataFrame({
        "Source IP": [src] * 12,
        "Destination IP": ["172.16.0.1"] * 12,
        "Destination Port": list(range(1, 13)),
        "SYN Flag Count": [1] * 12,
        "Timestamp": t_12,
    })
    # Même si individuellement chaque micro-flux est marqué BENIGN par un modèle local :
    verdicts = pd.Series(["BENIGN"] * 12)

    alerts = guard.process_batch(
        flows_df=df_12,
        verdicts=verdicts,
        s1_scores=np.zeros(12),
        s2_confs=np.zeros(12),
        timestamps=t_12,
    )

    assert len(alerts) == 1
    assert alerts[0].attack_class == "PortScan"
    assert alerts[0].flow_count >= 10


def test_ddos_flow_rate_spike_detection(guard_config: dict):
    """Vérifie qu'un pic de flux rapide (>=30 flux en <=5s) déclenche une alerte DDoS même si les flux sont BENIGN."""
    guard = LiveAlertGuard(guard_config)
    src = "192.168.1.50"

    t_35 = np.linspace(0.0, 3.0, 35)
    df_35 = pd.DataFrame({
        "Source IP": [src] * 35,
        "Destination IP": ["172.16.0.1"] * 35,
        "Destination Port": [80] * 35,
        "SYN Flag Count": [0] * 35,
        "Timestamp": t_35,
    })
    verdicts = pd.Series(["BENIGN"] * 35)

    alerts = guard.process_batch(
        flows_df=df_35,
        verdicts=verdicts,
        s1_scores=np.zeros(35),
        s2_confs=np.zeros(35),
        timestamps=t_35,
    )

    assert len(alerts) == 1
    assert alerts[0].attack_class == "DDoS"
    assert alerts[0].host_score >= 100.0
    assert alerts[0].flow_count >= 30


def test_ddos_ignores_port_443_https_assets(guard_config: dict):
    """Vérifie que des flux HTTPS bénins (port 443) ne déclenchent pas de faux DDoS."""
    guard = LiveAlertGuard(guard_config)
    src = "172.20.10.5"

    t_40 = np.linspace(0.0, 3.0, 40)
    df_40 = pd.DataFrame({
        "Source IP": [src] * 40,
        "Destination IP": ["102.132.104.53"] * 40,
        "Destination Port": [443] * 40,
        "SYN Flag Count": [0] * 40,
        "Timestamp": t_40,
    })
    verdicts = pd.Series(["BENIGN"] * 40)

    alerts = guard.process_batch(
        flows_df=df_40,
        verdicts=verdicts,
        s1_scores=np.zeros(40),
        s2_confs=np.zeros(40),
        timestamps=t_40,
    )
    assert len(alerts) == 0
