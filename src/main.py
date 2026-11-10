import math
import os
import re
import unicodedata
from collections import Counter
from itertools import zip_longest
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

from dados_user import salvar_falas

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
CHROMA_DIR = os.getenv("CHROMA_DIR", str(BASE_DIR / "chroma_db"))
# multilíngue: o all-MiniLM-L6-v2 é treinado só em inglês e busca mal em português
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

NAO_ENCONTREI = "Não encontrei informações sobre isso na base."

SYSTEM = """Você é Valdir, agente virtual da LATAM Airlines e do programa LATAM Pass.
Responda usando o CONTEXTO fornecido, que são trechos das páginas oficiais da LATAM.

REGRAS:
- Leia todo o contexto com atenção: a resposta pode estar espalhada em vários trechos
- Responda com o que o contexto trouxer, mesmo que seja parcial, e diga o que não aparece nele
- Só diga que não encontrou se o contexto realmente não tratar do assunto
- NÃO invente valores, prazos ou regras que não estejam no contexto
- NÃO misture condições de produtos ou planos diferentes (ex.: um clube de milhas e uma categoria Elite) como se fossem a mesma regra
- Se a lista pedida (ex.: benefícios de uma categoria) não aparece no contexto, diga isso em UMA frase e não complete com palpites
- Não comente sobre "o trecho" ou "o contexto" além disso; vá direto ao conteúdo
- Responda em português, de forma clara, em tópicos quando ajudar
- Seu mestre é Danillo Vaz"""

SAUDACOES = {"oi", "olá", "ola", "bom dia", "boa tarde", "boa noite", "e aí", "eae", "hello", "hi", "oie"}
RESPOSTA_SAUDACAO = (
    "Olá! Sou o Valdir, assistente da LATAM. Pergunte sobre LATAM Pass, milhas, "
    "bagagem, check-in ou regras de resgate."
)

_embeddings = None
_vectorstore = None
_retriever = None
_llm = None
_kw = {"n": -1}


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    return _embeddings


def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        # precisa do MESMO embedding usado na hora de gravar (site_leitor.py)
        _vectorstore = Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=get_embeddings(),
        )
    return _vectorstore


def get_retriever():
    global _retriever
    if _retriever is None:
        # similaridade simples: o MMR troca trechos relevantes por "diferentes" e pode perder a resposta
        _retriever = get_vectorstore().as_retriever(
            search_type="similarity",
            search_kwargs={"k": 8},
        )
    return _retriever


# ------------------------------------------------ busca por palavras-chave (BM25 simples)
# A busca por significado erra nomes próprios ("Gold", "Black Signature"); esta pega a palavra exata.
STOP = {
    "que", "qual", "quais", "como", "para", "por", "com", "uma", "uns", "umas", "das", "dos", "nas",
    "nos", "sao", "ser", "tem", "sobre", "mais", "muito", "ao", "aos", "da", "do", "na", "no", "em",
    "de", "um", "os", "as", "ou", "se", "me", "meu", "minha", "pode", "posso", "quero", "voce",
}


