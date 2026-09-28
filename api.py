"""FastAPI layer: exposes the pipeline over HTTP so the site widget can call it.

    uvicorn api:app --reload            # dev, http://127.0.0.1:8000
    uvicorn api:app --host 0.0.0.0 --port 8000   # deploy

Endpoints
---------
    GET  /health   -> {"status": "ok", "chunks": <n>}
    POST /ask      -> {"answer": str, "sources": [str], "question": str}

CORS is restricted to the origins in config.ALLOWED_ORIGINS (set via the
ALLOWED_ORIGINS env var). Your GitHub Pages origin must be in that list or
the browser will block the widget's request.

/ask is rate limited (slowapi) because the endpoint is public and every call
costs money: per IP per minute, per IP per day, and one global daily cap.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from answer import answer
from config import (
    ALLOWED_ORIGINS,
    RATE_LIMIT_GLOBAL_PER_DAY,
    RATE_LIMIT_PER_DAY,
    RATE_LIMIT_PER_MINUTE,
    TOP_K,
)
from retrieve import _collection

# Behind Caddy, uvicorn runs with --proxy-headers so get_remote_address sees
# the real visitor IP (from X-Forwarded-For) instead of Caddy's container IP.
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Portfolio RAG chatbot", version="1.0")
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def _rate_limited(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    # Same {"detail": ...} shape as other errors, so the widget can show it.
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Je stelt te veel vragen achter elkaar. "
            "Probeer het over een minuut opnieuw."
        },
        headers={"Retry-After": "60"},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    k: int = Field(default=TOP_K, ge=1, le=10)


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[str]


@app.get("/health")
def health() -> dict:
    try:
        n = _collection().count()
    except Exception:  # noqa: BLE001
        n = 0
    return {"status": "ok", "chunks": n}


@app.post("/ask", response_model=AskResponse)
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
@limiter.limit(f"{RATE_LIMIT_PER_DAY}/day")
@limiter.limit(f"{RATE_LIMIT_GLOBAL_PER_DAY}/day", key_func=lambda request: "global")
def ask(request: Request, req: AskRequest) -> AskResponse:
    try:
        result = answer(req.question, k=req.k)
    except RuntimeError as e:  # missing key, empty store, ...
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:  # noqa: BLE001 - upstream API failure, etc.
        raise HTTPException(status_code=502, detail=f"upstream error: {e}") from e
    return AskResponse(
        question=result.question, answer=result.text, sources=result.sources
    )
