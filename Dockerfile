FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    ANONYMIZED_TELEMETRY=False \
    TIKTOKEN_CACHE_DIR=/opt/tiktoken

WORKDIR /app

# Dependencies first, so this layer is cached until requirements.txt changes.
# tiktoken normally downloads its encoding on first use; fetch it at build
# time so `ingest.py` also works inside the container without surprises.
COPY requirements.txt .
RUN pip install -r requirements.txt \
 && (python -c "import tiktoken; tiktoken.get_encoding('cl100k_base')" || true)

# App code + content/ + storage/ (existing ChromaDB data). Secrets are NOT
# copied: .dockerignore excludes .env, and compose injects it at runtime.
RUN useradd --create-home --uid 1000 app
COPY --chown=app:app . .
RUN mkdir -p storage/chroma && chown -R app:app storage
USER app

EXPOSE 8000

# One worker: ChromaDB + the SDKs are memory-hungry and the target box is small.
# --proxy-headers lets the API see the real client IP behind Caddy (needed for
# rate limiting). Port 8000 is never published, only Caddy can reach it.
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]
