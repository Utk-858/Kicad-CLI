# fluxdiff/rag/chat/memory.py

from typing import List, Dict


class ChatMemory:
    def __init__(self, max_history: int = 5):
        self.history: List[Dict[str, str]] = []
        self.max_history = max_history

    # -----------------------------
    # Add new interaction
    # -----------------------------
    def add(self, user_query: str, assistant_response: str):
        self.history.append({
            "user": user_query,
            "assistant": assistant_response
        })

        # Keep only last N interactions
        if len(self.history) > self.max_history:
            self.history.pop(0)

    # -----------------------------
    # Get formatted memory
    # -----------------------------
    def get_context(self) -> str:
        if not self.history:
            return ""

        lines = ["Previous conversation:"]

        for turn in self.history:
            lines.append(f"User: {turn['user']}")
            lines.append(f"Assistant: {turn['assistant']}")

        return "\n".join(lines)

    # -----------------------------
    # Clear memory
    # -----------------------------
    def clear(self):
        self.history = []