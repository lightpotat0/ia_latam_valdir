from playwright.sync_api import sync_playwright
import os
from markdownify import markdownify as md
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
import shutil

load_dotenv()
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
if os.path.exists("./chroma_db"):
    shutil.rmtree("./chroma_db")
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings
)
def pote_de_biscoitos():
    if os.path.exists("state.json"):
        return
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.latamairlines.com/br/pt/central-ajuda")
        print("Aceite os cookies...")
        page.wait_for_timeout(10000)
        context.storage_state(path="state.json")
        browser.close()

def mapeamento(url_principal, pasta_destino, urls_especificas):
    pasta_abs = os.path.abspath(pasta_destino)
    os.makedirs(pasta_abs, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context_args = {"storage_state": "state.json"} if os.path.exists("state.json") else {}
        context = browser.new_context(**context_args)
        page = context.new_page()
        urls_coletadas = set(urls_especificas or [])
        try:
            print("Abrindo página principal...")
            page.goto(url_principal, timeout=60000)
            page.wait_for_load_state("networkidle")
            links = page.evaluate("""
                () => Array.from(document.querySelectorAll('a'))
                    .map(a => a.href)
                    .filter(h => h && h.includes('latamairlines.com'))
            """)

            urls_coletadas.update(links)
            for url in list(urls_coletadas):
                try:
                    page.goto(url, timeout=30000)
                    page.wait_for_load_state("domcontentloaded")

                    novos_links = page.evaluate("""
                        () => Array.from(document.querySelectorAll('a'))
                            .map(a => a.href)
                            .filter(h => h && h.includes('latamairlines.com'))
                    """)
                    urls_coletadas.update(novos_links)
                except:
                    continue

            print("Total de URLs:", len(urls_coletadas))
            for i, url in enumerate(urls_coletadas):
                try:
                    slug = url.replace("https://", "").replace("/", "-")[:150]
                    caminho_file = os.path.join(pasta_abs, f"{slug}.md")
                    if os.path.exists(caminho_file):
                        continue
                    print(f"[{i}] Salvando:", url)
                    page.goto(url, timeout=30000)
                    try:
                        page.wait_for_selector("main, article", timeout=8000)
                        html = page.inner_html("main")
                    except:
                        html = page.inner_html("body")
                    texto_md = md(html)
                    if len(texto_md.strip()) < 200:
                        continue
                    with open(caminho_file, "w", encoding="utf-8") as f:
                        f.write(f"FONTE: {url}\n\n{texto_md}")
                except:
                    continue
        finally:
            browser.close()

def enviar_para_chroma(pasta):
    docs = []
    arquivos = [f for f in os.listdir(pasta) if f.endswith(".md")]
    print("Arquivos encontrados:", len(arquivos))
    for arquivo in arquivos:
        with open(os.path.join(pasta, arquivo), "r", encoding="utf-8") as f:
            texto = f.read()

            docs.append(Document(
                page_content=texto,
                metadata={"source": arquivo}
            ))
    print("Antes do split:", len(docs))
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )
    docs = splitter.split_documents(docs)
    print("Depois do split:", len(docs))
    vectorstore.add_documents(docs)
    vectorstore.persist()
    print("Dados salvos no Chroma!")

if __name__ == "__main__":
    meus_links_extras = [
        "https://latampass.latam.com/pt_br/categorias-elite",
        "https://latampass.latam.com/pt_br/clube",
        "https://latampass.latam.com/pt_br/institucional",
        "https://latampass.latam.com/pt_br/junte-milhas/parceiros",
        "https://latampass.latam.com/pt_br/latampass-itau",
        "https://latampass.latam.com/pt_br/ganhar-milhas/cartoes-de-bancos",
        "https://latampass.latam.com/pt_br/milhas/acelere-suas-milhas/transferir",
        "https://latampass.latam.com/pt_br/regulamento/beneficios",
        "https://latampass.latam.com/pt_br/milhas/como-juntar-milhas/solicitar-milhas-em-voo/companhias-parceiras",
        "https://latampass.latam.com/pt_br/viagem/usar-milhas-para-voar/regras-de-resgate/latam/classe-economica"
    ]
    pote_de_biscoitos()
    mapeamento(
        "https://www.latamairlines.com/br/pt/central-ajuda",
        "./latam_arquivos_md",
        meus_links_extras
    )

    enviar_para_chroma("./latam_arquivos_md")