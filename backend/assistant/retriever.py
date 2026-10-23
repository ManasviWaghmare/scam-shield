"""TF-IDF retriever over the curated knowledge base. No new dependencies."""
import json
import os
from pathlib import Path

_HERE = Path(__file__).parent
_MANIFEST = _HERE / "knowledge" / "manifest.json"

_index = None


def _load_docs():
    manifest = json.loads(_MANIFEST.read_text())
    docs = []
    for entry in manifest["documents"]:
        text = (_HERE / "knowledge" / "documents" / entry["file"]).read_text()
        # strip the markdown title line; keep body as the passage
        body = "\n".join(l for l in text.splitlines() if not l.startswith("#")).strip()
        docs.append({
            "id": entry["id"], "title": entry["title"], "url": entry["url"],
            "topics": entry.get("topics", []), "passage": body,
        })
    return docs


def get_index():
    """Lazily built {vectorizer, matrix, docs}. Thread-safe enough for demo scale."""
    global _index
    if _index is None:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        docs = _load_docs()
        vec = TfidfVectorizer(ngram_range=(1, 2), max_features=4000)
        mat = vec.fit_transform([d["passage"] + " " + " ".join(d["topics"]) for d in docs])
        _index = {"vec": vec, "mat": mat, "docs": docs, "cos": cosine_similarity}
    return _index


def min_relevance() -> float:
    try:
        return float(os.getenv("RAG_MIN_RELEVANCE", "0.15"))
    except ValueError:
        return 0.15


def top_k_default() -> int:
    try:
        return max(1, min(6, int(os.getenv("RAG_TOP_K", "4"))))
    except ValueError:
        return 4


def search(query: str, top_k: int | None = None) -> list[dict]:
    """Return [{id, title, url, passage, score}] sorted by score desc."""
    idx = get_index()
    k = top_k or top_k_default()
    q = idx["vec"].transform([query])
    scores = idx["cos"](q, idx["mat"])[0]
    ranked = sorted(zip(idx["docs"], scores), key=lambda x: x[1], reverse=True)[:k]
    return [{"id": d["id"], "title": d["title"], "url": d["url"],
             "passage": d["passage"], "score": round(float(s), 4)}
            for d, s in ranked]


def has_sufficient_evidence(passages: list[dict]) -> bool:
    return bool(passages) and passages[0]["score"] >= min_relevance()


def list_sources() -> list[dict]:
    idx = get_index()
    return [{"id": d["id"], "title": d["title"], "url": d["url"]} for d in idx["docs"]]
