"""Alert pipeline + WhatsApp Cloud API tests — stdlib unittest, no network."""
import json
import tempfile
import unittest
import sys
import unittest.mock as mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import alert_pipeline
import whatsapp_cloud

RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>feeds</title>
<item><title>Fake KYC fraud link found in Delhi</title><link>https://news.example/a1</link></item>
<item><title>UPI refund scam targets bank customers</title><link>https://news.example/b2</link></item>
</channel></rss>"""


class TestData(unittest.TestCase):
    """Point alert_pipeline at a temp data dir for every test."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self._saved = {k: getattr(alert_pipeline, k) for k in
                       ("PENDING", "SUBSCRIBERS", "SUBSCRIBERS_EXAMPLE", "SENT_LOG")}
        alert_pipeline.PENDING = d / "pending.csv"
        alert_pipeline.SUBSCRIBERS = d / "subscribers.csv"
        alert_pipeline.SUBSCRIBERS_EXAMPLE = d / "subscribers.example.csv"
        alert_pipeline.SENT_LOG = d / "sent_log.csv"
        alert_pipeline.SUBSCRIBERS.write_text(
            "phone,name,status,consent_date,consent_source\n"
            "911111111111,Active Al,active,2026-10-01,form\n"
            "912222222222,Stopped Stu,stopped,2026-10-01,whatsapp keyword\n",
            encoding="utf-8")

    def tearDown(self):
        for k, v in self._saved.items():
            setattr(alert_pipeline, k, v)
        self.tmp.cleanup()


class TestPayload(unittest.TestCase):
    def test_three_var_template_shape(self):
        p = whatsapp_cloud.build_payload("+91 98765-43210", "KYC fraud", "desc", "act")
        self.assertEqual(p["messaging_product"], "whatsapp")
        self.assertEqual(p["type"], "template")
        self.assertEqual(p["to"], "919876543210")
        tpl = p["template"]
        self.assertEqual(tpl["name"], "scam_alert_notification")
        self.assertEqual(tpl["language"]["code"], "en_IN")
        params = tpl["components"][0]["parameters"]
        self.assertEqual(len(params), 3)
        self.assertEqual([x["text"] for x in params], ["KYC fraud", "desc", "act"])

    def test_fourth_source_var_added_when_provided(self):
        p = whatsapp_cloud.build_payload("911111111111", "a", "b", "c", source="https://x.in/report")
        params = p["template"]["components"][0]["parameters"]
        self.assertEqual(len(params), 4)
        self.assertEqual(params[3]["text"], "https://x.in/report")

    def test_msisdn_normalization(self):
        self.assertEqual(whatsapp_cloud.msisdn("+91-98765 43210"), "919876543210")
        self.assertEqual(whatsapp_cloud.msisdn("9876543210"), "919876543210")
        self.assertEqual(whatsapp_cloud.msisdn("00919876543210"), "919876543210")

    def test_broadcast_without_credentials_queues_outbox(self):
        with mock.patch.object(whatsapp_cloud, "is_configured", return_value=False), \
             mock.patch.object(whatsapp_cloud, "send_template") as st, \
             mock.patch.object(whatsapp_cloud, "_log_outbox") as lo:
            ok = whatsapp_cloud.broadcast_alert("KYC fraud", "d", "a", phones=["911111111111"])
        self.assertFalse(ok)
        st.assert_not_called()
        self.assertTrue(lo.called)


class TestCollect(TestData):
    def test_collect_dedupes_across_runs(self):
        first = alert_pipeline.collect(feeds=["fake://f"], fetcher=lambda u: RSS)
        self.assertEqual(first["new"], 2)
        second = alert_pipeline.collect(feeds=["fake://f"], fetcher=lambda u: RSS)
        self.assertEqual(second["new"], 0)
        self.assertEqual(second["queued"], 2)

    def test_classification_heuristic(self):
        self.assertEqual(alert_pipeline.classify("Fake KYC fraud link"), "KYC / bank verification fraud")
        self.assertEqual(alert_pipeline.classify("Lottery prize lure message"), "Lottery / prize fraud")
        self.assertEqual(alert_pipeline.classify("something odd"), "Scam campaign")


