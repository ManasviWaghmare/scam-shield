"""WhatsApp Business Cloud API (official Meta) — scam-alert template sender.

Implements Phases 1-4 of the alert automation plan (docs/WHATSAPP_CLOUD_API.md):
  Phase 1  Meta Business Suite → WhatsApp Cloud API → token + phone number ID
  Phase 2  WhatsApp Manager → template "scam_alert_notification" (en_IN) → approve
  Phase 3  Trigger logic → scheduler.refresh_threat_intel() calls broadcast_alert()
  Phase 4  Sandbox test → POST /alerts/test  or  python whatsapp_cloud.py
  Phase 5  Go-live → business verification + opt-in numbers in ALERT_PHONES

Env (backend/.env — NEVER committed):
  WA_CLOUD_TOKEN=EAAG...          permanent system-user access token
  WA_PHONE_NUMBER_ID=10987654321  from the API setup screen
  WA_TEMPLATE_NAME=scam_alert_notification
  WA_TEMPLATE_LANG=en_IN
  ALERT_PHONES=91XXXXXXXXXX,91YYYYYYYYYY   (opt-in recipients only)

Fallback: with no credentials every alert appends to alerts_outbox.log and is
visible at GET /alerts — demo works without Meta approval.
"""
import json
import urllib.error
import urllib.request
from datetime import datetime

from notify_whatsapp import _env, _log_outbox

GRAPH = "https://graph.facebook.com"
API_VERSION = "v20.0"
DEFAULT_TEMPLATE = "scam_alert_notification"
DEFAULT_LANG = "en_IN"


def is_configured() -> bool:
    token = _env("WA_CLOUD_TOKEN")
    phone_id = _env("WA_PHONE_NUMBER_ID")
    return bool(token and phone_id and "REPLACE" not in token and not phone_id.startswith("REPLACE"))


def msisdn(phone: str) -> str:
    """Normalize to Meta format: digits only, country code, no + / spaces / dashes."""
    d = "".join(ch for ch in str(phone) if ch.isdigit())
    if d.startswith("00"):
        d = d[2:]
    if len(d) == 10 and d[0] in "6789":
        d = "91" + d
    return d


def build_payload(to: str, scam_type: str, description: str, action: str, source: str | None = None) -> dict:
    """Exact Meta Cloud API template payload for scam_alert_notification (en_IN).
    4th variable (source link) is appended only when provided — matches the
    template submitted with 4 parameters."""
    params = [
        {"type": "text", "text": str(scam_type)},
        {"type": "text", "text": str(description)},
        {"type": "text", "text": str(action)},
    ]
    if source:
        params.append({"type": "text", "text": str(source)})
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": msisdn(to),
        "type": "template",
        "template": {
            "name": _env("WA_TEMPLATE_NAME", DEFAULT_TEMPLATE) or DEFAULT_TEMPLATE,
            "language": {"code": _env("WA_TEMPLATE_LANG", DEFAULT_LANG) or DEFAULT_LANG},
            "components": [
                {
                    "type": "body",
                    "parameters": params,
                }
            ],
        },
    }


def alert_body(scam_type: str, description: str, action: str, source: str | None = None) -> str:
    """Human-readable rendering of the approved template copy (for outbox/demo)."""
    text = (
        "🚨 CRITICAL SCAM ALERT 🚨\n"
        f"We have detected a new wave of {scam_type} targeting users.\n"
        f"How it works: {description}\n"
        f"Safety Action Required: {action}\n"
        "Stay safe. Do not share personal information or OTPs over the phone."
    )
    if source:
        text += f"\nSource: {source}"
    return text


def send_template(to: str, scam_type: str, description: str, action: str, source: str | None = None) -> dict:
    """POST one template message. Returns {ok, id|error}. Raises nothing."""
    token = _env("WA_CLOUD_TOKEN")
    phone_id = _env("WA_PHONE_NUMBER_ID")
    payload = build_payload(to, scam_type, description, action, source)
    url = f"{GRAPH}/{API_VERSION}/{phone_id}/messages"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = json.loads(r.read().decode(errors="ignore") or "{}")
            mid = body.get("messages", [{}])[0].get("id")
            print(f"[WA Cloud] sent ✅ to {payload['to']} id={mid}")
            return {"ok": True, "id": mid, "to": payload["to"]}
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="ignore")[:300]
        print(f"[WA Cloud] failed ❌ HTTP {e.code}: {detail}")
        return {"ok": False, "status": e.code, "error": detail, "to": payload["to"]}
    except Exception as e:
        print(f"[WA Cloud] failed ❌: {e}")
        return {"ok": False, "error": str(e), "to": payload["to"]}


def broadcast_alert(scam_type: str, description: str, action: str, phones: list[str] | None = None,
                    source: str | None = None) -> bool:
    """Phase 3 trigger: send the alert template to every opt-in phone.

    No credentials → render into alerts_outbox.log (GET /alerts) so the demo
    still shows what WOULD be sent.
    """
    body = alert_body(scam_type, description, action, source)
    if phones is None:
        raw = _env("ALERT_PHONES", _env("TEAM_PHONES", _env("CALLMEBOT_PHONE")))
        phones = [p.strip() for p in raw.split(",") if p.strip()]

    if not is_configured() or not phones:
        reason = "no WA_CLOUD_TOKEN/WA_PHONE_NUMBER_ID" if not is_configured() else "no ALERT_PHONES"
        print(f"[WA Cloud] QUEUED locally → alerts_outbox.log ({reason})")
        _log_outbox(body)
        return False

    ok = False
    for p in phones:
        res = send_template(p, scam_type, description, action)
        ok = ok or res.get("ok")
        if not res.get("ok"):
            _log_outbox(f"[fallback to phone {p}] {body}")
    return ok


def threat_alert(new_domains: list[str]) -> bool:
    """Build the 3 template variables from newly-verified threat indicators."""
    example = new_domains[0]
    extra = len(new_domains) - 1
    description = (
        f"New malicious link verified: {example}"
        + (f" (and {extra} more synced this cycle)" if extra else "")
    )
    return broadcast_alert(
        scam_type="Phishing / fake-link campaign",
        description=description,
        action="Do not click links from unknown senders or share OTPs. Verify at cybercrime.gov.in or call 1930.",
    )


if __name__ == "__main__":
    import sys
    phone = sys.argv[1] if len(sys.argv) > 1 else _env("WA_PHONE_NUMBER_ID") and _env("ALERT_PHONES", "").split(",")[0]
    if not phone or phone == "None":
        print("Usage: python whatsapp_cloud.py 91XXXXXXXXXX   (Meta sandbox number)")
        raise SystemExit(1)
    if not is_configured():
        print("Not configured — printing the payload that WOULD be sent:")
        print(json.dumps(build_payload(phone, "Electricity Bill Fraud",
                                       "Fake call claiming power will be cut in 30 minutes",
                                       "Do not click the link or share OTP"), indent=2))
        raise SystemExit(0)
    r = send_template(phone, "Electricity Bill Fraud",
                      "Fake call claiming power will be cut in 30 minutes",
                      "Do not click the link or share OTP")
    print(json.dumps(r, indent=2))
