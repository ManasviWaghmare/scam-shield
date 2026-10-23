"""Assistant routes: POST /assistant/chat, GET /assistant/sources, GET /assistant/health."""
import os
import time
from collections import defaultdict
from fastapi import APIRouter, HTTPException, Request

from . import generator, rag_service, retriever, safety
from .schemas import ChatRequest

router = APIRouter(prefix="/assistant", tags=["assistant"])

ASSISTANT_ENABLED = os.getenv("ASSISTANT_ENABLED", "true").lower() != "false"
_hits: dict[str, list[float]] = defaultdict(list)


def _rate_limited(ip: str, limit: int = 30, window: int = 60) -> bool:
    now = time.time()
    _hits[ip] = [t for t in _hits[ip] if now - t < window]
    if len(_hits[ip]) >= limit:
        return True
    _hits[ip].append(now)
    return False


@router.post("/chat")
def chat(req: ChatRequest, request: Request):
    if not ASSISTANT_ENABLED:
        raise HTTPException(503, "Assistant is disabled.")
    if _rate_limited(request.client.host if request.client else "local"):
        raise HTTPException(429, "Too many requests. Slow down and retry.")
    try:
        question = safety.validate_question(req.question)
        message = safety.validate_message(req.message)
    except ValueError as e:
        raise HTTPException(400, str(e))

    # Lazy import: avoids a main<->assistant import cycle; never logs a duplicate scan.
    from main import full_check
    resp = rag_service.answer_question(
        question, message, lang=req.lang or "en",
        history=[h.model_dump() for h in req.history],
        analyze=lambda m, lang="en": full_check(m, lang, log=False))
    return resp.model_dump()


@router.get("/sources")
def sources():
    return {"sources": retriever.list_sources()}


@router.get("/health")
def health():
    return {"enabled": ASSISTANT_ENABLED,
            "retrieval": "ok" if retriever.list_sources() else "empty",
            "documents": len(retriever.list_sources()),
            "generator": "hosted" if generator.hosted_configured() else "offline"}
