import json
import os
from typing import List, Dict

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/subsidies.json")
VECTOR_DB_PATH = os.path.join(os.path.dirname(__file__), "../data/faiss_index")

class RAG:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RAG, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        """
        Load data, create/load FAISS index using LangChain.
        """
        self.vector_store = None
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        # 1. Try loading existing index
        if os.path.exists(VECTOR_DB_PATH):
            try:
                print("Loading existing FAISS index...")
                self.vector_store = FAISS.load_local(
                    VECTOR_DB_PATH, 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print("FAISS index loaded.")
                return
            except Exception as e:
                print(f"Failed to load index: {e}. Rebuilding...")

        # 2. Rebuild index from JSON
        if not os.path.exists(DATA_PATH):
            print(f"Warning: Subsidy data file not found at {DATA_PATH}")
            return

        with open(DATA_PATH, "r") as f:
            data = json.load(f)

        documents = []
        for item in data:
            # Combine relevant fields for embedding
            page_content = (
                f"Scheme: {item['scheme_name']}\n"
                f"Eligibility: {item['eligibility']}\n"
                f"Benefits: {item['benefits']}\n"
                f"Notes: {item['notes']}"
            )
            # Store structured data as metadata
            documents.append(Document(page_content=page_content, metadata=item))

        print("Building new FAISS index...")
        self.vector_store = FAISS.from_documents(documents, self.embeddings)
        
        # Save for future speedup
        self.vector_store.save_local(VECTOR_DB_PATH)
        print("FAISS index built and saved.")

    def retrieve(self, query: str, k: int = 2) -> List[Dict]:
        """
        Retrieve top_k relevant documents using FAISS.
        Returns a list of original metadata dictionaries.
        """
        if not self.vector_store:
            return []

        # Search
        docs = self.vector_store.similarity_search(query, k=k)
        
        # Return the metadata (original JSON structure)
        return [d.metadata for d in docs]

# Singleton access
rag_service = RAG()