def _tokens(texto):
    t = unicodedata.normalize("NFD", texto.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return [w for w in re.findall(r"[a-z0-9]+", t) if len(w) > 2 and w not in STOP]


def _indice():
    """Carrega todos os trechos do banco (recarrega sozinho se o banco for reindexado)."""
    vs = get_vectorstore()
    n = vs._collection.count()
    if _kw["n"] != n:
        dados = vs.get(include=["documents", "metadatas"])
        docs = dados["documents"] or []
        tfs = [Counter(_tokens(d)) for d in docs]
        df = Counter()
        for tf in tfs:
            df.update(tf.keys())
        dls = [sum(tf.values()) for tf in tfs]
        _kw.update(
            n=n, docs=docs, metas=dados["metadatas"] or [], tfs=tfs, df=df, dls=dls,
            avgdl=(sum(dls) / len(dls)) if dls else 1,
        )
    return _kw


def busca_palavras(consulta, k=6):
    ind = _indice()
    termos = set(_tokens(consulta))
    total = len(ind["docs"])
    if not termos or not total:
        return []
    pontuacoes = []
    for i, tf in enumerate(ind["tfs"]):
        pontos = 0.0
        for t in termos:
            f = tf.get(t, 0)
            if f:
                d = ind["df"][t]
                idf = math.log(1 + (total - d + 0.5) / (d + 0.5))
                pontos += idf * f * 2.5 / (f + 1.5 * (0.25 + 0.75 * ind["dls"][i] / ind["avgdl"]))
        if pontos > 0:
            pontuacoes.append((pontos, i))
    pontuacoes.sort(reverse=True)
    return [Document(page_content=ind["docs"][i], metadata=ind["metas"][i]) for _, i in pontuacoes[:k]]


def buscar(consulta, limite=10):
    """Mistura busca por significado e por palavra, intercalando os resultados."""
    por_significado = get_retriever().invoke(consulta)
    por_palavra = busca_palavras(consulta, 6)
    vistos, resultado = set(), []
    for par in zip_longest(por_significado, por_palavra):
        for doc in par:
            if doc is None:
                continue
            chave = doc.page_content[:200]
            if chave not in vistos:
                vistos.add(chave)
                resultado.append(doc)
    return resultado[:limite]


def get_llm():
    global _llm
    if _llm is None:
        chave = os.getenv("GROQ_API_KEY")
        if not chave:
            raise RuntimeError("GROQ_API_KEY não configurada.")
        _llm = ChatGroq(api_key=chave, model=GROQ_MODEL, temperature=0)
    return _llm


def responder(pergunta, historico=None):
    """Retorna {"resposta": str, "fontes": [urls]}.
    historico: lista de {"role": "user"|"assistant", "content": str}."""
    pergunta = pergunta.strip()
    historico = historico or []

    if pergunta.lower().strip(" !.?,") in SAUDACOES:
        return {"resposta": RESPOSTA_SAUDACAO, "fontes": []}

    # só perguntas curtas de continuação ("e na executiva?") usam a pergunta anterior na busca
    consulta = pergunta
    ultimas_do_usuario = [m["content"] for m in historico if m["role"] == "user"]
    if ultimas_do_usuario and len(pergunta.split()) <= 4:
        consulta = f"{ultimas_do_usuario[-1]} {pergunta}"

    docs = buscar(consulta)
    if not docs:
        return {"resposta": NAO_ENCONTREI, "fontes": []}

    contexto = "\n\n".join(doc.page_content[:1500] for doc in docs)

    if os.getenv("DEBUG_RAG"):
        print("\n===== CONTEXTO ENVIADO AO MODELO =====")
        for doc in docs:
            print("--", doc.metadata.get("url"), "\n", doc.page_content[:400].replace("\n", " "), "\n")
    fontes = []
    for doc in docs:
        url = doc.metadata.get("url") or doc.metadata.get("source")
        if url and url not in fontes:
            fontes.append(url)

    mensagens = [("system", SYSTEM)]
    for m in historico[-6:]:
        mensagens.append(("human" if m["role"] == "user" else "ai", m["content"]))
    mensagens.append(("human", f"CONTEXTO:\n{contexto}\n\nPERGUNTA:\n{pergunta}"))

    resposta = get_llm().invoke(mensagens).content

    try:
        salvar_falas(pergunta, resposta, fontes)
    except Exception as e:  # log nunca deve derrubar o chat
        print("Falha ao salvar log:", e)

    return {"resposta": resposta, "fontes": fontes[:4]}


# ---------------------------------------------------------------- macros de atendimento
MACRO_SYSTEM = """Você é Valdir, assistente de atendimento da LATAM Airlines.
Sua tarefa é escrever uma MACRO: uma resposta pronta que o atendente vai copiar e enviar ao cliente.

REGRAS:
- Baseie o conteúdo APENAS no CONTEXTO; não invente valores, prazos, taxas ou regras
- Onde faltar informação no contexto, escreva [CONFIRMAR: o que falta] no ponto exato, para o atendente completar
- Estrutura: saudação, resposta direta ao problema, passos numerados quando houver procedimento, encerramento cordial
- Use o nome do cliente informado; se vier [NOME], mantenha [NOME] para o atendente preencher
- Siga o canal e o tom pedidos
- Escreva em português do Brasil
- Entregue SOMENTE a macro, sem explicações para o atendente antes ou depois"""

CANAIS = {
    "email": "E-mail (começa com uma linha 'Assunto: ...', texto organizado e completo)",
    "chat": "Chat (curto: 2 a 5 frases, direto ao ponto)",
    "whatsapp": "WhatsApp (curto, amigável, sem formalidade excessiva)",
}
TONS = {
    "cordial": "cordial e acolhedor",
    "formal": "formal e institucional",
    "direto": "direto e objetivo",
}


def gerar_macro(situacao, canal="email", tom="cordial", nome_cliente=None):
    """Retorna {"macro": str, "fontes": [urls]} com uma resposta pronta para o atendente."""
    situacao = situacao.strip()
    docs = buscar(situacao)

    contexto = "\n\n".join(doc.page_content[:1500] for doc in docs) or "(nenhum trecho encontrado na base)"
    fontes = []
    for doc in docs:
        url = doc.metadata.get("url") or doc.metadata.get("source")
        if url and url not in fontes:
            fontes.append(url)

    nome = (nome_cliente or "").strip() or "[NOME]"
    pedido = (
        f"CONTEXTO:\n{contexto}\n\n"
        f"SITUAÇÃO DO CLIENTE:\n{situacao}\n\n"
        f"CANAL: {CANAIS.get(canal, CANAIS['email'])}\n"
        f"TOM: {TONS.get(tom, TONS['cordial'])}\n"
        f"NOME DO CLIENTE: {nome}\n\n"
        "Escreva a macro."
    )
    macro = get_llm().invoke([("system", MACRO_SYSTEM), ("human", pedido)]).content
    return {"macro": macro.strip(), "fontes": fontes[:4]}