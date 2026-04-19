from fluxdiff.rag.schemas import RAGDocument
from fluxdiff.rag.embedding.embedder import Embedder
from fluxdiff.rag.embedding.vector_store import VectorStore

docs = [
    RAGDocument(content="Component R1 moved"),
    RAGDocument(content="Routing updated with new trace"),
    RAGDocument(content="Power net changed from GND to VCC")
]

embedder = Embedder()
store = VectorStore()

embeddings = embedder.embed_documents(docs)
store.add_documents(docs, embeddings)

print("Inserted docs:", len(docs))