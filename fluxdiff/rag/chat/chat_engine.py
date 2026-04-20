# fluxdiff/rag/chat/chat_engine.py

from fluxdiff.rag.retrieval.retriever import Retriever
from fluxdiff.rag.llm.llm_client import LLMClient
from fluxdiff.rag.llm.prompt_templates import (
    build_rag_prompt,
    format_documents
)
from fluxdiff.rag.schemas import ChatResponse, RAGQuery
from fluxdiff.rag.chat.memory import ChatMemory


class ChatEngine:
    def __init__(self):
        self.retriever = Retriever()
        self.llm = LLMClient()
        self.memory = ChatMemory()

    # -----------------------------
    # Simple chat
    # -----------------------------
    def ask(self, query: str) -> ChatResponse:
        """
        Basic RAG pipeline
        """
        # 0. Check for greetings or very short messages
        greetings = ["hi", "hello", "hey", "howdy", "greetings"]
        if query.lower().strip() in greetings:
            answer = self.llm.generate_response(f"The user said '{query}'. Respond with a friendly, professional greeting as a PCB Design Expert.")
            self.memory.add(query, answer)
            return ChatResponse(answer=answer, sources=[])

        # 1. Retrieve documents
        retrieval_result = self.retriever.retrieve(query)

        documents = retrieval_result.documents
        documents = [
            d for d in documents
            if d.content and "no changes" not in d.content.lower()
        ]

        # 2. Format context
        context = format_documents(documents)

        # 3. Build prompt
        memory_context = self.memory.get_context()
        prompt = build_rag_prompt(context, query, memory_context)

        # 4. Generate answer
        answer = self.llm.generate_response(prompt)
        self.memory.add(query, answer)

        # 5. Prepare sources (metadata)
        sources = [doc.metadata for doc in documents]

        return ChatResponse(
            answer=answer,
            sources=sources
        )

    # -----------------------------
    # Advanced chat with filters
    # -----------------------------
    def ask_with_filters(self, rag_query: RAGQuery) -> ChatResponse:
        """
        Supports metadata filtering
        """

        # 1. Retrieve documents with filters
        retrieval_result = self.retriever.retrieve_with_query(rag_query)

        documents = retrieval_result.documents

        # 2. Format context
        context = format_documents(documents)

        # 3. Build prompt
        prompt = build_rag_prompt(context, rag_query.query)

        # 4. Generate answer
        answer = self.llm.generate_response(prompt)

        # 5. Sources
        sources = [doc.metadata for doc in documents]

        return ChatResponse(
            answer=answer,
            sources=sources
        )