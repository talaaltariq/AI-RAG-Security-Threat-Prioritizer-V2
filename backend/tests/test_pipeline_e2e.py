"""Script-style end-to-end test for the Phase 17 integrated pipeline.

Runs POST /api/ingest/demo through the full ThreatPipeline with the real
knowledge base and LLM explainer (no stubbing), against a temporary
SQLite database. Validates the Phase 17 Definition of Done:

- POST /api/ingest/demo processes all 50 events without crashing
- At least 2 incidents are created (correlation works)
- At least 1 incident scores 80+
- LLM explanations are stored for high-score incidents
- RAG results are populated for all incidents

Run from the repository root::

    venv/Scripts/python backend/test_pipeline_e2e.py
"""

import os
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Isolate the test database before any backend.database import.
_TMP_DB = Path(tempfile.mkdtemp()) / "test_threatiq_e2e.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB}"

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

CHECKS = []


def check(name: str, condition: bool) -> None:
    CHECKS.append((name, condition))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}")


def main() -> int:
    with TestClient(app) as client:
        pipeline = getattr(app.state, "pipeline", None)
        check("app.state.pipeline initialized", pipeline is not None)
        check(
            "pipeline has detector/rag/explainer wired",
            pipeline is not None
            and pipeline.detector is not None
            and pipeline.rag_retriever is not None
            and pipeline.explainer is not None,
        )

        # 1. Run the full demo ingestion through the pipeline.
        resp = client.post("/api/ingest/demo", timeout=1800)
        check("POST /api/ingest/demo -> 201", resp.status_code == 201)
        if resp.status_code != 201:
            print(resp.text)
            return 1
        body = resp.json()
        check("50 events received", body.get("events_received") == 50)
        check("no persistence failures", body.get("incidents_failed") == 0)
        created = body.get("incidents_created") or 0
        check("at least 2 incidents created", created >= 2)
        check(
            "incident_ids match incidents_created",
            len(body.get("incident_ids") or []) == created,
        )
        print(f"       -> {created} incidents from 50 events "
              f"({(1 - created / 50) * 100:.0f}% alert reduction)")

        # 2. Incident queue: scoring and severity bands.
        resp = client.get("/api/incidents")
        check("GET /api/incidents -> 200", resp.status_code == 200)
        incidents = resp.json()
        check("incident list matches created count", len(incidents) == created)
        scores = [i["total_score"] for i in incidents]
        check("sorted by total_score DESC", scores == sorted(scores, reverse=True))
        high_scorers = [i for i in incidents if i["total_score"] >= 80]
        check("at least 1 incident scores >= 80", len(high_scorers) >= 1)
        for inc in incidents[:3]:
            print(
                f"       top: {inc['id'][:8]} score={inc['total_score']} "
                f"label={inc['severity_label']} asset={inc['asset']} "
                f"events={inc['events_count']} mitre={inc['mitre_technique']}"
            )

        # 3. Detail checks: RAG populated for all; LLM for high scores.
        all_rag_populated = True
        llm_ok = True
        for inc in incidents:
            detail = client.get(f"/api/incidents/{inc['id']}").json()
            if not detail.get("rag_results"):
                all_rag_populated = False
                print(f"       incident {inc['id'][:8]} has NO rag_results")
            explanation = detail.get("llm_explanation")
            if inc["total_score"] >= 60:
                populated = bool(
                    explanation
                    and explanation.get("observed_evidence")
                    and explanation.get("retrieved_context")
                    and explanation.get("ai_interpretation")
                    and explanation.get("recommended_action")
                )
                if not populated:
                    llm_ok = False
                    print(
                        f"       incident {inc['id'][:8]} score="
                        f"{inc['total_score']} missing LLM explanation"
                    )
                elif inc["total_score"] >= 80:
                    err = explanation.get("error")
                    print(
                        f"       80+ incident {inc['id'][:8]}: explanation "
                        f"confidence={explanation.get('confidence')} "
                        f"error={err or 'none'}"
                    )
        check("RAG results populated for all incidents", all_rag_populated)
        check("LLM explanations stored for score >= 60 incidents", llm_ok)

    failed = [name for name, ok in CHECKS if not ok]
    print(f"\n{len(CHECKS) - len(failed)}/{len(CHECKS)} checks passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
