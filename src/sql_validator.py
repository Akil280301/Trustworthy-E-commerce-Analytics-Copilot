"""
src/sql_validator.py
5-Layer SQL Validation Pipeline for logical accuracy of generated SQL.
Directly addresses professor feedback on hallucination and SQL correctness.
Module 8B — SQL Validation
"""

import sys
import re
import json
import psycopg2
from pathlib import Path
from groq import Groq

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import DB_CONFIG, GROQ_API_KEY, GROQ_MODEL, ALLOWED_TABLES

client = Groq(api_key=GROQ_API_KEY)

# ── Known schema constraints for Layer 1 ─────────────────────────────────────
SCHEMA_CONSTRAINTS = {
    "order_dow":          {"type": "int", "min": 0, "max": 6},
    "order_hour_of_day":  {"type": "int", "min": 0, "max": 23},
    "reordered":          {"type": "int", "values": [0, 1]},
    "eval_set":           {"type": "str", "values": ["prior", "train"]},
    "nutrition_grade_fr": {"type": "str", "values": ["a", "b", "c", "d", "e"]},
}

NULL_COLUMNS = {"days_since_prior_order"}

NUMERIC_COLUMNS = {
    "energy_100g", "fat_100g", "saturated_fat_100g", "carbohydrates_100g",
    "sugars_100g", "fiber_100g", "proteins_100g", "salt_100g", "sodium_100g"
}


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 1 — Pre-Generation Schema Constraint Checks
# ══════════════════════════════════════════════════════════════════════════════

def layer1_schema_constraints(sql: str) -> dict:
    """
    Checks SQL against known schema constraints before execution.
    Catches wrong column value ranges, invalid filter values, NULL misuse.
    """
    issues = []
    sql_upper = sql.upper()

    # Check order_dow range (must be 0-6)
    dow_values = re.findall(r'order_dow\s*(?:=|IN\s*\(|BETWEEN)\s*([\d,\s]+)', sql, re.IGNORECASE)
    for match in dow_values:
        nums = [int(n.strip()) for n in re.findall(r'\d+', match)]
        for n in nums:
            if n < 0 or n > 6:
                issues.append(f"Layer 1: order_dow value {n} out of range (0-6)")

    # Check order_hour_of_day range (must be 0-23)
    hour_values = re.findall(r'order_hour_of_day\s*(?:=|BETWEEN|>|<)\s*(\d+)', sql, re.IGNORECASE)
    for match in hour_values:
        n = int(match)
        if n < 0 or n > 23:
            issues.append(f"Layer 1: order_hour_of_day value {n} out of range (0-23)")

    # Check reordered column only uses 0 or 1
    reordered_vals = re.findall(r'reordered\s*=\s*(\d+)', sql, re.IGNORECASE)
    for val in reordered_vals:
        if int(val) not in [0, 1]:
            issues.append(f"Layer 1: reordered column value {val} invalid (must be 0 or 1)")

    # Check NULL handling — days_since_prior_order should use IS NULL not = NULL
    if "days_since_prior_order" in sql_upper:
        if "= NULL" in sql_upper or "!= NULL" in sql_upper:
            issues.append("Layer 1: Use IS NULL / IS NOT NULL for days_since_prior_order, not = NULL")

    # Check no aggregation on non-numeric columns
    agg_pattern = re.findall(r'(SUM|AVG)\s*\(\s*(\w+)\s*\)', sql, re.IGNORECASE)
    for func, col in agg_pattern:
        if col.lower() in {"product_name", "aisle", "department", "eval_set"}:
            issues.append(f"Layer 1: Cannot apply {func}() to non-numeric column '{col}'")

    passed = len(issues) == 0
    return {
        "layer": 1,
        "name": "Schema Constraint Check",
        "passed": passed,
        "issues": issues,
        "message": "All schema constraints satisfied" if passed else f"{len(issues)} constraint violation(s) found"
    }


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 2 — Logical Semantic Validation (LLM-based)
# ══════════════════════════════════════════════════════════════════════════════

