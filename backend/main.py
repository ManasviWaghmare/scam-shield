"""Scam Shield API — FastAPI + APScheduler."""
import hashlib
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form
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
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class CheckReq(BaseModel):
    message: str
    lang: str | None = None

def mask_pii(text: str) -> str:
    import re
    text = re.sub(r"\b\d{10,13}\b", "***PHONE***", text)
    text = re.sub(r"\b\d{12,16}\b", "***ACCT***", text)
    text = re.sub(r"\b\d{4,6}\b", "***OTP?***", text)
    return text

def full_check(message: str, lang=None):
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
    # privacy: store only hash, never raw text
    h = hashlib.sha256(message.encode()).hexdigest()[:16]
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
