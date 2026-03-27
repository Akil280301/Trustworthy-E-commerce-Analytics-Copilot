"""
src/text_to_sql.py
Converts natural language to validated SQL using Groq LLaMA 3.3 70B.
RAG context is injected into the prompt for grounding.
Module 8 — Text-to-SQL
"""

import sys
import re
import time
import psycopg2
from pathlib import Path
from groq import Groq

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import (
    DB_CONFIG, GROQ_API_KEY, GROQ_MODEL,
    ALLOWED_TABLES, MAX_RESULT_ROWS
)
from src.rag_retriever import retrieve_context

client = Groq(api_key=GROQ_API_KEY)

# ── Full schema for prompt injection ──────────────────────────────────────────
DB_SCHEMA = """
PostgreSQL Database Schema — Instacart E-commerce Warehouse

TABLE: orders
  order_id               INTEGER PRIMARY KEY
  user_id                INTEGER
  eval_set               VARCHAR  -- 'prior' or 'train'
  order_number           INTEGER  -- sequence per user, 1 = first order ever
  order_dow              INTEGER  -- day of week: 0=Sunday,1=Monday,2=Tuesday,3=Wednesday,4=Thursday,5=Friday,6=Saturday
  order_hour_of_day      INTEGER  -- hour: 0-23
  days_since_prior_order FLOAT    -- NULL for first order

TABLE: order_products__prior  (32.4M rows — main fact table)
  order_id            INTEGER REFERENCES orders
  product_id          INTEGER REFERENCES products
  add_to_cart_order   INTEGER
  reordered           INTEGER  -- 1=reorder, 0=first time buying this product

TABLE: order_products__train  (1.4M rows)
  order_id            INTEGER REFERENCES orders
  product_id          INTEGER REFERENCES products
  add_to_cart_order   INTEGER
  reordered           INTEGER

TABLE: products
  product_id          INTEGER PRIMARY KEY
  product_name        VARCHAR
  aisle_id            INTEGER REFERENCES aisles
  department_id       INTEGER REFERENCES departments

TABLE: aisles
  aisle_id            INTEGER PRIMARY KEY
  aisle               VARCHAR  -- e.g. 'fresh fruits', 'yogurt', 'chips pretzels'

TABLE: departments
  department_id       INTEGER PRIMARY KEY
  department          VARCHAR  -- e.g. 'produce', 'dairy eggs', 'snacks'

TABLE: product_enriched  (173K rows — Open Food Facts nutrition data)
  product_name        VARCHAR
  categories_en       VARCHAR
  main_category_en    VARCHAR
  energy_100g         FLOAT
  fat_100g            FLOAT
  saturated_fat_100g  FLOAT
  carbohydrates_100g  FLOAT
  sugars_100g         FLOAT
  fiber_100g          FLOAT
  proteins_100g       FLOAT
  salt_100g           FLOAT
  sodium_100g         FLOAT
  nutrition_grade_fr  VARCHAR  -- 'a'=healthiest, 'b', 'c', 'd', 'e'=worst
  ingredients_text    TEXT
  labels_en           VARCHAR

TABLE: holiday_features  (342 rows — US federal holidays 2004-2021)
  date                DATE
  holiday             VARCHAR  -- e.g. 'Christmas Day', 'Thanksgiving'
  weekday             VARCHAR
  month               INTEGER
  day                 INTEGER
  year                INTEGER

KEY JOIN PATTERNS:
  orders JOIN order_products__prior ON orders.order_id = order_products__prior.order_id
  order_products__prior JOIN products ON order_products__prior.product_id = products.product_id
  products JOIN aisles ON products.aisle_id = aisles.aisle_id
  products JOIN departments ON products.department_id = departments.department_id
  products JOIN product_enriched ON LOWER(products.product_name) = LOWER(product_enriched.product_name)
  Use UNION ALL of order_products__prior + order_products__train for complete product history
"""

