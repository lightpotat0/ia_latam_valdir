from playwright.sync_api import sync_playwright
import os


def pote_de_biscoitos():
    if os.path.exists("state.json"):
        return
    with sync_playwright() as p:
        caminho_chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        browser = p.chromium.launch(executable_path=caminho_chrome, headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.latamairlines.com/br/pt/central-ajuda")
        print("Aceite os cookies na janela que abriu...")
        page.wait_for_timeout(10000)
        context.storage_state(path="state.json")
        browser.close()


def mapeamento(url_principal, pasta_destino):
    pasta_abs = os.path.abspath(pasta_destino)
    os.makedirs(pasta_abs, exist_ok=True)

    with sync_playwright() as p:
        caminho_chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        browser = p.chromium.launch(executable_path=caminho_chrome, headless=True)

        context_args = {"storage_state": "state.json"} if os.path.exists("state.json") else {}
        context = browser.new_context(**context_args)
        page = context.new_page()

        print(f"Acessando: {url_principal}")

        try:
            page.goto(url_principal, wait_until="domcontentloaded", timeout=90000)

            print("Abrindo categorias e expandindo links ocultos...")
            botoes = page.locator('button[aria-expanded="false"], .latam-category-card').all()
            for i, btn in enumerate(botoes[:15]):
                try:
                    btn.click(timeout=3000)
                    page.wait_for_timeout(500)
                except:
                    continue

            page.wait_for_load_state("networkidle")
            print("Carregando...")

            for _ in range(12):
                page.mouse.wheel(0, 2000)
                page.wait_for_timeout(800)

            links_elementos = page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a'));
                    return links
                        .map(a => a.href)
                        .filter(href => href.includes('central-ajuda') && href.includes('/perguntas/'));
                }
            """)
            urls_para_baixar = sorted(list(set([u for u in links_elementos if u.startswith('https')])))
            print(f"Encontrados {len(urls_para_baixar)} links. Iniciando downloads...")

            for i, url in enumerate(urls_para_baixar):
                try:
                    nome_limpo = url.split("central-ajuda/")[-1].replace("/", "-").split("?")[0].strip("-")
                    if not nome_limpo or nome_limpo == "br-pt":
                        nome_limpo = f"home_ajuda_{i}"
                    caminho_pdf = os.path.join(os.path.abspath(pasta_destino), f"{nome_limpo}.pdf")

                    if not os.path.exists(caminho_pdf):
                        print(f"[{i + 1}/{len(urls_para_baixar)}] Baixando: {nome_limpo}")
                        page.goto(url, wait_until="domcontentloaded", timeout=45000)
                        page.wait_for_timeout(3000)
                        page.pdf(path=caminho_pdf, print_background=True, format="A4")
                    else:
                        print(f"[{i + 1}/{len(urls_para_baixar)}] Já existe: {nome_limpo}")
                except Exception as e:
                    print(f"Erro ao processar sublink {url}: {e}")

        except Exception as e:
            print(f"Erro ao acessar página principal: {e}")

        browser.close()

pote_de_biscoitos()
mapeamento("https://www.latamairlines.com/br/pt/central-ajuda", "../latam_arquives")