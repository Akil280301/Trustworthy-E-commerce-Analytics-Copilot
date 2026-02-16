"""
src/config.py
Centralized configuration. All modules import from here.
Never hardcode credentials anywhere else.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Database ──────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   os.getenv("DB_NAME", "instacart"),
    "user":     os.getenv("DB_USER", "instacart"),
    "password": os.getenv("DB_PASSWORD", "instacart123"),
}

DB_URL = (
    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
)

# ── Ollama ────────────────────────────────────────────────
OLLAMA_HOST  = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# ── RAG ──────────────────────────────────────────────────
VECTOR_STORE_PATH = "data_processed/vector_store"
DOCS_PATH         = "docs/"
CHUNK_SIZE        = 500    # tokens
CHUNK_OVERLAP     = 50
TOP_K_RETRIEVAL   = 3

# ── SQL Safety ───────────────────────────────────────────
ALLOWED_TABLES = {
    "orders",
    "order_products__prior",
    "order_products__train",
    "products",
    "aisles",
    "departments",
    "product_enriched",   # Module 5
    "holiday_features",   # Module 6
}

# ── App ──────────────────────────────────────────────────
MAX_RESULT_ROWS = 500   # cap results returned to UI