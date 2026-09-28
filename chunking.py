"""Markdown-aware chunking.

Why not just split every N characters? Because a chunk that starts in the
middle of one topic and ends in the middle of another embeds as a blurry
average of both, which hurts retrieval. So:

1. Split the document on Markdown headings. Each section carries a
   "breadcrumb" (e.g. ``Adzuna integration > Rate limiting``) so a chunk
   always knows which project/section it came from.
2. Inside a section, pack paragraphs together up to CHUNK_TARGET_TOKENS.
3. Carry CHUNK_OVERLAP_TOKENS of text from the end of one chunk into the
   start of the next, so a sentence split across a boundary still lands
   whole in at least one chunk.
4. A single oversized paragraph is hard-split on sentence boundaries.

The breadcrumb is prepended to the chunk text before embedding and storage,
so both the vector and the answer step see that context.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from config import CHUNK_MAX_TOKENS, CHUNK_OVERLAP_TOKENS, CHUNK_TARGET_TOKENS
from tokenizer import count_tokens, tail_by_tokens

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


@dataclass
class Chunk:
    text: str          # breadcrumb + body, this is what gets embedded/stored
    source: str         # path relative to content/, e.g. "adzuna.md"
    breadcrumb: str     # heading path within the file
    index: int          # 0-based position within the file


def _iter_sections(md: str):
    """Yield ``(breadcrumb, body)`` for each heading section in the file."""
    stack: list[tuple[int, str]] = []  # (heading level, title)
    buf: list[str] = []
    breadcrumb = ""

    def flush():
        body = "\n".join(buf).strip()
        if body:
            return breadcrumb, body
        return None

    for line in md.splitlines():
        m = _HEADING_RE.match(line)
        if not m:
            buf.append(line)
            continue
        out = flush()
        if out:
            yield out
        buf.clear()
        level = len(m.group(1))
        title = m.group(2).strip()
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, title))
        breadcrumb = " > ".join(t for _, t in stack)

    out = flush()
    if out:
        yield out


def _paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def _hard_split(paragraph: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    out: list[str] = []
    cur: list[str] = []
    cur_tokens = 0
    for s in sentences:
        st = count_tokens(s)
        if cur and cur_tokens + st > CHUNK_TARGET_TOKENS:
            out.append(" ".join(cur))
            cur, cur_tokens = [], 0
        cur.append(s)
        cur_tokens += st
    if cur:
        out.append(" ".join(cur))
    return out


def _pack(paragraphs: list[str]) -> list[str]:
    chunks: list[str] = []
    cur: list[str] = []
    cur_tokens = 0

    def flush():
        nonlocal cur, cur_tokens
        if cur:
            chunks.append("\n\n".join(cur))
        cur, cur_tokens = [], 0

    for p in paragraphs:
        pt = count_tokens(p)
        if pt > CHUNK_MAX_TOKENS:
            flush()
            chunks.extend(_hard_split(p))
            continue
        if cur and cur_tokens + pt > CHUNK_TARGET_TOKENS:
            prev = "\n\n".join(cur)
            flush()
            overlap = tail_by_tokens(prev, CHUNK_OVERLAP_TOKENS).strip()
            if overlap:
                cur.append(overlap)
                cur_tokens += count_tokens(overlap)
        cur.append(p)
        cur_tokens += pt
    flush()
    return chunks


def chunk_markdown(md: str, source: str) -> list[Chunk]:
    chunks: list[Chunk] = []
    for breadcrumb, body in _iter_sections(md):
        for piece in _pack(_paragraphs(body)):
            text = f"{breadcrumb}\n\n{piece}" if breadcrumb else piece
            chunks.append(
                Chunk(text=text, source=source, breadcrumb=breadcrumb, index=len(chunks))
            )
    return chunks
