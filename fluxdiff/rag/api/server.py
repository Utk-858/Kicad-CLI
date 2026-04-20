from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from fluxdiff.rag.chat.chat_engine import ChatEngine

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
chat_engine = ChatEngine()


class ChatRequest(BaseModel):
    query: str


@app.post("/chat")
def chat(req: ChatRequest):
    response = chat_engine.ask(req.query)

    return {
        "answer": response.answer,
        "sources": response.sources
    }

@app.get("/health")
def health():
    return {"status": "ok"} 