"""Phase 22 performance & stability verification for ThreatIQ.

Verifies the Phase 22 Definition of Done, fully offline (no live LLM or
embedding API calls):

1. Anomaly detector is pre-trained and inference is < 1 ms per event.
2. ChromaDB local search over the knowledge base is < 500 ms.
3. The per-incident-ID in-memory LLM cache serves repeat explanations
   without a delegate call (and never caches failures).
4. POST /api/ingest/demo queues background pre-generation, and the
   pregen pass upgrades rule-based fallback explanations to LLM
   explanations persisted in the DB.
5. GET /api/incidents/{id} answers in < 2 s with the pre-cached
   explanation (what the incident detail page needs).

Run from the repository root::

    venv\\Scripts\\python.exe scripts\\verify_performance.py

Exits 0 when every check passes, 1 otherwise.
"""

import os
import sys
import tempfile
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Isolate the test database before any backend.database import.
_TMP_DB = Path(tempfile.mkdtemp()) / "perf_threatiq.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB}"

CHECKS = []


def check(name: str, condition: bool, detail: str = "") -> None:
    CHECKS.append((name, condition))
    suffix = f" — {detail}" if detail else ""
    print(f"[{'PASS' if condition else 'FAIL'}] {name}{suffix}")


def skip(name: str, reason: str) -> None:
    print(f"[SKIP] {name} — {reason}")


# ------------------------------------------------------------------ #
# 1. Anomaly detector: pre-trained, < 1 ms inference
# ------------------------------------------------------------------ #


def bench_anomaly_detector() -> None:
    import numpy as np

    from backend.detection.anomaly_detector import (
        DEFAULT_MODEL_PATH,
        AnomalyDetector,
    )
    from backend.detection.fast_detector import FastAnomalyDetector

    check("pre-trained IsolationForest model file exists", DEFAULT_MODEL_PATH.exists())
    detector = FastAnomalyDetector()
    check("detector loaded a trained model at startup", detector.model is not None)

    # The fast path must reproduce sklearn's decision_function exactly.
    reference = AnomalyDetector()
    rng = np.random.default_rng(7)
    probe = rng.normal(size=(200, 7))
    probe_features = probe * [6, 10, 5000, 20000, 10, 1, 2] + [
        12, 5, 10000, 10000, 5, 0.5, 3,
    ]
    ref_scores = reference.model.decision_function(probe_features)
    fast_scores = np.array(
        [detector._raw_decision_function(row.reshape(1, -1)) for row in probe_features]
    )
    max_diff = float(np.abs(fast_scores - ref_scores).max())
    check(
        "fast inference matches sklearn decision_function",
        max_diff < 1e-9,
        f"max abs diff {max_diff:.2e} over 200 probes",
    )

    event = {
        "timestamp": "2026-08-30T14:05:00",
        "source_ip": "192.168.1.201",
        "event_type": "authentication_failure",
        "failed_attempts": 25,
        "bytes_transferred": 5200,
        "port": 3306,
        "asset_criticality": "critical",
    }
    detector.detect(event)  # warmup
    iterations = 200
    start = time.perf_counter()
    for _ in range(iterations):
        detector.detect(event)
    avg_ms = (time.perf_counter() - start) / iterations * 1000
    check(
        "anomaly inference < 1 ms per event",
        avg_ms < 1.0,
        f"avg {avg_ms:.3f} ms over {iterations} runs",
    )


# ------------------------------------------------------------------ #
# 2. RAG: ChromaDB local search < 500 ms
# ------------------------------------------------------------------ #


