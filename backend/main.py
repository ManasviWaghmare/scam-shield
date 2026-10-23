"""Scam Shield API — FastAPI + APScheduler."""
import hashlib
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import database as db
import classifier
import rules
import explainer
from scheduler import scheduler, start_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    start_scheduler()
    yield
    if scheduler.running:
        scheduler.shutdown()

app = FastAPI(title="Scam Shield", lifespan=lifespan)
import os as _os
_origins = [o.strip() for o in _os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=_origins, allow_methods=["*"], allow_headers=["*"])

try:
    from assistant.routes import router as assistant_router
    app.include_router(assistant_router)
    print("[Scam Shield] Assistant routes enabled (/assistant/chat, /sources, /health).")
except Exception as e:
    print(f"[Scam Shield] Assistant disabled ({e}). Scanner endpoints unaffected.")

class CheckReq(BaseModel):
    message: str
    lang: str | None = None

def mask_pii(text: str) -> str:
    import re
    text = re.sub(r"\b\d{10,13}\b", "***PHONE***", text)
    text = re.sub(r"\b\d{12,16}\b", "***ACCT***", text)
    text = re.sub(r"\b\d{4,6}\b", "***OTP?***", text)
    return text

def full_check(message: str, lang=None, log: bool = True):
    lang = lang or explainer.detect_lang(message)
    ml_label, ml_conf = classifier.predict_proba(message)
    rule_out = rules.analyze(message, lookup_fn=db.lookup_threat)
    verdict, score = explainer.fuse_verdict(ml_label, ml_conf, rule_out["rule_risk"])
    category = classifier.predict_category(message) if verdict != "Safe" else "Safe"
    explanation = explainer.build_explanation(category, rule_out["signals"], lang, verdict)
    highlights = explainer.highlight(message)
    model_tokens = classifier.explain_tokens(message)
    # merge model evidence into highlights (dedupe, keep order)
    for mt in model_tokens:
        tok = mt["token"].split()[-1]
        if tok not in highlights and len(tok) > 2:
            highlights.append(tok)
    masked = mask_pii(message)
    # privacy: store only hash, never raw text (assistant re-analysis passes log=False)
    h = hashlib.sha256(message.encode()).hexdigest()[:16]
    if log:
        db.log_scan(h, category, verdict, score, lang)
    return {
        "verdict": verdict,
        "score": score,
        "category": category,
        "lang": lang,
        "signals": rule_out["signals"],
        "urls": rule_out["urls"],
        "highlights": highlights,
        "model_tokens": model_tokens,
        "ml_label": ml_label,
        "ml_confidence": round(ml_conf, 3),
        "rule_risk": round(rule_out["rule_risk"], 3),
        "explanation": explanation,
        "advice": explainer.ADVICE.get(lang, explainer.ADVICE["en"]),
        "masked_preview": masked[:120],
    }

@app.get("/")
def root():
    jobs = [{"id": j.id, "next": str(j.next_run_time)} for j in scheduler.get_jobs()] if scheduler.running else []
    return {"status": "Scam Shield running", "scheduler_jobs": jobs}

@app.post("/check")
def check(req: CheckReq):
    return full_check(req.message, req.lang)

@app.post("/check-image")
async def check_image(file: UploadFile = File(...), lang: str = Form(None)):
    from ocr import image_to_text
    text = image_to_text(await file.read())
    if not text:
        return {"error": "OCR failed or empty. Install tesseract: sudo apt install tesseract-ocr tesseract-ocr-hin tesseract-ocr-mar"}
    out = full_check(text, lang)
    out["ocr_text"] = text
    return out

@app.get("/trends")
def trends():
    return {"trends": db.get_trends()}

@app.get("/history")
def history(limit: int = 10):
    """Anonymised recent verdicts for the dashboard (no message text)."""
    return {"history": db.get_recent_scans(min(limit, 50))}

@app.get("/stats")
def stats():
    return db.get_stats()

@app.get("/report-info")
def report_info():
    return {
        "helpline": "1930",
        "portal": "https://cybercrime.gov.in",
        "steps": ["Don't click/pay", "Screenshot the message", "Call 1930", "File complaint on cybercrime.gov.in"],
    }

@app.get("/scheduler-status")
def sched_status():
    if not scheduler.running:
        return {"running": False}
    return {"running": True, "jobs": [{"id": j.id, "next": str(j.next_run_time)} for j in scheduler.get_jobs()]}

@app.get("/alerts")
def alerts():
    """Fallback outbox: what scheduler WOULD send to WhatsApp (for demo without API key)."""
    from pathlib import Path
    p = Path(__file__).parent / "alerts_outbox.log"
    if not p.exists():
        return {"alerts": [], "note": "No alerts yet. Trigger: POST /check or wait for 9AM job."}
    lines = p.read_text().splitlines()[-20:]
    return {"alerts": lines, "note": "Forward these manually to WhatsApp until CallMeBot key works."}

class AlertTestReq(BaseModel):
    phone: str | None = None
    scam_type: str = "Electricity Bill Fraud"
    description: str = "Fake call claiming power will be cut in 30 minutes"
    action: str = "Do not click the link or share OTP. Call 1930 if you already paid."

