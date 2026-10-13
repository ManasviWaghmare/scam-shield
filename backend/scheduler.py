"""Scheduler layer — the differentiator in your submission.
4 jobs: threat refresh, trend aggregation, privacy purge, daily tip.
Runs inside FastAPI lifespan via APScheduler (Asia/Kolkata).
"""
from datetime import date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import database as db

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")

# Demo seed for threat intel (replace with PhishTank/OpenPhish fetch)
KNOWN_BAD = [
    ("sbi-kyc-update.xyz", "domain", True),
    ("prize-claim.top", "domain", True),
    ("paytm-kyc09.buzz", "domain", True),
    ("mega-loot.xyz", "domain", True),
    ("itrefund.top", "domain", True),
]

SCAM_TIPS = {
    "en": "Today's tip: Banks NEVER ask OTP/PIN on call. Cut the call, call 1930.",
    "hi": "आज की टिप: बैंक कभी OTP/PIN नहीं मांगता। कॉल काटें, 1930 पर कॉल करें।",
    "mr": "आजची टीप: बँक कधीही OTP/PIN मागत नाही. कॉल तोडून 1930 ला कॉल करा.",
}

def refresh_threat_intel():
    """Every 6h: sync malicious URL cache. Tries live PhishTank feed, falls back to seed list."""
    print("[Scheduler] Refreshing threat intel...")
    try:
        live = 0
        try:
            import requests
            from urllib.parse import urlparse
            r = requests.get("https://data.phishtank.com/data/online-valid.json", timeout=15)
            if r.ok:
                for entry in r.json()[:300]:
                    url = entry.get("url", "")
                    host = urlparse(url).netloc.lower() if url else ""
                    if host:
                        db.upsert_threat(host, "domain", True)
                        live += 1
                print(f"[Scheduler] Live PhishTank sync: {live} domains.")
        except Exception as e:
            print(f"[Scheduler] Live feed skipped ({e}); using seed list.")
        for indicator, kind, mal in KNOWN_BAD:
            db.upsert_threat(indicator, kind, mal)
        print(f"[Scheduler] Threat cache updated ({live} live + {len(KNOWN_BAD)} seed).")
    except Exception as e:
        print(f"[Scheduler] Threat refresh failed: {e}")

def aggregate_trends():
    """Every 1h: rebuild anonymized category counts for /trends dashboard."""
    print("[Scheduler] Aggregating trends...")
    try:
        conn = db.get_conn()
        rows = conn.execute(
            "SELECT category, COUNT(*) c FROM scans WHERE created_at > datetime('now','-1 day') GROUP BY category"
        ).fetchall()
        conn.close()
        counts = {r[0]: r[1] for r in rows} or {"Fake KYC": 0, "UPI Refund": 0}
        db.save_trends(str(date.today()), counts)
        print(f"[Scheduler] Trends saved: {counts}")
    except Exception as e:
        print(f"[Scheduler] Trend agg failed: {e}")

def privacy_purge():
    """Daily 00:05: delete raw scans older than 24h (privacy-first claim)."""
    print("[Scheduler] Privacy purge...")
    try:
        n = db.purge_old_scans(hours=24)
        print(f"[Scheduler] Purged {n} old scan rows.")
    except Exception as e:
        print(f"[Scheduler] Purge failed: {e}")

def daily_tip_push():
    """Daily 09:00 IST: rotate scam-of-the-day tip + WhatsApp/Telegram."""
    print("[Scheduler] Daily tip:")
    for lang, tip in SCAM_TIPS.items():
        print(f"  [{lang}] {tip}")
    try:
        from notify_whatsapp import broadcast, tip_message
        msg = tip_message("en") + "\n" + tip_message("hi")
        broadcast(msg)
        # Telegram fallback (instant, no block)
        try:
            from notify_telegram import send_telegram
            send_telegram("🛡️ Scam Shield daily tip\n" + msg)
        except Exception:
            pass
    except Exception as e:
        print(f"[Scheduler] tip failed: {e}")


def standup_nudge():
    """Daily 21:05 IST: standup reminder to WhatsApp group."""
    print("[Scheduler] Standup nudge...")
    try:
        from notify_whatsapp import broadcast, standup_reminder
        broadcast(standup_reminder())
    except Exception as e:
        print(f"[Scheduler] WhatsApp standup failed: {e}")

def start_scheduler():
    if scheduler.running:
        return
    scheduler.add_job(refresh_threat_intel, IntervalTrigger(hours=6), id="threat_refresh", replace_existing=True)
    scheduler.add_job(aggregate_trends, IntervalTrigger(hours=1), id="trends", replace_existing=True)
    scheduler.add_job(privacy_purge, CronTrigger(hour=0, minute=5), id="purge", replace_existing=True)
    scheduler.add_job(daily_tip_push, CronTrigger(hour=9, minute=0), id="tip", replace_existing=True)
    scheduler.add_job(standup_nudge, CronTrigger(hour=21, minute=5), id="standup", replace_existing=True)
    scheduler.start()
    print("[Scheduler] Started. Jobs:", [j.id for j in scheduler.get_jobs()])
    # run once at boot so demo has data immediately
    refresh_threat_intel()
    aggregate_trends()
