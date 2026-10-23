# TrustRAG Integration — Scam Shield Assistant (lite adapter)

## Decision
Full TrustRAG 0.0.15 was evaluated and rejected for this stack: it pins
`transformers==4.46.0` and pulls native builds (`datrie`, `faiss-cpu`, `xgboost`,
`FlagEmbedding`) plus GPU-grade rerankers and GB-sized model downloads — incompatible
with our Python 3.14 CPU-only hackathon setup (upstream targets Python 3.10/3.12).
Instead, `backend/assistant/` implements the same contract with zero new dependencies:
TF-IDF retrieval over a curated base (existing scikit-learn), citation validation,
offline extractive fallback, and an optional OpenAI-compatible hosted LLM via
`requests` (already pinned). No API key is required for the demo.

## Architecture
React Chat page → `POST /assistant/chat` → validate + redact → `full_check(log=False)`
→ TF-IDF `retriever.search` → abstain if weak → hosted LLM (if `LLM_API_KEY`) else
offline compose → `citations.validate` → fallback on failure. The scanner verdict
always comes from the detector; the LLM may only explain it.

## Endpoints
- `POST /assistant/chat` {question, message, lang, history} → {answer, evidence_status, citations[], safety_notice, abstained, verdict, generator}
- `GET /assistant/sources` → approved sources with stable IDs/URLs
- `GET /assistant/health` → {enabled, retrieval, documents, generator}

## Configuration (.env)
`LLM_API_KEY`, `LLM_BASE_URL` (default OpenAI), `LLM_MODEL` (default gpt-4o-mini),
`ASSISTANT_ENABLED`, `RAG_TOP_K=4`, `RAG_MIN_RELEVANCE=0.15`, `MAX_CHAT_MESSAGE_CHARS=4000`,
`ALLOWED_ORIGINS`. Frontend base URL via `VITE_API_BASE_URL` (fallback 127.0.0.1:8001).

## Knowledge base
10 curated docs in `backend/assistant/knowledge/documents/` + `manifest.json`
(SRC-001…SRC-010). Only these IDs/URLs can ever appear as citations.

## Evaluation
`python -m unittest discover -s tests`: 10 pipeline + 10 assistant tests green.
Covers retrieval relevance, unknown-ID rejection, abstention, PII redaction,
prompt-injection verdict stability, oversized rejection, scanner regression.

## Limitations
TF-IDF (no embeddings); `conflicting` state reserved; hosted path needs key + credits;
English-centric retrieval (HI/MR via topics + templates).

## Demo
1. `uvicorn main:app --port 8001` 2. Open `#/chat` (grounded mode badge) 3. Paste KYC
sample → verdict badge + cited answer 4. Ask off-corpus question → abstention message.
