import os
import random
import re
import time
from urllib.parse import urldefrag, urlparse

from markdownify import markdownify as md
from playwright.sync_api import sync_playwright
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from main import CHROMA_DIR, get_embeddings

URL_AJUDA = "https://www.latamairlines.com/br/pt/central-ajuda"
PASTA_MD = "./latam_arquivos_md"
HOSTS_PERMITIDOS = ("latamairlines.com", "latampass.latam.com")
MAX_URLS = int(os.getenv("MAX_URLS", "300"))
# SCRAPER_HEADLESS=0 abre o navegador na tela (mais difícil de bloquear)
HEADLESS = os.getenv("SCRAPER_HEADLESS", "1") != "0"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
ARGS = ["--disable-blink-features=AutomationControlled"]

LINKS_EXTRAS = [
    "https://latampass.latam.com/pt_br/categorias-elite",
    "https://latampass.latam.com/pt_br/clube",
    "https://latampass.latam.com/pt_br/institucional",
    "https://latampass.latam.com/pt_br/junte-milhas/parceiros",
    "https://latampass.latam.com/pt_br/latampass-itau",
    "https://latampass.latam.com/pt_br/ganhar-milhas/cartoes-de-bancos",
    "https://latampass.latam.com/pt_br/milhas/acelere-suas-milhas/transferir",
    "https://latampass.latam.com/pt_br/regulamento/beneficios",
    "https://latampass.latam.com/pt_br/milhas/como-juntar-milhas/solicitar-milhas-em-voo/companhias-parceiras",
    "https://latampass.latam.com/pt_br/viagem/usar-milhas-para-voar/regras-de-resgate/latam/classe-economica",
]

LINKS_JS = "() => Array.from(document.querySelectorAll('a')).map(a => a.href)"
LIMPEZA_JS = """() => document.querySelectorAll(
    'nav, footer, script, style, noscript, svg, [role="navigation"], [role="dialog"], [id*="cookie" i], [class*="cookie" i]'
).forEach(e => e.remove())"""


def bloqueada(texto):
    """Detecta a tela de bloqueio (Akamai) que o site mostra para robôs."""
    t = texto.lower()[:800]
    return any(m in t for m in ("access denied", "don't have permission to access", "edgesuite.net"))


def limpar(texto):
    """Tira imagens e links do markdown (fica só o texto) e junta linhas em branco."""
    texto = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", texto)
    texto = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", texto)
    return re.sub(r"\n{3,}", "\n\n", texto).strip()


def normalizar(url):
    """Tira #fragmento e ?query; devolve None se não for um site da LATAM."""
    if not url or not url.startswith("http"):
        return None
    url = urldefrag(url)[0].split("?")[0].rstrip("/")
    host = urlparse(url).netloc
    if not any(host.endswith(h) for h in HOSTS_PERMITIDOS):
        return None
    return url


# Padrão = igual ao seu código original (Chromium do Playwright, sem disfarce).
# Só use SCRAPER_STEALTH=1 se o padrão for bloqueado.
STEALTH = os.getenv("SCRAPER_STEALTH", "0") == "1"


def abrir_navegador(p, headless):
    if STEALTH:
        try:
            return p.chromium.launch(channel="chrome", headless=headless, args=ARGS)
        except Exception:
            return p.chromium.launch(headless=headless, args=ARGS)
    return p.chromium.launch(headless=headless)


def novo_contexto(browser):
    args = {"storage_state": "state.json"} if os.path.exists("state.json") else {}
    if not STEALTH:
        return browser.new_context(**args)
    context = browser.new_context(
        user_agent=UA, locale="pt-BR", timezone_id="America/Sao_Paulo",
        viewport={"width": 1366, "height": 800}, **args,
    )
    context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return context


def pote_de_biscoitos():
    """Roda uma vez, no seu PC (abre o navegador): aceite os cookies e navegue um pouco."""
    if os.path.exists("state.json"):
        return
    with sync_playwright() as p:
        browser = abrir_navegador(p, headless=False)
        context = novo_contexto(browser)
        page = context.new_page()
        page.goto(URL_AJUDA)
        print("Aceite os cookies e clique em uma ou duas páginas (você tem 25 segundos)...")
        page.wait_for_timeout(25000)
        context.storage_state(path="state.json")
        browser.close()


