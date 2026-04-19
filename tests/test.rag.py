from fluxdiff.rag.embedding.vector_store import VectorStore

store = VectorStore()
print("Documents:", len(store.documents))