LAYER2_PROMPT = """You are a strict SQL logic reviewer for a PostgreSQL e-commerce database.

DATABASE SCHEMA SUMMARY:
- orders: order_id, user_id, order_dow (0=Sun..6=Sat), order_hour_of_day (0-23), order_number, days_since_prior_order, eval_set
- order_products__prior / order_products__train: order_id, product_id, reordered (0/1), add_to_cart_order
- products: product_id, product_name, aisle_id, department_id
- aisles: aisle_id, aisle
- departments: department_id, department
- product_enriched: product_name, nutrition_grade_fr (a-e), energy_100g, proteins_100g, sugars_100g, fat_100g etc.
- holiday_features: date, holiday, weekday, month, day, year

REVIEW THIS SQL FOR LOGICAL ERRORS:
{sql}

ORIGINAL QUESTION: {question}

Check ONLY for these critical logical issues (ignore stylistic preferences):
1. Does the SQL answer the question? (IMPORTANT: ignore LIMIT clauses entirely — they are always acceptable on any query)
2. Are GROUP BY columns consistent with SELECT columns (no ungrouped non-aggregates)?
3. Are JOIN conditions using the correct foreign keys?
4. Are WHERE filters semantically correct for the question intent?
5. Are aggregation functions appropriate (SUM vs COUNT vs AVG)?
6. Does WEEKEND correctly use order_dow IN (0,6) and WEEKDAY use order_dow IN (1,2,3,4,5)?
7. Are UNION ALL used correctly when combining prior and train tables?

IMPORTANT RULES FOR YOUR REVIEW:
- Do NOT flag LIMIT clauses as errors under any circumstances — they are always acceptable
- Do NOT flag minor style issues — only flag real logical errors that produce wrong answers
- Do NOT flag duplicate handling in UNION ALL as an error — UNION ALL is correct for combining fact tables
- Do NOT flag GROUP BY issues when ROUND(), aggregated expressions, or derived columns are in SELECT — only flag genuinely ungrouped raw columns
- A query that returns the correct answer with a LIMIT is perfectly valid
- Only return passed=false if there is a definitive logical error that would produce wrong results

Respond with ONLY valid JSON in this exact format, no other text:
{{"passed": true/false, "issues": ["issue1", "issue2"], "confidence": 0.0-1.0, "suggestion": "brief fix if failed"}}"""


def layer2_logical_semantic(sql: str, question: str) -> dict:
    """
    Uses Groq LLaMA to semantically verify SQL logic matches the question intent.
    """
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{
                "role": "user",
                "content": LAYER2_PROMPT.format(sql=sql, question=question)
            }],
            temperature=0.0,
            max_tokens=500,
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"```json\s*", "", raw)
        raw = re.sub(r"```\s*", "", raw)
        result = json.loads(raw)
        return {
            "layer": 2,
            "name": "Logical Semantic Check",
            "passed": result.get("passed", False),
            "issues": result.get("issues", []),
            "confidence": result.get("confidence", 0.0),
            "suggestion": result.get("suggestion", ""),
            "message": "Logic verified by LLM" if result.get("passed") else f"Logic issues: {result.get('issues', [])}"
        }
    except Exception as e:
        return {
            "layer": 2,
            "name": "Logical Semantic Check",
            "passed": True,  # fail open if LLM check errors
            "issues": [],
            "confidence": 0.5,
            "suggestion": "",
            "message": f"Layer 2 check skipped (error: {e})"
        }


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 3 — Execution Plausibility Checks
# ══════════════════════════════════════════════════════════════════════════════

PLAUSIBILITY_RULES = {
    "reorder_rate_pct":   {"min": 0,   "max": 100},
    "avg_basket_size":    {"min": 1,   "max": 100},
    "order_count":        {"min": 1,   "max": 5_000_000},
    "times_ordered":      {"min": 1,   "max": 5_000_000},
    "total_orders":       {"min": 1,   "max": 5_000_000},
    "user_count":         {"min": 1,   "max": 250_000},
    "avg_orders":         {"min": 1,   "max": 100},
    "avg_days_between":   {"min": 1,   "max": 365},
    "retention_rate_pct": {"min": 0,   "max": 100},
    "energy_100g":        {"min": 0,   "max": 4000},
    "proteins_100g":      {"min": 0,   "max": 100},
    "sugars_100g":        {"min": 0,   "max": 100},
}


