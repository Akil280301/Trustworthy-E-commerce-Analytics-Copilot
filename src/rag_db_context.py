"""
src/rag_db_context.py
Live Database Context Retriever for RAG Pipeline.
Retrieves real data from PostgreSQL to ground the LLM with actual values.
This prevents hallucination of product names, department names, KPI values.
Module 7 Enhancement — Live RAG Context
"""

import sys
import re
import psycopg2
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import DB_CONFIG

# ── Keyword detectors ─────────────────────────────────────────────────────────
PRODUCT_KEYWORDS   = ["product", "item", "banana", "organic", "milk", "spinach",
                      "strawberr", "avocado", "bought", "ordered", "purchase",
                      "popular", "top", "best", "co-purchase", "together"]

DEPARTMENT_KEYWORDS = ["department", "dept", "produce", "dairy", "snack",
                       "beverage", "frozen", "bakery", "meat", "seafood",
                       "pantry", "deli", "breakfast", "alcohol", "baby"]

AISLE_KEYWORDS     = ["aisle", "fresh fruit", "vegetable", "yogurt", "cheese",
                      "chips", "water", "bread", "egg", "cream", "milk"]

NUTRITION_KEYWORDS = ["nutrition", "healthy", "health", "protein", "calorie",
                      "energy", "sugar", "fat", "fiber", "sodium", "grade",
                      "organic", "ingredient"]

KPI_KEYWORDS       = ["reorder", "basket", "retention", "cohort", "frequency",
                      "average", "total", "count", "rate", "percent", "trend",
                      "distribution", "segment", "diversity"]

TIME_KEYWORDS      = ["sunday", "monday", "tuesday", "wednesday", "thursday",
                      "friday", "saturday", "weekend", "weekday", "morning",
                      "evening", "night", "hour", "day", "week", "peak"]


def _conn():
    return psycopg2.connect(**DB_CONFIG)


def _matches(question: str, keywords: list) -> bool:
    q = question.lower()
    return any(kw in q for kw in keywords)


# ── Live context fetchers ─────────────────────────────────────────────────────

def get_product_context(question: str) -> str:
    """
    Fetches real product names, order counts, and reorder rates
    relevant to the question from the live database.
    """
    try:
        conn = _conn()
        cur  = conn.cursor()

        # Extract any product name hints from the question
        q_lower = question.lower()

        # Get top 20 products overall for context
        cur.execute("""
            SELECT p.product_name,
                   COUNT(*) AS times_ordered,
                   ROUND(100.0 * SUM(op.reordered)::numeric / COUNT(*), 1) AS reorder_pct,
                   a.aisle,
                   d.department
            FROM order_products__prior op
            JOIN products p ON op.product_id = p.product_id
            JOIN aisles a ON p.aisle_id = a.aisle_id
            JOIN departments d ON p.department_id = d.department_id
            GROUP BY p.product_name, a.aisle, d.department
            ORDER BY times_ordered DESC
            LIMIT 20
        """)
        top_products = cur.fetchall()

        # If question mentions a specific product, get its exact stats
        specific = []
        words = re.findall(r'\b\w{4,}\b', q_lower)
        for word in words:
            if word not in {"what", "which", "show", "give", "list", "that",
                            "with", "from", "have", "been", "most", "more",
                            "ordered", "order", "product", "products"}:
                cur.execute("""
                    SELECT p.product_name,
                           COUNT(*) AS times_ordered,
                           ROUND(100.0 * SUM(op.reordered)::numeric / COUNT(*), 1) AS reorder_pct
                    FROM order_products__prior op
                    JOIN products p ON op.product_id = p.product_id
                    WHERE LOWER(p.product_name) ILIKE %s
                    GROUP BY p.product_name
                    ORDER BY times_ordered DESC
                    LIMIT 5
                """, (f"%{word}%",))
                rows = cur.fetchall()
                specific.extend(rows)

        cur.close()
        conn.close()

        lines = ["LIVE PRODUCT DATA FROM DATABASE:"]
        lines.append("Top 20 most ordered products (name | orders | reorder% | aisle | department):")
        for row in top_products:
            lines.append(f"  {row[0]} | {row[1]:,} orders | {row[2]}% reorder | {row[3]} | {row[4]}")

        if specific:
            lines.append("\nProducts matching your query keywords:")
            for row in specific:
                lines.append(f"  {row[0]} | {row[1]:,} orders | {row[2]}% reorder")

        return "\n".join(lines)

    except Exception as e:
        return f"[Product context unavailable: {e}]"


