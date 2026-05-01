import os
import torch
from dotenv import load_dotenv
from pathlib import Path
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv()
print("GROQ KEY:", os.getenv("GROQ_API_KEY"))
device = "cuda" if torch.cuda.is_available() else "cpu"
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': device}
)
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

while True:
    pergunta = input("\nVocê: ")

    if pergunta.lower() in ["sair", "exit"]:
        break

    print("\nValdir:", responder(pergunta))