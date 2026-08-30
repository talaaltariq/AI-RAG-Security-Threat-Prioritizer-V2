import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.rag.knowledge_base import KnowledgeBase
from backend.rag.rag_retriever import RAGRetriever

def test_rag_knowledge_layer():
    kb = KnowledgeBase()
    retriever = RAGRetriever(kb)

    test_incident = {
        "event_type": "authentication_failure",
        "source_ip": "192.168.1.201",
        "mitre_technique": "credential_access"
    }

    results = retriever.retrieve(test_incident)
    print("Retrieved results count:", len(results))
    for i, res in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print("Source:", res.get("source"))
        print("Technique ID:", res.get("technique_id"))
        print("CVE ID:", res.get("cve_id"))
        print("Relevance Score:", res.get("relevance_score"))
        print("Content Preview:", res.get("content", "")[:200])

    assert len(results) > 0, "Expected at least one result from retrieval"
    print("\n[OK] RAG Knowledge Layer test passed!")

if __name__ == "__main__":
    test_rag_knowledge_layer()
