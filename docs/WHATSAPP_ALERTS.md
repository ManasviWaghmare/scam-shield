# WhatsApp Scam Alerts — Python Pipeline (official Cloud API)

How automated scam alerts work in this repo: **collect → human review → send**, with
consented subscribers and STOP handling. The no-code (n8n) equivalent is in the last section.

Code: `backend/whatsapp_cloud.py` (sender), `backend/alert_pipeline.py` (collect/send/webhook),
`backend/scheduler.py::collect_alert_queue` (6-hour trigger).

---

## Combined roadmap

| Stage | What | Audience | Where it lives here |
|---|---|---|---|
| **1. Prototype** | Meta test number, 1-5 verified recipients, template approval | You + family | `backend/.env` `WA_*` keys, `data/subscribers.csv` |
| **2. Harden** | Permanent token, dedupe, **approval gate**, logging, STOP handling | Same | `collect()` dedupe, `approved=yes` gate, `sent_log.csv`, `/whatsapp/webhook` |
| **3. Scale** | Business verification, own number, opt-in form, consent records | Public | `subscribers.csv` columns `consent_date,consent_source` already enforced |
| **4. Optimize** | Daily digest template, quality rating, cost review | Subscribers | Change `WA_TEMPLATE_NAME` + schedule; nothing else changes |

---

## Template (Meta-approved copy)

Payload built by `whatsapp_cloud.build_payload()`:

```json
{
  "messaging_product": "whatsapp",
  "recipient_type": "individual",
  "to": "<digits with country code>",
  "type": "template",
  "template": {
    "name": "scam_alert_notification",
    "language": { "code": "en_IN" },
    "components": [
      { "type": "body", "parameters": [
        { "type": "text", "text": "<1 scam type>" },
        { "type": "text", "text": "<2 how it works>" },
        { "type": "text", "text": "<3 safety action>" },
        { "type": "text", "text": "<4 source link> (optional)" }
      ] }
    ]
  }
}
```

What the user receives:

> 🚨 CRITICAL SCAM ALERT 🚨
> We have detected a new wave of **{{1}}** targeting users.
> How it works: **{{2}}**
> Safety Action Required: **{{3}}**
> Stay safe. Do not share personal information or OTPs over the phone.
> Source: **{{4}}**

---

## Python route — commands

All commands run from `backend/` inside the venv.

```bash
# Phase 3: fill the review queue (also runs every 6h via scheduler job "alert_queue")
python alert_pipeline.py collect

# Human gate: open data/pending.csv, fill how_it_works + action, set approved=yes
python alert_pipeline.py pending          # print the queue

# Send only approved=yes rows to status=active subscribers
python alert_pipeline.py send

# Add yourself (Phase 1 opt-in — consent columns are mandatory)
python alert_pipeline.py subscribe 91XXXXXXXXXX YourName "self opt-in for Phase 1"
```

Or via HTTP once the API is up:

```bash
curl -X POST http://127.0.0.1:8001/alerts/collect
curl -X POST http://127.0.0.1:8001/alerts/send
curl -X POST http://127.0.0.1:8001/alerts/test -H 'Content-Type: application/json' \
  -d '{"phone":"91XXXXXXXXXX"}'          # Phase 4 sandbox check
```

Without `WA_CLOUD_TOKEN` / `WA_PHONE_NUMBER_ID` every send is **rendered to
`alerts_outbox.log`** (`GET /alerts`) with the exact approved copy — the demo never
silently pretends to send.

### Review gate (why it exists)

`send_approved()` only ships rows where `approved=yes` **and** `status` is not
already `sent/queued`. Unreviewed feed items can never reach a phone. Dedupe is by
item URL across `pending.csv` + `sent_log.csv`, so re-running `collect` is safe.

### STOP handling (Phase 3 requirement)

`GET /whatsapp/webhook` — Meta's verification handshake (`hub.challenge`).
`POST /whatsapp/webhook` — inbound text `STOP/STOPALL/CANCEL/UNSUBSCRIBE/END` sets
the sender to `status=stopped`; `START/JOIN` re-activates (logged with consent
source `whatsapp keyword`). Delivery status callbacks are recorded.

Set `WA_VERIFY_TOKEN` in `backend/.env` to the same string you enter in Meta console.

---

## Subscriber consent rules

`data/subscribers.csv` (git-ignored — never commit phone numbers):

```
phone,name,status,consent_date,consent_source
```

- Only `status=active` rows are ever messaged (`active_subscribers()`).
- New opt-ins must carry `consent_date` + `consent_source` (`subscribe()` enforces this).
- `data/subscribers.example.csv` is the committed template; the real file is created on first run.
- **Delete test-number rows before any production broadcast.**

---

## No-code route: n8n equivalent

1. **Collector** — Schedule Trigger (`0 */6 * * *`) → RSS Feed Read (your feed URLs) →
   Code node dedupe by `link` (keep a `seen` array) → Google Sheets *Append row*
   (`title, scam_type, approved` empty, `how_it_works`, `action`).
2. **Sender** — Google Sheets Trigger (rows where `approved = yes`) → *Get rows where
   status = active* → Loop → **WhatsApp Business Cloud** node → Send Template
   (`scam_alert_notification`, 4 variables) → update row `status = sent`.
3. **Unsubscribe** — WhatsApp Trigger → IF `lowercase(body)` in STOP list → update
   subscriber `status = stopped`.

Same data contract as the Python route, so you can switch tools without migrating.

---

## Verify before relying on it

- **Feed URLs** — `FEEDS` in `alert_pipeline.py` uses Google News RSS placeholders;
  add official CERT-In / RBI / I4C / FTC feeds once you confirm their current addresses.
- **Template language** — `WA_TEMPLATE_LANG` must equal the code you selected when
  submitting the template (`en` vs `en_IN`).
- **Graph API version + pricing** — `whatsapp_cloud.API_VERSION` (currently `v20.0`);
  check Meta's current version and India per-message template rates.
- **Opt-in** — importing numbers without consent is the fastest route to a Meta ban.
  `active_subscribers()` is the single choke point; do not bypass it.
