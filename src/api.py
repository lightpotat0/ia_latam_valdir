from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from main import responder
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class Pergunta(BaseModel):
    pergunta: str

@app.post("/chat")
def chat(p: Pergunta):
    resposta = responder(p.pergunta)
    return {"resposta": resposta}