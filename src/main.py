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
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import os

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

def get_page_text(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )

        try:
            page.goto(url, timeout=60000)
            page.wait_for_load_state("domcontentloaded")

            html = page.content()

        except Exception as e:
            print("Erro ao carregar página:", e)
            html = ""

        finally:
            browser.close()

    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n", strip=True)

url = "https://www.latamairlines.com/br/pt/central-ajuda"
text = get_page_text(url)

print("\n--- TEXTO COLETADO ---\n")
print(text[:1000])

docs = [Document(page_content=text)]

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100
)

chunks = splitter.split_documents(docs)

print(f"\nChunks criados: {len(chunks)}")

embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

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