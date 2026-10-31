import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class AggregatedAlert:
    attack_type: str
    src_ip: str
    count: int = 1
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    dst_ports: Set[int] = field(default_factory=set)
    max_mse: float = 0.0
    is_zero_day: bool = False
    digest_sent: bool = False


class AlertThrottler:
    """Moteur anti-spam et d'agrégation d'alertes par fenêtre glissante."""

    def __init__(self, debounce_window_sec: float = 60.0):
        self.debounce_window_sec = debounce_window_sec
        self._active_buckets: Dict[str, AggregatedAlert] = {}

    def _bucket_key(self, attack_type: str, src_ip: str) -> str:
        return f"{attack_type}::{src_ip}"

    def process_event(
        self,
        attack_type: str,
        src_ip: str,
        dst_port: Optional[int] = None,
        mse_ae: float = 0.0,
        is_zero_day: bool = False,
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Traite un événement d'alerte.
        Retourne (should_send_immediate, immediate_data).
        - Si c'est la 1ère occurrence d'une attaque/IP : retourne True pour envoi immédiat.
        - Si c'est un doublon dans la fenêtre des 60s : accumule silencieusement et retourne False.
        """
        now = time.time()
        key = self._bucket_key(attack_type, src_ip)

        bucket = self._active_buckets.get(key)

        if bucket is None or (now - bucket.first_seen > self.debounce_window_sec and bucket.digest_sent):
            # Nouveau bucket ou ancien bucket déjà clôturé
            new_bucket = AggregatedAlert(
                attack_type=attack_type,
                src_ip=src_ip,
                count=1,
                first_seen=now,
                last_seen=now,
                dst_ports={int(dst_port)} if dst_port is not None else set(),
                max_mse=float(mse_ae),
                is_zero_day=is_zero_day,
                digest_sent=False,
            )
            self._active_buckets[key] = new_bucket
            return True, {
                "attack_type": attack_type,
                "src_ip": src_ip,
                "dst_port": dst_port,
                "mse_ae": mse_ae,
                "is_zero_day": is_zero_day,
                "timestamp": now,
                "is_immediate": True,
            }

        # Déjà dans la fenêtre glissante : on accumule
        bucket.count += 1
        bucket.last_seen = now
        if dst_port is not None:
            bucket.dst_ports.add(int(dst_port))
        if mse_ae > bucket.max_mse:
            bucket.max_mse = float(mse_ae)

        return False, None

    def collect_expired_digests(self) -> List[Dict]:
        """
        Vérifie les buckets ayant dépassé la fenêtre glissante et contenant plusieurs événements.
        Génère un digest pour chaque groupe et nettoie la mémoire.
        """
        now = time.time()
        digests = []
        keys_to_remove = []

        for key, bucket in list(self._active_buckets.items()):
            elapsed = now - bucket.first_seen
            if elapsed >= self.debounce_window_sec:
                # Si plus d'1 événement est survenu pendant la fenêtre, on envoie le résumé
                if bucket.count > 1 and not bucket.digest_sent:
                    digests.append({
                        "attack_type": bucket.attack_type,
                        "src_ip": bucket.src_ip,
                        "count": bucket.count,
                        "duration_sec": round(bucket.last_seen - bucket.first_seen, 1),
                        "ports": sorted(list(bucket.dst_ports))[:10],
                        "max_mse": round(bucket.max_mse, 4),
                        "is_zero_day": bucket.is_zero_day,
                        "first_seen": bucket.first_seen,
                        "last_seen": bucket.last_seen,
                    })
                    bucket.digest_sent = True

                # Bucket expiré et traité, prêt pour le nettoyage
                keys_to_remove.append(key)

        for k in keys_to_remove:
            self._active_buckets.pop(k, None)

        return digests

    def reset(self):
        """Réinitialise les buckets en mémoire."""
        self._active_buckets.clear()
