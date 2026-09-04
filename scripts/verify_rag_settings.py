import json
import sys
from unittest import mock

from backend.rag.knowledge_base import KnowledgeBase
from backend.rag.rag_retriever import RAGRetriever

kb = KnowledgeBase()
print("get_stats:", json.dumps(kb.get_stats()))

retriever = RAGRetriever(kb)
incident = {
    "asset": "db-server-01",
    "severity": "high",
    "mitre_technique": "T1190",
    "events": [{"event_type": "exploit", "details": "SQL injection attempt"}],
}

# Stub settings via load_settings
from backend.models_config import pipeline_settings

class FakeSettings:
    rag_top_k = 3
    rag_similarity_cutoff = 0.0

def fake_load(cutoff=0.0, top_k=3):
    s = FakeSettings()
    s.rag_top_k = top_k
    s.rag_similarity_cutoff = cutoff
    return s

with mock.patch.object(pipeline_settings, "load_settings", lambda: fake_load(0.0)):
    # patch the name imported into rag_retriever module
    import backend.rag.rag_retriever as rr
    with mock.patch.object(rr, "load_settings", lambda: fake_load(0.0)):
        r0 = rr.RAGRetriever(kb).retrieve(incident)
        print("cutoff=0.0 count:", len(r0))
    with mock.patch.object(rr, "load_settings", lambda: fake_load(0.9)):
        r1 = rr.RAGRetriever(kb).retrieve(incident)
        print("cutoff=0.9 count:", len(r1))
        print("cutoff=0.9 sample:", json.dumps(r1[0])[:200])
