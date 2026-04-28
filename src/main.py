from langchain_groq import ChatGroq
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
pasta_md = '../latam_arquivos_md'

loader = DirectoryLoader(
    './latam_arquivos_md',
    glob="./*.md",
    loader_cls=TextLoader,
    loader_kwargs={'encoding': 'utf-8'}
)

docs_web = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150
)
chunks = splitter.split_documents(docs_web)
vectorstore = FAISS.from_documents(chunks, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

def responder(pergunta):
    docs_import = retriever.invoke(pergunta)
    contexto = "\n\n".join([doc.page_content for doc in docs_import])

    prompt = f"""
Você é Valdir, agente da Latam Airlines.

REGRAS:
- Responda SOMENTE com base no contexto
- NÃO invente informações
- Se não encontrar, diga:
  "Não encontrei essa informação nos documentos"
- Depois de passar a informação, informe o nome do arquivo encontrado

Contexto:
{contexto}

Pergunta:
{pergunta}
"""

    resposta = llm.invoke(prompt)
    return resposta.content

while True:
    pergunta = input("\nVocê: ")

    if pergunta.lower() in ["sair", "exit", "parar"]:
        break

    resposta = responder(pergunta)
    print("\nValdir:", resposta)