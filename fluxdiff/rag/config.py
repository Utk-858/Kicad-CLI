# fluxdiff/rag/config.py

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

RAG_CONFIG = {
    # =========================
    # REPO SETTINGS
    # =========================
    "repo_path": "/Users/utkarshbansal/pcbs-test",  # change later

    # =========================
    # EMBEDDING SETTINGS
    # =========================
    "embedding_model": "text-embedding-3-small",  # or local later

    # =========================
    # VECTOR DB SETTINGS
    # =========================
    "vector_db_path": os.path.join(BASE_DIR, "rag_db"),

    # =========================
    # CHUNKING SETTINGS
    # =========================
    "chunk_size": 500,
    "chunk_overlap": 50,

    # =========================
    # RETRIEVAL SETTINGS
    # =========================
    "top_k": 3,

    # =========================
    # LLM SETTINGS
    # =========================
    "llm_model": "gpt-4o-mini",  # fast + cheap
}