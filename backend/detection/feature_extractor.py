"""Feature extraction for the ThreatIQ anomaly detection module.

Converts a normalized event dictionary (see backend/models/event.py) into the
fixed 7-dimensional numeric feature vector consumed by the IsolationForest
anomaly detector.
"""

import ipaddress
from datetime import datetime
from typing import Any, Optional

import numpy as np

# Canonical feature order used for training and inference.
FEATURE_NAMES = [
    "hour_of_day",
    "failed_attempts",
    "bytes_transferred",
    "port_number",
    "events_from_ip_last_hour",
    "is_known_ip",
    "asset_criticality_score",
]

# Common service ports seen in normal traffic (used by the detector for
# synthetic training data).
COMMON_PORTS = [22, 53, 80, 443, 445, 3306, 3389, 8080]

# Numeric mapping aligned with ASSET_CRITICALITY_SCORES in backend/models/event.py.
_ASSET_CRITICALITY_SCORES = {
    "low": 1,
    "medium": 2,
    "high": 4,
    "critical": 5,
}

# Private/known networks treated as internal assets (mirrors event.py).
_KNOWN_IP_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("192.168.0.0/16"),
]


def _to_number(value: Any, default: float) -> float:
    """Coerce a value to float, falling back to the given default."""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _extract_hour(event: dict) -> float:
    """Return hour_of_day (0-23), deriving it from the timestamp if needed."""
    if event.get("hour_of_day") is not None:
        return _to_number(event.get("hour_of_day"), -1.0)
    timestamp: Optional[Any] = event.get("timestamp")
    if isinstance(timestamp, datetime):
        return float(timestamp.hour)
    if isinstance(timestamp, str):
        try:
            return float(datetime.fromisoformat(timestamp).hour)
        except ValueError:
            return -1.0
    return -1.0


def _extract_is_known_ip(event: dict) -> float:
    """Return 1 when the source IP sits in a known/private network, else 0."""
    if event.get("is_known_ip") is not None:
        return _to_number(event.get("is_known_ip"), 0.0)
    ip = event.get("source_ip")
    if not ip:
        return 0.0
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return 0.0
    return float(any(address in network for network in _KNOWN_IP_NETWORKS))


def _extract_asset_criticality(event: dict) -> float:
    """Return the 1-5 asset criticality score, mapping string labels if needed."""
    if event.get("asset_criticality_score") is not None:
        return _to_number(event.get("asset_criticality_score"), -1.0)
    label = event.get("asset_criticality")
    if isinstance(label, str):
        return float(_ASSET_CRITICALITY_SCORES.get(label.lower(), -1))
    return -1.0


def extract_features(event: dict) -> np.ndarray:
    """Extract the 7-feature numeric vector from a normalized event dict.

    Feature order: hour_of_day, failed_attempts, bytes_transferred,
    port_number, events_from_ip_last_hour, is_known_ip,
    asset_criticality_score.

    Missing counts default to 0; unknown categorical/time fields default to -1.

    Returns:
        numpy array of shape (1, 7), dtype float64.
    """
    features = [
        _extract_hour(event),
        _to_number(event.get("failed_attempts", event.get("attempts")), 0.0),
        _to_number(event.get("bytes_transferred"), 0.0),
        _to_number(event.get("port_number", event.get("port")), -1.0),
        _to_number(event.get("events_from_ip_last_hour"), 1.0),
        _extract_is_known_ip(event),
        _extract_asset_criticality(event),
    ]
    return np.array(features, dtype=float).reshape(1, len(FEATURE_NAMES))


class FeatureExtractor:
    """Stateful wrapper around :func:`extract_features` for dependency injection."""

    feature_names = FEATURE_NAMES

    def extract(self, event: dict) -> np.ndarray:
        """Return the (1, 7) feature vector for a normalized event dict."""
        return extract_features(event)