def get_department_aisle_context() -> str:
    """
    Fetches all department and aisle names with their order volumes.
    Ensures LLM uses exact names from the database.
    """
    try:
        conn = _conn()
        cur  = conn.cursor()

        cur.execute("""
            SELECT d.department,
                   COUNT(DISTINCT op.order_id) AS order_count,
                   ROUND(100.0 * SUM(op.reordered)::numeric / COUNT(*), 1) AS reorder_pct
            FROM order_products__prior op
            JOIN products p ON op.product_id = p.product_id
            JOIN departments d ON p.department_id = d.department_id
            GROUP BY d.department
            ORDER BY order_count DESC
        """)
        departments = cur.fetchall()

        cur.execute("""
            SELECT a.aisle,
                   COUNT(*) AS items_ordered
            FROM order_products__prior op
            JOIN products p ON op.product_id = p.product_id
            JOIN aisles a ON p.aisle_id = a.aisle_id
            GROUP BY a.aisle
            ORDER BY items_ordered DESC
            LIMIT 30
        """)
        aisles = cur.fetchall()

        cur.close()
        conn.close()

        lines = ["LIVE DEPARTMENT AND AISLE DATA:"]
        lines.append("All departments (exact names | orders | reorder%):")
        for row in departments:
            lines.append(f"  '{row[0]}' | {row[1]:,} orders | {row[2]}% reorder")

        lines.append("\nTop 30 aisles by volume (exact names):")
        for row in aisles:
            lines.append(f"  '{row[0]}' | {row[1]:,} items")

        return "\n".join(lines)

    except Exception as e:
        return f"[Department/aisle context unavailable: {e}]"


def get_kpi_context() -> str:
    """
    Fetches current live KPI values directly from the database.
    Grounds the LLM with actual numbers so it never hallucinates metrics.
    """
    try:
        conn = _conn()
        cur  = conn.cursor()

        kpis = {}

        cur.execute("SELECT COUNT(*) FROM orders")
        kpis["total_orders"] = cur.fetchone()[0]

        cur.execute("""
            SELECT ROUND(AVG(basket.items)::numeric, 2)
            FROM (SELECT order_id, COUNT(*) AS items
                  FROM order_products__prior GROUP BY order_id) basket
        """)
        kpis["avg_basket_size"] = cur.fetchone()[0]

        cur.execute("""
            SELECT ROUND(100.0 * SUM(reordered)::numeric / COUNT(*), 2)
            FROM order_products__prior
        """)
        kpis["reorder_rate_pct"] = cur.fetchone()[0]

        cur.execute("""
            SELECT ROUND(AVG(days_since_prior_order)::numeric, 2)
            FROM orders WHERE days_since_prior_order IS NOT NULL
        """)
        kpis["avg_days_between_orders"] = cur.fetchone()[0]

        cur.execute("SELECT COUNT(DISTINCT user_id) FROM orders")
        kpis["total_unique_users"] = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM products")
        kpis["total_products"] = cur.fetchone()[0]

        cur.execute("""
            SELECT ROUND(AVG(aisle_count)::numeric, 2)
            FROM (
                SELECT op.order_id, COUNT(DISTINCT p.aisle_id) AS aisle_count
                FROM order_products__prior op
                JOIN products p ON op.product_id = p.product_id
                GROUP BY op.order_id
            ) t
        """)
        kpis["avg_basket_diversity_aisles"] = cur.fetchone()[0]

        cur.close()
        conn.close()

        lines = ["LIVE KPI VALUES FROM DATABASE (use these exact numbers):"]
        for k, v in kpis.items():
            lines.append(f"  {k}: {v:,}")
        return "\n".join(lines)

    except Exception as e:
        return f"[KPI context unavailable: {e}]"


