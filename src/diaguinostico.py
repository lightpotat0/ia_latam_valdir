"""Uso (dentro de src/):  python diagnostico.py "Como transfiro milhas para outra pessoa?"

1) mostra quantos .md foram salvos e o começo do arquivo da página de transferir
2) mostra os trechos que a busca entrega ao modelo
"""
import glob
import os
import sys

from main import buscar

pergunta = " ".join(sys.argv[1:]) or "Como transfiro milhas para outra pessoa?"

arquivos = glob.glob("latam_arquivos_md/*.md")
print(f"\n{len(arquivos)} arquivos .md em latam_arquivos_md\n")

for caminho in arquivos:
    if "acelere-suas-milhas-transferir" in caminho:
        with open(caminho, encoding="utf-8") as f:
            texto = f.read()
        print(f"--- {os.path.basename(caminho)} ({len(texto)} caracteres) ---")
        print(texto[:1500])
        print("--- fim do trecho ---\n")
        break
else:
    print("Arquivo da página de transferir NÃO encontrado em latam_arquivos_md.\n")

print(f"Pergunta: {pergunta}\n")
for i, doc in enumerate(buscar(pergunta), 1):
    print(f"[{i}] {doc.metadata.get('url')}")
    print("    " + doc.page_content[:300].replace("\n", " ") + "\n")