def bench_rag_retrieval() -> None:
    try:
        from backend.rag.knowledge_base import KnowledgeBase
    except Exception as exc:  # noqa: BLE001 - offline runs may lack deps/key
        skip("ChromaDB local search benchmark", f"knowledge base unavailable: {exc}")
        return

    try:
        kb = KnowledgeBase()
    except Exception as exc:  # noqa: BLE001 - e.g. no embedding API key
        skip("ChromaDB local search benchmark", f"knowledge base unavailable: {exc}")
        return

    docs = kb.mitre_collection.count() + kb.cve_collection.count()
    check("knowledge base is populated", docs > 0, f"{docs} documents")
    if docs == 0:
        return

    # Benchmark the local similarity search with a real stored embedding,
    # so no network call (query embedding) is involved at all.
    sample = kb.mitre_collection.get(limit=1, include=["embeddings"])
    vector = sample["embeddings"][0]
    iterations = 5
    start = time.perf_counter()
    for _ in range(iterations):
        kb.mitre_collection.query(query_embeddings=[vector], n_results=3)
        kb.cve_collection.query(query_embeddings=[vector], n_results=3)
    avg_ms = (time.perf_counter() - start) / iterations * 1000
    check(
        "ChromaDB local search < 500 ms",
        avg_ms < 500.0,
        f"avg {avg_ms:.1f} ms over {docs} documents (both collections)",
    )


# ------------------------------------------------------------------ #
# 3. In-memory per-incident-ID LLM cache
# ------------------------------------------------------------------ #


class _StubExplainer:
    """Counts explain() calls; returns a fixed (optionally errored) result."""

    def __init__(self, error: str = None) -> None:
        self.calls = 0
        self.error = error

    def explain(self, incident_dict, score_factors_dict, rag_results_list):
        from backend.llm.explainer import ExplanationResult

        self.calls += 1
        return ExplanationResult(
            observed_evidence="stub evidence",
            retrieved_context="stub context",
            ai_interpretation="stub interpretation",
            recommended_action="stub action",
            confidence="high",
            confidence_reason="stubbed explainer",
            error=self.error,
        )


def check_incident_llm_cache() -> None:
    from backend.llm.incident_cache import IncidentCachedExplainer

    stub = _StubExplainer()
    cached = IncidentCachedExplainer(stub)
    incident = {"id": "inc-cache-test"}
    first = cached.explain(incident, {}, [])
    second = cached.explain(incident, {}, [])
    check(
        "repeat explanation for same incident ID served from dict cache",
        stub.calls == 1 and first is second,
        f"delegate calls: {stub.calls}",
    )

    failing = _StubExplainer(error="boom")
    cached_failing = IncidentCachedExplainer(failing)
    cached_failing.explain(incident, {}, [])
    cached_failing.explain(incident, {}, [])
    check(
        "failed explanations are never cached (retry stays possible)",
        failing.calls == 2,
        f"delegate calls: {failing.calls}",
    )


# ------------------------------------------------------------------ #
# 4-5. API: background pregen + incident detail latency
# ------------------------------------------------------------------ #


class _FakeLLMExplainer:
    """Deterministic stand-in for the live LLM (no external calls)."""

    MARKER = "PREGENERATED-LLM-EXPLANATION"

    def __init__(self) -> None:
        self.calls = 0

    def explain(self, incident_dict, score_factors_dict, rag_results_list):
        from backend.llm.explainer import ExplanationResult

        self.calls += 1
        return ExplanationResult(
            observed_evidence=f"{self.MARKER}: observed evidence",
            retrieved_context=f"{self.MARKER}: retrieved context",
            ai_interpretation=f"{self.MARKER}: interpretation",
            recommended_action=f"{self.MARKER}: action",
            confidence="high",
            confidence_reason="pre-generated by the Phase 22 background pass",
            error=None,
        )


