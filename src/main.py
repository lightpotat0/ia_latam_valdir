import os
import pickle
from pathlib import Path
from chromadb import Client
from chromadb.config import Settings
from sklearn.metrics.pairwise import cosine_similarity
from langchain_groq import ChatGroq

BASE_DIR = Path(__file__).resolve().parent
with open(BASE_DIR / "vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)
client = Client(Settings(persist_directory=str(BASE_DIR / "chroma_db")))
collection = client.get_collection(name="latam_docs")
llm = None
def get_llm():
    global llm
    if llm is None:
        llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.1-8b-instant",
            temperature=0
        )
    return llm

def buscar_docs(pergunta, k=5):
    query_vec = vectorizer.transform([pergunta]).toarray()[0]

    results = collection.get(include=["documents", "embeddings"])

    docs = results["documents"]
    embeddings = results["embeddings"]

    sims = cosine_similarity([query_vec], embeddings)[0]

    indices = sims.argsort()[-k:][::-1]

    return [docs[i] for i in indices]

def responder(pergunta):
    docs = buscar_docs(pergunta)
    if not docs:
        return "Não encontrei informações sobre isso na base."
    contexto = ""
    for doc in docs:
        contexto += doc[:1500] + "\n\n"
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
    """
    resposta = get_llm().invoke(prompt).content
    return resposta