"""ChromaDB-backed knowledge base for ThreatIQ threat intelligence.

Indexes MITRE ATT&CK techniques and CVE summaries into two persistent
collections (``mitre_attack`` and ``cve_summaries``) using Google
Generative AI embeddings. Loading is idempotent: a collection that
already contains documents is not re-embedded or re-stored.
"""

import json
import os
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional

import chromadb
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

_DEFAULT_PERSIST_DIR = (
    Path(__file__).resolve().parent.parent / "data" / "chroma_db"
)
_DEFAULT_EMBEDDING_MODEL = "models/gemini-embedding-001"


class KnowledgeBase:
    """Persistent vector store of MITRE ATT&CK and CVE documents."""

    MITRE_COLLECTION: ClassVar[str] = "mitre_attack"
    CVE_COLLECTION: ClassVar[str] = "cve_summaries"

    def __init__(self, persist_directory: Optional[str] = None) -> None:
        """Initialize the persistent ChromaDB client and embedding model.

        Args:
            persist_directory: storage path for ChromaDB; defaults to
                ``backend/data/chroma_db``.

        Raises:
            RuntimeError: if neither ``GEMINI_API_KEY`` nor
                ``GOOGLE_API_KEY`` is set.
        """
        load_dotenv()
        self.persist_directory = str(persist_directory or _DEFAULT_PERSIST_DIR)
        self.embedding_model = os.getenv(
            "EMBEDDING_MODEL", _DEFAULT_EMBEDDING_MODEL
        )
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Embedding API key missing: set GEMINI_API_KEY or "
                "GOOGLE_API_KEY in the environment or backend/.env"
            )
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=self.embedding_model,
            google_api_key=api_key,
        )
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.mitre_collection = self.client.get_or_create_collection(
            name=self.MITRE_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        self.cve_collection = self.client.get_or_create_collection(
            name=self.CVE_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )

    def load_mitre_attack(self, json_path: str) -> int:
        """Parse MITRE ATT&CK JSON and index one document per technique.

        Each document contains the technique id, name, tactic, description,
        and mitigations; the technique id and tactic are kept as metadata.

        Args:
            json_path: path to the MITRE ATT&CK technique JSON file.

        Returns:
            Number of documents indexed (0 if already loaded).
        """
        if self.mitre_collection.count() > 0:
            print(
                f"[KnowledgeBase] '{self.MITRE_COLLECTION}' already contains "
                f"{self.mitre_collection.count()} documents - skipping load."
            )
            return 0

        with open(json_path, "r", encoding="utf-8") as f:
            techniques = json.load(f)

        ids, documents, metadatas = [], [], []
        for technique in techniques:
            technique_id = str(technique.get("technique_id", "")).strip()
            if not technique_id:
                continue
            name = technique.get("name", "")
            tactic = technique.get("tactic", "")
            description = technique.get("description", "")
            mitigations = technique.get("mitigations") or []
            mitigation_text = (
                "; ".join(str(m) for m in mitigations)
                if isinstance(mitigations, list)
                else str(mitigations)
            )
            document = (
                f"{technique_id} - {name} ({tactic}). "
                f"{description} Mitigations: {mitigation_text}"
            )
            ids.append(technique_id)
            documents.append(document)
            metadatas.append(
                {
                    "source": self.MITRE_COLLECTION,
                    "technique_id": technique_id,
                    "name": name,
                    "tactic": tactic,
                }
            )

        count = self._embed_and_store(
            self.mitre_collection, ids, documents, metadatas
        )
        print(
            f"[KnowledgeBase] Indexed {count} MITRE ATT&CK techniques into "
            f"'{self.MITRE_COLLECTION}'."
        )
        return count

    def load_cve_summaries(self, json_path: str) -> int:
        """Parse CVE JSON and index one document per CVE.

        Each document contains the CVE id, description, affected software,
        and CVSS score; the id and score are kept as metadata.

        Args:
            json_path: path to the CVE summaries JSON file.

        Returns:
            Number of documents indexed (0 if already loaded).
        """
        if self.cve_collection.count() > 0:
            print(
                f"[KnowledgeBase] '{self.CVE_COLLECTION}' already contains "
                f"{self.cve_collection.count()} documents - skipping load."
            )
            return 0

        with open(json_path, "r", encoding="utf-8") as f:
            cves = json.load(f)

        ids, documents, metadatas = [], [], []
        for cve in cves:
            cve_id = str(cve.get("cve_id", "")).strip()
            if not cve_id:
                continue
            description = cve.get("description", "")
            affected = cve.get("affected_software", "")
            cvss_score = cve.get("cvss_score", 0.0)
            remediation = cve.get("remediation", "")
            document = (
                f"{cve_id} (CVSS {cvss_score}). {description} "
                f"Affected software: {affected}. Remediation: {remediation}"
            )
            ids.append(cve_id)
            documents.append(document)
            metadatas.append(
                {
                    "source": self.CVE_COLLECTION,
                    "cve_id": cve_id,
                    "affected_software": affected,
                    "cvss_score": float(cvss_score or 0.0),
                }
            )

        count = self._embed_and_store(
            self.cve_collection, ids, documents, metadatas
        )
        print(
            f"[KnowledgeBase] Indexed {count} CVE summaries into "
            f"'{self.CVE_COLLECTION}'."
        )
        return count

    # ------------------------------------------------------------------ #
    # Embedding helpers
    # ------------------------------------------------------------------ #

    def _embed_and_store(
        self,
        collection: Any,
        ids: List[str],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> int:
        """Embed documents with Google Generative AI and store in Chroma."""
        if not documents:
            return 0
        vectors = self.embeddings.embed_documents(documents)
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=vectors,
        )
        return len(documents)
