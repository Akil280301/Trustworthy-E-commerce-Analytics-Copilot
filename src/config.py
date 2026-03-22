"""
src/config.py
Centralized configuration. All modules import from here.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Database ──────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5433)),
    "dbname":   os.getenv("DB_NAME", "instacart"),
    "user":     os.getenv("DB_USER", "instacart"),
    "password": os.getenv("DB_PASSWORD", "instacart123"),
}

DB_URL = (
    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
)

# ── Groq ──────────────────────────────────────────────────────────
GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL    = "llama-3.3-70b-versatile"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# ── RAG ───────────────────────────────────────────────────────────
VECTOR_STORE_PATH = "data_processed/vector_store"
DOCS_PATH         = "docs/"
CHUNK_SIZE        = 500
CHUNK_OVERLAP     = 50
TOP_K_RETRIEVAL   = 3
CONFIDENCE_THRESHOLD = 0.6

# ── SQL Safety ────────────────────────────────────────────────────
ALLOWED_TABLES = {
    "orders",
    "order_products__prior",
    "order_products__train",
    "products",
    "aisles",
    "departments",
    "product_enriched",
    "holiday_features",
}

# ── App ───────────────────────────────────────────────────────────
MAX_RESULT_ROWS = 500