# fluxdiff/rag/embedding/embedder.py

from typing import List
from fluxdiff.rag.schemas import RAGDocument
from fluxdiff.rag.config import RAG_CONFIG
import os
from openai import OpenAI

from dotenv import load_dotenv

load_dotenv()
class Embedder:
    def __init__(self):
        self.model = RAG_CONFIG["embedding_model"] # requires OPENAI_API_KEY
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
    # -----------------------------
    # Embed list of documents
    # -----------------------------
    def embed_documents(self, documents: List[RAGDocument]) -> List[List[float]]:
        texts = [doc.content for doc in documents]

        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )

        embeddings = [item.embedding for item in response.data]
        return embeddings

    # -----------------------------
    # Embed single query
    # -----------------------------
    def embed_query(self, query: str) -> List[float]:
        response = self.client.embeddings.create(
            model=self.model,
            input=query
        )

        return response.data[0].embedding