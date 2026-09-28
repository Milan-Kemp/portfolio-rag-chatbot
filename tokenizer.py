"""Token counting for chunk sizing.

Voyage and Claude each tokenize slightly differently, but for *sizing* chunks
we only need a stable, consistent count. tiktoken's cl100k_base is a good
proxy and is what most RAG tutorials use. If tiktoken can't load (e.g. no
network on first run to fetch the encoding), we fall back to a rough
chars/4 heuristic so ingestion never hard-crashes on this.
"""
from __future__ import annotations

_enc = None
try:  # pragma: no cover - depends on environment
    import tiktoken

    _enc = tiktoken.get_encoding("cl100k_base")
except Exception:  # noqa: BLE001 - any failure -> heuristic
    _enc = None


def count_tokens(text: str) -> int:
    if _enc is not None:
        return len(_enc.encode(text))
    return max(1, len(text) // 4)


def tail_by_tokens(text: str, n_tokens: int) -> str:
    """Return roughly the last ``n_tokens`` tokens of ``text`` (used for
    overlap between consecutive chunks)."""
    if n_tokens <= 0:
        return ""
    if _enc is not None:
        toks = _enc.encode(text)
        if len(toks) <= n_tokens:
            return text
        return _enc.decode(toks[-n_tokens:])
    approx_chars = n_tokens * 4
    return text[-approx_chars:] if len(text) > approx_chars else text
