"""RAG retriever for ThreatIQ incident threat-intelligence lookup.

Builds a semantic query from an incident payload and searches both the
MITRE ATT&CK and CVE knowledge-base collections, returning grounded
RAGResult entries only (no fabricated content).
"""

from typing import Any, Dict, List, Optional, TypedDict

from backend.models_config.pipeline_settings import load_settings
from backend.rag.knowledge_base import KnowledgeBase


class RAGResult(TypedDict):
    """One retrieved threat-intelligence document."""

    content: str
    source: str
    technique_id: Optional[str]
    cve_id: Optional[str]
    relevance_score: float


NO_RESULT_FALLBACK: RAGResult = {
    "content": "No specific threat intelligence retrieved.",
    "source": "system",
    "technique_id": None,
    "cve_id": None,
    "relevance_score": 0.0,
}


class RAGRetriever:
    """Retrieves relevant threat intelligence for a given incident."""

    def __init__(self, knowledge_base: KnowledgeBase) -> None:
        """Store the KnowledgeBase used for all similarity searches."""
        self.knowledge_base = knowledge_base

    def retrieve(
        self,
        incident_dict: Dict[str, Any],
        top_k: Optional[int] = None,
    ) -> List[RAGResult]:
        """Search both collections for documents relevant to the incident.

        Retrieval parameters (``rag_top_k``, ``rag_similarity_cutoff``) are
        read from the persisted PipelineSettings; ``top_k`` may be passed
        explicitly to override the configured value. Results whose
        relevance_score falls below the configured cutoff are dropped
        (no filtering when the cutoff is 0.0).

        Args:
            incident_dict: incident payload (asset, severity, mitre_technique,
                events with event_type/details, etc.).
            top_k: optional override for the configured rag_top_k.

        Returns:
            RAGResult entries sorted by relevance (best first), or a single
            fallback entry when nothing is retrieved or filtering removes
            all results.
        """
        settings = load_settings()
        if top_k is None:
            top_k = settings.rag_top_k
        similarity_cutoff = settings.rag_similarity_cutoff

        query = self._build_query(incident_dict)
        query_vector = self.knowledge_base.embeddings.embed_query(query)

        results: List[RAGResult] = []
        results.extend(
            self._search(
                self.knowledge_base.mitre_collection,
                query_vector,
                top_k,
                KnowledgeBase.MITRE_COLLECTION,
            )
        )
        results.extend(
            self._search(
                self.knowledge_base.cve_collection,
                query_vector,
                top_k,
                KnowledgeBase.CVE_COLLECTION,
            )
        )

        if similarity_cutoff > 0.0:
            results = [
                r
                for r in results
                if r["relevance_score"] >= similarity_cutoff
            ]

        results.sort(key=lambda r: r["relevance_score"], reverse=True)
        if len(results) < 1:
            return [dict(NO_RESULT_FALLBACK)]
        return results

    # ------------------------------------------------------------------ #
    # Query construction and search helpers
    # ------------------------------------------------------------------ #

    def _build_query(self, incident_dict: Dict[str, Any]) -> str:
        """Compose a natural-language query string from incident fields."""
        parts: List[str] = []
        severity = incident_dict.get("severity")
        if severity:
            parts.append(f"Severity: {severity}.")
        mitre_technique = incident_dict.get("mitre_technique")
        if mitre_technique:
            parts.append(f"MITRE ATT&CK technique: {mitre_technique}.")
        asset = incident_dict.get("asset")
        criticality = incident_dict.get("asset_criticality")
        if asset:
            label = f"Targeted asset: {asset}"
            if criticality:
                label += f" ({criticality} criticality)"
            parts.append(label + ".")
        for event in incident_dict.get("events") or []:
            if not isinstance(event, dict):
                continue
            event_type = event.get("event_type")
            details = event.get("details")
            if event_type:
                parts.append(f"Event type: {event_type}.")
            if details:
                parts.append(str(details))
        return " ".join(parts) or "security incident"

    def _search(
        self,
        collection: Any,
        query_vector: List[float],
        top_k: int,
        source: str,
    ) -> List[RAGResult]:
        """Query one collection and map raw hits to RAGResult entries."""
        if collection.count() == 0:
            return []
        response = collection.query(
            query_embeddings=[query_vector],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        documents = (response.get("documents") or [[]])[0]
        metadatas = (response.get("metadatas") or [[]])[0]
        distances = (response.get("distances") or [[]])[0]

        results: List[RAGResult] = []
        for document, metadata, distance in zip(documents, metadatas, distances):
            if not document:
                continue
            metadata = metadata or {}
            results.append(
                RAGResult(
                    content=document,
                    source=str(metadata.get("source") or source),
                    technique_id=metadata.get("technique_id"),
                    cve_id=metadata.get("cve_id"),
                    relevance_score=self._distance_to_score(distance),
                )
            )
        return results

    def _distance_to_score(self, distance: Any) -> float:
        """Convert a Chroma cosine distance to a [0.0, 1.0] relevance score."""
        try:
            score = 1.0 - float(distance)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, score))
