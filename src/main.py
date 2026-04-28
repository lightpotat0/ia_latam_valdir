import os
import torch
from dotenv import load_dotenv
from pathlib import Path
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

device = "cuda" if torch.cuda.is_available() else "cpu"
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={'device': device}
)

FAISS_PATH = "faiss_index_latam"
pasta_md = '../latam_arquivos_md'

if not os.path.exists(FAISS_PATH):
    loader = DirectoryLoader(pasta_md, glob="./*.md", loader_cls=TextLoader, loader_kwargs={'encoding': 'utf-8'})
    docs_web = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(docs_web)
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(FAISS_PATH)
else:
    vectorstore = FAISS.load_local(
        FAISS_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )

retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

def responder(pergunta):
    docs_import = retriever.invoke(pergunta)
    contexto = ""
    fontes = set()
    for doc in docs_import:
        contexto += doc.page_content + "\n\n"
        fontes.add(os.path.basename(doc.metadata.get('source', 'desconhecido')))

    prompt = f"""Você é Valdir, agente da Latam Airlines, utilizado para tirar dúvidas.
Responda APENAS com base no contexto abaixo:
{contexto}
Pergunta: {pergunta}
Fontes consultadas: {', '.join(fontes)}"""

    return llm.invoke(prompt).content

while True:
    pergunta = input("\nVocê: ")
    if pergunta.lower() in ["sair", "exit"]:
        break
    print("\nValdir:", responder(pergunta))
