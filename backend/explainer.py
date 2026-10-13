"""Explainability: highlight evidence + plain-language advice in EN/HI/MR."""
import re

HIGHLIGHT_WORDS = [
    "otp", "pin", "cvv", "kyc", "blocked", "suspended", "urgent", "verify",
    "expire", "refund", "prize", "winner", "lottery", "job", "bit.ly",
    "http", "तुरंत", "बंद", "केवायसी", "ओटीपी", "लॉटरी", "इनाम", "नौकरी", "तत्काळ",
]

ADVICE = {
    "en": "Don't click or reply. Don't share OTP/PIN. Report at cybercrime.gov.in or call 1930.",
    "hi": "लिंक पर क्लिक न करें, OTP/PIN न बताएं। cybercrime.gov.in पर रिपोर्ट करें या 1930 पर कॉल करें।",
    "mr": "लिंकवर क्लिक करू नका, OTP/PIN देऊ नका। cybercrime.gov.in वर तक्रार करा किंवा 1930 ला कॉल करा.",
}

EXPLAIN_TMPL = {
    "en": "This looks like {category}. Key red flags: {flags}. {advice}",
    "hi": "यह {category} जैसा लगता है। खतरे के संकेत: {flags}। {advice}",
    "mr": "हे {category} सारखे दिसते. धोक्याचे संकेत: {flags}. {advice}",
}

def detect_lang(text: str) -> str:
    if re.search(r"[\u0900-\u097F]", text):
        # crude HI vs MR split
        if any(w in text for w in ["आहे", "नाही", "तुम्ही", "करू"]):
            return "mr"
        return "hi"
    return "en"

def highlight(text: str) -> list[str]:
    low = text.lower()
    return sorted({w for w in HIGHLIGHT_WORDS if w in low})

def build_explanation(category, signals, lang="en", verdict="Scam") -> str:
    if lang not in ADVICE:
        lang = "en"
    flags = "; ".join(signals[:3]) if signals else "suspicious pattern"
    tmpl = EXPLAIN_TMPL[lang]
    if verdict == "Safe":
        return {"en": "No major red flags found. Still verify sender before trusting.",
                "hi": "कोई बड़ा खतरा नहीं मिला। फिर भी भेजने वाले की पुष्टि करें।",
                "mr": "मोठा धोका आढळला नाही. तरीही पाठवणाऱ्याची खात्री करा."}[lang]
    return tmpl.format(category=category, flags=flags, advice=ADVICE[lang])

def fuse_verdict(ml_label: str, ml_conf: float, rule_risk: float) -> tuple[str, float]:
    """Combine ML + rules into Safe/Suspicious/Scam + 0-1 score."""
    score = 0.6 * (ml_conf if ml_label in ("scam", "suspicious") else (1 - ml_conf) * 0.3) + 0.4 * rule_risk
    # boost: strong rule signals alone => scam
    if rule_risk >= 0.5:
        score = max(score, 0.8)
    elif rule_risk >= 0.3:
        score = max(score, 0.55)
    if score >= 0.7:
        return "Scam", round(min(score, 0.99), 2)
    if score >= 0.4:
        return "Suspicious", round(score, 2)
    return "Safe", round(1 - score, 2)
