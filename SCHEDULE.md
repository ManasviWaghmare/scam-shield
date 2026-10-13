# 🗓️ Scam Shield — Day-wise Checklist (3rd → 10th Oct 2026)
Team: SOLO (Manasvi) | Backend freeze: **5th Oct** | Hack: Hack-A-Throne 2026 (Online)
Frontend: React + Tailwind (`frontend-react/`) | WhatsApp: CallMeBot | Simple HTML kept as backup in `frontend/`

> Solo mode: do 1 box per day max, 2hrs/day. Order is fixed: Backend → DB → Frontend.

> Tick boxes as you go. Daily 15-min standup 9PM on WhatsApp group.

## Roles (pick for 2-4 people)
- [ ] **Member A — Backend + AI:** `classifier.py`, `rules.py`, `train.py`, accuracy number
- [ ] **Member B — API + Scheduler + DB:** `main.py`, `scheduler.py`, `database.py`, WhatsApp notify
- [ ] **Member C — Frontend + Demo:** `frontend/index.html`, voice, trends UI, demo video
- [ ] **Member D (if 4th) — Docs + Testing:** README, Unstop text, PPT, test 20 messages EN/HI/MR
- [ ] WhatsApp group created + all numbers added for scheduler alerts

---

## 3rd Oct (Sat, Today) — Backend Core
### Backend + AI (A)
- [ ] Run `python train.py` in `backend/` → note accuracy (current baseline 87.5%)
- [ ] Test 3 messages via `full_check()`: KYC scam → Scam, Hindi lottery → Scam, meeting msg → Safe
- [ ] Add 10 more synthetic Hindi/Marathi rows to `data/synthetic_dataset.csv` if accuracy <85%
- [ ] Commit: `backend-core-day1`

### API + Scheduler (B)
- [ ] `uvicorn main:app --reload` boots without error
- [ ] `GET /scheduler-status` shows 4 jobs: threat_refresh, trends, purge, tip
- [ ] Console shows `[Scheduler] Threat cache updated` + `[Scheduler] Trends saved`

### Frontend (C)
- [ ] Open `frontend/index.html` → backend URL set to `http://127.0.0.1:8000`
- [ ] Paste-box check works for 1 scam sample

### Docs (D)
- [ ] GitHub repo created, `scam-shield/` pushed
- [ ] Unstop draft opened, domain selected

**Exit criteria 3rd:** `/check` returns verdict+score+explanation for EN/HI/MR.

---

## 4th Oct (Sun) — Scheduler + OCR + WhatsApp
### Backend + AI (A)
- [ ] `rules.py` tested: short link (+0.25), OTP/PIN (+0.30), urgency (+0.20) scoring
- [ ] `explainer.py` tested: highlights list non-empty for scam, empty for safe
- [ ] OCR install: `sudo apt install tesseract-ocr tesseract-ocr-hin tesseract-ocr-mar`
- [ ] `POST /check-image` tested with 1 WhatsApp screenshot

### API + Scheduler + WhatsApp (B)
- [ ] `notify_whatsapp.py` created (CallMeBot key added in `.env`, NOT in git)
- [ ] `daily_tip_push()` sends WhatsApp: “Scam Shield daily tip” to self number — screenshot proof
- [ ] `refresh_threat_intel()` upserts 5+ domains, verified via `lookup_threat()`
- [ ] `aggregate_trends()` saves after 10 test `/check` calls, verified via `GET /trends`

### Frontend (C)
- [ ] Screenshot upload button wired to `/check-image`
- [ ] Speak button (Web Speech API) works for EN/HI/MR

### Docs (D)
- [ ] 20-message test sheet started (text, expected, got, pass/fail)

**Exit criteria 4th:** WhatsApp alert received on phone + OCR works.

---

## 5th Oct (Mon) — BACKEND FREEZE 🧊
- [ ] Full matrix test (A+B): 5 EN + 5 HI + 5 MR (mix scam/safe) → all correct verdict family
- [ ] `GET /trends`, `/report-info`, `/scheduler-status` all 200 OK
- [ ] No raw message text in DB: check `scans` table has only `message_hash`
- [ ] Tag commit: `backend-v1-freeze` — **NO new backend features after today, only bugfixes**
- [ ] 30-sec screen recording: terminal scheduler logs + API responses (for viva)
- [ ] Update Unstop Proposed Solution with final accuracy number

