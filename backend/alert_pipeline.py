"""Scam alert pipeline — collect → review → send, with consented subscribers.

Python route of the alert automation roadmap (docs/WHATSAPP_ALERTS.md):

  collect  fetch RSS threat/scam news, dedupe, append to data/pending.csv
  review   human fills how_it_works + action, sets approved=yes  (the gate)
  send     only approved rows → WhatsApp Cloud API template → active subscribers
  webhook  STOP/START keywords + delivery status (GET/POST /whatsapp/webhook)

Consent rule: never message a number that is not status=active in
data/subscribers.csv. DELETE test-number rows before any production broadcast.

CLI (run from backend/):
  python alert_pipeline.py collect          # fill the review queue
  python alert_pipeline.py send             # flush approved rows
  python alert_pipeline.py pending          # print the queue as a table
  python alert_pipeline.py subscribe 91XXXX Name source
"""
import csv
import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
PENDING = DATA_DIR / "pending.csv"
SUBSCRIBERS = DATA_DIR / "subscribers.csv"
SUBSCRIBERS_EXAMPLE = DATA_DIR / "subscribers.example.csv"
SENT_LOG = DATA_DIR / "sent_log.csv"

PENDING_COLS = ["id", "source_url", "title", "scam_type", "how_it_works", "action", "approved", "status", "added_at"]
SUB_COLS = ["phone", "name", "status", "consent_date", "consent_source"]
SENT_COLS = ["id", "phone", "sent_at", "channel", "status"]

# Placeholder feeds — swap in CERT-In / RBI / I4C / FTC RSS once you verify their URLs.
FEEDS = [
    "https://news.google.com/rss/search?q=UPI+scam+OR+KYC+fraud+india&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=cyber+fraud+OTP+phishing+india&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=digital+arrest+lottery+scam&hl=en-IN&gl=IN&ceid=IN:en",
]

SCAM_TYPES = [
    ("KYC / bank verification fraud", ["kyc", "bank account", "account blocked", "verify your account"]),
    ("UPI / refund fraud", ["upi", "refund", "cashback", "qr code", "collect request", "payment request"]),
    ("OTP / PIN theft", ["otp", "one time password", "pin", "cvv"]),
    ("Lottery / prize fraud", ["lottery", "prize", "you have won", "lucky draw", "jackpot"]),
    ("Job / investment scam", ["job", "part-time", "part time", "investment", "trading", "earn from home", "work from home"]),
    ("Digital arrest threat", ["digital arrest", "arrest warrant", "cyber police", "video call warrant"]),
    ("Sextortion / blackmail", ["blackmail", "explicit video", "obscene"]),
    ("Phishing link", ["phishing", "click the link", "verify now", "login credentials"]),
]

STOP_KEYWORDS = {"STOP", "STOPALL", "CANCEL", "UNSUBSCRIBE", "END", "QUIT"}
START_KEYWORDS = {"START", "JOIN", "YES", "SUBSCRIBE"}


def classify(title: str) -> str:
    t = title.lower()
    for name, keys in SCAM_TYPES:
        if any(k in t for k in keys):
            return name
    return "Scam campaign"


def _read_csv(path: Path, cols: list[str]) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if any(r.values())]


