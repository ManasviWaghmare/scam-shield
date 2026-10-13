"""Rules + reputation layer. Fast, explainable, language-independent."""
import re
from urllib.parse import urlparse

URL_RE = re.compile(r"https?://[^\s]+|www\.[^\s]+|bit\.ly/[^\s]+|t\.me/[^\s]+", re.I)
SHORTENER_RE = re.compile(r"bit\.ly|tinyurl|t\.co|goo\.gl|is\.gd|cutt\.ly", re.I)
SUSPICIOUS_TLD = (".xyz", ".top", ".tk", ".ml", ".cf", ".gq", ".buzz", ".shop-offer")

URGENCY_WORDS = [
    "urgent", "immediately", "24 hours", "last chance", "blocked", "suspended",
    "expire", "verify now", "तुरंत", "तत्काळ", "बंद हो जाएगा", "बंद होईल", "last warning",
]
SECRET_WORDS = ["otp", "pin", "cvv", "password", "upi pin", "ओटीपी", "पिन"]
KYC_PATTERNS = [r"kyc.*(expir|blocked|suspend|update|verify)", r"केवायसी.*(बंद|अपडेट)"]

SENDER_PATTERNS = [r"^\+?\d{10,13}$", r"^[A-Z]{2}-\d{6}$"]  # unknown numeric sender

def extract_urls(text: str) -> list[str]:
    return URL_RE.findall(text)

def check_url_reputation(url: str, lookup_fn=None) -> dict:
    """lookup_fn(url) -> True/False/None (cached threat intel)."""
    reasons = []
    score_add = 0.0
    parsed = urlparse(url if url.startswith("http") else "http://" + url)
    domain = parsed.netloc.lower()
    if SHORTENER_RE.search(url):
        reasons.append(f"Shortened link hides real site: {url}")
        score_add += 0.25
    if any(domain.endswith(t) for t in SUSPICIOUS_TLD):
        reasons.append(f"Suspicious domain ending: {domain}")
        score_add += 0.25
    if "@" in url or len(url) > 120:
        reasons.append("Obfuscated extra-long link")
        score_add += 0.15
    if lookup_fn:
        hit = lookup_fn(url)
        if hit is True:
            reasons.append("Link found in known phishing database")
            score_add += 0.40
    return {"url": url, "risk_add": min(score_add, 0.6), "reasons": reasons}

def analyze(text: str, lookup_fn=None) -> dict:
    t = text.lower()
    signals = []
    risk = 0.0

    urls = extract_urls(text)
    for u in urls:
        r = check_url_reputation(u, lookup_fn)
        risk += r["risk_add"]
        signals.extend(r["reasons"])

    urgency_hits = [w for w in URGENCY_WORDS if w in t]
    if urgency_hits:
        signals.append(f"Creates panic/urgency: {', '.join(urgency_hits[:3])}")
        risk += 0.20

    secret_hits = [w for w in SECRET_WORDS if w in t]
    if secret_hits:
        signals.append(f"Asks for secret ({', '.join(secret_hits)}). Banks NEVER ask this.")
        risk += 0.30

    for pat in KYC_PATTERNS:
        if re.search(pat, t):
            signals.append("Fake KYC/bank-impersonation pattern")
            risk += 0.25
            break

    if re.search(r"(congrat|winner|prize.*claim|लॉटरी.*जीते|इनाम)", t):
        signals.append("Lottery/prize lure to get fees or clicks")
        risk += 0.25

    if re.search(r"(part.?time.*earn|work from home.*\d+.*per day|job.*fee|नौकरी.*फीस)", t):
        signals.append("Fake job offer asking advance fee/task scam")
        risk += 0.25

    return {"urls": urls, "signals": signals, "rule_risk": min(risk, 1.0)}
