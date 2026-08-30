"""One-time setup script: build the ThreatIQ RAG knowledge base.

Indexes MITRE ATT&CK techniques and CVE summaries from ``backend/data``
into the persistent ChromaDB store at ``backend/data/chroma_db``.
Re-running is safe: collections that already contain documents are skipped.

Usage (from the repository root)::

    venv/Scripts/python scripts/build_knowledge_base.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(PROJECT_ROOT / "backend" / ".env")

from backend.rag.knowledge_base import KnowledgeBase  # noqa: E402

MITRE_JSON_PATH = PROJECT_ROOT / "backend" / "data" / "mitre_attack.json"
CVE_JSON_PATH = PROJECT_ROOT / "backend" / "data" / "cve_summaries.json"


def main() -> None:
    """Load both threat-intelligence sources into the knowledge base."""
    print("=" * 60)
    print("ThreatIQ knowledge base build")
    print("=" * 60)

    knowledge_base = KnowledgeBase()
    print(f"[build] Persistent store: {knowledge_base.persist_directory}")
    print(f"[build] Embedding model:  {knowledge_base.embedding_model}")

    print(f"[build] Loading MITRE ATT&CK techniques from {MITRE_JSON_PATH} ...")
    mitre_count = knowledge_base.load_mitre_attack(str(MITRE_JSON_PATH))

    print(f"[build] Loading CVE summaries from {CVE_JSON_PATH} ...")
    cve_count = knowledge_base.load_cve_summaries(str(CVE_JSON_PATH))

    mitre_total = knowledge_base.mitre_collection.count()
    cve_total = knowledge_base.cve_collection.count()
    print("-" * 60)
    print(f"[build] Newly indexed this run: {mitre_count + cve_count} "
          f"(MITRE: {mitre_count}, CVE: {cve_count})")
    print(f"[build] Total documents indexed: {mitre_total + cve_total} "
          f"(mitre_attack: {mitre_total}, cve_summaries: {cve_total})")
    print("[build] Done.")


if __name__ == "__main__":
    main()
