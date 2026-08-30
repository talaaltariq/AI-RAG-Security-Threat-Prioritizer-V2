"""Verify the "Operation Shadow DB" demo scenario end to end (Phase 20).

Runs the full ThreatPipeline against backend/demo_data/demo_events.json
on a throwaway SQLite database (no LLM, no RAG -> deterministic, fast)
and asserts the demo Definition of Done:

  1. The attack chain correlates into exactly two incidents:
       Incident #1 = evt-0041..evt-0044 (Reconnaissance + Brute Force)
       Incident #2 = evt-0045..evt-0050 (Exfiltration + Persistence)
  2. Both incidents score >= 80 (CRITICAL band) and top the queue.
  3. The whole 50-event ingest completes in < 30 seconds.

Run from the repository root:

    venv\\Scripts\\python.exe scripts\\verify_demo_scenario.py

Exits 0 on success, 1 on any failed check.
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Bind a throwaway database BEFORE importing backend modules: the database
# layer reads DATABASE_URL at import time, and load_dotenv() does not
# override variables that are already set.
_TMP_DIR = tempfile.mkdtemp(prefix="threatiq_demo_verify_")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_TMP_DIR, 'verify.db').as_posix()}"

from backend.correlation.correlator import EventCorrelator  # noqa: E402
from backend.database.db import IncidentModel, SessionLocal, init_db  # noqa: E402
from backend.detection.anomaly_detector import AnomalyDetector  # noqa: E402
from backend.pipeline import ThreatPipeline  # noqa: E402
from backend.scoring.risk_scorer import RiskScorer  # noqa: E402

DEMO_EVENTS_PATH = (
    PROJECT_ROOT / "backend" / "demo_data" / "demo_events.json"
)

EXPECTED_INCIDENT_1 = {"evt-0041", "evt-0042", "evt-0043", "evt-0044"}
EXPECTED_INCIDENT_2 = {
    "evt-0045", "evt-0046", "evt-0047", "evt-0048", "evt-0049", "evt-0050",
}
MIN_ATTACK_SCORE = 80
MAX_INGEST_SECONDS = 30.0


def main() -> int:
    raw_events = json.loads(DEMO_EVENTS_PATH.read_text(encoding="utf-8"))

    init_db()
    db = SessionLocal()
    try:
        pipeline = ThreatPipeline(
            detector=AnomalyDetector(),
            correlator=EventCorrelator(),
            scorer=RiskScorer(),
            rag_retriever=None,
            explainer=None,  # rule-based fallback keeps the check offline
            db=db,
        )

        start = time.perf_counter()
        pipeline.process(raw_events)
        elapsed = time.perf_counter() - start

        # Snapshot plain dicts while the session is open; ORM relationships
        # lazy-load, so nothing may be accessed after db.close().
        incidents = [
            {
                "id": inc.id,
                "total_score": inc.total_score,
                "severity_label": inc.severity_label,
                "asset": inc.asset,
                "mitre_technique": inc.mitre_technique,
                "event_ids": {
                    json.loads(e.raw_data).get("event_id")
                    for e in inc.events
                },
            }
            for inc in db.query(IncidentModel).all()
        ]
    finally:
        db.close()

    def find_incident(event_id: str):
        return next(
            (i for i in incidents if event_id in i["event_ids"]), None
        )

    incident_1 = find_incident("evt-0041")
    incident_2 = find_incident("evt-0045")

    failures = []

    def check(label: str, ok: bool, detail: str) -> None:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {detail}")
        if not ok:
            failures.append(label)

    print("Operation Shadow DB - demo scenario verification")
    print("-" * 60)

    check(
        "Ingest time < 30s",
        elapsed < MAX_INGEST_SECONDS,
        f"{len(raw_events)} events -> {len(incidents)} incidents in "
        f"{elapsed:.1f}s",
    )

    if incident_1 is None or incident_2 is None:
        check("Attack incidents exist", False, "attack chain incident(s) missing")
    else:
        check(
            "Incident #1 grouping (Recon + Brute Force)",
            incident_1["event_ids"] == EXPECTED_INCIDENT_1,
            f"events={sorted(incident_1['event_ids'])}",
        )
        check(
            "Incident #2 grouping (Exfiltration + Persistence)",
            incident_2["event_ids"] == EXPECTED_INCIDENT_2,
            f"events={sorted(incident_2['event_ids'])}",
        )
        check(
            "Incident #1 score >= 80 (critical)",
            incident_1["total_score"] >= MIN_ATTACK_SCORE
            and incident_1["severity_label"] == "critical",
            f"score={incident_1['total_score']} "
            f"label={incident_1['severity_label']} "
            f"asset={incident_1['asset']} "
            f"mitre={incident_1['mitre_technique']}",
        )
        check(
            "Incident #2 score >= 80 (critical)",
            incident_2["total_score"] >= MIN_ATTACK_SCORE
            and incident_2["severity_label"] == "critical",
            f"score={incident_2['total_score']} "
            f"label={incident_2['severity_label']} "
            f"asset={incident_2['asset']} "
            f"mitre={incident_2['mitre_technique']}",
        )

        top_two = sorted(
            incidents, key=lambda i: i["total_score"], reverse=True
        )[:2]
        check(
            "Both incidents top the threat queue",
            {i["id"] for i in top_two}
            == {incident_1["id"], incident_2["id"]},
            "top scores: "
            + ", ".join(
                f"{i['asset']}={i['total_score']}" for i in top_two
            ),
        )

    print("-" * 60)
    if failures:
        print(f"FAILED: {len(failures)} check(s) failed: {failures}")
        return 1
    print("ALL CHECKS PASSED - demo scenario is ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
