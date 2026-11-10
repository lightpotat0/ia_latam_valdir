FROM python:3.11-slim
WORKDIR /app

# torch só CPU (bem menor)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# baixa o modelo de embeddings já no build
RUN python -c "from langchain_huggingface import HuggingFaceEmbeddings; HuggingFaceEmbeddings(model_name='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"

COPY main.py api.py dados_user.py tabela_fixa.py cabines.json ./
COPY latam-chat ./latam-chat
COPY chroma_db ./chroma_db

ENV PORT=7860
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT}"]