@app.post("/alerts/test")
def alert_test(req: AlertTestReq):
    """Phase 4 sandbox: send the approved template to one number (or queue it)."""
    import whatsapp_cloud
    from notify_whatsapp import _env
    phone = req.phone or (_env("ALERT_PHONES", "").split(",")[0].strip() or None)
    if not phone:
        return {"ok": False, "error": "No phone. Pass phone=91XXXXXXXXXX or set ALERT_PHONES in .env."}
    payload = whatsapp_cloud.build_payload(phone, req.scam_type, req.description, req.action)
    if not whatsapp_cloud.is_configured():
        from notify_whatsapp import _log_outbox
        _log_outbox(whatsapp_cloud.alert_body(req.scam_type, req.description, req.action))
        return {"ok": False, "queued": True, "configured": False,
                "note": "WA_CLOUD_TOKEN/WA_PHONE_NUMBER_ID not set — rendered to GET /alerts instead.",
                "payload": payload}
    return {"ok": True, "configured": True, **whatsapp_cloud.send_template(phone, req.scam_type, req.description, req.action)}

@app.post("/alerts/collect")
def alerts_collect():
    """Phase 3: fill the review queue now (scheduler also runs it every 6h)."""
    import alert_pipeline
    return alert_pipeline.collect()

@app.post("/alerts/send")
def alerts_send():
    """Phase 3: send approved=yes rows to active subscribers (consent-gated)."""
    import alert_pipeline
    return alert_pipeline.send_approved()

class SubscribeIn(BaseModel):
    phone: str
    name: str = ""
    consent: bool = False

@app.post("/alerts/subscribe")
def alerts_subscribe(body: SubscribeIn):
    """Web opt-in form → consent recorded in data/subscribers.csv (status=active)."""
    import alert_pipeline
    if not body.consent:
        raise HTTPException(400, "Consent is required to receive alerts")
    digits = "".join(ch for ch in body.phone if ch.isdigit())
    if not (10 <= len(digits) <= 15):
        raise HTTPException(400, "Enter a valid WhatsApp number with country code (10-15 digits)")
    row = alert_pipeline.add_subscriber(digits, body.name.strip()[:60], "web opt-in form")
    return {"status": "subscribed", "phone": row["phone"],
            "consent_source": row["consent_source"], "consent_date": row["consent_date"]}

class ApproveIn(BaseModel):
    url: str
    how_it_works: str
    action: str

def _admin_ok(request: Request) -> bool:
    """ADMIN_KEY set → require X-Admin-Key. Unset → localhost only."""
    from notify_whatsapp import _env
    key = _env("ADMIN_KEY")
    if not key:
        host = (request.client.host if request.client else "") or ""
        return host in ("127.0.0.1", "::1", "localhost")
    return request.headers.get("x-admin-key") == key

@app.get("/alerts/pending")
def alerts_pending(request: Request):
    """Review queue (admin). Middleware-free simple gate — see _admin_ok."""
    import alert_pipeline
    if not _admin_ok(request):
        raise HTTPException(403, "Admin key required")
    rows = alert_pipeline.load_pending()
    queue = [r for r in rows if r.get("approved", "").lower() != "yes" and r.get("status") != "sent"]
    return {"pending": queue[-50:], "total": len(rows), "awaiting_review": len(queue)}

@app.post("/alerts/approve")
def alerts_approve(body: ApproveIn, request: Request):
    """Fill the two required text fields and set approved=yes (admin)."""
    import alert_pipeline
    if not _admin_ok(request):
        raise HTTPException(403, "Admin key required")
    if not body.how_it_works.strip() or not body.action.strip():
        raise HTTPException(400, "Both how_it_works and action are required before approval")
    row = alert_pipeline.approve_pending(body.url, body.how_it_works, body.action)
    if not row:
        raise HTTPException(404, "Alert not found in the review queue")
    return {"status": "approved", "row": row}

@app.get("/whatsapp/webhook")
def whatsapp_webhook_verify(request: Request):
    """Meta webhook verification handshake (Phase 3 / STOP handling).
    Meta sends dotted params: hub.mode, hub.verify_token, hub.challenge."""
    from fastapi.responses import PlainTextResponse
    from notify_whatsapp import _env
    q = request.query_params
    if q.get("hub.mode") == "subscribe" and q.get("hub.verify_token") == _env("WA_VERIFY_TOKEN", "scamshield"):
        return PlainTextResponse(q.get("hub.challenge") or "")
    return {"error": "verification failed", "hint": "set WA_VERIFY_TOKEN in backend/.env and the same in Meta console"}

@app.post("/whatsapp/webhook")
def whatsapp_webhook(body: dict):
    """Inbound WhatsApp messages (STOP/START) + delivery status callbacks."""
    import alert_pipeline
    result = alert_pipeline.handle_webhook(body)
    return {"ok": True, **result}

class SpeakReq(BaseModel):
    text: str
    lang: str | None = "en"

@app.post("/speak")
def speak(req: SpeakReq):
    """Server-side voice (gTTS mp3, cached by hash). Falls back to browser speech on failure."""
    import hashlib
    from pathlib import Path
    from fastapi.responses import FileResponse
    lang = {"hi": "hi", "mr": "mr"}.get((req.lang or "en"), "en")
    h = hashlib.sha256(f"{lang}:{req.text}".encode()).hexdigest()[:16]
    d = Path(__file__).parent / "static" / "tts"
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{h}.mp3"
    if not f.exists() or f.stat().st_size == 0:
        try:
            from gtts import gTTS
            gTTS(text=req.text[:500], lang=lang).save(str(f))
        except Exception as e:
            return {"error": f"TTS unavailable ({e}). Use the browser Listen button."}
    return FileResponse(str(f), media_type="audio/mpeg", filename=f"{h}.mp3")
