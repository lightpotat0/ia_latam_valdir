
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m playwright install --with-deps chromium

RUN python -c "from langchain_huggingface import HuggingFaceEmbeddings; HuggingFaceEmbeddings(model_name='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"

COPY . .

ENV PORT=10000

CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT}"]
