"""Fine-tune MuRIL for scam detection (OPT-IN, heavy).
Needs: pip install torch transformers datasets accelerate
Run:  python train_muril.py [--epochs 2]
Saves to backend/models/muril/. Enable with: SCAMSHIELD_MODEL=muril uvicorn main:app
Baseline TF-IDF stays the default so the demo never breaks.
"""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data" / "synthetic_dataset.csv"
OUT = HERE / "models" / "muril"
LABELS = ["safe", "scam", "suspicious"]
MODEL_ID = "google/muril-base-cased"


def main(epochs: int = 2):
    try:
        import pandas as pd
        import torch
        from datasets import Dataset
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, f1_score
        from transformers import (AutoTokenizer, AutoModelForSequenceClassification,
                                  TrainingArguments, Trainer)
    except ImportError as e:
        print(f"Missing dep ({e}). Run: pip install torch transformers datasets accelerate")
        return

    df = pd.read_csv(DATA)
    df["label_id"] = df["label"].map({l: i for i, l in enumerate(LABELS)})
    tr, te = train_test_split(df, test_size=0.2, random_state=42, stratify=df["label"])
    tok = AutoTokenizer.from_pretrained(MODEL_ID)

    def tok_fn(b):
        return tok(b["text"], truncation=True, padding="max_length", max_length=128)

    dtr = Dataset.from_pandas(tr[["text", "label_id"]].rename(columns={"label_id": "labels"})).map(tok_fn, batched=True)
    dte = Dataset.from_pandas(te[["text", "label_id"]].rename(columns={"label_id": "labels"})).map(tok_fn, batched=True)
    cols = ["input_ids", "attention_mask", "labels"]
    dtr.set_format(type="torch", columns=cols)
    dte.set_format(type="torch", columns=cols)

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_ID, num_labels=3, id2label={i: l for i, l in enumerate(LABELS)},
        label2id={l: i for i, l in enumerate(LABELS)})

    def metrics(p):
        import numpy as np
        pred = np.argmax(p.predictions, axis=1)
        return {"accuracy": accuracy_score(p.label_ids, pred),
                "macro_f1": f1_score(p.label_ids, pred, average="macro")}

    args = TrainingArguments(output_dir=str(OUT / "ckpt"), num_train_epochs=epochs,
                             per_device_train_batch_size=8, per_device_eval_batch_size=16,
                             eval_strategy="epoch", save_strategy="epoch", load_best_model_at_end=True,
                             logging_steps=10, report_to="none", seed=42)
    Trainer(model=model, args=args, train_dataset=dtr, eval_dataset=dte,
            compute_metrics=metrics).train()
    OUT.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(OUT)
    tok.save_pretrained(OUT)
    (OUT / "labels.json").write_text(json.dumps(LABELS))
    print(f"Saved MuRIL model to {OUT}. Enable: SCAMSHIELD_MODEL=muril uvicorn main:app")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=2)
    main(ap.parse_args().epochs)
