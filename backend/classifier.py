"""Baseline multilingual classifier: TF-IDF + LogisticRegression.
Swap with MuRIL/IndicBERT fine-tune later without changing main.py.
"""
import re
from pathlib import Path
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

MODEL_PATH = Path(__file__).parent / "models" / "scam_clf.joblib"
DATA_PATH = Path(__file__).parent / "data" / "synthetic_dataset.csv"

CATEGORIES = ["Fake KYC", "UPI Refund", "Job Scam", "Lottery", "Phishing Link", "Safe"]

def clean(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text

def build_pipeline():
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=8000)),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])

def train(csv_path=DATA_PATH, save_path=MODEL_PATH):
    df = pd.read_csv(csv_path)
    df["text_clean"] = df["text"].astype(str).apply(clean)
    X_train, X_test, y_train, y_test = train_test_split(
        df["text_clean"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
    )
    pipe = build_pipeline()
    pipe.fit(X_train, y_train)
    acc = accuracy_score(y_test, pipe.predict(X_test))
    print(f"Accuracy: {acc:.3f}")
    print(classification_report(y_test, pipe.predict(X_test)))
    save_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, save_path)
    print(f"Saved to {save_path}")
    return acc

_model = None

def get_model():
    global _model
    if _model is None and MODEL_PATH.exists():
        _model = joblib.load(MODEL_PATH)
    return _model

def predict_proba(text: str):
    """Returns (label, confidence). Falls back to rule-leaning heuristic if no model."""
    model = get_model()
    if model is None:
        t = text.lower()
        scam_hits = sum(k in t for k in ["otp", "kyc", "blocked", "urgent", "lottery", "prize", "refund", "verify", "तुरंत", "बंद", "otp", "खाता"])
        if scam_hits >= 2:
            return "scam", 0.75
        if scam_hits == 1:
            return "suspicious", 0.55
        return "safe", 0.80
    proba = model.predict_proba([clean(text)])[0]
    idx = proba.argmax()
    label = model.classes_[idx]
    return label, float(proba[idx])

def predict_category(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["kyc", "kyc expired", "kyc अपडेट", "केवायसी"]):
        return "Fake KYC"
    if any(k in t for k in ["refund", "upi", "money back", "रिफंड"]):
        return "UPI Refund"
    if any(k in t for k in ["job", "part-time", "work from home", "नौकरी", "ऑफर"]):
        return "Job Scam"
    if any(k in t for k in ["lottery", "winner", "prize", "लॉटरी", "इनाम"]):
        return "Lottery"
    if "http" in t or "bit.ly" in t or ".xyz" in t or ".top" in t:
        return "Phishing Link"
    return "Safe"


def explain_tokens(text: str, top_k: int = 8) -> list[dict]:
    """SHAP-lite: top TF-IDF tokens pushing toward the predicted class.

    Uses the trained LogisticRegression coefficients: contribution of each
    token = tfidf_value * coef for the predicted class. Returns
    [{token, weight}] sorted by weight desc. Empty list if no model.
    Swap with shap.LinearExplainer / transformer attributions later —
    main.py only consumes the returned list.
    """
    model = get_model()
    if model is None:
        return []
    try:
        vec = model.named_steps["tfidf"]
        clf = model.named_steps["clf"]
        X = vec.transform([clean(text)])
        pred = clf.predict(X)[0]
        classes = list(clf.classes_)
        coefs = clf.coef_
        # binary: coef_[0] is for classes_[1]; multiclass: one row per class
        if len(classes) == 2:
            w = coefs[0] if pred == classes[1] else -coefs[0]
        else:
            w = coefs[classes.index(pred)]
        names = vec.get_feature_names_out()
        idx = X.nonzero()[1]
        scored = [(names[i], float(X[0, i] * w[i])) for i in idx if w[i] > 0]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [{"token": tok, "weight": round(wt, 4)} for tok, wt in scored[:top_k]]
    except Exception:
        return []
