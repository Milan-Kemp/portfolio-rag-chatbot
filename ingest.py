"""Ingest step of the RAG pipeline.

    content/*.md  ->  chunks  ->  Voyage embeddings  ->  local ChromaDB

Usage
-----
    python ingest.py            # incremental: only re-embeds new/changed chunks
    python ingest.py --reset    # wipe the vector store AND the cache, rebuild

Cost note: embeddings are a paid API call. The default run caches every
embedding by a hash of its chunk text, so re-running after editing one file
only pays for the chunks that actually changed. `--reset` clears the cache
and therefore re-embeds everything.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time

import chromadb
import voyageai

from chunking import chunk_markdown
from config import (
    CACHE_PATH,
    COLLECTION_NAME,
    CONTENT_DIR,
    DB_DIR,
    EMBED_MODEL,
    VOYAGE_API_KEY,
)

_BATCH = 100  # Voyage accepts up to 128 inputs per call
_TEXT_EXTS = {".md", ".markdown", ".txt"}  # files in content/ we ingest


def _load_cache() -> dict[str, list[float]]:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def _save_cache(cache: dict[str, list[float]]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache), encoding="utf-8")


def _key(text: str) -> str:
    """Cache key: model + chunk text. Changing the model invalidates cleanly."""
    return hashlib.sha256(f"{EMBED_MODEL}\x00{text}".encode()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--reset",
        action="store_true",
        help="wipe the vector store and embedding cache, then rebuild from scratch",
    )
    args = ap.parse_args()

    if not VOYAGE_API_KEY:
        print(
            "VOYAGE_API_KEY is not set. Copy .env.example to .env and fill it in.",
            file=sys.stderr,
        )
        return 1

    files = sorted(
        p
        for p in CONTENT_DIR.glob("**/*")
        if p.is_file()
        and p.suffix.lower() in _TEXT_EXTS
        and not p.name.startswith("_")
    )
    if not files:
        print(
            f"No .md / .txt files found in {CONTENT_DIR}\\. "
            "Add your case studies, READMEs and specs there first.\n"
            "(Files whose name starts with '_' are ignored, so you can keep notes there.)",
            file=sys.stderr,
        )
        return 1

    # 1. chunk every file
    all_chunks = []
    for path in files:
        rel = path.relative_to(CONTENT_DIR).as_posix()
        file_chunks = chunk_markdown(path.read_text(encoding="utf-8"), source=rel)
        all_chunks.extend(file_chunks)
        note = "  <- empty or unreadable, skipped" if not file_chunks else ""
        print(f"  {rel}: {len(file_chunks)} chunks{note}")
    print(f"{len(all_chunks)} chunks from {len(files)} file(s)")

    if not all_chunks:
        print("Files contained no usable text.", file=sys.stderr)
        return 1

    # 2. embed, reusing the cache
    cache = {} if args.reset else _load_cache()
    todo = [c for c in all_chunks if _key(c.text) not in cache]
    print(
        f"{len(todo)} chunk(s) need embedding, "
        f"{len(all_chunks) - len(todo)} reused from cache"
    )

    if todo:
        vo = voyageai.Client(api_key=VOYAGE_API_KEY)
        for i in range(0, len(todo), _BATCH):
            batch = todo[i : i + _BATCH]
            resp = vo.embed(
                [c.text for c in batch], model=EMBED_MODEL, input_type="document"
            )
            for chunk, emb in zip(batch, resp.embeddings):
                cache[_key(chunk.text)] = list(emb)
            print(f"  embedded {min(i + _BATCH, len(todo))}/{len(todo)}")
            time.sleep(0.1)
        _save_cache(cache)

    # 3. (re)write the collection
    client = chromadb.PersistentClient(path=str(DB_DIR))
    if args.reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:  # noqa: BLE001 - fine if it didn't exist
            pass
    col = client.get_or_create_collection(
        COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )

    # Small corpus: simplest correct approach is to replace all rows.
    existing = col.get()
    if existing["ids"]:
        col.delete(ids=existing["ids"])

    col.add(
        ids=[f"{c.source}::{c.index}" for c in all_chunks],
        documents=[c.text for c in all_chunks],
        embeddings=[cache[_key(c.text)] for c in all_chunks],
        metadatas=[
            {"source": c.source, "breadcrumb": c.breadcrumb, "chunk_index": c.index}
            for c in all_chunks
        ],
    )
    print(f"Wrote {len(all_chunks)} chunks to {DB_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
