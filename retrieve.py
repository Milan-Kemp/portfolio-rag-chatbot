"""Retrieve step of the RAG pipeline.

    question  ->  query embedding  ->  top-k nearest chunks from ChromaDB

Usage
-----
    python retrieve.py "how did Milan solve the Adzuna rate limit"

`answer.py` (later step) calls `retrieve()` and passes the hits to Claude.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass

import chromadb
import voyageai

from config import COLLECTION_NAME, DB_DIR, EMBED_MODEL, TOP_K, VOYAGE_API_KEY


@dataclass
class Hit:
    text: str
    source: str
    breadcrumb: str
    score: float  # cosine similarity in [-1, 1]; higher = more relevant


def _collection():
    client = chromadb.PersistentClient(path=str(DB_DIR))
    return client.get_or_create_collection(
        COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )


def retrieve(question: str, k: int = TOP_K) -> list[Hit]:
    if not VOYAGE_API_KEY:
        raise RuntimeError("VOYAGE_API_KEY is not set (see .env.example).")

    col = _collection()
    if col.count() == 0:
        raise RuntimeError(
            "The vector store is empty. Run `python ingest.py` first."
        )

    vo = voyageai.Client(api_key=VOYAGE_API_KEY)
    # input_type="query" tells Voyage to embed this as a search query, not a
    # document. It measurably improves retrieval vs. embedding both the same way.
    q_emb = vo.embed([question], model=EMBED_MODEL, input_type="query").embeddings[0]

    res = col.query(query_embeddings=[q_emb], n_results=k)
    hits: list[Hit] = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        hits.append(
            Hit(
                text=doc,
                source=str(meta.get("source", "?")),
                breadcrumb=str(meta.get("breadcrumb", "")),
                score=1.0 - float(dist),  # chroma returns cosine distance
            )
        )
    return hits


def _main() -> int:
    # Windows consoles default to cp1252 and mangle accented characters
    # (ë, é, ï) on print. Force UTF-8 for CLI output.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    if len(sys.argv) < 2:
        print('usage: python retrieve.py "your question"', file=sys.stderr)
        return 1
    question = " ".join(sys.argv[1:])
    hits = retrieve(question)
    if not hits:
        print("No chunks returned.")
        return 0
    for i, h in enumerate(hits, 1):
        loc = f"{h.source}" + (f"  ({h.breadcrumb})" if h.breadcrumb else "")
        print(f"\n--- {i}. {loc}   score={h.score:.3f} ---")
        preview = h.text if len(h.text) <= 700 else h.text[:700] + " …"
        print(preview)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
