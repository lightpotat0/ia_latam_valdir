import json
import os

with open('cabines.json', "r", encoding="utf-8") as f:
    cabines = json.load(f)

def calculo(cabine, trechos):
    table = tabelas.get(cabine)
    milhas = 0
    detalhes = []

    try:
        for origem, destino in trechos:
            conta = table[origem][destino]
            milhas += conta
            detalhes.append(f"{origem} para {destino}: {conta:,} milhas")
        resultado = "\n".join(detalhes)
        return f"Resumo da viagem na cabine {cabine}:\n{resultado}\nTOTAL: {milhas:,} milhas"

    except KeyError as e:
        return f"Erro: Uma das rotas ({e}) não existe na tabela {cabine}."

tabelas = {
    "Primeira Classe": cabines.get("tabela_fixa_first"),
    "Classe Executiva": cabines.get("tabela_fixa_executive"),
    "Premium Economy": cabines.get("tabela_fixa_ecopremium"),
    "Class Economy": cabines.get("tabela_fixa_economy")
}

trechos_viagem = [
    ("Oceania", "Europa"),
    ("Europa", "Oriente Médio")
]

result = calculo("Class Economy", trechos_viagem)
print(result)