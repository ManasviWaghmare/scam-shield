# 🛡️ Scam Shield — SMS / WhatsApp scam detector

AI & Intelligent Systems · EN + Hindi + Marathi · Safe / Suspicious / Scam with a risk score,
plain-language reason, cited assistant, and a consent-gated WhatsApp alert pipeline.

## Structure
```
scam-shield/
  backend/
    main.py              # FastAPI API (check, trends, history, stats, alerts, assistant, webhooks)
    scheduler.py         # 6 APScheduler jobs (Asia/Kolkata)
    classifier.py        # TF-IDF + LogReg baseline (MuRIL opt-in via SCAMSHIELD_MODEL)
    rules.py             # URL, urgency, OTP/PIN, KYC/job/lottery patterns
    explainer.py         # 0.6·ML + 0.4·rules fusion + EN/HI/MR explanations
    ocr.py               # Tesseract eng+hin+mar screenshot OCR
    database.py          # SQLite: scans (hash only), threat_cache, trends
    assistant/           # TrustRAG-lite: retrieval, citations, safety, offline fallback
    whatsapp_cloud.py    # official Meta Cloud API template sender
    alert_pipeline.py    # collect → review → send, subscribers + STOP webhook
    tests/               # 33 unittest tests (pipeline, assistant, alerts)
    data/                # 166-row trilingual dataset, review queue, subscribers
  frontend-react/        # React 18 + Vite + Tailwind (dark HEXLY theme, PWA)
    src/pages/           # Home, Dashboard, Learn, Chat, About, Subscribe, Review
  docs/                  # WHATSAPP_ALERTS.md, TRUSTRAG_INTEGRATION.md
  chrome-extension/      # MV3 popup scanner
  Dockerfile · docker-compose.yml · .github/workflows/ci.yml
```

## Quick run
```bash
# Backend (port 8001 — 8000 is often taken)
cd scam-shield/backend
source ../.venv/bin/activate          # or: python -m venv ../.venv && pip install -r ../requirements.txt
python train.py                       # only if models/scam_clf.joblib is missing
uvicorn main:app --reload --host 127.0.0.1 --port 8001

# Frontend (second terminal)
cd scam-shield/frontend-react
npm install
npm run dev -- --host 127.0.0.1 --port 5174     # open http://127.0.0.1:5174
```

Try:
- KYC scam: `Dear customer your SBI KYC expired urgently verify at http://sbi-kyc-update.xyz within 24 hours`
- Hindi lottery: `बधाई हो! आपने 25000 की लॉटरी जीती है http://inam-claim.top पर Rs 99 फीस देकर पाएं`
- Safe: `Meeting at 5pm tomorrow bring the report thanks`

## Main endpoints
| Area | Endpoints |
|---|---|
| Detection | `POST /check`, `POST /check-image`, `POST /speak` |
| Dashboard | `GET /trends`, `GET /history`, `GET /stats`, `GET /scheduler-status` |
| Assistant | `POST /assistant/chat`, `GET /assistant/sources`, `GET /assistant/health` |
| Alerts | `POST /alerts/collect`, `POST /alerts/send`, `POST /alerts/test`, `POST /alerts/subscribe`, `GET /alerts/pending`, `POST /alerts/approve`, `GET /alerts` |
| WhatsApp | `GET /whatsapp/webhook` (verify), `POST /whatsapp/webhook` (STOP/START + statuses) |

## Scheduler (6 jobs, Asia/Kolkata)
| Job | Schedule | Why |
|---|---|---|
| `refresh_threat_intel` | every 6h | PhishTank live sync + seed domains; alerts on new threats |
| `aggregate_trends` | every 1h | community dashboard without storing PII |
| `privacy_purge` | daily 00:05 | deletes scans >24h, keeps only hashes |
| `daily_tip_push` | daily 09:00 | awareness nudge EN/HI/MR |
| `standup_nudge` | daily 21:05 | standup reminder |
| `alert_queue` | every 6h (:30) | fills `data/pending.csv` review queue from scam-news feeds |

## WhatsApp alert pipeline
`collect → human review (approved=yes) → send`, consent-gated subscribers, STOP handling.
See `docs/WHATSAPP_ALERTS.md`.

```bash
python alert_pipeline.py collect   # fill review queue (also every 6h)
python alert_pipeline.py pending   # inspect queue
python alert_pipeline.py send      # only approved rows → active subscribers
```
Without Meta credentials every send is rendered to `GET /alerts` (outbox) — the demo never
pretends a message was delivered.

## Honest metrics
| Evaluation | Result | Note |
|---|---|---|
| 38 hand-written messages | **87.5%** | headline number |
| 166-row template split | **100%** | optimistic — same-template leakage |
| Train on templates → test hand-written | **65.8%** | the gap MuRIL is meant to close |
| Tests | **33/33** | pipeline + assistant + citations + safety + alerts |

## Tests
```bash
cd backend && source ../.venv/bin/activate
python -m unittest discover -s tests
```

## Privacy
Raw messages are never stored — only a SHA-256 hash + verdict + category. PII is masked
before display and purged after 24h. Subscriber numbers live in a git-ignored CSV with
consent date + source.

## Docs
- `docs/WHATSAPP_ALERTS.md` — Cloud API setup, review gate, STOP handling, n8n equivalent
- `docs/TRUSTRAG_INTEGRATION.md` — why TrustRAG-lite instead of the full framework