SYSTEM_PROMPT = f"""You are an expert PostgreSQL data analyst for a large e-commerce data warehouse.
Your sole job is to convert natural language business questions into correct, executable PostgreSQL SQL.

{DB_SCHEMA}

STRICT RULES — follow every one of these without exception:
1. Output ONLY the raw SQL query. No explanation, no markdown, no code fences, no preamble.
2. Always include a LIMIT clause — use LIMIT 20 unless the user specifies a different number.
3. Only use SELECT statements. Never use INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE.
4. Only query these exact tables: orders, order_products__prior, order_products__train,
   products, aisles, departments, product_enriched, holiday_features.
5. Always use table aliases to qualify every column name — never use bare column names.
6. Use ROUND(value::numeric, 2) for all decimal outputs — always cast to ::numeric before ROUND.
7. Use ILIKE for all string matching to be case-insensitive.
8. Use CTEs (WITH clauses) for any query with more than one aggregation step.
9. For product co-purchase queries, always filter out the seed product from results.
10. order_dow mapping: 0=Sunday, 1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday.
    WEEKEND = order_dow IN (0, 6). WEEKDAY = order_dow IN (1, 2, 3, 4, 5).
11. When joining product_enriched, always use LOWER() on both sides of the join condition.
    CRITICAL: product_enriched has duplicate product names — always use DISTINCT or add
    GROUP BY with MIN()/AVG() on nutrition columns to avoid duplicate rows.
    Use this pattern: JOIN (SELECT LOWER(product_name) as pname,
    nutrition_grade_fr, AVG(energy_100g) as energy_100g,
    AVG(proteins_100g) as proteins_100g, AVG(sugars_100g) as sugars_100g
    FROM product_enriched GROUP BY LOWER(product_name), nutrition_grade_fr) pe
    ON LOWER(p.product_name) = pe.pname12. Never use ROUND(float_column, 2) directly — always write ROUND(float_column::numeric, 2).
13. If the question truly cannot be answered with the available schema, return exactly:
    UNSUPPORTED_QUERY
"""


def build_prompt(question: str, context: str) -> str:
    return f"""RELEVANT CONTEXT FROM KNOWLEDGE BASE:
{context}

BUSINESS QUESTION: {question}

Write the PostgreSQL query now:"""


