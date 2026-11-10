"""Sensor telemetry and PCAP replay management endpoints."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
import time
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException

from dashboard.backend.config import DB_PATH, REPO_ROOT
from dashboard.backend.database import (
    get_attack_distribution,
    get_engine_distribution,
    get_kpis,
    get_sensors_list,
    get_targeted_stats,
    get_timeline,
    get_traffic_summary,
    insert_and_correlate_flows,
    record_sensor_heartbeat,
)
from dashboard.backend.models import (
    ReplayStartPayload,
    SensorHeartbeatPayload,
    SensorHeartbeatResponse,
)
from dashboard.backend.ws_manager import ws_manager

logger = logging.getLogger("dashboard.routes.sensors")
router = APIRouter(tags=["Sensors & Replay"])


@router.post("/sensor/heartbeat", response_model=SensorHeartbeatResponse)
async def sensor_heartbeat(payload: SensorHeartbeatPayload) -> SensorHeartbeatResponse:
    """Registers an operational heartbeat from a NIDS capture sensor node."""
    record_sensor_heartbeat(
        sensor_id=payload.sensor_id,
        interface=payload.interface,
        status=payload.status,
        packets_captured=payload.packets_captured or 0,
        flows_count=payload.flows_count or 0,
        db_path=DB_PATH,
    )

    await ws_manager.broadcast("sensor_heartbeat", payload.model_dump())
    return SensorHeartbeatResponse(
        status="acknowledged",
        server_time=time.time(),
        sensor_id=payload.sensor_id,
    )


@router.get("/sensors")
async def list_sensors() -> list[dict]:
    """Lists all registered capture sensors and their operational telemetry."""
    return get_sensors_list(db_path=DB_PATH)


@router.get("/pcaps")
async def list_available_pcaps() -> list[dict]:
    """Discovers available PCAP files in repository directories (pcap/, data/samples/)."""
    discovered: list[dict] = []
    search_dirs = [
        REPO_ROOT / "pcap",
        REPO_ROOT / "data" / "samples",
        Path("/tmp/nids_capture"),
    ]

    for sdir in search_dirs:
        if not sdir.exists():
            continue
        for pfile in sorted(sdir.glob("*.pcap")):
            try:
                st = pfile.stat()
                discovered.append({
                    "filename": pfile.name,
                    "path": str(pfile.resolve()),
                    "size_bytes": st.st_size,
                    "size_kb": round(st.st_size / 1024, 2),
                    "modified_time": st.st_mtime,
                })
            except OSError:
                continue

    return discovered


async def _run_pcap_replay_worker(pcap_path: str, speed_multiplier: float) -> None:
    """Asynchronous worker that processes a PCAP file with the NIDS pipeline and ingests into dashboard."""
    try:
        from nids.flow_extractor import convert_pcap_to_flows
        from nids.adapters.stage1 import CatBoostStage1, XGBoostStage1
        from nids.adapters.stage2 import DnnStage2
        from nids.kitsune_runner import KitNETAnomalyDetector
        from nids.pipeline import CascadedNIDSPipeline
        from nids.live_guard import LiveAlertGuard
        from nids.dpi_inspector import DPIInspector, fuse_predictions_with_dpi
        import yaml

        logger.info(f"Starting PCAP replay for: {pcap_path}")
        p_path = Path(pcap_path)
        if not p_path.exists():
            logger.error(f"Replay failed: PCAP file {pcap_path} not found")
            return

        cfg_path = REPO_ROOT / "configs" / "live_guard.yaml"
        config = {}
        if cfg_path.exists():
            with open(cfg_path) as f:
                config = yaml.safe_load(f)

        flows_df = convert_pcap_to_flows(p_path)
        if len(flows_df) == 0:
            logger.warning(f"Replay: No flows extracted from {pcap_path}")
            return

        pipe = CascadedNIDSPipeline(
            [CatBoostStage1(), XGBoostStage1()],
            DnnStage2(),
            t1=0.50,
            t2=0.70,
            kitsune_detector=KitNETAnomalyDetector(n_features=78, fm_grace=0, ad_grace=0),
            t3=0.0100,
        )
        guard = LiveAlertGuard(config)
        dpi = DPIInspector()

        # Step 1: Predict supervised + kitsune
        sup_df = pipe.predict(flows_df)

        # Step 2: DPI Inspection
        dpi_matches = dpi.inspect_pcap(p_path)
        sup_df = fuse_predictions_with_dpi(sup_df, flows_df, dpi_matches)

        # Step 3: Guard verification
        _ = guard.process_batch(
            flows_df=flows_df,
            verdicts=sup_df["verdict"],
            s1_scores=sup_df["stage1_score"].values,
            s2_confs=sup_df["confidence"].values,
        )

        # Ingest flows into DB
        flow_records = []
        for i, row in sup_df.iterrows():
            orig_row = flows_df.iloc[i]
            ts = float(orig_row.get("timestamp", time.time()))
            flow_records.append({
                "timestamp": ts,
                "src_ip": str(orig_row.get("src_ip", "127.0.0.1")),
                "dst_ip": str(orig_row.get("dst_ip", "127.0.0.1")),
                "src_port": int(orig_row.get("src_port", 0)),
                "dst_port": int(orig_row.get("dst_port", 0)),
                "protocol": str(orig_row.get("protocol", "TCP")),
                "packet_count": int(orig_row.get("Tot Fwd Pkts", 1) + orig_row.get("Tot Bwd Pkts", 0)),
                "verdict": str(row.get("verdict", "BENIGN")),
                "stage1_score": float(row.get("stage1_score", 0.0)),
                "confidence": float(row.get("confidence", 0.0)),
                "kitsune_score": float(row.get("kitsune_score", 0.0)),
                "decision_path": str(row.get("decision_path", "STAGE1_BENIGN")),
                "dpi_rule": str(row.get("dpi_rule", "") or ""),
                "dpi_category": str(row.get("dpi_category", "") or ""),
                "is_anomaly": bool(row.get("is_anomaly", False)),
                "raw_metrics": {
                    "duration": float(orig_row.get("Flow Duration", 0)),
                    "fwd_pkts": int(orig_row.get("Tot Fwd Pkts", 0)),
                    "bwd_pkts": int(orig_row.get("Tot Bwd Pkts", 0)),
                    "tot_bytes": float(orig_row.get("TotLen Fwd Pkts", 0) + orig_row.get("TotLen Bwd Pkts", 0)),
                },
            })

        inserted, incidents = insert_and_correlate_flows(
            flow_records, sensor_id="replay-engine", db_path=DB_PATH
        )
        logger.info(f"Replay complete: {inserted} flows ingested, {incidents} incidents generated.")

        # Broadcast telemetry
        kpis = get_kpis(db_path=DB_PATH)
        traffic = get_traffic_summary(db_path=DB_PATH)
        timeline = get_timeline(window_minutes=15, buckets=20, db_path=DB_PATH)
        engine_dist = get_engine_distribution(db_path=DB_PATH)
        targeted_stats = get_targeted_stats(db_path=DB_PATH)
        attack_dist = get_attack_distribution(db_path=DB_PATH)

        await ws_manager.broadcast("telemetry_update", {
            "sensor_id": "replay-engine",
            "inserted_flows": inserted,
            "generated_incidents": incidents,
            "kpis": kpis,
            "traffic": traffic,
            "timeline": timeline,
            "engine_distribution": engine_dist,
            "targeted_stats": targeted_stats,
            "attack_distribution": attack_dist,
        })
        await ws_manager.broadcast("replay_completed", {
            "pcap": p_path.name,
            "flows": inserted,
            "incidents": incidents,
        })
    except Exception as exc:
        logger.error(f"Replay failed with error: {exc}", exc_info=True)


@router.post("/replay/start")
async def start_pcap_replay(
    payload: ReplayStartPayload, background_tasks: BackgroundTasks
) -> dict:
    """Triggers background processing of a PCAP file to simulate live traffic."""
    target_path = payload.pcap_path or payload.pcap_name or ""
    pcap_path = Path(target_path)
    if not pcap_path.is_absolute():
        pcap_path = REPO_ROOT / target_path

    if not pcap_path.exists():
        raise HTTPException(status_code=404, detail=f"PCAP file {pcap_path} not found")

    speed = payload.speed_multiplier if payload.speed_multiplier != 1.0 else payload.speed
    background_tasks.add_task(_run_pcap_replay_worker, str(pcap_path), speed)
    return {
        "status": "started",
        "pcap": pcap_path.name,
        "message": f"Started replay of {pcap_path.name}",
    }
