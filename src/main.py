from unittest import loader
from urllib import request

import bs4
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

loader = DirectoryLoader(
    './documentos_latam',
    glob="./*.pdf",
    loader_cls=PyPDFLoader
)

docs_pdf = loader.load()

url = "https://www.latamairlines.com/br/pt/central-ajuda"
try:
    html_text = get_page_text(url)
    docs_web = [Document(page_content=html_text, metadata={"source": url})]
except Exception as e:
    print(f"Aviso: Não foi possível ler o site. Erro: {e}")
    docs_web = []

todos_os_docs = docs_pdf + docs_web

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100
)

chunks = splitter.split_documents(todos_os_docs)

vectorstore = FAISS.from_documents(chunks, embeddings)

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

def responder(pergunta):
    docs_relevantes = retriever.invoke(pergunta)

    contexto = "\n\n".join([doc.page_content for doc in docs_relevantes])

    prompt = f"""
Você é Valdir, agente da Latam Airlines.

REGRAS:
- Responda SOMENTE com base no contexto
- NÃO invente informações
- Se não encontrar, diga:
  "Não encontrei essa informação nos documentos"

Contexto:
{contexto}

Pergunta:
{pergunta}
"""

    resposta = llm.invoke(prompt)
    return resposta.content

while True:
    pergunta = input("\nVocê: ")

    if pergunta.lower() in ["sair", "exit"]:
        break

    resposta = responder(pergunta)
    print("\nValdir:", resposta)