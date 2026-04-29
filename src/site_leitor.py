from playwright.sync_api import sync_playwright
import os
from markdownify import markdownify as md


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

def mapeamento(url_principal, pasta_destino, urls_especificas):
    pasta_abs = os.path.abspath(pasta_destino)
    os.makedirs(pasta_abs, exist_ok=True)

    with sync_playwright() as p:
        caminho_chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        browser = p.chromium.launch(executable_path=caminho_chrome, headless=True)

        context_args = {"storage_state": "state.json"} if os.path.exists("state.json") else {}
        context = browser.new_context(
            **context_args,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print(f"Iniciando Mapeamento: {url_principal}")
        urls_coletadas = set()

        if urls_especificas:
            for url in urls_especificas:
                urls_coletadas.add(url)
            print(f"Adicionadas {len(urls_especificas)} URLs específicas à fila.")

        try:
            page.goto(url_principal, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)
            cards = page.locator('a[class*="MotionLinkstyles"], .latam-category-card').all()
            print(f"Encontradas {len(cards)} categorias principais.")

            for i in range(len(cards)):
                try:
                    card = page.locator('a[class*="MotionLinkstyles"], .latam-category-card').nth(i)
                    print(f"[{i + 1}/{len(cards)}] Abrindo Nível 2 (Categoria)...")
                    card.click(timeout=10000)
                    page.wait_for_load_state("domcontentloaded")
                    page.wait_for_timeout(3000)

                    subcategorias = page.locator(
                        'a:has-text("Ver artigos"), a[href*="/perguntas/"]:not([href$="/perguntas/"])').all()

                    sub_urls = []
                    for sub in subcategorias:
                        href = sub.get_attribute("href")
                        if href and "/perguntas/" in href:
                            sub_urls.append(href if href.startswith("http") else f"https://www.latamairlines.com{href}")

                    sub_urls = list(set(sub_urls))
                    print(f"Encontradas {len(sub_urls)} subcategorias. Explorando Nível 3...")

                    for sub_url in sub_urls:
                        try:
                            page.goto(sub_url, wait_until="domcontentloaded", timeout=30000)
                            page.wait_for_timeout(2000)

                            try:
                                ver_mais = page.locator(
                                    'button:has-text("Ver mais"), button:has-text("Ver todos"), button:has-text("Conferir benefícios")').all()
                                for btn in ver_mais: btn.click(timeout=2000)
                            except:
                                pass

                            links_finais = page.evaluate("""
                                () => {
                                    const base1 = "https://www.latamairlines.com/br/pt/central-ajuda";
                                    const base2 = "https://latampass.latam.com/pt_br/clube";
                                    return Array.from(document.querySelectorAll('a'))
                                        .map(a => a.href)
                                        .filter(href => {
                                            const h = href.toLowerCase();
                                            return (h.startsWith(base1) && h.split('/').length >= 9) || 
                                                   (h.startsWith(base2) && h.split('/').length >= 6);
                                        });
                                }
                            """)
                            for l in links_finais: urls_coletadas.add(l)
                        except:
                            continue
                    page.goto(url_principal, wait_until="domcontentloaded")
                except:
                    continue
            lista_final = sorted(list(urls_coletadas))
            print(f"\nTotal: {len(lista_final)} artigos finais (Nível 4) encontrados.")

            for i, url in enumerate(lista_final):
                try:
                    slug = url.replace("https://", "").replace("www.", "").replace("/", "-").replace(".", "-").replace(
                        "?", "-").strip("-")
                    if len(slug) > 150: slug = slug[:150]

                    caminho_file = os.path.join(pasta_abs, f"{slug}.md")

                    if not os.path.exists(caminho_file):
                        print(f"[{i + 1}/{len(lista_final)}] Baixando conteúdo: {slug}")
                        page.goto(url, wait_until="domcontentloaded", timeout=45000)
                        try:
                            page.wait_for_selector("main, article, #content, .content", timeout=5000)
                            html_main = page.inner_html("main") or page.inner_html("article") or page.inner_html("#content")
                        except:
                            html_main = page.inner_html("body")

                        texto_md = md(html_main, strip=['script', 'style', 'nav', 'footer', 'header', 'button'])
                        with open(caminho_file, "w", encoding="utf-8") as f:
                            f.write(f"FONTE: {url}\n\n{texto_md}")
                except Exception as e:
                    print(f"Erro em {url}: {e}")

        except Exception as e:
            print(f"Erro fatal: {e}")
        finally:
            browser.close()

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
        url_principal="https://www.latamairlines.com/br/pt/central-ajuda",
        pasta_destino="../latam_arquivos_md",
        urls_especificas=meus_links_extras
    )