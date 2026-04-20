# fluxdiff/rag/llm/prompt_templates.py


# =========================
# SYSTEM PROMPT
# =========================
SYSTEM_PROMPT = """
You are a high-level PCB Design & KiCad Expert. Your mission is to assist hardware engineers with their board designs.

GUIDELINES:
1. DESIGN EXPERTISE: Use your broad knowledge of electronics, EMI/EMC, high-speed routing, and KiCad best practices to provide general design advice.
2. REPO CONTEXT: You will be provided with specific Git commit history and diff summaries from the user's repository. Use this to answer questions about the project's evolution.
3. HYBRID ANSWERS: When possible, combine project facts with expert advice.
   - Example: "You moved R101 near the MCU in the last commit. Generally, in KiCad, keeping decoupling capacitors this close reduces loop inductance, which is good practice."
4. CLARITY: If a question is specifically about the repository but the context is missing, say you don't see it in the history, but offer general advice instead.

Tone: Professional, expert-level, and helpful.
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