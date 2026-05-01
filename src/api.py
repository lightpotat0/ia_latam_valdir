from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from main import responder, ChatRequest
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def home():
    return {"status": "ok", "message": "Valdir API online 🚀"}

@app.post("/chat")
def chat(req: ChatRequest):
    resposta = responder(req.pergunta)
    return {"resposta": resposta}