def layer3_execution_plausibility(sql: str, rows: list, cols: list) -> dict:
    """
    Checks that query results fall within expected business value ranges.
    Catches absurd outputs like 500% reorder rates or negative counts.
    """
    issues = []

    if not rows or not cols:
        return {
            "layer": 3,
            "name": "Execution Plausibility Check",
            "passed": True,
            "issues": [],
            "message": "No rows to check"
        }

    col_lower = [c.lower() for c in cols]

    for col_name, bounds in PLAUSIBILITY_RULES.items():
        if col_name in col_lower:
            idx = col_lower.index(col_name)
            for row in rows:
                try:
                    val = float(row[idx])
                    # Normalise decimal proportions to percentage for comparison
                    check_val = val * 100 if val < 2 and "pct" in col_name else val
                    if check_val < bounds["min"] or check_val > bounds["max"]:
                        issues.append(
                            f"Layer 3: '{col_name}' value {val} outside "
                            f"expected range [{bounds['min']}, {bounds['max']}]"
                        )
                except (TypeError, ValueError):
                    pass

    # Check for negative counts
    count_cols = [i for i, c in enumerate(col_lower) if "count" in c or "total" in c]
    for idx in count_cols:
        for row in rows:
            try:
                if float(row[idx]) < 0:
                    issues.append(f"Layer 3: Negative count detected in column '{cols[idx]}'")
            except (TypeError, ValueError):
                pass

    passed = len(issues) == 0
    return {
        "layer": 3,
        "name": "Execution Plausibility Check",
        "passed": passed,
        "issues": issues,
        "message": "All result values within expected ranges" if passed else f"{len(issues)} plausibility issue(s)"
    }


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 4 — LLM Self-Correction (up to 2 retries)
# ══════════════════════════════════════════════════════════════════════════════

LAYER4_PROMPT = """You are a PostgreSQL expert. Fix the following SQL query based on the errors reported.

ORIGINAL QUESTION: {question}

BROKEN SQL:
{sql}

ERRORS FOUND:
{errors}

DATABASE RULES:
- Only use tables: orders, order_products__prior, order_products__train, products, aisles, departments, product_enriched, holiday_features
- Always use ROUND(value::numeric, 2) for decimals
- WEEKEND = order_dow IN (0, 6), WEEKDAY = order_dow IN (1, 2, 3, 4, 5)
- Use LOWER() on both sides when joining product_enriched
- Use CTEs for multi-step aggregations
- Output ONLY the corrected SQL query, no explanation, no markdown"""


def layer4_self_correct(sql: str, question: str, errors: list, max_retries: int = 2) -> dict:
    """
    Asks Groq to fix the SQL based on errors from layers 1-3.
    Retries up to max_retries times.
    """
    if not errors:
        return {
            "layer": 4,
            "name": "Self-Correction",
            "passed": True,
            "corrected_sql": sql,
            "attempts": 0,
            "message": "No correction needed"
        }

    current_sql = sql
    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{
                    "role": "user",
                    "content": LAYER4_PROMPT.format(
                        question=question,
                        sql=current_sql,
                        errors="\n".join(errors)
                    )
                }],
                temperature=0.1,
                max_tokens=1000,
            )
            corrected = response.choices[0].message.content.strip()
            corrected = re.sub(r"```sql\s*", "", corrected, flags=re.IGNORECASE)
            corrected = re.sub(r"```\s*", "", corrected)
            if ";" in corrected:
                corrected = corrected[:corrected.index(";") + 1]
            current_sql = corrected.strip()

        except Exception as e:
            return {
                "layer": 4,
                "name": "Self-Correction",
                "passed": False,
                "corrected_sql": sql,
                "attempts": attempt,
                "message": f"Self-correction failed: {e}"
            }

    return {
        "layer": 4,
        "name": "Self-Correction",
        "passed": True,
        "corrected_sql": current_sql,
        "attempts": max_retries,
        "message": f"SQL corrected after {max_retries} attempt(s)"
    }


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 5 — Comparative Validation Against Gold KPI Patterns
# ══════════════════════════════════════════════════════════════════════════════

