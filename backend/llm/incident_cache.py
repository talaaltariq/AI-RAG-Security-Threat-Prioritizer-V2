"""In-memory per-incident LLM response cache for ThreatIQ (Phase 22).

``IncidentCachedExplainer`` wraps any explainer with the standard
``explain(incident_dict, score_factors_dict, rag_results_list)`` contract
and caches successful ``ExplanationResult`` objects in a plain thread-safe
Python ``dict`` keyed by incident ID. When the same incident is explained
again — a re-ingest of the same dataset, or the background pre-generation
pass revisiting an incident the pipeline already explained — the cached
response is returned instantly with no delegate (LLM) call.

This is deliberately a simple in-process dict, not Redis: the demo runs a
single uvicorn worker, and the DB remains the durable store (explanations
are persisted to ``llm_explanations`` at ingest time). The dict only
removes redundant LLM calls within the lifetime of the process.

Failed explanations (``error`` set) are never cached, so a transient LLM
outage does not poison the cache.

Wiring (backend/main.py lifespan)::

    from backend.llm.cached_explainer import CachedExplainer
    from backend.llm.incident_cache import IncidentCachedExplainer

    app.state.explainer = IncidentCachedExplainer(
        CachedExplainer(ThreatExplainer())
    )
"""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING, Any, Dict, List

from backend.llm.explainer import ExplanationResult

if TYPE_CHECKING:
    from backend.llm.explainer import ThreatExplainer
    from backend.rag.rag_retriever import RAGResult

logger = logging.getLogger(__name__)


class IncidentCachedExplainer:
    """Drop-in explainer wrapper caching LLM responses per incident ID.

    Implements the same ``explain(incident_dict, score_factors_dict,
    rag_results_list)`` contract as ``ThreatExplainer``/``CachedExplainer``,
    so it can sit anywhere in the wrapper chain without pipeline changes.
    """

    def __init__(self, delegate: "ThreatExplainer") -> None:
        self.delegate = delegate
        self._cache: Dict[str, ExplanationResult] = {}
        self._lock = threading.Lock()

    def explain(
        self,
        incident_dict: Dict[str, Any],
        score_factors_dict: Dict[str, Any],
        rag_results_list: List["RAGResult"],
    ) -> ExplanationResult:
        """Return the cached explanation for this incident ID, else delegate.

        Successful delegate results (``error`` is None) are stored under the
        incident ID; failures pass through uncached so later calls can retry.
        """
        incident_id = str(
            incident_dict.get("id") or incident_dict.get("incident_id") or ""
        )
        if incident_id:
            with self._lock:
                cached = self._cache.get(incident_id)
            if cached is not None:
                logger.info(
                    "LLM response cache hit for incident %s (no delegate call).",
                    incident_id,
                )
                return cached

        result = self.delegate.explain(
            incident_dict, score_factors_dict, rag_results_list
        )

        if incident_id and result.error is None:
            with self._lock:
                self._cache[incident_id] = result
            logger.info("Cached LLM response for incident %s.", incident_id)
        return result

    # ------------------------------------------------------------------ #
    # Introspection helpers (used by the Phase 22 verification script)
    # ------------------------------------------------------------------ #

    def __len__(self) -> int:
        """Number of incident IDs currently cached."""
        with self._lock:
            return len(self._cache)

    def is_cached(self, incident_id: str) -> bool:
        """Return True when an explanation for the incident ID is cached."""
        with self._lock:
            return incident_id in self._cache
