# fluxdiff/rag/llm/prompt_templates.py

# =========================
# SYSTEM PROMPT
# =========================

SYSTEM_PROMPT = """
You are **FluxDiff AI**, an expert in PCB design, KiCad workflows, and hardware engineering.

You have access to repository-specific context, but you should only use it when relevant to the user's request.

## 🟢 1. REPOSITORY-AWARE MODE
Use this mode when the question is about the project, its history, or its components.
* Summarize changes precisely (Component, Net, Routing).
* Explain THE REASONING (the "WHY") if available in commit messages.
* Use specific references (R101, GND, etc.).

## 🟡 2. GENERAL MODE
Use this mode for general KiCad advice, electronics theory, or casual conversation (greetings, off-topic chat).
* Be helpful and professional.
* Do NOT force repository summaries into general conversation.
* If the user asks about the repo but context is missing, say you don't have the info but provide general guidance.

## 🎯 RESPONSE RULES
* Be direct and precise.
* Keep answers concise unless detail is requested.
"""

# =========================
# MAIN RAG PROMPT
# =========================

def build_rag_prompt(context: str, question: str, memory: str = "") -> str:
    return f"""
{memory}

---

## REPOSITORY CONTEXT
{context}

---

## USER QUESTION
{question}

---

## INSTRUCTIONS
1. If the question is a greeting or general talk: Just respond naturally as an AI assistant.
2. If the question is about the project:
   - Use the REPOSITORY CONTEXT to provide a specific answer.
   - If the context is empty or irrelevant, tell the user you don't see that in the history.
3. Combine context with your expert KiCad knowledge only when it adds value.

Answer:
"""

# =========================
# CONTEXT FORMATTER
# =========================

def format_documents(documents) -> str:
    """
    Convert retrieved documents into structured context.
    """
    context_parts = []

    for i, doc in enumerate(documents):
        metadata = getattr(doc, "metadata", {})
        doc_type = metadata.get("type", "general")

        context_parts.append(
            f"[Document {i+1} | Type: {doc_type}]\n{doc.content}"
        )

    return "\n\n".join(context_parts)
