import os
from dotenv import load_dotenv
from pathlib import Path
from langchain_groq import ChatGroq
from langchain_chroma import Chroma

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
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
    for doc in docs:
        contexto += doc.page_content[:1500] + "\n\n"
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

    resposta = llm.invoke(prompt).content
    return resposta