import os
from pathlib import Path
from langchain_groq import ChatGroq
from langchain_chroma import Chroma

BASE_DIR = Path(__file__).resolve().parent.parent
vectorstore = Chroma(
    persist_directory=str(BASE_DIR / "chroma_db"),
)
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 8}
)
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

    resposta = get_llm().invoke(prompt).content
    return resposta