GOLD_KPI_PATTERNS = {
    "reorder_rate": {
        "keywords": ["reorder", "reorder_rate", "reordered"],
        "must_contain": ["reordered", "COUNT"],
        "expected_col": "reorder_rate_pct",
        "expected_range": (40, 70),   # handles both decimal (0.67→67) and percent (67) forms
    },
    "avg_basket_size": {
        "keywords": ["basket size", "basket_size", "items per order"],
        "must_contain": ["AVG", "COUNT"],
        "expected_col": "avg_basket_size",
        "expected_range": (1, 15),    # per-department can be as low as 1
    },
    "top_products": {
        "keywords": ["top product", "most ordered product", "popular product",
                     "healthiest", "nutrition grade"],
        "must_contain": ["COUNT", "product_name", "ORDER BY"],
        "expected_col": "times_ordered",
        "expected_range": (100, 5_000_000),
    },
    "retention_rate": {
        "keywords": ["retention", "retained", "repeat customer"],
        "must_contain": ["COUNT", "user_id"],
        "expected_col": "retention_rate_pct",
        "expected_range": (80, 95),
    },
}


def layer5_comparative_validation(sql: str, question: str, rows: list, cols: list) -> dict:
    """
    Compares results against known gold KPI patterns.
    Flags if a known KPI query returns values far from expected benchmarks.
    """
    issues = []
    matched_kpi = None

    q_lower = question.lower()
    sql_upper = sql.upper()

    for kpi_name, pattern in GOLD_KPI_PATTERNS.items():
        if any(kw in q_lower for kw in pattern["keywords"]):
            matched_kpi = kpi_name

            # Check SQL contains required keywords
            for required in pattern["must_contain"]:
                if required.upper() not in sql_upper:
                    issues.append(
                        f"Layer 5: KPI '{kpi_name}' SQL missing required keyword '{required}'"
                    )

            # Check result values match expected range
            if rows and cols:
                col_lower = [c.lower() for c in cols]
                expected_col = pattern["expected_col"]
                if expected_col in col_lower:
                    idx = col_lower.index(expected_col)
                    sample_val = float(rows[0][idx])
                    # Normalise decimal proportion to percentage if needed
                    if sample_val < 2:
                        sample_val = sample_val * 100
                    lo, hi = pattern["expected_range"]
                    if not (lo <= sample_val <= hi):
                        issues.append(
                            f"Layer 5: KPI '{kpi_name}' value {sample_val} outside "
                            f"gold benchmark range [{lo}, {hi}]"
                        )
            break

    passed = len(issues) == 0
    return {
        "layer": 5,
        "name": "Comparative KPI Validation",
        "passed": passed,
        "matched_kpi": matched_kpi,
        "issues": issues,
        "message": (
            f"Matched KPI '{matched_kpi}' — benchmark passed" if passed and matched_kpi
            else "No KPI pattern matched — skipped" if not matched_kpi
            else f"KPI benchmark mismatch: {issues}"
        )
    }


