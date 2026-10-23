"""Citation validation: every cited ID must come from the retrieved set."""
from . import retriever


def validate(cited_ids: list[str], passages: list[dict]) -> tuple[list[dict], list[str]]:
    """Return (accepted citation dicts, rejected ids). Server maps IDs to stored metadata."""
    by_id = {p["id"]: p for p in passages}
    accepted, rejected = [], []
    for cid in cited_ids or []:
        if cid in by_id:
            p = by_id[cid]
            accepted.append({"id": p["id"], "title": p["title"], "url": p["url"],
                             "passage": p["passage"][:400]})
        else:
            rejected.append(cid)
    # de-dupe while keeping order
    seen, deduped = set(), []
    for a in accepted:
        if a["id"] not in seen:
            seen.add(a["id"])
            deduped.append(a)
    return deduped, rejected


def source_exists(cid: str) -> bool:
    return any(s["id"] == cid for s in retriever.list_sources())