def extract_sql(raw: str) -> str:
    """Strip accidental markdown fences or extra text."""
    raw = raw.strip()
    raw = re.sub(r"```sql\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"```\s*", "", raw)
    if ";" in raw:
        raw = raw[:raw.index(";") + 1]
    return raw.strip()


def validate_sql(sql: str) -> tuple[bool, str]:
    """Safety validation — blocks writes and unauthorized tables."""
    if not sql or sql.strip() == "UNSUPPORTED_QUERY":
        return False, "Query not supported with available schema."

    sql_upper = sql.upper().strip()

    # Must start with SELECT or WITH (CTE)
    if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
        return False, "Only SELECT or WITH (CTE) queries are permitted."

    # Block all write/admin operations
    forbidden_ops = [
        "INSERT", "UPDATE", "DELETE", "DROP", "CREATE",
        "ALTER", "TRUNCATE", "GRANT", "REVOKE", "EXECUTE", "COPY"
    ]
    for op in forbidden_ops:
        if re.search(rf"\b{op}\b", sql_upper):
            return False, f"Forbidden operation detected: {op}"

    # Extract CTE names so we don't flag them as unauthorized tables
    cte_names = set(re.findall(r'\b(\w+)\s+AS\s*\(', sql_upper))

    # Check only allowed tables are used (excluding CTE names)
    mentioned = re.findall(r'\bFROM\s+(\w+)|\bJOIN\s+(\w+)', sql_upper)
    used_tables = {t for pair in mentioned for t in pair if t}
    used_tables -= cte_names
    illegal = used_tables - {t.upper() for t in ALLOWED_TABLES}
    if illegal:
        return False, f"Unauthorized table(s) referenced: {illegal}"

    return True, "Validation passed"


def execute_sql(sql: str) -> tuple[list, list, str | None, float]:
    """Execute SQL against PostgreSQL, auto-fix ROUND cast issues."""
    # Auto-fix: ensure ROUND always uses ::numeric cast for PostgreSQL compatibility
    sql = re.sub(
        r'ROUND\((?!.*::numeric)([^,]+),\s*(\d+)\)',
        lambda m: f"ROUND({m.group(1).strip()}::numeric, {m.group(2)})",
        sql
    )
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        start = time.time()
        cur.execute(sql)
        rows = cur.fetchmany(MAX_RESULT_ROWS)
        latency = round(time.time() - start, 3)
        cols = [desc[0] for desc in cur.description]
        cur.close()
        conn.close()
        return rows, cols, None, latency
    except Exception as e:
        return [], [], str(e), 0.0


def generate_sql(question: str) -> dict:
    """
    Full RAG → Groq → Validate → Execute pipeline.
    Returns a structured result dict with all intermediate outputs.
    """
    # Step 1: Retrieve relevant context — FAISS docs + Live DB data
    from src.rag_db_context import get_live_db_context
    faiss_context  = retrieve_context(question, top_k=3)
    live_context   = get_live_db_context(question)
    context        = faiss_context + "\n\n" + live_context

    # Step 2: Call Groq LLaMA 3.3 70B
    t_start = time.time()
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": build_prompt(question, context)}
        ],
        temperature=0.1,
        max_tokens=1000,
    )
    groq_latency = round(time.time() - t_start, 3)
    raw_output = response.choices[0].message.content

    # Step 3: Extract clean SQL
    sql = extract_sql(raw_output)

    # Step 4: Validate
    valid, validation_msg = validate_sql(sql)

    result = {
        "question":      question,
        "context_used":  context,
        "generated_sql": sql,
        "groq_latency":  groq_latency,
        "validation":    {"passed": valid, "message": validation_msg},
        "columns":       [],
        "rows":          [],
        "db_latency":    0.0,
        "error":         None,
    }

    # Step 5: Execute if valid
    if valid:
        rows, cols, error, db_latency = execute_sql(sql)
        result["columns"]    = cols
        result["rows"]       = rows
        result["db_latency"] = db_latency
        result["error"]      = error

    return result


def pretty_print(result: dict):
    """Print a formatted result to the console."""
    sep = "=" * 70
    print(f"\n{sep}")
    print(f"QUESTION  : {result['question']}")
    print(sep)
    print(f"\nGENERATED SQL:\n{result['generated_sql']}")
    print(f"\nVALIDATION : {result['validation']['message']}")
    print(f"Groq latency : {result['groq_latency']}s")

    if result["error"]:
        print(f"\nEXECUTION ERROR: {result['error']}")
    elif result["rows"]:
        cols = result["columns"]
        rows = result["rows"]
        print(f"\nRESULTS — {len(rows)} row(s) | DB latency: {result['db_latency']}s")
        widths = [
            max(len(str(c)), max(len(str(r[i])) for r in rows))
            for i, c in enumerate(cols)
        ]
        header = " | ".join(str(c).ljust(w) for c, w in zip(cols, widths))
        print(header)
        print("-" * len(header))
        for row in rows[:15]:
            print(" | ".join(str(v).ljust(w) for v, w in zip(row, widths)))
        if len(rows) > 15:
            print(f"   ... and {len(rows) - 15} more rows")
    else:
        print("\nNo rows returned.")
    print()


if __name__ == "__main__":
    test_questions = [
        # Basic KPI queries
        "What are the top 5 most ordered products?",
        "What is the reorder rate across all orders?",
        # Intermediate queries
        "Which departments have the highest reorder rates?",
        "What is the average basket size per department?",
        "Which aisles are most popular between 6am and 11am?",
        # Complex CTE queries
        "Show me customer segments by order frequency as low medium and high",
        "Which products are most often bought together with organic strawberries?",
        # Nutrition join
        "Show the top 10 healthiest most ordered products with nutrition grade a or b",
        # Time-based
        "How do order volumes compare on weekdays versus weekends?",
        "Which hour of the day has the highest average basket size?",
    ]

    print("=" * 70)
    print("MODULE 8 — TEXT-TO-SQL TEST RUN")
    print(f"Model : {GROQ_MODEL}")
    print("=" * 70)

    passed = 0
    failed = 0
    errors = 0

    for q in test_questions:
        result = generate_sql(q)
        pretty_print(result)
        if result["error"]:
            errors += 1
        elif not result["validation"]["passed"]:
            failed += 1
        else:
            passed += 1

    print("=" * 70)
    print(f"SUMMARY — Passed: {passed} | Validation Failed: {failed} | Execution Errors: {errors}")
    print("=" * 70)