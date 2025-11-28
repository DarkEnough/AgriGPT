import json
import os
from typing import List, Dict
import unicodedata
import re

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/subsidies.json")
VECTOR_DB_PATH = os.path.join(os.path.dirname(__file__), "../data/faiss_index")

# -------------------------------
# Query cleaning (FAISS-safe)
# -------------------------------
def _clean_query(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\x00-\x1f\x7f]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


class RAG:
    """
    RAG singleton for subsidy retrieval.
    - OpenAPI-safe (returns plain dicts only)
    - FAISS-backed
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RAG, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        # ✅ Slightly stronger embeddings (better semantic recall)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L12-v2"
        )

        self.vector_store = None

        # ---------------------------------------------------
        # Attempt to load existing FAISS index
        # ---------------------------------------------------
        if os.path.exists(VECTOR_DB_PATH):
            try:
                print("[RAG] Loading existing FAISS index...")
                self.vector_store = FAISS.load_local(
                    VECTOR_DB_PATH,
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                )
                print("[RAG] FAISS index loaded.")
                return
            except Exception as e:
                print(f"[RAG] Failed to load FAISS index: {e}")
                print("[RAG] Rebuilding index...")
                try:
                    import shutil
                    shutil.rmtree(VECTOR_DB_PATH)
                except Exception:
                    pass

        # ---------------------------------------------------
        # Build FAISS index from subsidies.json
        # ---------------------------------------------------
        if not os.path.exists(DATA_PATH):
            print(f"[RAG] subsidies.json not found at: {DATA_PATH}")
            return

        with open(DATA_PATH, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        documents: List[Document] = []

        for item in raw_data:
            scheme_name = item.get("scheme_name", "Unknown Scheme")
            eligibility = item.get("eligibility", "Not Provided")
            benefits = item.get("benefits", "Not Provided")
            notes = item.get("notes", "")

            content = (
                f"Scheme: {scheme_name}\n"
                f"Eligibility: {eligibility}\n"
                f"Benefits: {benefits}\n"
                f"Notes: {notes}\n"
            )

            documents.append(Document(page_content=content, metadata=item))

        print("[RAG] Building FAISS index...")
        self.vector_store = FAISS.from_documents(documents, self.embeddings)
        self.vector_store.save_local(VECTOR_DB_PATH)
        print("[RAG] FAISS index built and saved.")

    # ---------------------------------------------------
    # Retrieval (OpenAPI-safe)
    # ---------------------------------------------------
    def retrieve(self, query: str, k: int = 2) -> List[Dict[str, str]]:
        """
        ✅ Returns plain dicts only.
        ✅ Applies similarity score threshold.
        """
        if not query or not query.strip():
            return []

        # ✅ Context-boosting for subsidy domain
        query_clean = _clean_query(query.strip() + " india agriculture subsidy")

        if not self.vector_store:
            print("[RAG] Vector store not loaded.")
            return []

        try:
            docs_with_scores = self.vector_store.similarity_search_with_score(
                query_clean, k=k
            )
        except Exception as e:
            print(f"[RAG] Retrieval error: {e}")
            return []

        results: List[Dict[str, str]] = []

        for doc, score in docs_with_scores:
            # ✅ Distance threshold (tunable, conservative)
            if score > 0.7:
                continue

            meta = doc.metadata if isinstance(doc.metadata, dict) else {}

            results.append({
                "scheme_name": str(meta.get("scheme_name", "Unknown Scheme")),
                "eligibility": str(meta.get("eligibility", "Not Provided")),
                "benefits": str(meta.get("benefits", "Not Provided")),
                "application_steps": str(meta.get("application_steps", "")),
                "documents": str(meta.get("documents", "")),
                "notes": str(meta.get("notes", "")),
            })

        return results


# ✅ Singleton instance
rag_service = RAG()
