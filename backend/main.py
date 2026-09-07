"""ThreatIQ FastAPI application entry point.

Wires every backend module into a single application: anomaly detection,
correlation, risk scoring, RAG retrieval, LLM explanation, and the
SQLAlchemy persistence layer.

Run from the repository root::

    uvicorn backend.main:app --reload

or from the ``backend/`` directory (the playbook convention)::

    cd backend
    uvicorn main:app --reload

All secrets (GEMINI_API_KEY / GOOGLE_API_KEY, DATABASE_URL, model names)
are loaded from environment variables via python-dotenv; nothing is
hard-coded.
"""

import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

# Allow both `uvicorn backend.main:app` (repo root) and `uvicorn main:app`
# (backend/ directory): the package modules import via `backend.*`.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parent / ".env")

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from backend.api import incidents, ingest, llm_config, reports, settings, stats, upload  # noqa: E402
from backend.correlation.correlator import EventCorrelator  # noqa: E402
from backend.database.db import init_db  # noqa: E402
from backend.detection.anomaly_detector import AnomalyDetector  # noqa: E402
from backend.detection.fast_detector import FastAnomalyDetector  # noqa: E402
from backend.llm.cached_explainer import CachedExplainer  # noqa: E402
from backend.llm.explainer import ThreatExplainer  # noqa: E402
from backend.llm.incident_cache import IncidentCachedExplainer  # noqa: E402
from backend.pipeline import ThreatPipeline  # noqa: E402
from backend.rag.knowledge_base import KnowledgeBase  # noqa: E402
from backend.rag.rag_retriever import RAGRetriever  # noqa: E402
from backend.scoring.risk_scorer import RiskScorer  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("threatiq")

_DATA_DIR = Path(__file__).resolve().parent / "data"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB tables, detector, knowledge base, and pipeline services."""
    logger.info("ThreatIQ startup: initializing database tables.")
    init_db()

    # Deterministic local services never fail.
    app.state.correlator = EventCorrelator()
    app.state.scorer = RiskScorer()

    logger.info("ThreatIQ startup: loading anomaly detector.")
    try:
        # Phase 22: compiled vectorized inference (<1 ms/event); falls back
        # to the plain sklearn path if forest compilation ever fails.
        app.state.detector = FastAnomalyDetector()
    except Exception:  # noqa: BLE001 - degrade gracefully, keep the API up
        logger.exception("Fast detector unavailable; using base detector.")
        try:
            app.state.detector = AnomalyDetector()
        except Exception:  # noqa: BLE001
            app.state.detector = None
            logger.exception("Anomaly detector failed to load; /api/ingest disabled.")

    logger.info("ThreatIQ startup: loading RAG knowledge base.")
    try:
        knowledge_base = KnowledgeBase(
            # Deployment: CHROMA_PERSIST_DIR relocates the vector store
            # (e.g. onto a mounted persistent disk); unset keeps the default
            # backend/data/chroma_db location.
            persist_directory=os.getenv("CHROMA_PERSIST_DIR") or None
        )
        knowledge_base.load_mitre_attack(str(_DATA_DIR / "mitre_attack.json"))
        knowledge_base.load_cve_summaries(str(_DATA_DIR / "cve_summaries.json"))
        app.state.rag_retriever = RAGRetriever(knowledge_base)
        logger.info(
            "Knowledge base ready (mitre_attack=%d, cve_summaries=%d documents).",
            knowledge_base.mitre_collection.count(),
            knowledge_base.cve_collection.count(),
        )
    except Exception:  # noqa: BLE001 - ingest continues without RAG context
        app.state.rag_retriever = None
        logger.exception("Knowledge base unavailable; RAG retrieval disabled.")

    logger.info("ThreatIQ startup: initializing LLM explainer.")
    try:
        # Wrapper chain (innermost first): live Gemini explainer -> Phase 20
        # JSON cache of pre-generated demo explanations -> Phase 22
        # in-memory per-incident-ID response cache.
        app.state.explainer = IncidentCachedExplainer(
            CachedExplainer(ThreatExplainer())
        )
    except Exception:  # noqa: BLE001 - ingest continues without explanations
        app.state.explainer = None
        logger.exception("LLM explainer unavailable; explanations disabled.")

    # Assemble the end-to-end pipeline from the components above. The
    # request-scoped DB session is bound per request via with_db().
    logger.info("ThreatIQ startup: assembling threat pipeline.")
    app.state.pipeline = ThreatPipeline(
        detector=app.state.detector,
        correlator=app.state.correlator,
        scorer=app.state.scorer,
        rag_retriever=app.state.rag_retriever,
        explainer=app.state.explainer,
    )

    logger.info("ThreatIQ startup complete.")
    yield
    logger.info("ThreatIQ shutdown.")


app = FastAPI(title="ThreatIQ", version="1.0.0", lifespan=lifespan)

# Deployment: allowed origins come from the CORS_ORIGINS environment
# variable as a comma-separated list (or "*" to allow every origin).
# Defaults to the local frontend so development behavior is unchanged.
_cors_raw = os.getenv("CORS_ORIGINS", "http://localhost:3000").strip()
_allow_all_origins = _cors_raw == "*"
_allow_origins = (
    ["*"]
    if _allow_all_origins
    else [origin.strip() for origin in _cors_raw.split(",") if origin.strip()]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?|https?://.*(\.ngrok-free\.app|\.ngrok-free\.dev|\.ngrok\.io|\.vercel\.app)(:\d+)?",
    # Wildcard "*" cannot be combined with credentials (browser rule).
    allow_credentials=not _allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every request method, path, status code, and duration."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %d (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


app.include_router(incidents.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(llm_config.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


@app.get("/health")
def health() -> dict:
    """Liveness probe."""
    return {"status": "ok", "version": "1.0.0"}