def _write_csv(path: Path, cols: list[str], rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def ensure_subscribers():
    """Create data/subscribers.csv from the example on first run."""
    if not SUBSCRIBERS.exists() and SUBSCRIBERS_EXAMPLE.exists():
        SUBSCRIBERS.write_text(SUBSCRIBERS_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    if not SUBSCRIBERS.exists():
        _write_csv(SUBSCRIBERS, SUB_COLS, [])


def load_pending() -> list[dict]:
    return _read_csv(PENDING, PENDING_COLS)


def save_pending(rows: list[dict]):
    _write_csv(PENDING, PENDING_COLS, rows)


def active_subscribers() -> list[dict]:
    ensure_subscribers()
    return [r for r in _read_csv(SUBSCRIBERS, SUB_COLS) if r.get("status", "").strip().lower() == "active"]


def set_subscriber_status(phone: str, status: str, source: str = "webhook") -> bool:
    ensure_subscribers()
    rows = _read_csv(SUBSCRIBERS, SUB_COLS)
    digits = "".join(c for c in phone if c.isdigit())
    hit = False
    for r in rows:
        if "".join(c for c in r["phone"] if c.isdigit()) == digits:
            r["status"] = status
            hit = True
    if not hit and status == "active":
        rows.append({"phone": digits, "name": "", "status": "active",
                     "consent_date": datetime.now().date().isoformat(), "consent_source": source})
        hit = True
    if hit:
        _write_csv(SUBSCRIBERS, SUB_COLS, rows)
    return hit


def subscribe(phone: str, name: str = "", source: str = "manual opt-in") -> dict:
    return {"phone": phone, "name": name, "status": "active",
            "consent_date": datetime.now().date().isoformat(), "consent_source": source}


def _digits(s: str) -> str:
    return "".join(ch for ch in str(s) if ch.isdigit())


def add_subscriber(phone: str, name: str = "", source: str = "manual opt-in") -> dict:
    """Consent-recorded upsert. Re-opts-in an existing number (fresh consent row)."""
    ensure_subscribers()
    digits = _digits(phone)
    rows = _read_csv(SUBSCRIBERS, SUB_COLS)
    for r in rows:
        if _digits(r.get("phone", "")) == digits:
            r["name"] = name or r.get("name", "")
            r["status"] = "active"
            r["consent_date"] = datetime.now().date().isoformat()
            r["consent_source"] = source
            _write_csv(SUBSCRIBERS, SUB_COLS, rows)
            return r
    row = subscribe(digits, name, source)
    rows.append(row)
    _write_csv(SUBSCRIBERS, SUB_COLS, rows)
    return row


def approve_pending(item_id: str, how_it_works: str, action: str) -> dict | None:
    """Human review gate: fill copy and mark approved=yes. Returns the row or None."""
    rows = load_pending()
    for r in rows:
        if r["id"] == item_id:
            r["how_it_works"] = how_it_works.strip()
            r["action"] = action.strip()
            r["approved"] = "yes"
            save_pending(rows)
            return r
    return None


def _default_fetch(url: str, timeout: int = 15) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "ScamShield/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _parse_rss(payload: bytes, limit_per_feed: int = 20) -> list[dict]:
    items = []
    root = ET.fromstring(payload)
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if title and link:
            items.append({"title": title[:200], "link": link})
        if len(items) >= limit_per_feed:
            break
    return items


def collect(feeds: list[str] | None = None, fetcher=None) -> dict:
    """Phase: fetch → dedupe → append rows to the review queue. Returns summary."""
    fetcher = fetcher or _default_fetch
    rows = load_pending()
    seen = {r["id"] for r in rows}
    try:
        if SENT_LOG.exists():
            seen |= {r["id"] for r in _read_csv(SENT_LOG, SENT_COLS)}
    except Exception:
        pass
    added, failed = 0, 0
    for url in (feeds if feeds is not None else FEEDS):
        try:
            payload = fetcher(url)
            for it in _parse_rss(payload):
                rid = it["link"]
                if rid in seen:
                    continue
                seen.add(rid)
                rows.append({
                    "id": rid,
                    "source_url": it["link"],
                    "title": it["title"],
                    "scam_type": classify(it["title"]),
                    "how_it_works": "",
                    "action": "",
                    "approved": "",
                    "status": "pending",
                    "added_at": datetime.now().isoformat(timespec="seconds"),
                })
                added += 1
        except Exception as e:
            failed += 1
            print(f"[collect] feed failed {url.split('?')[0]}: {e}")
    save_pending(rows)
    print(f"[collect] queue={len(rows)} new={added} feeds_failed={failed}")
    return {"queued": len(rows), "new": added, "feeds_failed": failed}


def _log_sent(rid: str, phone: str, status: str):
    rows = _read_csv(SENT_LOG, SENT_COLS)
    rows.append({"id": rid, "phone": phone, "sent_at": datetime.now().isoformat(timespec="seconds"),
                 "channel": "whatsapp_cloud", "status": status})
    _write_csv(SENT_LOG, SENT_COLS, rows)


def send_approved() -> dict:
    """Send only rows with approved=yes to active subscribers. Never sends unreviewed rows."""
    import whatsapp_cloud
    from notify_whatsapp import _log_outbox

    rows = load_pending()
    subs = active_subscribers()
    ready = [r for r in rows
             if r.get("approved", "").strip().lower() == "yes"
             and r.get("status", "") not in ("sent", "queued")]
    summary = {"approved": len(ready), "subscribers": len(subs), "sent": 0, "queued": 0, "failed": 0}
    if not ready:
        print("[send] nothing approved yet — fill how_it_works/action and set approved=yes in data/pending.csv")
        return summary
    if not subs:
        print("[send] no active subscribers — add opt-in rows to data/subscribers.csv")
        return summary

    configured = whatsapp_cloud.is_configured()
    for r in ready:
        ok_any = False
        if not configured:
            _log_outbox(f"[queued alert {r['scam_type']}] {whatsapp_cloud.alert_body(r['scam_type'], r['how_it_works'] or r['title'], r['action'] or 'Do not click links or share OTPs. Call 1930.')}")
            r["status"] = "queued"
            summary["queued"] += 1
            continue
        for s in subs:
            res = whatsapp_cloud.send_template(s["phone"], r["scam_type"],
                                               r["how_it_works"] or r["title"],
                                               r["action"] or "Do not click links or share OTPs. Call 1930.",
                                               source=r.get("source_url", ""))
            if res.get("ok"):
                ok_any = True
                _log_sent(r["id"], s["phone"], "sent")
                summary["sent"] += 1
            else:
                _log_sent(r["id"], s["phone"], "failed")
                summary["failed"] += 1
        r["status"] = "sent" if ok_any else "failed"
    save_pending(rows)
    print(f"[send] {summary}")
    return summary


def handle_webhook(body: dict) -> dict:
    """Meta webhook POST body → STOP/START handling + delivery status logging."""
    from notify_whatsapp import _log_outbox
    out = {"stopped": [], "started": [], "statuses": []}
    try:
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []):
                    text = (msg.get("text", {}).get("body") or "").strip().upper()
                    phone = msg.get("from", "")
                    if text in STOP_KEYWORDS:
                        set_subscriber_status(phone, "stopped", source="whatsapp keyword")
                        out["stopped"].append(phone)
                        _log_outbox(f"[STOP honored] {phone} unsubscribed")
                    elif text in START_KEYWORDS:
                        set_subscriber_status(phone, "active", source="whatsapp keyword")
                        out["started"].append(phone)
                for st in value.get("statuses", []):
                    out["statuses"].append({"id": st.get("id"), "status": st.get("status")})
    except Exception as e:
        out["error"] = str(e)
    return out


def _cli(argv: list[str]) -> int:
    cmd = argv[0] if argv else ""
    if cmd == "collect":
        collect()
        return 0
    if cmd == "send":
        print(json.dumps(send_approved(), indent=2))
        return 0
    if cmd == "pending":
        for r in load_pending():
            flag = "✅" if r["approved"].lower() == "yes" else "  "
            print(f"{flag} [{r['status']:8}] {r['scam_type']:32} {r['title'][:60]}")
        return 0
    if cmd == "subscribe":
        if len(argv) < 2:
            print("usage: python alert_pipeline.py subscribe 91XXXXXXXXXX [name] [source]")
            return 1
        add_subscriber(argv[1], argv[2] if len(argv) > 2 else "",
                       argv[3] if len(argv) > 3 else "manual opt-in")
        print(f"[subscribed] {argv[1]}")
        return 0
    print("commands: collect | send | pending | subscribe 91XXXX Name source")
    return 1


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
