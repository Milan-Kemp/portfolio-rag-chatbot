"""Central configuration. Everything reads from here so there is one place
to change model names, paths and chunk sizes.

Secrets come from environment variables (loaded from a local .env file).
Never hard-code API keys here.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- paths ---
ROOT = Path(__file__).parent
CONTENT_DIR = ROOT / "content"
STORAGE_DIR = ROOT / "storage"
DB_DIR = STORAGE_DIR / "chroma"
CACHE_PATH = STORAGE_DIR / "embedding_cache.json"
COLLECTION_NAME = "portfolio"

# --- secrets ---
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# --- models ---
EMBED_MODEL = os.getenv("EMBED_MODEL", "voyage-3.5")
# Claude model that writes the final answer. Default is the most capable
# tier; for a public widget you can drop to "claude-sonnet-5" (≈2.5x cheaper
# output, fine for grounded Q&A) by setting ANSWER_MODEL in .env.
ANSWER_MODEL = os.getenv("ANSWER_MODEL", "claude-opus-5")
ANSWER_MAX_TOKENS = int(os.getenv("ANSWER_MAX_TOKENS", "1024"))

# --- chunking (tokens) ---
CHUNK_TARGET_TOKENS = int(os.getenv("CHUNK_TARGET_TOKENS", "400"))
CHUNK_MAX_TOKENS = int(os.getenv("CHUNK_MAX_TOKENS", "500"))
CHUNK_OVERLAP_TOKENS = int(os.getenv("CHUNK_OVERLAP_TOKENS", "80"))

# --- retrieval ---
TOP_K = int(os.getenv("TOP_K", "4"))

# --- rate limiting (public /ask endpoint) ---
# Per visitor (IP address), plus one global daily cap so the total Claude
# spend has a hard ceiling even if someone rotates IPs.
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "5"))
RATE_LIMIT_PER_DAY = int(os.getenv("RATE_LIMIT_PER_DAY", "50"))
RATE_LIMIT_GLOBAL_PER_DAY = int(os.getenv("RATE_LIMIT_GLOBAL_PER_DAY", "300"))

# --- API / widget ---
# Comma-separated list of origins allowed to call the API from a browser.
# Must include your portfolio's origin. "*" is allowed for quick local tests
# but don't ship it.
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS",
        "https://milan-kemp.github.io,http://localhost:8000,http://127.0.0.1:8000",
    ).split(",")
    if o.strip()
]
