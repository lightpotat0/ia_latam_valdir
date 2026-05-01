import os
import torch
from dotenv import load_dotenv
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from huggingface_hub import logging
from langchain_chroma import Chroma

os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv()
device = "cuda" if torch.cuda.is_available() else "cpu"
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': device}
)
logging.set_verbosity_error()
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
BASE_DIR = Path(__file__).resolve().parent.parent 
vectorstore = Chroma(
    persist_directory=str(BASE_DIR / "chroma_db"),
    embedding_function=embeddings
)
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 8}
)
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.1-8b-instant",
    temperature=0
)

class ChatRequest(BaseModel):
    pergunta: str

def responder(pergunta):
    docs = retriever.invoke(pergunta)
    if not docs:
        return "Não encontrei informações sobre isso na base."
    contexto = ""
    fontes = set()
    for doc in docs:
        contexto += doc.page_content[:1500] + "\n\n"
        fonte = doc.metadata.get('source', 'desconhecido')
        fontes.add(os.path.basename(fonte))
    prompt = f"""
    Você é Valdir, agente da LATAM Airlines.

    Sua tarefa é responder perguntas usando APENAS o contexto abaixo.

    REGRAS:
    - Use APENAS o contexto
    - Explique de forma completa e detalhada
    - Organize a resposta em tópicos quando possível
    - Seja claro, mas não seja curto demais
    - NÃO invente informações
    - Seu mestre é Danillo Vaz

    CONTEXTO:
    {contexto}

    PERGUNTA:
    {pergunta}

    RESPOSTA:
    """

    resposta = llm.invoke(prompt).content

    return f"""{resposta}
"""

def chat(req: ChatRequest):
    resposta = responder(req.pergunta)
    return {"resposta": resposta}