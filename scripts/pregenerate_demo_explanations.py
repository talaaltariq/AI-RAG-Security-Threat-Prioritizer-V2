"""Pre-generate and cache LLM explanations for the demo scenario (Phase 20).

Runs the full ThreatPipeline on the "Operation Shadow DB" attack-chain
events (evt-0041..evt-0050) with the live Gemini explainer, records the
two resulting explanations keyed by stable incident fingerprint, and
writes them to backend/demo_data/demo_explanations.json.

At demo time, wrapping the explainer with ``CachedExplainer`` (see
backend/llm/cached_explainer.py) serves these explanations instantly,
so POST /api/ingest/demo stays well under the 30-second budget even if
the LLM API is slow or unreachable.

Prerequisites:
  - GEMINI_API_KEY (or GOOGLE_API_KEY) set in backend/.env
  - Optional: the RAG knowledge base for grounded citations; if it fails
    to load the script continues without RAG context (same as main.py).

Run from the repository root:

    venv\\Scripts\\python.exe scripts\\pregenerate_demo_explanations.py
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Throwaway database, bound before importing backend modules (the database
# layer reads DATABASE_URL at import time).
_TMP_DIR = tempfile.mkdtemp(prefix="threatiq_demo_pregen_")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_TMP_DIR, 'pregen.db').as_posix()}"

from dotenv import load_dotenv  # noqa: E402

load_dotenv(PROJECT_ROOT / "backend" / ".env")

from backend.correlation.correlator import EventCorrelator  # noqa: E402
from backend.database.db import SessionLocal, init_db  # noqa: E402
from backend.detection.anomaly_detector import AnomalyDetector  # noqa: E402
from backend.llm.cached_explainer import (  # noqa: E402
    DEFAULT_CACHE_PATH,
    incident_fingerprint,
)
from backend.llm.explainer import ThreatExplainer  # noqa: E402
from backend.pipeline import ThreatPipeline  # noqa: E402
from backend.scoring.risk_scorer import RiskScorer  # noqa: E402

DEMO_EVENTS_PATH = PROJECT_ROOT / "backend" / "demo_data" / "demo_events.json"
DATA_DIR = PROJECT_ROOT / "backend" / "data"
ATTACK_EVENT_IDS = {f"evt-{n:04d}" for n in range(41, 51)}  # evt-0041..evt-0050

# Demo-script citation contract (DEMO_SCENARIO.md): Incident #1 must cite
# T1110.001 and mention credential stuffing; Incident #2 must cite T1041
# and T1059.001. LLM phrasing is non-deterministic, so generation retries
# until every marker is present (or MAX_ATTEMPTS is reached; the attempt
# with the most markers wins).
REQUIRED_MARKERS = {
    "auth_brute_force": ("t1110.001", "credential stuffing"),  # incident #1
    "data_exfiltration": ("t1041", "t1059.001"),  # incident #2
}
MAX_ATTEMPTS = 5


class RecordingExplainer:
    """Delegate wrapper that records every explanation by fingerprint."""

    def __init__(self, delegate: ThreatExplainer) -> None:
        self.delegate = delegate
        self.recorded = {}

    def explain(self, incident_dict, score_factors_dict, rag_results_list):
        result = self.delegate.explain(
            incident_dict, score_factors_dict, rag_results_list
        )
        fingerprint = incident_fingerprint(incident_dict)
        self.recorded[fingerprint] = result.model_dump()
        print(
            f"  recorded explanation for {fingerprint} "
            f"(confidence={result.confidence}, error={result.error})"
        )
        return result


def build_rag_retriever():
    """Load the ChromaDB knowledge base; return None on any failure."""
    try:
        from backend.rag.knowledge_base import KnowledgeBase
        from backend.rag.rag_retriever import RAGRetriever

        knowledge_base = KnowledgeBase()
        knowledge_base.load_mitre_attack(str(DATA_DIR / "mitre_attack.json"))
        knowledge_base.load_cve_summaries(str(DATA_DIR / "cve_summaries.json"))
        return RAGRetriever(knowledge_base)
    except Exception:  # noqa: BLE001 - RAG is optional context
        print("  WARNING: knowledge base unavailable; continuing without RAG.")
        return None


def marker_score(explanations: dict) -> int:
    """Count how many required citation markers the explanations contain."""
    score = 0
    for fingerprint, explanation in explanations.items():
        blob = json.dumps(explanation).lower()
        for fragment, markers in REQUIRED_MARKERS.items():
            if fragment in fingerprint:
                score += sum(1 for m in markers if m in blob)
    return score


def run_generation_attempt(
    attack_events: list, rag_retriever, db: SessionLocal
) -> dict:
    """Run the pipeline once over the attack events; return recorded results."""
    recorder = RecordingExplainer(ThreatExplainer())
    pipeline = ThreatPipeline(
        detector=AnomalyDetector(),
        correlator=EventCorrelator(),
        scorer=RiskScorer(),
        rag_retriever=rag_retriever,
        explainer=recorder,
        db=db,
    )
    pipeline.process(attack_events)
    db.rollback()  # throwaway DB; persisted rows are irrelevant
    return recorder.recorded


def main() -> int:
    raw_events = json.loads(DEMO_EVENTS_PATH.read_text(encoding="utf-8"))
    attack_events = [
        e for e in raw_events if str(e.get("event_id", "")) in ATTACK_EVENT_IDS
    ]
    if len(attack_events) != 10:
        print(f"ERROR: expected 10 attack events, found {len(attack_events)}")
        return 1

    print("Pre-generating demo explanations (live LLM calls)...")
    init_db()
    db = SessionLocal()
    try:
        rag_retriever = build_rag_retriever()
        best: dict = {}
        best_score = -1
        target_score = sum(len(m) for m in REQUIRED_MARKERS.values())
        for attempt in range(1, MAX_ATTEMPTS + 1):
            print(f"Attempt {attempt}/{MAX_ATTEMPTS}:")
            recorded = run_generation_attempt(attack_events, rag_retriever, db)
            score = marker_score(recorded)
            print(f"  citation markers: {score}/{target_score}")
            if score > best_score:
                best, best_score = recorded, score
            if score == target_score:
                break
    finally:
        db.close()

    if len(best) != 2:
        print(
            f"ERROR: expected 2 recorded explanations, got {len(best)}"
        )
        return 1
    if best_score < target_score:
        print(
            f"WARNING: citation contract incomplete ({best_score}/"
            f"{target_score} markers); keeping the best attempt."
        )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": os.getenv("LLM_MODEL", "gemini-3.6-flash"),
        "explanations": best,
    }
    DEFAULT_CACHE_PATH.write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(best)} explanations -> {DEFAULT_CACHE_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
