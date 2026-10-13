# 🛡️ Scam Shield — WhatsApp/SMS Scam Detector (with Scheduler)

AI & Intelligent Systems | EN + Hindi + Marathi | Safe/Suspicious/Scam + risk score + plain-language reason.

## Full structure
```
scam-shield/
  requirements.txt
  Dockerfile
  README.md
  backend/
    main.py          # FastAPI API + lifespan (starts scheduler)
    scheduler.py     # ⭐ 4 jobs: threat refresh / trends / purge / daily tip
    classifier.py    # TF-IDF baseline (swap with MuRIL/IndicBERT later)
    rules.py         # URL, urgency, OTP/PIN, KYC/job/lottery patterns
    explainer.py     # verdict fusion + EN/HI/MR explanations + highlights
    ocr.py           # Tesseract OCR (eng+hin+mar) for screenshots
    database.py      # SQLite: scans, threat_cache, trends
    train.py         # train baseline
    data/synthetic_dataset.csv  # 40 EN/HI/MR examples to start
    models/          # trained .joblib (after train)
  frontend/
    index.html       # demo UI (no build needed) + voice + trends
```

## Quick run (2 min demo)
```bash
cd scam-shield/backend
pip install -r ../requirements.txt
python train.py        # prints Accuracy — put it in Unstop form
uvicorn main:app --reload
# open frontend: double-click ../frontend/index.html
# or: python -m http.server 5500 --directory ../frontend
```

Try:
- KYC scam: `Dear customer your SBI KYC expired urgently verify at http://sbi-kyc-update.xyz within 24 hours`
- Hindi lottery: `बधाई हो! आपने 25000 की लॉटरी जीती है http://inam-claim.top पर Rs 99 फीस देकर पाएं`
- Safe: `Meeting at 5pm tomorrow bring the report thanks`

Check scheduler live:
- `GET /scheduler-status` → 4 jobs running
- Console logs: `[Scheduler] Refreshing threat intel... / Aggregating trends...`
- `GET /trends` → hourly-aggregated dashboard data

## Scheduler (for submission + viva)
| Job | Schedule | Why |
|---|---|---|
| `refresh_threat_intel` | every 6h | keeps URL blacklist fresh (PhishTank/OpenPhish) |
| `aggregate_trends` | every 1h | community dashboard without storing PII |
| `privacy_purge` | daily 00:05 | deletes raw scans >24h, stores only hash |
| `daily_tip_push` | daily 09:00 IST | awareness nudge EN/HI/MR |

Built on APScheduler AsyncIOScheduler, Asia/Kolkata, started in FastAPI lifespan.

## Upgrade path (if judges ask)
- Replace `classifier.py` with fine-tuned `google/muril-base-cased` on UCI SMS Spam + synthetic HI/MR (same function signature).
- Add SHAP for token highlights; LLM API only for final sentence.
- Add Chrome extension calling `POST /check`.
- Postgres + Redis + Docker for prod (Dockerfile included).

## Unstop fields
- Domain: AI & Intelligent Systems
- Helpline to quote: 1930, portal cybercrime.gov.in
- Metric: run `python train.py` and write "achieved XX% accuracy on 40 test messages (baseline; MuRIL target 90%+)"

## Privacy
Raw messages never stored — only SHA hash + verdict + category. PII masked before display.
