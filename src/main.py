from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from pathlib import Path
import os

# 🔥 força o caminho correto do .env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# debug (pode remover depois)
print("API KEY:", os.getenv("GROQ_API_KEY"))

llm = ChatGroq(
    model="llama-3.3-8b-instant"
)

prompt = ChatPromptTemplate.from_template(
    "Você é um assistente útil. Responda de forma direta.\nPergunta: {pergunta}"
)

chain = prompt | llm

while True:
    pergunta = input("Você: ")

    if pergunta.lower() in ["sair", "exit"]:
        break

    resposta = chain.invoke({"pergunta": pergunta})
    print("IA:", resposta.content)