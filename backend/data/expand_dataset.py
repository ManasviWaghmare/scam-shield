"""Expand the trilingual dataset with seeded template variations (deterministic).
Keeps the original 40 rows, appends generated rows to reach ~200 total.
Run: python data/expand_dataset.py && python train.py
"""
import csv
import random
from pathlib import Path

HERE = Path(__file__).parent
CSV = HERE / "synthetic_dataset.csv"
rng = random.Random(20261007)

BANKS = ["SBI", "HDFC", "ICICI", "Paytm", "PhonePe", "Axis"]
DOMAINS = ["sbi-kyc-update.xyz", "prize-claim.top", "paytm-kyc09.buzz", "mega-loot.xyz",
           "itrefund.top", "bit.ly/3xKyc9", "upi-refund.top", "job-earn.xyz"]
AMOUNTS = ["1999", "4999", "9999", "25000", "50000", "2500", "999", "15000"]

SCAM_T = {
    "en": [
        "Dear customer your {b} KYC expired urgently verify at http://{d} within 24 hours else account blocked",
        "Your {b} account will be SUSPENDED click http://{d} to update PAN now",
        "Congratulations! You won Rs {a} lottery claim at http://{d} entry fee Rs 99",
        "Part-time job earn Rs {a} per day work from home pay Rs 500 registration fee on UPI",
        "UPI refund of Rs {a} pending share your UPI PIN to receive money at http://{d}",
        "Income tax refund Rs {a} approved verify bank details at http://{d}",
        "Credit card reward points expiring redeem at http://{d} with OTP",
        "Your son is in police custody send Rs {a} immediately or case will be filed",
    ],
    "hi": [
        "आपका {b} KYC समाप्त हो गया है तुरंत http://{d} पर verify करें वरना खाता बंद हो जाएगा",
        "बधाई हो! आपने {a} की लॉटरी जीती है http://{d} पर Rs 99 फीस देकर पाएं",
        "घर बैठे नौकरी Rs {a} रोज कमाएं पहले Rs 300 रजिस्ट्रेशन फीस UPI पर भेजें",
        "आपका UPI रिफंड Rs {a} अटका है पैसे पाने के लिए अपना UPI PIN बताएं",
        "आपका {b} खाता बंद हो जाएगा http://{d} पर तुरंत अपडेट करें",
    ],
    "mr": [
        "तुमचे {b} KYC संपले आहे तात्काळ http://{d} वर verify करा नाहीतर खाते बंद होईल",
        "अभिनंदन! तुम्ही {a} लॉटरी जिंकली http://{d} वर Rs 99 फी भरून घ्या",
        "घरबसल्या नोकरी Rs {a} रोज कमवा आधी Rs 500 UPI वर पाठवा",
        "तुमचा UPI refund Rs {a} अडकला आहे पैसे मिळवण्यासाठी UPI PIN सांगा",
    ],
}
SUSP_T = {
    "en": ["Your {b} OTP is {a} to verify login never share it",
           "Hi mom I changed my number please send Rs {a} urgently on this UPI"],
    "hi": ["आपका OTP {a} है किसी के साथ शेयर न करें"],
    "mr": ["तुमचा OTP {a} आहे कोणासोबतही शेअर करू नका"],
}
SAFE_T = {
    "en": ["Meeting at 5pm tomorrow bring the report thanks",
           "Your electricity bill due pay on official app ignore fake SMS asking OTP",
           "Bank never asks for OTP PIN CVV on call says RBI guideline stay safe",
           "Hi just checking train tickets for tomorrow confirmed?",
           "Dinner at 8pm today at home see you"],
    "hi": ["कल शाम 5 बजे मीटिंग है रिपोर्ट लेकर आना धन्यवाद",
           "आपका बिजली बिल बकाया है आधिकारिक ऐप से भरें OTP मांगने वाले SMS से बचें",
           "बैंक कभी कॉल पर OTP PIN नहीं मांगता सतर्क रहें",
           "कल की ट्रेन टिकट कन्फर्म हो गई क्या?"],
    "mr": ["उद्या संध्याकाळी 5 वाजता मीटिंग आहे अहवाल घेऊन या",
           "तुमचे वीज बिल थकले आहे अधिकृत अ‍ॅपवरून भरा OTP मागणाऱ्या SMS पासून सावध रहा",
           "बँक कधीही कॉलवर OTP PIN मागत नाही सतर्क रहा",
           "उद्याचे ट्रेन तिकीट कन्फर्म झाले का?"],
}

def fill(t):
    return t.format(b=rng.choice(BANKS), d=rng.choice(DOMAINS), a=rng.choice(AMOUNTS))

def main(target_total=200):
    rows = list(csv.DictReader(open(CSV)))
    have = {(r["text"], r["label"]) for r in rows}
    cur = {"scam": sum(1 for r in rows if r["label"] == "scam"),
           "suspicious": sum(1 for r in rows if r["label"] == "suspicious"),
           "safe": sum(1 for r in rows if r["label"] == "safe")}
    print("Current:", cur, "total:", len(rows))
    new_rows = []
    def add(label, lang, text):
        key = (text, label)
        if key not in have:
            have.add(key)
            new_rows.append({"text": text, "label": label, "lang": lang})
            return True
        return False
    for _ in range(400):
        if sum(cur.values()) + len(new_rows) >= target_total:
            break
        counts = {"scam": 0, "suspicious": 0, "safe": 0}
        for r in rows + new_rows:
            counts[r["label"]] = counts.get(r["label"], 0) + 1
        if counts["scam"] < 128:
            lang = rng.choice(["en", "en", "hi", "mr"])
            add("scam", lang, fill(rng.choice(SCAM_T[lang])))
        elif counts.get("suspicious", 0) < 24:
            lang = rng.choice(["en", "hi", "mr"])
            add("suspicious", lang, fill(rng.choice(SUSP_T[lang])))
        else:
            lang = rng.choice(["en", "en", "hi", "mr"])
            add("safe", lang, fill(rng.choice(SAFE_T[lang])))
    with open(CSV, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["text", "label", "lang"])
        w.writerows(new_rows)
    final = list(csv.DictReader(open(CSV)))
    from collections import Counter
    print(f"Added {len(new_rows)} rows → total {len(final)}")
    print(Counter((r["label"], r["lang"]) for r in final))

if __name__ == "__main__":
    main()
