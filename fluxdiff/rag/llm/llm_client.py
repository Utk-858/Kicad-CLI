# fluxdiff/rag/llm/llm_client.py

from openai import OpenAI
import os
from dotenv import load_dotenv

from fluxdiff.rag.config import RAG_CONFIG
from fluxdiff.rag.llm.prompt_templates import SYSTEM_PROMPT

load_dotenv()


class LLMClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = RAG_CONFIG["llm_model"]

    # -----------------------------
    # Generate response
    # -----------------------------
    def generate_response(self, prompt: str) -> str:
        """
        Sends prompt to LLM and returns response.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2  # low = factual answers
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print("LLM Error:", str(e))
            return "Error generating response."