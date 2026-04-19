from fluxdiff.rag.retrieval.retriever import Retriever

retriever = Retriever()

res = retriever.retrieve("routing")

for doc in res.documents:
    print(doc.content)