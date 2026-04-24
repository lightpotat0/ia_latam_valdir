from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from pathlib import Path
import os

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from langchain_groq import ChatGroq

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.7
)

prompt = ChatPromptTemplate.from_template(
    "Você é um agente de IA da Latam Airlines, seu nome é Valdir, você ajuda a agentes da latam tirem dúvidas sobre procedimentos da Latam e informações em geral.\nPergunta: {pergunta}"
)

chain = prompt | llm

while True:
    pergunta = input("Você: ")

    if pergunta.lower() in ["sair", "exit"]:
        break

    resposta = chain.invoke({"pergunta": pergunta})
    print("Valdir:", resposta.content)