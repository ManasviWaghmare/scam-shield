"""Train baseline: python train.py"""
from classifier import train
from database import init_db

if __name__ == "__main__":
    init_db()
    acc = train()
    print(f"Done. Accuracy={acc:.3f} — paste this number in your Unstop form.")
