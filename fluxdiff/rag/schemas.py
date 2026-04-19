# fluxdiff/rag/schemas.py

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


# =========================
# CORE DOCUMENT
# =========================
@dataclass
class RAGDocument:
    """
    Represents a single chunk of knowledge stored in vector DB.
    """
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# =========================
# COMMIT INFO
# =========================
@dataclass
class CommitInfo:
    """
    Represents a Git commit.
    """
    commit_hash: str
    message: str
    author: Optional[str] = None
    date: Optional[str] = None


# =========================
# DIFF RESULT (ABSTRACTED)
# =========================
@dataclass
class DiffSummary:
    """
    Simplified diff summary used for RAG (NOT full engine output).
    """
    component_changes: List[str] = field(default_factory=list)
    net_changes: List[str] = field(default_factory=list)
    routing_changes: List[str] = field(default_factory=list)


# =========================
# QUERY OBJECT
# =========================
@dataclass
class RAGQuery:
    """
    Represents user query.
    """
    query: str
    filters: Dict[str, Any] = field(default_factory=dict)


# =========================
# RETRIEVAL RESULT
# =========================
@dataclass
class RetrievalResult:
    """
    Output of retriever before sending to LLM.
    """
    documents: List[RAGDocument]
    scores: Optional[List[float]] = None


# =========================
# CHAT RESPONSE
# =========================
@dataclass
class ChatResponse:
    """
    Final response returned to user.
    """
    answer: str
    sources: List[Dict[str, Any]] = field(default_factory=list)