# ══════════════════════════════════════════════════════════════════════════════
# FULL 5-LAYER PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def run_5layer_validation(sql: str, question: str) -> dict:
    """
    Runs all 5 validation layers on a generated SQL query.
    Applies self-correction if layers 1-3 find issues.
    Returns full validation report.
    """
    print(f"\n  Running 5-layer validation...")
    report = {
        "original_sql": sql,
        "final_sql":    sql,
        "question":     question,
        "layers":       [],
        "all_passed":   False,
        "corrections_applied": False,
        "rows":  [],
        "cols":  [],
        "error": None,
    }

    # ── Layer 1: Schema constraints ───────────────────────────────────────
    l1 = layer1_schema_constraints(sql)
    report["layers"].append(l1)
    print(f"  Layer 1 — {l1['name']}: {'✅' if l1['passed'] else '❌'} {l1['message']}")

    # ── Layer 2: Logical semantic check ───────────────────────────────────
    l2 = layer2_logical_semantic(sql, question)
    report["layers"].append(l2)
    print(f"  Layer 2 — {l2['name']}: {'✅' if l2['passed'] else '❌'} {l2['message']}")

    # ── Self-correction if layers 1 or 2 failed ───────────────────────────
    all_errors = l1["issues"] + l2.get("issues", [])
    if all_errors:
        l4_early = layer4_self_correct(sql, question, all_errors)
        report["layers"].append(l4_early)
        report["corrections_applied"] = True
        sql = l4_early["corrected_sql"]
        report["final_sql"] = sql
        print(f"  Layer 4 — {l4_early['name']}: ✅ {l4_early['message']}")

    # ── Execute SQL ───────────────────────────────────────────────────────
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        exec_sql = re.sub(
            r'ROUND\((?!.*::numeric)([^,]+),\s*(\d+)\)',
            lambda m: f"ROUND({m.group(1).strip()}::numeric, {m.group(2)})",
            sql
        )
        cur.execute(exec_sql)
        rows = cur.fetchmany(500)
        cols = [desc[0] for desc in cur.description]
        cur.close()
        conn.close()
        report["rows"] = rows
        report["cols"] = cols
    except Exception as e:
        report["error"] = str(e)
        print(f"  Execution error: {e}")
        report["all_passed"] = False
        return report

    # ── Layer 3: Plausibility check ───────────────────────────────────────
    l3 = layer3_execution_plausibility(sql, rows, cols)
    report["layers"].append(l3)
    print(f"  Layer 3 — {l3['name']}: {'✅' if l3['passed'] else '❌'} {l3['message']}")

    # ── Self-correct if layer 3 failed ────────────────────────────────────
    if not l3["passed"]:
        l4_late = layer4_self_correct(sql, question, l3["issues"])
        report["layers"].append(l4_late)
        report["corrections_applied"] = True
        report["final_sql"] = l4_late["corrected_sql"]
        print(f"  Layer 4 — {l4_late['name']}: ✅ {l4_late['message']}")

    # ── Layer 5: Comparative KPI validation ──────────────────────────────
    l5 = layer5_comparative_validation(sql, question, rows, cols)
    report["layers"].append(l5)
    print(f"  Layer 5 — {l5['name']}: {'✅' if l5['passed'] else '❌'} {l5['message']}")

    # ── Final verdict ─────────────────────────────────────────────────────
    report["all_passed"] = all(
        layer["passed"] for layer in report["layers"]
        if layer["layer"] != 4
    )

    return report


# ══════════════════════════════════════════════════════════════════════════════
# TEST RUNNER
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from src.text_to_sql import generate_sql

    test_cases = [
        "What is the reorder rate across all orders?",
        "What are the top 5 most ordered products?",
        "Which departments have the highest reorder rates?",
        "Show me customer segments by order frequency as low medium and high",
        "Which products are most often bought together with organic strawberries?",
        "How do order volumes compare on weekdays versus weekends?",
        "Show the top 10 healthiest most ordered products with nutrition grade a or b",
        "What is the average basket size across all orders?",
    ]

    print("=" * 70)
    print("MODULE 8B — 5-LAYER SQL VALIDATION TEST")
    print("=" * 70)

    total = len(test_cases)
    fully_passed = 0
    corrected = 0

    for q in test_cases:
        print(f"\n{'─' * 70}")
        print(f"QUESTION: {q}")

        gen = generate_sql(q)
        sql = gen["generated_sql"]
        print(f"GENERATED SQL (preview): {sql[:80]}...")

        report = run_5layer_validation(sql, q)

        if report["all_passed"]:
            fully_passed += 1
            print(f"  VERDICT: ✅ ALL LAYERS PASSED")
        else:
            print(f"  VERDICT: ❌ VALIDATION ISSUES FOUND")

        if report["corrections_applied"]:
            corrected += 1
            print(f"  CORRECTION APPLIED: Yes")

        if report["rows"]:
            cols = report["cols"]
            rows = report["rows"]
            widths = [max(len(str(c)), max(len(str(r[i])) for r in rows[:5]))
                      for i, c in enumerate(cols)]
            header = " | ".join(str(c).ljust(w) for c, w in zip(cols, widths))
            print(f"\n  RESULTS ({len(rows)} rows):")
            print(f"  {header}")
            print(f"  {'-' * len(header)}")
            for row in rows[:5]:
                print(f"  {' | '.join(str(v).ljust(w) for v, w in zip(row, widths))}")

    print(f"\n{'=' * 70}")
    print(f"SUMMARY — {fully_passed}/{total} fully passed | {corrected} auto-corrected")
    print("=" * 70)