def mapeamento(url_principal, pasta_destino, urls_especificas=None, sobrescrever=False):
    pasta_abs = os.path.abspath(pasta_destino)
    os.makedirs(pasta_abs, exist_ok=True)
    salvas = bloqueadas = 0

    with sync_playwright() as p:
        browser = abrir_navegador(p, headless=HEADLESS)
        context = novo_contexto(browser)
        page = context.new_page()

        extras = {u for u in map(normalizar, urls_especificas or []) if u}
        coletadas = set(extras)
        try:
            print("Abrindo página principal...")
            page.goto(url_principal, timeout=60000)
            page.wait_for_load_state("networkidle")
            if bloqueada(page.inner_text("body")):
                print("AVISO: o site bloqueou o acesso (Access Denied). Veja as dicas no final.")
            coletadas.update(u for u in map(normalizar, page.evaluate(LINKS_JS)) if u)

            # segunda camada de links, com limite para não rodar para sempre
            for url in list(coletadas)[:MAX_URLS]:
                try:
                    page.goto(url, timeout=30000)
                    page.wait_for_load_state("domcontentloaded")
                    coletadas.update(u for u in map(normalizar, page.evaluate(LINKS_JS)) if u)
                    time.sleep(random.uniform(0.5, 1.2))
                except Exception:
                    continue

            urls = sorted(coletadas)[:MAX_URLS]
            print("Total de URLs:", len(urls))

            for i, url in enumerate(urls):
                try:
                    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", url.replace("https://", ""))[:150]
                    caminho = os.path.join(pasta_abs, f"{slug}.md")
                    # as páginas extras (suas) são sempre baixadas de novo
                    if os.path.exists(caminho) and not sobrescrever and url not in extras:
                        continue
                    print(f"[{i}] Salvando:", url)
                    page.goto(url, timeout=30000)
                    try:
                        page.wait_for_load_state("networkidle", timeout=15000)
                    except Exception:
                        pass
                    page.wait_for_timeout(1500)
                    page.evaluate(LIMPEZA_JS)
                    html = None
                    for seletor in ("main", "article", "body"):
                        try:
                            html = page.inner_html(seletor, timeout=3000)
                            break
                        except Exception:
                            continue
                    if not html:
                        print("   sem conteúdo:", url)
                        continue
                    texto_md = re.sub(r"\n{3,}", "\n\n", md(html, strip=["a", "img"])).strip()
                    if bloqueada(texto_md):
                        bloqueadas += 1
                        print("   BLOQUEADA (Access Denied), não salva:", url)
                        continue
                    if len(texto_md) < 200:
                        print("   ignorada (conteúdo curto):", url)
                        continue
                    with open(caminho, "w", encoding="utf-8") as f:
                        f.write(f"FONTE: {url}\n\n{texto_md}")
                    salvas += 1
                    time.sleep(random.uniform(0.8, 1.8))
                except Exception:
                    continue
        finally:
            browser.close()

    print(f"\nPáginas salvas: {salvas} | bloqueadas: {bloqueadas}")
    if bloqueadas:
        print("O site está bloqueando o robô. Tente, nesta ordem:")
        print("1) recriar o state.json (apague e rode de novo, aceitando os cookies na janela);")
        print("2) navegador visível:  $env:SCRAPER_HEADLESS='0'; python site_leitor.py")
        print("3) modo furtivo:       $env:SCRAPER_STEALTH='1'; python site_leitor.py")


def enviar_para_chroma(pasta):
    """Substitui o conteúdo da coleção (sem apagar a pasta, então a API em execução continua funcionando)."""
    docs = []
    ignorados = 0
    arquivos = [f for f in os.listdir(pasta) if f.endswith(".md")]
    print("Arquivos encontrados:", len(arquivos))

    for arquivo in arquivos:
        with open(os.path.join(pasta, arquivo), "r", encoding="utf-8") as f:
            texto = f.read()
        url = arquivo
        if texto.startswith("FONTE:"):
            primeira, _, texto = texto.partition("\n\n")
            url = primeira.replace("FONTE:", "").strip()
        if bloqueada(texto):
            ignorados += 1
            continue
        texto = limpar(texto)
        if len(texto) < 100:
            continue
        docs.append(Document(page_content=texto, metadata={"source": arquivo, "url": url}))

    if ignorados:
        print(f"Ignorados {ignorados} arquivos que eram 'Access Denied'.")
    if not docs:
        print("Nenhum conteúdo válido: a base NÃO foi alterada.")
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    docs = splitter.split_documents(docs)
    print("Chunks:", len(docs))

    vectorstore = Chroma(persist_directory=CHROMA_DIR, embedding_function=get_embeddings())
    ids_antigos = vectorstore.get()["ids"]
    for i in range(0, len(ids_antigos), 500):
        vectorstore.delete(ids=ids_antigos[i:i + 500])

    for i in range(0, len(docs), 500):
        vectorstore.add_documents(docs[i:i + 500])
    print("Dados salvos no Chroma!")


if __name__ == "__main__":
    import sys

    if "--indexar" in sys.argv:
        # só indexa os .md que já existem, sem abrir navegador nem rastrear o site
        enviar_para_chroma(PASTA_MD)
    else:
        pote_de_biscoitos()
        mapeamento(URL_AJUDA, PASTA_MD, LINKS_EXTRAS)
        enviar_para_chroma(PASTA_MD)