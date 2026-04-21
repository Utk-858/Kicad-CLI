# fluxdiff/rag/embedding/vector_store.py

import os
import pickle
import faiss
import numpy as np
from typing import List

from fluxdiff.rag.schemas import RAGDocument
from fluxdiff.rag.config import RAG_CONFIG


class VectorStore:
    def __init__(self):
        self.db_path = RAG_CONFIG["vector_db_path"]
        self.index = None
        self.documents: List[RAGDocument] = []

        os.makedirs(self.db_path, exist_ok=True)

        self.index_file = os.path.join(self.db_path, "faiss.index")
        self.doc_file = os.path.join(self.db_path, "documents.pkl")

        self._load()

    # -----------------------------
    # Initialize FAISS index
    # -----------------------------
    def _init_index(self, dim: int):
        self.index = faiss.IndexFlatL2(dim)

    # -----------------------------
    # Add documents
    # -----------------------------
    def add_documents(
        self,
        documents: List[RAGDocument],
        embeddings: List[List[float]]
    ):
        if not embeddings:
            return

        vectors = np.array(embeddings).astype("float32")

        if self.index is None:
            self._init_index(vectors.shape[1])

        self.index.add(vectors)
        self.documents.extend(documents)

    # -----------------------------
    # Similarity search
    # -----------------------------
    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = None
    ) -> List[RAGDocument]:

        if self.index is None or len(self.documents) == 0:
            return []

        top_k = top_k or RAG_CONFIG["top_k"]

        query_vector = np.array([query_embedding]).astype("float32")

        distances, indices = self.index.search(query_vector, top_k)

        results = []
        for idx in indices[0]:
            if idx < len(self.documents):
                results.append(self.documents[idx])

        return results

    # -----------------------------
    # Save DB
    # -----------------------------
    def save(self):
        if self.index:
            faiss.write_index(self.index, self.index_file)

        with open(self.doc_file, "wb") as f:
            pickle.dump(self.documents, f)

    # -----------------------------
    # Load DB
    # -----------------------------
    def _load(self):
        if os.path.exists(self.index_file):
            self.index = faiss.read_index(self.index_file)

        if os.path.exists(self.doc_file):
            with open(self.doc_file, "rb") as f:
                self.documents = pickle.load(f)