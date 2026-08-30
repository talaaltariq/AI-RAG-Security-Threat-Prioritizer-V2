"""Event correlation layer for ThreatIQ.

Groups normalized, detection-enriched event dicts into incident dicts.
Two events belong to the same incident when they share a source IP and
occur within a 15-minute window (chained transitively), or when they map
to the same MITRE ATT&CK technique. Events that match no group become
single-event incidents.
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """Return the current UTC time as a naive datetime (SQLite-friendly)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

# MITRE ATT&CK technique detection from the event type.
EVENT_TYPE_TO_MITRE: Dict[str, str] = {
    "authentication_failure": "T1110.001",
    "port_scan": "T1046",
    "data_exfiltration": "T1041",
    "process_spawn": "T1059",
}

# Ordinal rankings used to pick the strongest severity / criticality in a group.
_SEVERITY_ORDER = {
    "informational": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}
_CRITICALITY_ORDER = {"low": 1, "medium": 2, "high": 4, "critical": 5}


class EventCorrelator:
    """Clusters event dicts into incident dicts (``IncidentDict``)."""

    TIME_WINDOW_MINUTES = 15

    def correlate(self, events_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group events into incidents.

        Args:
            events_list: normalized event dicts (must carry ``timestamp``,
                ``source_ip``, ``event_type``; ``severity``, ``asset`` and
                ``asset_criticality`` are used when present).

        Returns:
            A list of incident dicts with keys ``id``, ``created_at``,
            ``status``, ``asset``, ``asset_criticality``, ``severity``,
            ``latest_event_time``, ``mitre_technique``, and ``events``.
            Every input event lands in exactly one incident; ungrouped
            events become single-event incidents.
        """
        events = self._prepare(events_list)
        if not events:
            return []

        parent = list(range(len(events)))

        def find(i: int) -> int:
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        def union(a: int, b: int) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        self._union_by_source_ip_window(events, union)
        self._union_by_technique(events, union)

        groups: Dict[int, List[int]] = defaultdict(list)
        for i in range(len(events)):
            groups[find(i)].append(i)

        incidents = [
            self._build_incident([events[i] for i in indices])
            for indices in groups.values()
        ]
        incidents.sort(
            key=lambda inc: inc["latest_event_time"] or datetime.min,
            reverse=True,
        )
        logger.info(
            "Correlated %d events into %d incidents.", len(events), len(incidents)
        )
        return incidents

    # ------------------------------------------------------------------ #
    # Grouping rules
    # ------------------------------------------------------------------ #

    def _union_by_source_ip_window(self, events, union) -> None:
        """Union events from the same source IP within the time window."""
        by_ip: Dict[str, List[int]] = defaultdict(list)
        for i, event in enumerate(events):
            source_ip = event.get("source_ip")
            if source_ip:
                by_ip[str(source_ip)].append(i)

        window_seconds = self.TIME_WINDOW_MINUTES * 60
        for indices in by_ip.values():
            indices.sort(
                key=lambda i: events[i]["_dt"] or datetime.min
            )
            for a, b in zip(indices, indices[1:]):
                t_a, t_b = events[a]["_dt"], events[b]["_dt"]
                if t_a and t_b and (t_b - t_a).total_seconds() <= window_seconds:
                    union(a, b)

    def _union_by_technique(self, events, union) -> None:
        """Union events that map to the same MITRE ATT&CK technique."""
        by_technique: Dict[str, List[int]] = defaultdict(list)
        for i, event in enumerate(events):
            technique = event.get("_mitre")
            if technique:
                by_technique[technique].append(i)
        for indices in by_technique.values():
            for other in indices[1:]:
                union(indices[0], other)

    # ------------------------------------------------------------------ #
    # Incident assembly
    # ------------------------------------------------------------------ #

    def _build_incident(self, group: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build one incident dict from a group of prepared events."""
        group.sort(key=lambda e: e["_dt"] or datetime.min)

        timestamps = [e["_dt"] for e in group if e["_dt"] is not None]
        latest_event_time = max(timestamps) if timestamps else None

        severity = max(
            (str(e.get("severity") or "low").lower() for e in group),
            key=lambda s: _SEVERITY_ORDER.get(s, 1),
        )
        criticality = max(
            (str(e.get("asset_criticality") or "low").lower() for e in group),
            key=lambda c: _CRITICALITY_ORDER.get(c, 1),
        )
        # Asset taken from the most critical event(s); most frequent wins ties.
        top_assets = [
            str(e.get("asset") or "unknown")
            for e in group
            if _CRITICALITY_ORDER.get(str(e.get("asset_criticality") or "low").lower(), 1)
            == _CRITICALITY_ORDER[criticality]
        ]
        asset = max(set(top_assets), key=top_assets.count) if top_assets else "unknown"

        mitre_technique = next(
            (e["_mitre"] for e in group if e.get("_mitre")), None
        )

        clean_events = [
            {k: v for k, v in e.items() if not k.startswith("_")} for e in group
        ]

        return {
            "id": str(uuid4()),
            "created_at": _utcnow(),
            "status": "active",
            "asset": asset,
            "asset_criticality": criticality,
            "severity": severity,
            "latest_event_time": latest_event_time,
            "mitre_technique": mitre_technique,
            "events": clean_events,
        }

    # ------------------------------------------------------------------ #
    # Preparation helpers
    # ------------------------------------------------------------------ #

    def _prepare(self, events_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Copy event dicts and attach parsed timestamp / MITRE technique."""
        prepared = []
        for event in events_list:
            if not isinstance(event, dict):
                continue
            item = dict(event)
            item["_dt"] = self._parse_timestamp(event.get("timestamp"))
            item["_mitre"] = EVENT_TYPE_TO_MITRE.get(
                str(event.get("event_type") or "").strip().lower()
            )
            prepared.append(item)
        return prepared

    def _parse_timestamp(self, value: Any) -> Optional[datetime]:
        """Parse a datetime or ISO-8601 string; None when unparseable."""
        if isinstance(value, datetime):
            return value.replace(tzinfo=None)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                ).replace(tzinfo=None)
            except ValueError:
                return None
        return None
