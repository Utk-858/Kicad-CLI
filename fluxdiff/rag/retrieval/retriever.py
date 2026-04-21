# fluxdiff/rag/retrieval/retriever.py

from typing import List

from fluxdiff.rag.embedding.embedder import Embedder
from fluxdiff.rag.embedding.vector_store import VectorStore
from fluxdiff.rag.schemas import RAGDocument, RetrievalResult, RAGQuery
from fluxdiff.rag.config import RAG_CONFIG


class Retriever:
    def __init__(self):
        self.embedder = Embedder()
        self.store = VectorStore()

    # -----------------------------
    # Main retrieve function
    # -----------------------------
    def retrieve(self, query: str) -> RetrievalResult:
        """
        Basic retrieval without filters.
        """

        # 1. Convert query → embedding
        query_embedding = self.embedder.embed_query(query)

        # 2. Search vector DB
        documents = self.store.similarity_search(
            query_embedding,
            top_k=RAG_CONFIG["top_k"]
        )

        return RetrievalResult(documents=documents)

    # -----------------------------
    # Advanced retrieval (with filters)
    # -----------------------------
    def retrieve_with_query(self, rag_query: RAGQuery) -> RetrievalResult:
        """
        Supports filtering (future ready).
        """

        query_embedding = self.embedder.embed_query(rag_query.query)

        documents = self.store.similarity_search(
            query_embedding,
            top_k=RAG_CONFIG["top_k"]
        )

        # Apply filters (if any)
        if rag_query.filters:
            documents = self._apply_filters(documents, rag_query.filters)

        return RetrievalResult(documents=documents)

    # -----------------------------
    # Direct Filter Lookup
    # -----------------------------
    def retrieve_by_type(self, doc_type: str) -> List[RAGDocument]:
        """
        Force-fetch documents of a specific type (e.g. project_structure).
        """
        return [d for d in self.store.documents if d.metadata.get("type") == doc_type]

    def retrieve_by_filename(self, filename: str) -> List[RAGDocument]:
        """
        Force-fetch documents by filename (e.g. README.md).
        """
        return [d for d in self.store.documents if d.metadata.get("file") == filename or d.metadata.get("filename") == filename]

    # -----------------------------
    # Filter logic
    # -----------------------------
    def _apply_filters(
        self,
        documents: List[RAGDocument],
        filters: dict
    ) -> List[RAGDocument]:

        filtered = documents

        # Filter by commit
        if "commit" in filters:
            filtered = [
                d for d in filtered
                if d.metadata.get("commit") == filters["commit"]
            ]

        # Filter by type (component/net/routing/summary)
        if "type" in filters:
            filtered = [
                d for d in filtered
                if d.metadata.get("type") == filters["type"]
            ]

        # Filter by file
        if "file" in filters:
            filtered = [
                d for d in filtered
                if d.metadata.get("file") == filters["file"]
            ]

        return filtered