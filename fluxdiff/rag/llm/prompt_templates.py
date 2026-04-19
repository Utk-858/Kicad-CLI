# fluxdiff/rag/llm/prompt_templates.py


# =========================
# SYSTEM PROMPT
# =========================
SYSTEM_PROMPT = """
You are a PCB analysis assistant specialized in analyzing KiCad PCB changes from Git repositories.

STRICT RULES:
- Use ONLY the provided context
- Do NOT assume or infer missing details
- If something is not explicitly mentioned, say so
- Avoid repeating information
- Focus only on relevant changes

When answering:
- Highlight ONLY meaningful changes
- Ignore commits with no changes
- Be precise and concise
"""


# =========================
# MAIN RAG PROMPT
# =========================
def build_rag_prompt(context: str, question: str, memory: str = "") -> str:
    return f"""
{memory}

Context:
{context}

Question:
{question}

Instructions:
- Answer ONLY from context
- Ignore irrelevant documents
- Do NOT repeat "no changes" commits
- Be concise and structured
- If multiple commits exist, summarize efficiently

Answer:
"""


# =========================
# CONTEXT FORMATTER
# =========================
def format_documents(documents) -> str:
    """
    Convert retrieved documents into a single context string.
    """
    context_parts = []

    for i, doc in enumerate(documents):
        context_parts.append(f"[Document {i+1}]\n{doc.content}")

    return "\n\n".join(context_parts)