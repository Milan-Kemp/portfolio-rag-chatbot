"""CLI to test the full pipeline locally: type a question, see the grounded
answer and its sources.

    python main.py                 # interactive loop
    python main.py "one question"  # single shot
"""
from __future__ import annotations

import sys

from answer import answer


def _run_once(question: str) -> None:
    result = answer(question)
    print(f"\n{result.text}\n")
    if result.sources:
        print("Bronnen: " + ", ".join(result.sources))
    print()


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    if len(sys.argv) > 1:
        _run_once(" ".join(sys.argv[1:]))
        return 0

    print("Portfolio RAG chatbot — stel een vraag, of Ctrl+C om te stoppen.\n")
    try:
        while True:
            q = input("vraag> ").strip()
            if not q:
                continue
            if q.lower() in {"exit", "quit", "stop"}:
                break
            _run_once(q)
    except (KeyboardInterrupt, EOFError):
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
