from unittest import loader
from urllib import request

import bs4
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from pathlib import Path
from langchain_community.document_loaders import RecursiveUrlLoader
from bs4 import BeautifulSoup as soup
import os

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

loader = RecursiveUrlLoader(
    url="https://www.latamairlines.com/br/pt/central-ajuda",
    max_depth=2,
    extractor=lambda x: soup(x, "html.parser").get_text(separator="\n", strip=True),
    prevent_outside=True
)

docs = loader.load()
print(f"Baixei {len(docs)} páginas de perguntas!")

if docs:
    contexto_dos_docs = "\n\n".join([doc.page_content for doc in docs[:10]])
else:
    contexto_dos_docs = "Nenhum documentro encontrado no site"

from langchain_groq import ChatGroq

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.7)

prompt = ChatPromptTemplate.from_template(
    "Você é um agente de IA da Latam Airlines, seu nome é Valdir e é importante que você se aprensente, "
    "você ajuda a agentes da latam tirem dúvidas "
    "sobre procedimentos da Latam e informações em geral. Responda apenas em base nos documentos"
    "fornecidos. e a informação não estiver nos documentos, diga explicitamente que não encontrou e oriente o "
    "agente a consultar o supervisor.\n"
    "Contexto: {context}\n"
    "Pergunta: {pergunta}"
)

chain = prompt | llm

resposta = chain.invoke({
    "context": "Sem documentos fornecidos ainda",
    "pergunta": "oi"
})

while True:

    print("Valdir:", resposta.content)
    pergunta = input("Você: ")

    if pergunta.lower() in ["sair", "exit"]:
        break

    resposta = chain.invoke({
        "context": contexto_dos_docs,
        "pergunta": pergunta
    })

    print("Valdir:", resposta.content)