class TestSend(TestData):
    def _queue_one(self):
        alert_pipeline.PENDING.write_text(
            "id,source_url,title,scam_type,how_it_works,action,approved,status,added_at\n"
            "https://n/1,https://n/1,T1,KYC / bank verification fraud,d1,a1,yes,pending,2026-10-23\n"
            "https://n/2,https://n/2,T2,UPI / refund fraud,d2,a2,,pending,2026-10-23\n"
            "https://n/3,https://n/3,T3,Lottery / prize fraud,d3,a3,YES,sent,2026-10-23\n",
            encoding="utf-8")

    def test_only_approved_and_not_sent_rows_go_out(self):
        self._queue_one()
        with mock.patch.object(whatsapp_cloud, "is_configured", return_value=False), \
             mock.patch("notify_whatsapp._log_outbox"):
            s = alert_pipeline.send_approved()
        self.assertEqual(s["approved"], 1)
        self.assertEqual(s["queued"], 1)
        rows = {r["id"]: r for r in alert_pipeline.load_pending()}
        self.assertEqual(rows["https://n/1"]["status"], "queued")
        self.assertEqual(rows["https://n/2"]["status"], "pending")  # not approved yet

    def test_configured_send_marks_sent_and_logs(self):
        self._queue_one()
        with mock.patch.object(whatsapp_cloud, "is_configured", return_value=True), \
             mock.patch.object(whatsapp_cloud, "send_template", return_value={"ok": True, "id": "wamid.1"}), \
             mock.patch("notify_whatsapp._log_outbox"):
            s = alert_pipeline.send_approved()
        self.assertEqual(s["sent"], 1)   # only the active subscriber
        self.assertEqual(s["failed"], 0)
        rows = {r["id"]: r for r in alert_pipeline.load_pending()}
        self.assertEqual(rows["https://n/1"]["status"], "sent")
        log = alert_pipeline._read_csv(alert_pipeline.SENT_LOG, alert_pipeline.SENT_COLS)
        self.assertEqual([r["phone"] for r in log], ["911111111111"])  # stopped number untouched


class TestReviewAndConsent(TestData):
    def test_add_subscriber_upserts_and_records_consent(self):
        row = alert_pipeline.add_subscriber("+91 11111-11111", "Active Al", "web opt-in form")
        self.assertEqual(row["status"], "active")
        self.assertEqual(row["consent_source"], "web opt-in form")
        rows = alert_pipeline._read_csv(alert_pipeline.SUBSCRIBERS, alert_pipeline.SUB_COLS)
        self.assertEqual(len(rows), 2)  # no duplicate row for the same number
        self.assertEqual(sum(1 for r in rows if r["phone"] == "911111111111"), 1)

    def test_approve_pending_fills_copy_and_flags(self):
        alert_pipeline.PENDING.write_text(
            "id,source_url,title,scam_type,how_it_works,action,approved,status,added_at\n"
            "https://n/9,https://n/9,T9,KYC,d0,a0,,pending,2026-10-23\n", encoding="utf-8")
        row = alert_pipeline.approve_pending("https://n/9", "Updated copy", "Updated action")
        self.assertEqual(row["approved"], "yes")
        self.assertEqual(row["how_it_works"], "Updated copy")
        self.assertIsNone(alert_pipeline.approve_pending("https://missing", "x", "y"))


class TestWebhook(TestData):
    def test_stop_and_start_keywords(self):
        body = {"entry": [{"changes": [{"value": {"messages": [
            {"from": "911111111111", "text": {"body": " stop "}},
            {"from": "912222222222", "text": {"body": "START"}},
        ]}}]}]}
        with mock.patch("notify_whatsapp._log_outbox"):
            out = alert_pipeline.handle_webhook(body)
        self.assertEqual(out["stopped"], ["911111111111"])
        self.assertEqual(out["started"], ["912222222222"])
        subs = {r["phone"]: r["status"] for r in
                alert_pipeline._read_csv(alert_pipeline.SUBSCRIBERS, alert_pipeline.SUB_COLS)}
        self.assertEqual(subs["911111111111"], "stopped")
        self.assertEqual(subs["912222222222"], "active")

    def test_status_callbacks_do_not_crash(self):
        body = {"entry": [{"changes": [{"value": {"statuses": [
            {"id": "wamid.9", "status": "delivered"}]}}]}]}
        out = alert_pipeline.handle_webhook(body)
        self.assertEqual(out["statuses"][0]["status"], "delivered")

    def test_consent_gate_blocks_stopped(self):
        active = alert_pipeline.active_subscribers()
        self.assertEqual([r["phone"] for r in active], ["911111111111"])


if __name__ == "__main__":
    unittest.main()
