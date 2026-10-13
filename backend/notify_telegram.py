"""Telegram fallback — works in 2 min, no 24h block. Use until CallMeBot unblocks.
Setup:
1. Telegram → search @BotFather → /newbot → name: ScamShieldBot → copy BOT_TOKEN
2. Search your bot, press Start (or send any msg)
3. Get your CHAT_ID: open https://api.telegram.org/bot<TOKEN>/getUpdates, look for "id":123456
4. Put in backend/.env:
   TELEGRAM_TOKEN=123456:ABC...
   TELEGRAM_CHAT_ID=123456
5. Test: python notify_telegram.py "hello"
"""
import os
import urllib.parse
import urllib.request
import json

def _env(k, default=""):
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

def send_telegram(text: str) -> bool:
    token = _env("TELEGRAM_TOKEN")
    chat = _env("TELEGRAM_CHAT_ID")
    if not token or not chat or "REPLACE" in token:
        print("[Telegram] SKIP — set TELEGRAM_TOKEN/CHAT_ID in backend/.env")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
    try:
        with urllib.request.urlopen(url, data=data, timeout=15) as r:
            print(f"[Telegram] sent ✅: {r.status}")
            return True
    except Exception as e:
        print(f"[Telegram] failed ❌: {e}")
        return False

if __name__ == "__main__":
    import sys
    send_telegram(" ".join(sys.argv[1:]) or "Scam Shield test ✅")
