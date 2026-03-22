"""
src/rag_indexer.py
Builds FAISS vector index from all knowledge base documents.
Module 7 — RAG Pipeline
"""

import sys
import json
import faiss
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import VECTOR_STORE_PATH, CHUNK_SIZE, CHUNK_OVERLAP

MODEL_NAME = "all-MiniLM-L6-v2"
STORE = Path(VECTOR_STORE_PATH)


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + chunk_size])
        start += chunk_size - overlap
    return chunks


def load_all_documents():
    all_docs = []

    # 1. All markdown docs (schema, KPI index, examples, data sources)
    for md_file in Path("docs").rglob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        for i, chunk in enumerate(chunk_text(text)):
            all_docs.append({"text": chunk, "source": str(md_file), "chunk_id": i, "type": "doc"})

    # 2. All KPI SQL files as annotated examples
    for sql_file in Path("sql/kpis").glob("*.sql"):
        sql = sql_file.read_text(encoding="utf-8")
        name = sql_file.stem.replace("_", " ").title()
        text = f"KPI Query: {name}\nSQL:\n{sql}"
        all_docs.append({"text": text, "source": str(sql_file), "chunk_id": 0, "type": "sql"})

    print(f"   Docs from markdown : {sum(1 for d in all_docs if d['type'] == 'doc')}")
    print(f"   KPI SQL examples   : {sum(1 for d in all_docs if d['type'] == 'sql')}")
    print(f"   Total chunks       : {len(all_docs)}")
    return all_docs


def build_index():
    print("=" * 70)
    print("RAG INDEXER — Building FAISS Vector Store")
    print("=" * 70)

    print("\nLoading model: all-MiniLM-L6-v2 ...")
    model = SentenceTransformer(MODEL_NAME)

    print("\nLoading knowledge base...")
    docs = load_all_documents()

    print("\nEncoding all documents...")
    embeddings = model.encode(
        [d["text"] for d in docs],
        show_progress_bar=True,
        batch_size=32
    )
    embeddings = np.array(embeddings).astype("float32")

    print("\nBuilding FAISS index...")
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    print(f"   Vectors indexed: {index.ntotal} (dim={embeddings.shape[1]})")

    STORE.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(STORE / "index.faiss"))
    with open(STORE / "documents.json", "w", encoding="utf-8") as f:
        json.dump(docs, f, indent=2)

    print(f"\n   Saved index to {STORE}/")
    print("=" * 70)
    print("RAG INDEX COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    build_index()