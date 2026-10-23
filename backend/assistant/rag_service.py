"""Orchestration: validate → detect (no duplicate logging) → retrieve → generate → validate."""
from . import citations, generator, retriever, safety
from .schemas import ChatResponse


def _scan_evidence(scan: dict) -> dict:
    return {"verdict": scan.get("verdict"), "score": scan.get("score"),
            "category": scan.get("category"), "lang": scan.get("lang"),
            "signals": (scan.get("signals") or [])[:4],
            "urls": (scan.get("urls") or [])[:3]}


def insufficient() -> ChatResponse:
    return ChatResponse(
        answer=("I don't have enough trusted evidence to answer that. Try asking about KYC fraud, "
                "UPI and OTP safety, phishing links, job or lottery scams — or paste the message "
                "itself and I will analyse it with the detector."),
        evidence_status="insufficient", citations=[], abstained=True)


def answer_question(question: str, message: str = "", lang: str = "en",
                    history: list | None = None, analyze=None) -> ChatResponse:
    """analyze: callable(message, lang) -> full_check dict with log=False. Injected to avoid import cycles."""
    q = safety.validate_question(question)
    m = safety.validate_message(message or "")
    safe_q = safety.redact_pii(q)
    safe_m = safety.redact_pii(m)

    scan = None
    if safe_m and analyze is not None:
        scan = analyze(safe_m, lang=lang)
    evidence = _scan_evidence(scan) if scan else {"verdict": None, "category": "general",
                                                 "signals": [], "urls": []}

    query = f"{safe_q}\n{evidence.get('category', '')}\n{' '.join(evidence.get('signals', []))}"
    passages = retriever.search(query)
    if not retriever.has_sufficient_evidence(passages):
        resp = insufficient()
        resp.verdict = evidence if scan else None
        return resp

    if generator.hosted_configured():
        try:
            draft = generator.generate(
                question=safety.wrap_untrusted("question", safe_q), scan_evidence=evidence,
                passages=[{**p, "passage": safety.wrap_untrusted("passage", p["passage"])}
                           for p in passages],
                lang=lang, history=history or [])
        except Exception:
            draft = generator.offline_answer(safe_q, evidence, passages)
    else:
        draft = generator.offline_answer(safe_q, evidence, passages)

    accepted, _rejected = citations.validate(draft.get("citations", []), passages)
    if not accepted:
        # citation failure → safe extractive fallback over the same passages
        draft = generator.offline_answer(safe_q, evidence, passages)
        accepted, _ = citations.validate(draft.get("citations", []), passages)

    return ChatResponse(answer=draft["answer"] or insufficient().answer,
                        evidence_status="supported" if accepted else "insufficient",
                        citations=accepted,
                        abstained=not bool(accepted),
                        verdict=evidence if scan else None,
                        generator=draft.get("generator", "offline"))