def get_nutrition_context() -> str:
    """
    Fetches nutrition grade distribution and top healthy products.
    """
    try:
        conn = _conn()
        cur  = conn.cursor()

        cur.execute("""
            SELECT nutrition_grade_fr, COUNT(*) AS product_count
            FROM product_enriched
            WHERE nutrition_grade_fr IS NOT NULL
            GROUP BY nutrition_grade_fr
            ORDER BY nutrition_grade_fr
        """)
        grades = cur.fetchall()

        cur.execute("""
            SELECT p.product_name, pe.nutrition_grade_fr,
                   ROUND(pe.proteins_100g::numeric, 1) AS protein,
                   ROUND(pe.energy_100g::numeric, 1) AS energy,
                   COUNT(*) AS times_ordered
            FROM order_products__prior op
            JOIN products p ON op.product_id = p.product_id
            JOIN product_enriched pe ON LOWER(p.product_name) = LOWER(pe.product_name)
            WHERE pe.nutrition_grade_fr IN ('a', 'b')
            GROUP BY p.product_name, pe.nutrition_grade_fr,
                     pe.proteins_100g, pe.energy_100g
            ORDER BY times_ordered DESC
            LIMIT 15
        """)
        healthy = cur.fetchall()

        cur.close()
        conn.close()

        lines = ["LIVE NUTRITION DATA FROM DATABASE:"]
        lines.append("Nutrition grade distribution:")
        for row in grades:
            lines.append(f"  Grade {row[0]}: {row[1]:,} products")

        lines.append("\nTop 15 healthy (grade A/B) most ordered products:")
        for row in healthy:
            lines.append(
                f"  {row[0]} | Grade {row[1]} | "
                f"Protein: {row[2]}g | Energy: {row[3]}kcal | "
                f"{row[4]:,} orders"
            )
        return "\n".join(lines)

    except Exception as e:
        return f"[Nutrition context unavailable: {e}]"


def get_time_context() -> str:
    """
    Fetches order distribution by hour and day of week.
    """
    try:
        conn = _conn()
        cur  = conn.cursor()

        cur.execute("""
            SELECT order_dow,
                   CASE order_dow
                       WHEN 0 THEN 'Sunday' WHEN 1 THEN 'Monday'
                       WHEN 2 THEN 'Tuesday' WHEN 3 THEN 'Wednesday'
                       WHEN 4 THEN 'Thursday' WHEN 5 THEN 'Friday'
                       ELSE 'Saturday' END AS day_name,
                   COUNT(*) AS orders
            FROM orders
            GROUP BY order_dow
            ORDER BY order_dow
        """)
        days = cur.fetchall()

        cur.execute("""
            SELECT order_hour_of_day, COUNT(*) AS orders
            FROM orders
            GROUP BY order_hour_of_day
            ORDER BY order_hour_of_day
        """)
        hours = cur.fetchall()

        cur.close()
        conn.close()

        lines = ["LIVE TIME-BASED ORDER DATA:"]
        lines.append("Orders by day of week (order_dow | day | count):")
        for row in days:
            lines.append(f"  {row[0]} = {row[1]}: {row[2]:,} orders")

        lines.append("\nOrders by hour (0-23):")
        hour_str = " | ".join(f"{r[0]}h:{r[1]//1000}K" for r in hours)
        lines.append(f"  {hour_str}")

        return "\n".join(lines)

    except Exception as e:
        return f"[Time context unavailable: {e}]"


# ── Master live context builder ───────────────────────────────────────────────

def get_live_db_context(question: str) -> str:
    """
    Intelligently selects which live DB context to fetch based on the question.
    Returns a combined context string to inject into the RAG prompt.
    Caches nothing — always fetches fresh from PostgreSQL.
    """
    q = question.lower()
    sections = []

    # Always include KPI context — grounds every query with real numbers
    sections.append(get_kpi_context())

    # Conditionally add department/aisle context
    if _matches(q, DEPARTMENT_KEYWORDS + AISLE_KEYWORDS):
        sections.append(get_department_aisle_context())

    # Conditionally add product context
    if _matches(q, PRODUCT_KEYWORDS):
        sections.append(get_product_context(question))

    # Conditionally add nutrition context
    if _matches(q, NUTRITION_KEYWORDS):
        sections.append(get_nutrition_context())

    # Conditionally add time context
    if _matches(q, TIME_KEYWORDS):
        sections.append(get_time_context())

    return "\n\n" + "─" * 60 + "\n".join(sections)


if __name__ == "__main__":
    test_questions = [
        "What are the top 5 most ordered products?",
        "Which departments have the highest reorder rates?",
        "Show the healthiest products with nutrition grade A",
        "How do orders vary by hour of the day?",
        "What is the average basket size?",
    ]

    print("=" * 70)
    print("LIVE DB CONTEXT TEST")
    print("=" * 70)

    for q in test_questions:
        print(f"\nQuestion: {q}")
        ctx = get_live_db_context(q)
        print(ctx[:300] + "...\n")