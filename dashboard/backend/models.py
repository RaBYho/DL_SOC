"""Schémas Pydantic V2 stricts et flexibles pour l'API du Dashboard SOC."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class FlowRecord(BaseModel):
    """Représentation d'un flux réseau ingéré avec métriques de télémétrie."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    received_at: Optional[float] = None
    sensor_id: Optional[str] = "sensor-live"
    flow_start_ms: Optional[float] = None
    src_ip: str = Field(default="127.0.0.1", alias="Source IP")
    dst_ip: str = Field(default="127.0.0.1", alias="Destination IP")
    src_port: int = Field(default=0, alias="Source Port")
    dst_port: int = Field(default=80, alias="Destination Port")
    protocol: Any = Field(default=6, alias="Protocol")
    src_mac: Optional[str] = "00:00:00:00:00:00"
    total_fwd_packets: Optional[int] = Field(default=None, alias="Total Fwd Packets")
    total_bwd_packets: Optional[int] = Field(default=None, alias="Total Backward Packets")
    flow_duration: Optional[float] = Field(default=None, alias="Flow Duration")
    flow_bytes_s: Optional[float] = Field(default=None, alias="Flow Bytes/s")
    flow_packets_s: Optional[float] = Field(default=None, alias="Flow Packets/s")


class FlowIngestPayload(BaseModel):
    """Payload de transmission d'un micro-batch de capture réseau."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    sensor_id: str = "sensor-live"
    interface: str = "live"
    flow_records: List[Dict[str, Any]] = []
    flows: Optional[List[Dict[str, Any]]] = None
    predictions: List[str] = []
    confidences: List[float] = []
    mse_values: List[float] = []
    anomaly_values: List[int] = []
    duration_ms: float = 0.0

    @model_validator(mode="after")
    def sync_flows(self) -> "FlowIngestPayload":
        if self.flows and not self.flow_records:
            self.flow_records = self.flows
        elif self.flow_records and not self.flows:
            self.flows = self.flow_records
        return self


class FlowIngestResponse(BaseModel):
    """Réponse d'ingestion retournée au capteur."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    status: str = "success"
    inserted: int = 0
    inserted_flows: int = 0
    alerts: int = 0
    generated_incidents: int = 0
    total_packets_analyzed: int = 0
    traffic_status: str = "NORMAL"
    message: Optional[str] = None

    @model_validator(mode="after")
    def sync_counts(self) -> "FlowIngestResponse":
        if self.inserted and not self.inserted_flows:
            self.inserted_flows = self.inserted
        elif self.inserted_flows and not self.inserted:
            self.inserted = self.inserted_flows

        if self.alerts and not self.generated_incidents:
            self.generated_incidents = self.alerts
        elif self.generated_incidents and not self.alerts:
            self.alerts = self.generated_incidents
        return self


class SensorHeartbeatPayload(BaseModel):
    """Battement de cœur périodique émis par une sonde réseau."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    sensor_id: str
    interface: str = "eth0"
    status: str = "Online"
    packets_captured: int = 0
    flows_count: int = 0
    packets_per_sec: Optional[float] = 0.0
    flows_per_sec: Optional[float] = 0.0
    inference_latency_ms: Optional[float] = 0.0


class SensorHeartbeatResponse(BaseModel):
    """Accusé de réception du battement de cœur."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    status: str = "acknowledged"
    sensor_id: str
    server_time: Optional[float] = None


class SystemLogPayload(BaseModel):
    """Événement ou incident technique du moteur."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    source: Optional[str] = "system"
    component: Optional[str] = None
    message: str
    level: str = "INFO"
    details: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def sync_fields(self) -> "SystemLogPayload":
        if self.component and not self.source:
            self.source = self.component
        elif not self.source:
            self.source = "system"
        if self.metadata and not self.details:
            self.details = self.metadata
        return self


class SystemLogResponse(BaseModel):
    """Accusé de réception de log technique."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    status: str = "logged"


class IncidentStatusUpdate(BaseModel):
    """Mise à jour du statut d'investigation d'un incident."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    status: str = Field(..., description="OPEN, INVESTIGATING, RESOLVED, FALSE_POSITIVE")
    notes: Optional[str] = None
    comment: Optional[str] = None

    @model_validator(mode="after")
    def sync_notes(self) -> "IncidentStatusUpdate":
        if self.comment and not self.notes:
            self.notes = self.comment
        return self


class ReplayStartPayload(BaseModel):
    """Commande de lancement de rejeu de capture PCAP."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    pcap_name: Optional[str] = None
    pcap_path: Optional[str] = None
    speed: float = 1.0
    speed_multiplier: float = 1.0

    @model_validator(mode="after")
    def sync_replay(self) -> "ReplayStartPayload":
        if self.pcap_path and not self.pcap_name:
            self.pcap_name = self.pcap_path
        elif self.pcap_name and not self.pcap_path:
            self.pcap_path = self.pcap_name
        if self.speed_multiplier != 1.0 and self.speed == 1.0:
            self.speed = self.speed_multiplier
        return self


class TrafficStateResponse(BaseModel):
    """Synthèse d'état du trafic réseau pour la top status bar."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    status: str = "NORMAL"  # NORMAL, ELEVATED, CRITICAL
