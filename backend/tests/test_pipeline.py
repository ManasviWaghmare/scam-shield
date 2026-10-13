"""Scam Shield pipeline tests — stdlib only: python -m unittest discover -s tests -v"""
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import classifier
import rules
import explainer
import database


class TestClassifier(unittest.TestCase):
    def test_scam_sample(self):
        label, conf = classifier.predict_proba(
            "Dear customer your SBI KYC expired urgently verify at http://sbi-kyc-update.xyz")
        self.assertIn(label, ("scam", "suspicious"))
        self.assertGreaterEqual(conf, 0.4)

    def test_safe_sample(self):
        label, _ = classifier.predict_proba("Meeting at 5pm tomorrow bring the report thanks")
        self.assertEqual(label, "safe")

    def test_explain_tokens(self):
        toks = classifier.explain_tokens(
            "Dear customer your SBI KYC expired urgently verify at http://sbi-kyc-update.xyz")
        self.assertIsInstance(toks, list)
        self.assertTrue(all("token" in t and "weight" in t for t in toks))

    def test_category(self):
        self.assertEqual(classifier.predict_category("kyc expired verify now"), "Fake KYC")


class TestRules(unittest.TestCase):
    def test_url_extract(self):
        self.assertIn("http://sbi-kyc-update.xyz",
                      rules.extract_urls("verify at http://sbi-kyc-update.xyz now"))

    def test_otp_raises_risk(self):
        out = rules.analyze("share your OTP now")
        self.assertGreater(out["rule_risk"], 0.2)
        self.assertTrue(any("OTP" in s or "secret" in s for s in out["signals"]))


class TestFusion(unittest.TestCase):
    def test_strong_rules_force_scam(self):
        verdict, score = explainer.fuse_verdict("safe", 0.9, 0.8)
        self.assertEqual(verdict, "Scam")

    def test_clean_is_safe(self):
        verdict, _ = explainer.fuse_verdict("safe", 0.9, 0.0)
        self.assertEqual(verdict, "Safe")


class TestAPI(unittest.TestCase):
    def test_full_check_shape(self):
        from main import full_check
        out = full_check("Your SBI KYC expired verify at http://sbi-kyc-update.xyz")
        for key in ("verdict", "score", "category", "signals", "highlights",
                    "model_tokens", "ml_label", "rule_risk", "explanation"):
            self.assertIn(key, out)

    def test_db_stats(self):
        database.init_db()
        s = database.get_stats()
        self.assertIn("total_scans", s)


if __name__ == "__main__":
    unittest.main()
