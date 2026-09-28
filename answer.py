"""Generate step of the RAG pipeline.

    question + retrieved chunks  ->  Claude  ->  grounded answer + sources

The whole point of RAG lives in the system prompt here: Claude must answer
*only* from the supplied context and must say so plainly when the context
doesn't cover the question, instead of falling back on general knowledge.

Usage
-----
    python answer.py "hoe loste Milan onderwerpherhaling op"
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field

import anthropic

from config import ANSWER_MAX_TOKENS, ANSWER_MODEL, ANTHROPIC_API_KEY, TOP_K
from retrieve import Hit, retrieve

_SYSTEM = """\
Je bent de assistent op Milans portfolio-site. Je beantwoordt vragen van \
bezoekers over Milans projecten.

Strikte regels:
- Antwoord UITSLUITEND op basis van de tekst in <context>. Gebruik geen \
kennis van buiten die tekst.
- Staat het antwoord niet (of maar deels) in de context, zeg dat dan \
expliciet, bijvoorbeeld: "Daar zeggen Milans projectteksten niets over." \
Verzin niets en vul geen gaten op.
- Verwijs naar je bron met de bestandsnaam tussen vierkante haken, bijv. \
[Job Alert bot.txt]. Meerdere bronnen mag.
- Schrijf beknopt en zakelijk Nederlands, 2-5 zinnen. Geen opsomming tenzij \
de vraag daar echt om vraagt.
- Praat over Milan in de derde persoon ("Milan loste dit op door ...").
"""

_PROMPT = """\
<context>
{context}
</context>

Vraag van de bezoeker: {question}

Beantwoord de vraag volgens de regels. Vergeet de bronvermelding niet."""


@dataclass
class Answer:
    text: str
    question: str
    hits: list[Hit] = field(default_factory=list)

    @property
    def sources(self) -> list[str]:
        """Unique source files behind the retrieved context, in order."""
        seen: list[str] = []
        for h in self.hits:
            if h.source not in seen:
                seen.append(h.source)
        return seen


def _format_context(hits: list[Hit]) -> str:
    blocks = []
    for h in hits:
        header = h.source + (f" — {h.breadcrumb}" if h.breadcrumb else "")
        blocks.append(f"[{header}]\n{h.text}")
    return "\n\n---\n\n".join(blocks)


def answer(question: str, k: int = TOP_K) -> Answer:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY is not set (see .env.example).")

    hits = retrieve(question, k=k)
    if not hits:
        return Answer(
            text="Er staat nog geen content in de kennisbank om dit mee te beantwoorden.",
            question=question,
            hits=[],
        )

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    resp = client.messages.create(
        model=ANSWER_MODEL,
        max_tokens=ANSWER_MAX_TOKENS,
        system=_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": _PROMPT.format(
                    context=_format_context(hits), question=question
                ),
            }
        ],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    return Answer(text=text, question=question, hits=hits)


def _main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    if len(sys.argv) < 2:
        print('usage: python answer.py "your question"', file=sys.stderr)
        return 1

    result = answer(" ".join(sys.argv[1:]))
    print(result.text)
    print("\nGeraadpleegde bronnen:")
    for s in result.sources:
        print(f"  - {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
