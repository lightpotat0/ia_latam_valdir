import json
from pathlib import Path

CABINES_PATH = Path(__file__).resolve().parent / "cabines.json"

_CHAVES = {
    "Primeira Classe": "tabela_fixa_first",
    "Classe Executiva": "tabela_fixa_executive",
    "Premium Economy": "tabela_fixa_ecopremium",
    "Classe Econômica": "tabela_fixa_economy",
}

_tabelas = None


def _carregar():
    global _tabelas
    if _tabelas is None:
        with open(CABINES_PATH, "r", encoding="utf-8") as f:
            dados = json.load(f)
        _tabelas = {nome: dados.get(chave) or {} for nome, chave in _CHAVES.items()}
    return _tabelas


def opcoes():
    """{cabine: {origem: [destinos]}} para a interface montar os seletores."""
    return {
        cabine: {origem: sorted(destinos) for origem, destinos in tabela.items()}
        for cabine, tabela in _carregar().items()
        if tabela
    }


def calcular(cabine, trechos):
    """trechos: lista de (origem, destino). Levanta ValueError se algo não existir."""
    tabela = _carregar().get(cabine)
    if not tabela:
        raise ValueError(f"Cabine '{cabine}' não encontrada.")
    if not trechos:
        raise ValueError("Informe pelo menos um trecho.")

    detalhes, total = [], 0
    for origem, destino in trechos:
        try:
            milhas = tabela[origem][destino]
        except KeyError:
            raise ValueError(f"A rota {origem} → {destino} não existe na tabela {cabine}.")
        total += milhas
        detalhes.append({"origem": origem, "destino": destino, "milhas": milhas})
    return {"cabine": cabine, "detalhes": detalhes, "total": total}


def calculo(cabine, trechos):
    """Versão em texto, igual à sua função original."""
    try:
        r = calcular(cabine, trechos)
    except ValueError as e:
        return f"Erro: {e}"
    linhas = [f"{d['origem']} para {d['destino']}: {d['milhas']:,} milhas" for d in r["detalhes"]]
    return f"Resumo da viagem na cabine {cabine}:\n" + "\n".join(linhas) + f"\nTOTAL: {r['total']:,} milhas"


if __name__ == "__main__":
    print(calculo("Classe Econômica", [("Oceania", "Europa"), ("Europa", "Oriente Médio")]))