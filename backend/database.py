"""SQLite layer: scans, threat cache, trends. Privacy-first: raw text auto-purged."""
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

# Override for prod: SCAMSHIELD_DB=/data/scans.db  (Postgres path: swap get_conn only)
DB_PATH = Path(os.getenv("SCAMSHIELD_DB", Path(__file__).parent / "scamshield.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  message_hash TEXT,
  category TEXT,
  verdict TEXT,
  score REAL,
  lang TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS threat_cache (
  indicator TEXT PRIMARY KEY,
  kind TEXT,
  malicious INTEGER,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS trends (
  date TEXT,
  category TEXT,
  count INTEGER,
  PRIMARY KEY (date, category)
);
CREATE TABLE IF NOT EXISTS tips (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lang TEXT,
  text TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()

def log_scan(message_hash, category, verdict, score, lang):
    conn = get_conn()
    conn.execute(
        "INSERT INTO scans (message_hash, category, verdict, score, lang) VALUES (?,?,?,?,?)",
        (message_hash, category, verdict, score, lang),
    )
    conn.commit()
    conn.close()

def get_trends(limit=7):
    conn = get_conn()
    rows = conn.execute(
        "SELECT date, category, count FROM trends ORDER BY date DESC LIMIT ?",
        (max(int(limit), 1) * 10,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_trends(date_str, counts: dict):
    conn = get_conn()
    for cat, c in counts.items():
        conn.execute(
            "INSERT OR REPLACE INTO trends (date, category, count) VALUES (?,?,?)",
            (date_str, cat, c),
        )
    conn.commit()
    conn.close()

def upsert_threat(indicator, kind, malicious: bool):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO threat_cache (indicator, kind, malicious) VALUES (?,?,?)",
        (indicator, kind, 1 if malicious else 0),
    )
    conn.commit()
    conn.close()

def lookup_threat(indicator):
    conn = get_conn()
    row = conn.execute(
        "SELECT malicious FROM threat_cache WHERE indicator=?", (indicator,)
    ).fetchone()
    conn.close()
    return bool(row["malicious"]) if row else None

def purge_old_scans(hours=24):
    cutoff = datetime.now() - timedelta(hours=hours)
    conn = get_conn()
    cur = conn.execute("DELETE FROM scans WHERE created_at < ?", (cutoff,))
    n = cur.rowcount
    conn.commit()
    conn.close()
    return n

def get_recent_scans(limit=10):
    """Anonymised history for dashboard: no raw text, hashes only."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT category, verdict, score, lang, created_at FROM scans ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_stats():
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) c FROM scans").fetchone()["c"]
    by_verdict = {r["verdict"]: r["c"] for r in conn.execute(
        "SELECT verdict, COUNT(*) c FROM scans GROUP BY verdict").fetchall()}
    threats = conn.execute("SELECT COUNT(*) c FROM threat_cache").fetchone()["c"]
    conn.close()
    return {"total_scans": total, "by_verdict": by_verdict, "threat_indicators": threats}

if __name__ == "__main__":
    init_db()
    print(f"DB ready at {DB_PATH}")