def check_api_perf_and_pregen() -> None:
    from fastapi.testclient import TestClient

    from backend.api.pregen import RULE_BASED_MARKER, pregenerate_explanations
    from backend.llm.incident_cache import IncidentCachedExplainer
    from backend.main import app

    with TestClient(app) as client:
        # Keep the run fully offline: no RAG embedding calls, stubbed LLM.
        app.state.rag_retriever = None

        # --- Pass 1: ingest with NO explainer -> rule-based fallbacks.
        app.state.explainer = None
        start = time.perf_counter()
        resp = client.post("/api/ingest/demo")
        ingest_s = time.perf_counter() - start
        check("POST /api/ingest/demo -> 201", resp.status_code == 201)
        body = resp.json()
        check(
            "demo ingest creates 41 incidents and queues pregen for all of them",
            body.get("incidents_created") == 41
            and body.get("explanations_pregen_queued") == 41,
            f"created={body.get('incidents_created')}, "
            f"queued={body.get('explanations_pregen_queued')}",
        )
        check(
            "demo ingest (no LLM) completes in < 30 s",
            ingest_s < 30.0,
            f"{ingest_s:.1f} s",
        )

        incidents = client.get("/api/incidents").json()
        top_two = incidents[:2]
        check(
            "demo scenario intact: top-2 incidents are CRITICAL >= 80",
            len(incidents) == 41
            and all(i["severity_label"] == "critical" for i in top_two)
            and all(i["total_score"] >= 80 for i in top_two),
            f"scores: {[i['total_score'] for i in top_two]}",
        )
        high_plus = [i for i in incidents if i["total_score"] >= 60]

        detail = client.get(f"/api/incidents/{top_two[0]['id']}").json()
        explanation = detail.get("llm_explanation") or {}
        check(
            "fallback explanation marked rule-based when no LLM ran",
            RULE_BASED_MARKER in (explanation.get("confidence_reason") or ""),
        )

        # --- Pass 2: run the background pregen pass with a fake LLM.
        fake = _FakeLLMExplainer()
        app.state.explainer = fake
        stats = pregenerate_explanations(
            app, [i["id"] for i in incidents]
        )
        check(
            "pregen pass upgrades every HIGH+ incident and nothing else",
            stats["regenerated"] == len(high_plus) and stats["failed"] == 0,
            f"{stats} (HIGH+ incidents: {len(high_plus)})",
        )

        detail = client.get(f"/api/incidents/{top_two[0]['id']}").json()
        explanation = detail.get("llm_explanation") or {}
        check(
            "upgraded explanation persisted in DB (read back via API)",
            _FakeLLMExplainer.MARKER in (explanation.get("observed_evidence") or "")
            and explanation.get("confidence") == "high",
        )

        # Idempotency: a second pass regenerates nothing.
        stats2 = pregenerate_explanations(app, [i["id"] for i in incidents])
        check(
            "pregen pass is idempotent (second run regenerates nothing)",
            stats2["regenerated"] == 0
            and stats2["already_cached"] == len(high_plus),
            f"{stats2}",
        )

        # --- Incident detail latency with the pre-cached explanation.
        timings = []
        for _ in range(3):
            start = time.perf_counter()
            resp = client.get(f"/api/incidents/{top_two[0]['id']}")
            timings.append((time.perf_counter() - start) * 1000)
        check(
            "GET /api/incidents/{id} < 2000 ms (explanation pre-cached)",
            resp.status_code == 200 and max(timings) < 2000,
            f"max {max(timings):.1f} ms over 3 fetches",
        )

        # --- Pass 3: re-ingest through the full wrapper chain
        # (IncidentCachedExplainer) — the demo rehearsal flow must not crash.
        app.state.explainer = IncidentCachedExplainer(fake)
        resp = client.post("/api/ingest/demo")
        check(
            "repeat demo ingest (cache chain active) does not crash",
            resp.status_code == 201 and resp.json().get("incidents_created") == 41,
        )


def main() -> int:
    bench_anomaly_detector()
    bench_rag_retrieval()
    check_incident_llm_cache()
    check_api_perf_and_pregen()

    failed = [name for name, ok in CHECKS if not ok]
    print(f"\n{len(CHECKS) - len(failed)}/{len(CHECKS)} checks passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
