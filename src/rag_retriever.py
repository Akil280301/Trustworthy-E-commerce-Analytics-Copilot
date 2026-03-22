"""
src/rag_retriever.py
Retrieves top-K relevant context chunks for a query using FAISS.
Module 7 — RAG Pipeline
"""

import sys
import json
import faiss
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import VECTOR_STORE_PATH, TOP_K_RETRIEVAL, CONFIDENCE_THRESHOLD

MODEL_NAME = "all-MiniLM-L6-v2"
STORE = Path(VECTOR_STORE_PATH)

_model = None
_index = None
_documents = None


def _load():
    global _model, _index, _documents
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    if _index is None:
        _index = faiss.read_index(str(STORE / "index.faiss"))
        with open(STORE / "documents.json", "r", encoding="utf-8") as f:
            _documents = json.load(f)


def retrieve(query: str, top_k: int = TOP_K_RETRIEVAL) -> list[dict]:
    _load()
    embedding = _model.encode([query]).astype("float32")
    distances, indices = _index.search(embedding, top_k)
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        doc = _documents[idx].copy()
        doc["score"] = float(dist)
        results.append(doc)
    return results


def retrieve_context(query: str, top_k: int = TOP_K_RETRIEVAL) -> str:
    """
    Returns formatted context string for prompt injection.
    Falls back to best result if all scores exceed confidence threshold.
    """
    results = retrieve(query, top_k)
    filtered = [r for r in results if r["score"] < CONFIDENCE_THRESHOLD]
    if not filtered:
        filtered = results[:1]

    parts = []
    for i, r in enumerate(filtered, 1):
        source = Path(r["source"]).name
        parts.append(f"[Context {i} | Source: {source} | Score: {r['score']:.3f}]\n{r['text']}")
    return "\n\n".join(parts)


if __name__ == "__main__":
    queries = [
        "Which products are bought together with bananas?",
        "Show customer segments by order frequency",
        "What is the reorder rate by department?",
        "How do orders vary on holidays?",
        "Which aisles are popular in the morning?",
        "Show nutrition grade of top ordered products",
        "What is the average basket size per department?",
        "Who are the most active users?",
    ]

    print("=" * 70)
    print("RAG RETRIEVER — Test Queries")
    print("=" * 70)
    for q in queries:
        print(f"\nQuery : {q}")
        results = retrieve(q, top_k=3)
        for r in results:
            print(f"  [{r['score']:.4f}] {Path(r['source']).name} — {r['text'][:70]}...")