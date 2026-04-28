import schedule
import time
import os
import shutil
from site_leitor import pote_de_biscoitos, mapeamento

def atualizar_base_latam():
    try:
        pote_de_biscoitos()
        mapeamento("https://www.latamairlines.com/br/pt/central-ajuda", "../latam_arquivos_md")
        caminho_faiss = "faiss_index_latam"
        if os.path.exists(caminho_faiss):
            shutil.rmtree(caminho_faiss)
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] ❌ Erro na atualização: {e}")
schedule.every().sunday.at("02:00").do(atualizar_base_latam)

while True:
    schedule.run_pending()
    time.sleep(60)