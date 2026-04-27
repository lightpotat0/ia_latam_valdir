from playwright.sync_api import sync_playwright
import os
#session storage

def baixar_biscoitos():
    with sync_playwright() as p:
        caminho_chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        browser = p.chromium.launch(executable_path=caminho_chrome, headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.latamairlines.com/br/pt/central-ajuda")

        page.wait_for_timeout(10000)

        context.storage_state(path="state.json")
        browser.close()

baixar_biscoitos()

def baixar_pdf(url, output_dir):
    os.makedirs(os.path.dirname(output_dir), exist_ok=True)

    with sync_playwright() as p:
        caminho_chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

        browser = p.chromium.launch(executable_path=caminho_chrome, headless=True)
        if os.path.exists("state.json"):
            context = browser.new_context(storage_state="state.json")
        else:
            context = browser.new_context()
        page = context.new_page()

        print(f"Acessando: {url}...")
        page.goto(url, wait_until="networkidle", timeout=90000)

        page.wait_for_timeout(3000)

        print("Gerando PDF...")
        page.pdf(
            path=output_dir,
            print_background=True,
            format="A4"
        )
        print(f"Sucesso! Salvo como {output_dir}")
        browser.close()

baixar_pdf("https://www.latamairlines.com/br/pt/central-ajuda", "../latam_arquives/teste_latam.pdf")