import time

import schedule

from site_leitor import (
    PASTA_MD, URL_AJUDA, LINKS_EXTRAS,
    pote_de_biscoitos, mapeamento, enviar_para_chroma,
)


def atualizar_base_latam():
    try:
        print(f"[{time.strftime('%H:%M:%S')}] Atualizando base da LATAM...")
        pote_de_biscoitos()
        mapeamento(URL_AJUDA, PASTA_MD, LINKS_EXTRAS, sobrescrever=True)
        enviar_para_chroma(PASTA_MD)
        print(f"[{time.strftime('%H:%M:%S')}] Base atualizada.")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Erro na atualização: {e}")


schedule.every().sunday.at("02:00").do(atualizar_base_latam)

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(60)