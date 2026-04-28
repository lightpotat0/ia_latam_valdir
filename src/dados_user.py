import csv
from datetime import datetime

from huggingface_hub import file_exists


def salvar_falas(pergunta, resposta, fontes):
    log_file = "feedback"
    file_exists = os.path.isfile(log_file)

    with open(log_file, 'a', encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Data", "Pergunta", "Resposta", "Fontes"])

        writer.writerow([
            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            pergunta,
            resposta.replace("\n", " "),
            ", ".join(fontes),
        ])

def responder(pergunta):
    docs_import = retriever.invoke(pergunta)
    contexto = ""
    fontes = set()
    for doc in docs_import:
        contexto += doc.page_content + "\n\n"
