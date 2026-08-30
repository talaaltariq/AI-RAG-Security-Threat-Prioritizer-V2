"""Script-style integration test for the ThreatIQ FastAPI backend.

Covers the Phase 14 Definition of Done: app startup, /health, ingestion
pipeline, incident listing/detail, analyst actions, and stats.

Runs against a temporary SQLite database with RAG/LLM services stubbed
out (no external API calls). Run from the repository root::

    venv/Scripts/python backend/test_api_integration.py
"""

import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Isolate the test database before any backend.database import.
_TMP_DB = Path(tempfile.mkdtemp()) / "test_threatiq.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB}"

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

CHECKS = []


def check(name: str, condition: bool) -> None:
    CHECKS.append((name, condition))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}")


def main() -> int:
    with TestClient(app) as client:
        # Keep the test offline: stub out external services after startup.
        app.state.rag_retriever = None
        app.state.explainer = None

        # 1. Health check.
        resp = client.get("/health")
        check("GET /health -> 200", resp.status_code == 200)
        body = resp.json()
        check(
            "health body has status/version",
            body.get("status") == "ok" and body.get("version") == "1.0.0",
        )

        # 2. Ingest: 2 correlated port_scan events + 1 singleton.
        # Timestamps are relative to today so the /api/stats "events
        # today" check never goes stale.
        today_10am = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        ts = lambda dt: dt.isoformat()  # noqa: E731
        events = [
            {
                "timestamp": ts(today_10am),
                "source_ip": "203.0.113.9",
                "dest_ip": "10.0.0.5",
                "event_type": "port_scan",
                "asset": "prod-db-01",
                "asset_criticality": "critical",
                "port": 3306,
                "raw_payload": {"raw_severity": "high", "details": "scan burst"},
            },
            {
                "timestamp": ts(today_10am + timedelta(minutes=5)),
                "source_ip": "203.0.113.9",
                "dest_ip": "10.0.0.5",
                "event_type": "authentication_failure",
                "asset": "prod-db-01",
                "asset_criticality": "critical",
                "attempts": 25,
                "port": 3306,
                "raw_payload": {"raw_severity": "critical"},
            },
            {
                "timestamp": ts(today_10am + timedelta(hours=2)),
                "source_ip": "10.0.0.50",
                "dest_ip": "10.0.0.1",
                "event_type": "https_session",
                "asset": "web-proxy-01",
                "asset_criticality": "low",
                "port": 443,
                "raw_payload": {"raw_severity": "low"},
            },
        ]
        resp = client.post("/api/ingest", json=events)
        check("POST /api/ingest -> 201", resp.status_code == 201)
        ingest_body = resp.json()
        check(
            "2 correlated + 1 singleton = 2 incidents",
            ingest_body.get("incidents_created") == 2,
        )
        check("3 events received", ingest_body.get("events_received") == 3)

        # 3. List incidents sorted by score desc.
        resp = client.get("/api/incidents")
        check("GET /api/incidents -> 200", resp.status_code == 200)
        incidents = resp.json()
        check("2 incidents listed", len(incidents) == 2)
        scores = [i["total_score"] for i in incidents]
        check("sorted by total_score DESC", scores == sorted(scores, reverse=True))
        top = incidents[0]
        check(
            "top incident has 2 correlated events + MITRE technique",
            top["events_count"] == 2 and top["mitre_technique"] in ("T1046", "T1110.001"),
        )

        # 4. Incident detail.
        resp = client.get(f"/api/incidents/{top['id']}")
        check("GET /api/incidents/{id} -> 200", resp.status_code == 200)
        detail = resp.json()
        check("detail has 2 events", len(detail.get("events", [])) == 2)
        check(
            "detail has score_factors with raw anomaly score",
            detail.get("score_factors", {}).get("anomaly_score_raw") is not None,
        )
        check(
            "detail has rag_results/llm_explanation/analyst_actions keys",
            all(
                k in detail
                for k in ("rag_results", "llm_explanation", "analyst_actions")
            ),
        )

        # 5. Unknown incident -> 404.
        resp = client.get("/api/incidents/does-not-exist")
        check("GET unknown incident -> 404", resp.status_code == 404)

        # 6. Analyst action flow: acknowledge -> resolve -> 409 on terminal.
        resp = client.post(
            f"/api/incidents/{top['id']}/action",
            json={"action": "acknowledge", "analyst_note": "triaging"},
        )
        check("POST action acknowledge -> 200", resp.status_code == 200)
        check(
            "status transitioned to acknowledged",
            resp.json().get("incident_status") == "acknowledged",
        )
        resp = client.post(
            f"/api/incidents/{top['id']}/action", json={"action": "resolve"}
        )
        check("POST action resolve -> 200", resp.status_code == 200)
        check(
            "status transitioned to resolved",
            resp.json().get("incident_status") == "resolved",
        )
        resp = client.post(
            f"/api/incidents/{top['id']}/action", json={"action": "acknowledge"}
        )
        check("action on resolved incident -> 409", resp.status_code == 409)
        resp = client.post(
            f"/api/incidents/{top['id']}/action", json={"action": "bogus"}
        )
        check("invalid action literal -> 422", resp.status_code == 422)

        # 7. Stats.
        resp = client.get("/api/stats")
        check("GET /api/stats -> 200", resp.status_code == 200)
        stats = resp.json()
        check(
            "stats fields present",
            all(
                k in stats
                for k in (
                    "total_events_today",
                    "total_incidents",
                    "critical_count",
                    "high_count",
                    "medium_count",
                    "low_count",
                    "alert_reduction_pct",
                )
            ),
        )
        check("stats: 3 events today", stats["total_events_today"] == 3)
        check("stats: 2 incidents", stats["total_incidents"] == 2)
        check(
            "alert reduction = 33.3%",
            abs(stats["alert_reduction_pct"] - 33.3) < 0.05,
        )

        # 8. Phase 19 input validation guards (failed requests persist nothing).
        resp = client.post(
            "/api/ingest",
            json=[{
                "timestamp": ts(today_10am),
                "source_ip": "10.0.0.9",
                "event_type": "totally_made_up_type",
                "asset": "prod-db-01",
            }],
        )
        check("invalid event_type -> 422", resp.status_code == 422)
        oversized = [
            {
                "timestamp": ts(today_10am),
                "source_ip": "10.0.0.9",
                "event_type": "port_scan",
                "asset": "prod-db-01",
            }
        ] * 1001
        resp = client.post("/api/ingest", json=oversized)
        check(">1000 events -> 413", resp.status_code == 413)
        resp = client.get("/api/incidents")
        check(
            "rejected requests persisted nothing (still 2 incidents)",
            len(resp.json()) == 2,
        )

    failed = [name for name, ok in CHECKS if not ok]
    print(f"\n{len(CHECKS) - len(failed)}/{len(CHECKS)} checks passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
