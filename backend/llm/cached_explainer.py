"""Caching wrapper for the ThreatIQ LLM explainer (Phase 20 demo support).

``CachedExplainer`` wraps a real ``ThreatExplainer`` and serves
pre-generated explanations from a JSON cache
(``backend/demo_data/demo_explanations.json``) when the incident matches a
cached fingerprint. This keeps the "Operation Shadow DB" demo fast and
deterministic: the two attack incidents get their Gemini explanations
instantly at ingest time, with no live API call, while any non-demo
incident still flows through to the wrapped live explainer.

The cache is keyed by a stable incident fingerprint (asset, criticality,
event count, and sorted event types), not by the random incident UUID, so
it survives database resets and re-ingestion of the demo dataset.

Opt-in wiring (one line in backend/main.py lifespan, left to the operator
per the immutable-legacy policy)::

    from backend.llm.cached_explainer import CachedExplainer
    app.state.explainer = CachedExplainer(ThreatExplainer())

Generate the cache with::

    venv\\Scripts\\python.exe scripts\\pregenerate_demo_explanations.py
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from backend.llm.explainer import ExplanationResult

if TYPE_CHECKING:
    from backend.llm.explainer import ThreatExplainer
    from backend.rag.rag_retriever import RAGResult

logger = logging.getLogger(__name__)

DEFAULT_CACHE_PATH = (
    Path(__file__).resolve().parents[1]
    / "demo_data"
    / "demo_explanations.json"
)


def incident_fingerprint(incident_dict: Dict[str, Any]) -> str:
    """Return a stable fingerprint for an incident dict.

    Composed of the fields that characterize the demo incidents: primary
    asset, asset criticality, event count, and the sorted set of event
    types. Random incident IDs and timestamps are deliberately excluded so
    the fingerprint is identical on every re-ingest of the demo dataset.
    """
    events = incident_dict.get("events") or []
    event_types = sorted(
        {str(e.get("event_type") or "unknown") for e in events if isinstance(e, dict)}
    )
    return "|".join(
        [
            str(incident_dict.get("asset") or "unknown"),
            str(incident_dict.get("asset_criticality") or "low"),
            str(len(events)),
            ",".join(event_types),
        ]
    )


class CachedExplainer:
    """Drop-in ``ThreatExplainer`` replacement with a JSON read-through cache.

    Implements the same ``explain(incident_dict, score_factors_dict,
    rag_results_list)`` contract, so the pipeline needs no changes.
    """

    def __init__(
        self,
        delegate: "ThreatExplainer",
        cache_path: Optional[Path] = None,
    ) -> None:
        self.delegate = delegate
        self.cache_path = Path(cache_path) if cache_path else DEFAULT_CACHE_PATH
        self._cache: Dict[str, Dict[str, Any]] = {}
        if self.cache_path.exists():
            try:
                payload = json.loads(
                    self.cache_path.read_text(encoding="utf-8")
                )
                self._cache = payload.get("explanations", {})
                logger.info(
                    "Loaded %d cached demo explanation(s) from %s.",
                    len(self._cache),
                    self.cache_path,
                )
            except (OSError, json.JSONDecodeError):
                logger.exception(
                    "Demo explanation cache %s is unreadable; ignoring it.",
                    self.cache_path,
                )

    def explain(
        self,
        incident_dict: Dict[str, Any],
        score_factors_dict: Dict[str, Any],
        rag_results_list: List["RAGResult"],
    ) -> ExplanationResult:
        """Return the cached explanation on a fingerprint hit, else delegate."""
        fingerprint = incident_fingerprint(incident_dict)
        cached = self._cache.get(fingerprint)
        if cached is not None:
            logger.info(
                "Demo explanation cache hit for %s (no LLM call).", fingerprint
            )
            result = ExplanationResult.model_validate(cached)
            result.confidence_reason += (
                " Served from the pre-generated demo explanation cache."
            )
            return result
        return self.delegate.explain(
            incident_dict, score_factors_dict, rag_results_list
        )
