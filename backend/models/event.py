"""Core event schemas for ThreatIQ ingestion and normalization."""

import ipaddress
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class AssetCriticality(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventSeverity(str, Enum):
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Numeric mapping used for ML features and scoring.
ASSET_CRITICALITY_SCORES: dict[AssetCriticality, int] = {
    AssetCriticality.LOW: 1,
    AssetCriticality.MEDIUM: 2,
    AssetCriticality.HIGH: 4,
    AssetCriticality.CRITICAL: 5,
}

# Private/known networks treated as internal assets.
KNOWN_IP_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("192.168.0.0/16"),
]

# Allowed event types accepted from ingestion sources (Phase 19 input
# validation): the demo dataset telemetry, the MITRE-mapped detection
# types used by the correlator, and common authentication outcomes.
# Anything else is rejected at the API boundary with a 422.
ALLOWED_EVENT_TYPES = frozenset(
    {
        # Demo dataset / attack-chain telemetry.
        "https_session",
        "dns_query",
        "dns_spike",
        "ssh_session",
        "port_probe",
        "off_hour_login",
        "failed_vpn_login",
        "usb_device_insertion",
        "privilege_escalation_attempt",
        "after_hours_file_access",
        "impossible_travel_login",
        "malware_quarantined",
        "service_account_anomaly",
        "ssh_failed_login",
        "auth_brute_force",
        "login_success",
        "process_execution",
        "account_creation",
        "c2_reverse_shell",
        "certificate_modification",
        # MITRE-mapped detection types (see correlation/correlator.py).
        "authentication_failure",
        "port_scan",
        "data_exfiltration",
        "process_spawn",
        # Common authentication outcomes used by tests and integrations.
        "authentication",
        "failed_login",
        "successful_login",
        # Fallback for sources that omit the type.
        "unknown",
    }
)


class EventInput(BaseModel):
    """Raw security event as received from an ingestion source."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime | str
    source_ip: str
    dest_ip: Optional[str] = None
    event_type: str
    username: Optional[str] = None
    attempts: int = 1
    bytes_transferred: int = 0
    port: int = 0
    asset: str = "unknown"
    asset_criticality: AssetCriticality = AssetCriticality.LOW
    protocol: Optional[str] = "TCP"
    raw_payload: Optional[dict] = None

    @model_validator(mode="after")
    def coerce_timestamp(self) -> "EventInput":
        """Accept ISO-8601 strings for timestamp and store a datetime."""
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)
        return self

    @model_validator(mode="after")
    def validate_event_type(self) -> "EventInput":
        """Normalize event_type and enforce the allowed-type list."""
        self.event_type = str(self.event_type or "unknown").strip().lower()
        if self.event_type not in ALLOWED_EVENT_TYPES:
            raise ValueError(
                f"Unsupported event_type {self.event_type!r}; "
                f"allowed types: {sorted(ALLOWED_EVENT_TYPES)}"
            )
        return self


class NormalizedEvent(EventInput):
    """Event enriched with numeric features for detection and scoring."""

    hour_of_day: int = Field(ge=0, le=23)
    is_known_ip: int = Field(ge=0, le=1)
    asset_criticality_score: int = Field(ge=1, le=5)
    anomaly_score: float = 0.0
    is_anomaly: bool = False


def _is_known_ip(ip: Optional[str]) -> int:
    """Return 1 if the IP belongs to a private/known network, else 0."""
    if not ip:
        return 0
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return 0
    return int(any(address in network for network in KNOWN_IP_NETWORKS))


def normalize_event(event: EventInput) -> NormalizedEvent:
    """Convert an EventInput into a feature-rich NormalizedEvent.

    - Parses ISO timestamps (already coerced by the model validator).
    - Extracts hour_of_day (0-23) from the event timestamp.
    - Maps asset criticality to a 1-5 numeric score.
    - Flags whether the source IP is within known private networks.
    """
    timestamp = event.timestamp
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp)

    return NormalizedEvent(
        **event.model_dump(),
        hour_of_day=timestamp.hour,
        is_known_ip=_is_known_ip(event.source_ip),
        asset_criticality_score=ASSET_CRITICALITY_SCORES[event.asset_criticality],
    )
