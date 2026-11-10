import csv
import os
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(os.getenv("LOG_FILE", Path(__file__).resolve().parent / "feedback.csv"))


def salvar_falas(pergunta, resposta, fontes):
    """Registra cada conversa em CSV. Só isso: a lógica de resposta fica em main.py."""
    novo = not LOG_FILE.is_file()
    with open(LOG_FILE, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if novo:
            writer.writerow(["Data", "Pergunta", "Resposta", "Fontes"])
        writer.writerow([
            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            pergunta,
            resposta.replace("\n", " "),
            ", ".join(fontes),
        ])