**Exit criteria 5th:** Backend frozen. If it breaks, fix only, don’t add.

---

## 6th Oct (Tue) — DB Day 🗄️
Owner: B, help A
- [ ] `database.py init_db()` recreates `scans, threat_cache, trends, tips` cleanly
- [ ] Seed 20+ threat indicators (domains + short links) in `threat_cache`
- [ ] `privacy_purge()` test: insert row with old timestamp → purge deletes it
- [ ] `aggregate_trends()` hourly test: 10 scans → `/trends` shows counts by category
- [ ] `.gitignore` has `*.db`, `*.joblib`, `.env` (no secrets pushed)
- [ ] Decide: stay on SQLite (recommended for hackathon) OR note Postgres path in README

**Exit criteria 6th:** Delete `scamshield.db`, re-run `init_db()+train`, full flow still passes.

---

## 7th Oct (Wed) — Frontend Build 🎨
Owner: C, help D
- [ ] 3 demo buttons work: KYC scam / Lottery HI / Safe
- [ ] Verdict card shows: color badge (red/orange/green) + score% + category + lang
- [ ] Explanation + red-flags + links + highlights rendered
- [ ] Trends section loads `GET /trends` (hourly data note visible)
- [ ] Helpline box: “Call 1930, cybercrime.gov.in” always visible
- [ ] Mobile responsive check (360px width, no overflow)

---

## 8th Oct (Thu) — Integration + Polish ✨
All members
- [ ] End-to-end: frontend → backend → DB → scheduler → WhatsApp, on 2 laptops
- [ ] Voice output tested in Hindi + Marathi on Chrome
- [ ] Edge cases: empty msg, very long msg, image with no text → friendly error
- [ ] Add loading spinner + “scheduler: running ✅” status in header
- [ ] Freeze frontend: `frontend-v1-freeze`

---

## 9th Oct (Fri) — Submission Pack 📦
Owner: D, all review
- [ ] README final: structure + run steps + accuracy + scheduler table + privacy note
- [ ] Unstop fields pasted: Problem, Solution (with scheduler step 6), Description, Tech Stack <500 chars
- [ ] GitHub public + README + Dockerfile + demo screenshots
- [ ] 5-slide PPT: Problem → Solution+Architecture (with scheduler lane) → Demo → Impact → Next (Chrome extn)
- [ ] 2-min demo video script rehearsed (see below)

## 10th Oct (Sat) — Buffer + Submit 🚀
- [ ] Final video recorded + uploaded (unlisted YouTube / Loom)
- [ ] Unstop Submit clicked before 11PM, screenshot of confirmation in WhatsApp group
- [ ] Backup: zip `scam-shield/` to Drive

---

## 2-min Demo Script (use for video)
1. (0:00-0:20) Problem: “1 tap on KYC SMS drains account, filters don’t work in Hindi/Marathi.”
2. (0:20-1:00) Paste KYC scam → show Scam 80% + highlights + Hindi explanation + voice. Upload screenshot → same.
3. (1:00-1:30) Show `/scheduler-status` 4 jobs + terminal logs + WhatsApp daily tip on phone + `/trends` dashboard.
4. (1:30-2:00) Privacy (hash only, purge daily) + impact + next: Chrome extension, MuRIL fine-tune.

## Daily WhatsApp Alerts (auto via scheduler)
- 9:00 AM — scam-of-the-day tip (EN/HI/MR) → WhatsApp group
- 9:05 PM — standup reminder: reply with ✅/❌ + blocker
- On freeze days (5th/8th/10th) — “Freeze today, push tag” reminder
See `backend/notify_whatsapp.py` + `.env` setup. Never commit `.env`.

## Definition of Done
- [ ] Backend frozen 5th, DB done 6th, Frontend done 8th, Submitted 10th
- [ ] Accuracy number in Unstop matches `train.py` output
- [ ] Scheduler proven: logs + WhatsApp screenshot + trends data
- [ ] No secrets in git (`git status` clean, `.env` ignored)
