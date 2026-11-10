import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import tabela_fixa
from main import gerar_macro, responder

app = FastAPI(title="Valdir - Assistente LATAM")

# "*" só vale sem credenciais; em produção defina ALLOWED_ORIGINS=https://seu-site.com
origens = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origens,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

INDEX = Path(__file__).resolve().parent / "latam-chat" / "index.html"


class Mensagem(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    pergunta: str = Field(min_length=1, max_length=1000)
    historico: list[Mensagem] = Field(default_factory=list, max_length=20)


class MacroRequest(BaseModel):
    situacao: str = Field(min_length=5, max_length=1000)
    canal: Literal["email", "chat", "whatsapp"] = "email"
    tom: Literal["cordial", "formal", "direto"] = "cordial"
    nome_cliente: str | None = Field(default=None, max_length=80)


class Trecho(BaseModel):
    origem: str
    destino: str


class CalcRequest(BaseModel):
    cabine: str
    trechos: list[Trecho] = Field(min_length=1, max_length=10)


@app.get("/")
def home():
    if INDEX.exists():
        return FileResponse(INDEX)
    return {"status": "ok", "message": "Valdir API online"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest):
    try:
        return responder(req.pergunta, [m.model_dump() for m in req.historico])
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        print("Erro no /chat:", repr(e))
        raise HTTPException(status_code=500, detail="Não consegui responder agora. Tente de novo em instantes.")


@app.post("/macro")
def macro(req: MacroRequest):
    try:
        return gerar_macro(req.situacao, req.canal, req.tom, req.nome_cliente)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        print("Erro no /macro:", repr(e))
        raise HTTPException(status_code=500, detail="Não consegui gerar a macro agora. Tente de novo em instantes.")


@app.get("/opcoes")
def opcoes():
    try:
        return tabela_fixa.opcoes()
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Arquivo cabines.json não encontrado no servidor.")


@app.post("/calcular")
def calcular(req: CalcRequest):
    try:
        return tabela_fixa.calcular(req.cabine, [(t.origem, t.destino) for t in req.trechos])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Arquivo cabines.json não encontrado no servidor.")