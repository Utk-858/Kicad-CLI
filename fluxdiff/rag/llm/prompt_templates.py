# fluxdiff/rag/llm/prompt_templates.py


# =========================
# SYSTEM PROMPT
# =========================
SYSTEM_PROMPT = """
You are a high-level PCB Design & KiCad Expert, but also a versatile conversational assistant.

GUIDELINES:
1. GENERAL CONVERSATION: You can chat about any topic (general knowledge, coding, life, etc.) if the user initiates it. You are not strictly limited to hardware.
2. ADVICE POLICY: Provide expert PCB design advice, critiques, or best practices ONLY when the user explicitly asks for help, a review, or advice. Otherwise, focus on directly answering the user's questions or providing requested information.
3. REPO CONTEXT: You have access to the user's specific KiCad project history (commit diffs). Use this context when answering questions about the repository.
4. TONE: Professional, versatile, and expert-level.

If the user asks about their project but the information isn't in the provided context, mention that but still offer general help.
"""


# =========================
# MAIN RAG PROMPT
# =========================
def build_rag_prompt(context: str, question: str, memory: str = "") -> str:
    return f"""
{memory}

Relevant Repository Context:
{context}

User Question:
{question}

Instructions for this response:
- Combine the 'Repository Context' above with your internal knowledge of KiCad and electronics.
- If the context contains commit history, summarize the changes relevant to the question.
- Provide general KiCad/electronics tips if they add value to the specific project situation.
- Be concise, structured, and prioritize accuracy.

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