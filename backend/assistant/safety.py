"""Safety: PII redaction, input validation, injection containment."""
import re

MAX_MESSAGE_CHARS = 4000


def redact_pii(text: str) -> str:
    """Redact identifiers before any external transmission. Local-first: never send raw text out."""
    t = text
    t = re.sub(r"\b\d{10,13}\b", "[PHONE]", t)          # phone numbers
    t = re.sub(r"\b\d{12,19}\b", "[ACCOUNT]", t)        # account / card numbers
    t = re.sub(r"(?i)\b(otp|pin|cvv|password)\b\s*(is|:)?\s*\d{3,8}", r"\1 [REDACTED]", t)
    t = re.sub(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b", "[EMAIL]", t)  # emails
    t = re.sub(r"\b[\w.+-]+@[a-z]+\b", "[UPI-ID]", t)   # bare UPI handles
    return t


def validate_question(q: str) -> str:
    q = (q or "").strip()
    if not q:
        raise ValueError("Question is empty.")
    if len(q) > 2000:
        raise ValueError("Question exceeds 2000 characters.")
    return q


def validate_message(m: str) -> str:
    m = (m or "").strip()
    if len(m) > MAX_MESSAGE_CHARS:
        raise ValueError(f"Message exceeds {MAX_MESSAGE_CHARS} characters.")
    return m


INJECTION_PATTERNS = [
    r"ignore (all|previous|above) (rules|instructions)",
    r"disregard (all|previous|above)",
    r"you are now ",
    r"system prompt",
    r"reveal your (instructions|prompt|system)",
    r"jailbreak",
]


def contains_injection(text: str) -> bool:
    t = (text or "").lower()
    return any(re.search(p, t) for p in INJECTION_PATTERNS)


def wrap_untrusted(label: str, text: str) -> str:
    """Mark model inputs as data so hosted LLMs treat them as untrusted content, not commands."""
    return f"<untrusted-{label}>\n{text[:2000]}\n</untrusted-{label}>"
