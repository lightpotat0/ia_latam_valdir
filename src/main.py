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

SYSTEM = """Você é Valdir, assistente virtual da LATAM Airlines e do programa LATAM Pass.
Converse de forma natural, simpática e clara, como um assistente de IA completo: explique, não apenas copie trechos.

COMO RESPONDER:
- A cada pergunta você recebe trechos de páginas oficiais da LATAM (CONTEXTO). Use-os como fonte principal para regras, prazos, valores, benefícios e procedimentos da LATAM, explicando com suas próprias palavras
- Explique, resuma, compare e dê exemplos; organize em tópicos quando ajudar e, quando fizer sentido, ofereça um próximo passo ou pergunte se a pessoa quer detalhar algo
- Perguntas simples, conceitos gerais (o que são milhas, como funciona overbooking, dicas de viagem) e conversa comum: responda normalmente, sem depender do contexto
- Se o contexto não trouxer o detalhe específico da LATAM que a pessoa pediu, NÃO pare em "não encontrei": explique o que o contexto traz sobre o tema, complemente com conhecimento geral e deixe claro, em uma frase, que aquela parte é uma visão geral e não veio das páginas da LATAM, sugerindo confirmar no site oficial
- Nunca apresente números, valores, prazos ou nomes de benefícios inventados como se fossem regra oficial da LATAM; se não tiver certeza, diga que varia e indique onde confirmar
- Não misture regras de produtos diferentes (ex.: clubes de milhas e categorias Elite)
- Responda em português do Brasil, no tamanho que a pergunta pede: curto para perguntas simples, completo para as complexas
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
        _llm = ChatGroq(api_key=chave, model=GROQ_MODEL, temperature=0.3)
    return _llm


def reformular(pergunta, historico):
    """Transforma 'quais os benefícios de cada?' em uma pergunta completa, usando a conversa."""
    if not historico:
        return pergunta
    conversa = "\n".join(
        f"{'Cliente' if m['role'] == 'user' else 'Valdir'}: {m['content'][:300]}" for m in historico[-4:]
    )
    try:
        r = get_llm().invoke([
            ("system", "Reescreva a ÚLTIMA pergunta do cliente como uma pergunta completa e independente, "
                       "incluindo o assunto citado antes na conversa. Responda SOMENTE com a pergunta "
                       "reescrita, em português."),
            ("human", f"{conversa}\n\nÚLTIMA PERGUNTA: {pergunta}"),
        ]).content.strip()
        return r if 3 < len(r) < 400 else pergunta
    except Exception:
        return pergunta


def responder(pergunta, historico=None):
    """Retorna {"resposta": str, "fontes": [urls]}.
    historico: lista de {"role": "user"|"assistant", "content": str}."""
    pergunta = pergunta.strip()
    historico = historico or []

    if pergunta.lower().strip(" !.?,") in SAUDACOES:
        return {"resposta": RESPOSTA_SAUDACAO, "fontes": []}

    # perguntas de continuação ("e de cada uma?") ganham o assunto da conversa antes de buscar
    consulta = reformular(pergunta, historico)

    docs = buscar(consulta)
    # sem trechos na base, o Valdir ainda responde (conhecimento geral), avisando que não veio da LATAM
    contexto = "\n\n".join(doc.page_content[:1500] for doc in docs) or "(nenhum trecho encontrado na base)"

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