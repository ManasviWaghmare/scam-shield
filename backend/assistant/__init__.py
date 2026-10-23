"""Scam Shield assistant: TrustRAG-lite adapter.

Retrieval over a curated local knowledge base (TF-IDF, no new deps),
optional hosted-LLM generation, citation validation, offline fallback.
The scanner verdict always comes from the detector — never from the LLM.
"""
