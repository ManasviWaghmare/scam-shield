"""WhatsApp notifications for scheduler — CallMeBot (free, no approval).
Official setup (2026): number is +34 694 23 41 84 (old numbers are dead).
1. Save +34 694 23 41 84 as contact "CallMeBot".
2. WhatsApp it EXACTLY: I allow callmebot to send me messages
3. Bot replies "API Activated ... Your APIKEY is 123123" in ~30 sec.
   If no reply in 2 min: DO NOT spam — wait 24h (rate-limit), use fallback below.
4. Put in backend/.env (NEVER commit):
   CALLMEBOT_PHONE=91XXXXXXXXXX
   CALLMEBOT_APIKEY=123456
   TEAM_PHONES=91XXXXXXXXXX
5. Test: python notify_whatsapp.py "Scam Shield test"
Fallback for hackathon demo (no key needed): every broadcast also appends to
backend/alerts_outbox.log, and GET /alerts shows it. Forward manually to WhatsApp.
Docs: https://www.callmebot.com/blog/free-api-whatsapp-messages/
"""
import os
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

OUTBOX = Path(__file__).parent / "alerts_outbox.log"

def _env(k, default=""):
    # try .env file manually (avoid python-dotenv dependency)
    v = os.getenv(k, "")
    if v:
        return v
    try:
        with open(os.path.join(os.path.dirname(__file__), ".env")) as f:
            for line in f:
                if line.strip().startswith(k + "="):
                    return line.strip().split("=", 1)[1]
    except FileNotFoundError:
        pass
    return default

def _log_outbox(text: str, keep: int = 500):
    try:
        lines = []
        if OUTBOX.exists():
            lines = OUTBOX.read_text().splitlines()
        lines.append(f"[{datetime.now().isoformat(timespec='seconds')}] {text}")
        OUTBOX.write_text("\n".join(lines[-keep:]) + "\n")
    except Exception:
        pass

def send_whatsapp(text: str, phone: str | None = None, apikey: str | None = None) -> bool:
    phone = phone or _env("CALLMEBOT_PHONE")
    apikey = apikey or _env("CALLMEBOT_APIKEY")
    _log_outbox(text)
    if not phone or not apikey or "REPLACE" in apikey:
        print("[WhatsApp] QUEUED locally → alerts_outbox.log (no API key yet)")
        print(f"[WhatsApp] Would send: {text[:200]}")
        return False
    url = "https://api.callmebot.com/whatsapp.php?phone=" + phone + "&text=" + urllib.parse.quote(text) + "&apikey=" + apikey
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            body = r.read().decode(errors="ignore")
            ok = "Message queued" in body or r.status == 200
            print(f"[WhatsApp] {'sent ✅' if ok else 'maybe ❓'} to {phone}: {body[:100]}")
            return ok
    except Exception as e:
        print(f"[WhatsApp] failed ❌: {e}")
        return False

def broadcast(text: str):
    """Send to all TEAM_PHONES comma-separated."""
    phones = [p.strip() for p in _env("TEAM_PHONES", _env("CALLMEBOT_PHONE")).split(",") if p.strip()]
    apikey = _env("CALLMEBOT_APIKEY")
    if not phones or not apikey or "REPLACE" in apikey:
        print("[WhatsApp] QUEUED locally → alerts_outbox.log (set real APIKEY to auto-send)")
        print(f"[WhatsApp] Would send: {text[:200]}")
        _log_outbox(text)
        return False
    for p in phones:
        send_whatsapp(text, phone=p, apikey=apikey)
    return True

# --- message builders used by scheduler.py ---
def tip_message(lang="en"):
    from scheduler import SCAM_TIPS
    return "🛡️ Scam Shield daily tip\n" + SCAM_TIPS.get(lang, SCAM_TIPS["en"])

def standup_reminder():
    return "🛡️ Scam Shield standup 9PM: reply ✅ done / ❌ blocked + blocker. Freeze dates: backend 5th, frontend 8th, submit 10th."

def freeze_alert(what: str):
    return f"🧊 Scam Shield FREEZE today: {what}. Push tag + send demo screenshot here."

if __name__ == "__main__":
    import sys
    msg = " ".join(sys.argv[1:]) or "Scam Shield test ✅ scheduler working"
    broadcast(msg)
