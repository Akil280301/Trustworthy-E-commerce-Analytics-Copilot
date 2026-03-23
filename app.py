"""
app.py
Trustworthy E-commerce Analytics Copilot — Streamlit Dashboard
Module 10 — Final UI
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).parent))
from src.text_to_sql import generate_sql
from src.sql_validator import run_5layer_validation

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Trustworthy E-commerce Analytics Copilot",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #666;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        border-left: 4px solid #1f77b4;
    }
    .sql-box {
        background: #1e1e1e;
        color: #d4d4d4;
        padding: 1rem;
        border-radius: 8px;
        font-family: monospace;
        font-size: 0.85rem;
        white-space: pre-wrap;
        overflow-x: auto;
    }
    .layer-pass { color: #28a745; font-weight: 600; }
    .layer-fail { color: #dc3545; font-weight: 600; }
    .stAlert { border-radius: 8px; }
    div[data-testid="stExpander"] {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shopping-cart.png", width=60)
    st.markdown("## 🛒 Analytics Copilot")
    st.markdown("**Team Texas** | FSE 570 Capstone")
    st.divider()

    st.markdown("### ⚙️ Settings")
    enable_validation = st.toggle("5-Layer SQL Validation", value=True,
                                  help="Run full validation pipeline on generated SQL")
    show_sql = st.toggle("Show Generated SQL", value=True)
    show_context = st.toggle("Show RAG Context", value=False)

    st.divider()
    st.markdown("### 📊 Quick KPIs")
    st.markdown("""
    - 🏪 **3.4M** orders
    - 📦 **37.3M** order-product rows
    - 🛍️ **49,688** products
    - 🏬 **21** departments
    - 🥗 **134** aisles
    - 📅 **342** US holidays
    - 🧪 **173K** nutrition records
    """)

    st.divider()
    st.markdown("### 💡 Example Queries")
    example_queries = [
        "What are the top 5 most ordered products?",
        "Which departments have the highest reorder rates?",
        "Show customer segments by order frequency",
        "Which products are most often bought with bananas?",
        "What is the average basket size per department?",
        "Show the healthiest most ordered products",
        "How do orders compare on weekdays vs weekends?",
        "Which aisle has the highest reorder rate?",
        "What hour of the day has the most orders?",
        "Show me new vs returning customer orders by day",
    ]
    selected_example = st.selectbox("Pick an example", [""] + example_queries)

    st.divider()
    st.markdown("### 📈 Evaluation Results")
    st.markdown("""
    | Metric | Score |
    |--------|-------|
    | Adversarial Safety | **100%** |
    | Hallucination Rate | **0%** |
    | Compositional | **58.3%** |
    | SQL Validation | **7/8** |
    """)


# ── Main content ──────────────────────────────────────────────────────────────
st.markdown('<div class="main-header">🛒 Trustworthy E-commerce Analytics Copilot</div>',
            unsafe_allow_html=True)
st.markdown('<div class="sub-header">Natural language → Validated SQL → Real data from 37.3M order warehouse</div>',
            unsafe_allow_html=True)

# ── Query input ───────────────────────────────────────────────────────────────
col1, col2 = st.columns([5, 1])
with col1:
    query_input = st.text_input(
        "Ask a business question",
        value=selected_example if selected_example else "",
        placeholder="e.g. What are the top 10 most ordered products?",
        label_visibility="collapsed",
    )
with col2:
    run_btn = st.button("🔍 Analyse", type="primary", use_container_width=True)

# ── Run pipeline ──────────────────────────────────────────────────────────────
if run_btn and query_input.strip():

    with st.spinner("🤖 Generating SQL with Groq LLaMA 3.3 70B..."):
        t_start = time.time()
        result  = generate_sql(query_input.strip())
        gen_time = round(time.time() - t_start, 2)

    # Run 5-layer validation if enabled
    validation_report = None
    if enable_validation and result["validation"]["passed"]:
        with st.spinner("🔍 Running 5-layer SQL validation..."):
            validation_report = run_5layer_validation(
                result["generated_sql"], query_input.strip()
            )

    # ── Status banner ─────────────────────────────────────────────────────────
    if result["error"]:
        st.error(f"❌ Execution error: {result['error'][:200]}")
    elif not result["validation"]["passed"]:
        st.warning(f"⚠️ Query not supported or blocked: {result['validation']['message']}")
    elif result["rows"]:
        st.success(f"✅ Query executed successfully — {len(result['rows'])} row(s) returned")
    else:
        st.info("ℹ️ Query ran but returned no results")

    # ── Metrics row ───────────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Groq Latency", f"{result['groq_latency']}s")
    with m2:
        st.metric("DB Latency", f"{result['db_latency']}s")
    with m3:
        st.metric("Rows Returned", len(result.get("rows", [])))
    with m4:
        val_status = "✅ Passed" if result["validation"]["passed"] else "❌ Failed"
        st.metric("Validation", val_status)

    st.divider()

    # ── Main results area ─────────────────────────────────────────────────────
    left_col, right_col = st.columns([3, 2])

    with left_col:

        # Results table
        if result["rows"] and result["columns"]:
            st.markdown("### 📋 Query Results")
            df = pd.DataFrame(result["rows"], columns=result["columns"])

            # Convert numeric columns
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    pass

            st.dataframe(df, use_container_width=True, height=350)

            # ── Auto-visualisation ────────────────────────────────────────────
            st.markdown("### 📊 Visualisation")
            numeric_cols = df.select_dtypes(include="number").columns.tolist()
            text_cols    = df.select_dtypes(exclude="number").columns.tolist()

            if numeric_cols and text_cols:
                x_col = text_cols[0]
                y_col = numeric_cols[0]

                # Pick chart type based on number of rows
                if len(df) <= 2:
                    fig = go.Figure(go.Pie(
                        labels=df[x_col].astype(str),
                        values=df[y_col],
                        hole=0.4,
                    ))
                    fig.update_layout(title=f"{y_col} by {x_col}")
                elif len(df) <= 25:
                    fig = px.bar(
                        df, x=x_col, y=y_col,
                        title=f"{y_col} by {x_col}",
                        color=y_col,
                        color_continuous_scale="Blues",
                        text_auto=".2s",
                    )
                    fig.update_layout(xaxis_tickangle=-35)
                else:
                    fig = px.line(
                        df, x=x_col, y=y_col,
                        title=f"{y_col} over {x_col}",
                        markers=True,
                    )

                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=10, r=10, t=40, b=10),
                    height=350,
                )
                st.plotly_chart(fig, use_container_width=True)

            elif len(numeric_cols) >= 2 and not text_cols:
                # All numeric — scatter
                fig = px.scatter(
                    df, x=numeric_cols[0], y=numeric_cols[1],
                    title=f"{numeric_cols[1]} vs {numeric_cols[0]}"
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)

            else:
                st.info("No suitable columns for automatic visualisation.")

            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                "⬇️ Download results as CSV",
                csv,
                file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )

    with right_col:

        # Generated SQL
        if show_sql:
            st.markdown("### 🧾 Generated SQL")
            st.markdown(
                f'<div class="sql-box">{result["generated_sql"]}</div>',
                unsafe_allow_html=True
            )

        # 5-Layer Validation report
        if validation_report:
            st.markdown("### 🛡️ 5-Layer Validation")
            for layer in validation_report["layers"]:
                if layer["layer"] == 4:
                    continue  # Skip self-correction layer in display
                icon  = "✅" if layer["passed"] else "❌"
                label = f"{icon} Layer {layer['layer']}: {layer['name']}"
                with st.expander(label, expanded=not layer["passed"]):
                    st.markdown(f"**Status:** {layer['message']}")
                    if layer.get("issues"):
                        for issue in layer["issues"]:
                            st.markdown(f"- ⚠️ {issue}")
                    if layer.get("matched_kpi"):
                        st.markdown(f"**Matched KPI:** `{layer['matched_kpi']}`")
                    if layer.get("confidence"):
                        st.markdown(f"**Confidence:** {layer['confidence']:.0%}")

            if validation_report.get("corrections_applied"):
                st.info("🔧 SQL was auto-corrected by Layer 4 self-correction")

            overall = "✅ All layers passed" if validation_report["all_passed"] else "⚠️ Some layers flagged issues"
            st.markdown(f"**Overall:** {overall}")

        # RAG context
        if show_context:
            st.markdown("### 🔍 RAG Context Used")
            st.text_area(
                "Retrieved context",
                value=result.get("context_used", "No context retrieved"),
                height=200,
                disabled=True,
            )


# ── History tab ───────────────────────────────────────────────────────────────
elif not run_btn:
    st.markdown("---")
    st.markdown("### 🚀 How it works")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""
        #### 1️⃣ RAG Retrieval
        Your question is embedded using **MiniLM-L6-v2** and matched against
        the FAISS knowledge base of KPI docs and SQL examples.
        """)
    with c2:
        st.markdown("""
        #### 2️⃣ SQL Generation
        **Groq LLaMA 3.3 70B** generates schema-aware PostgreSQL
        with RAG context injected into the prompt.
        """)
    with c3:
        st.markdown("""
        #### 3️⃣ 5-Layer Validation
        Schema constraints → Logical check → Plausibility →
        Self-correction → KPI benchmark comparison.
        """)
    with c4:
        st.markdown("""
        #### 4️⃣ Live Execution
        Validated SQL runs directly against **37.3M rows**
        in PostgreSQL. Numbers are never hallucinated.
        """)

    st.markdown("---")
    st.markdown("### 📊 Warehouse at a glance")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Orders", "3.4M")
    col2.metric("Products", "49,688")
    col3.metric("Reorder Rate", "58.97%")
    col4.metric("Avg Basket Size", "10.09 items")
    col5.metric("Basket Diversity", "7.26 aisles")

    st.markdown("---")
    st.markdown("### 🏆 Top Products")
    top_products = pd.DataFrame({
        "Product": ["Banana", "Bag of Organic Bananas", "Organic Strawberries",
                    "Organic Baby Spinach", "Organic Hass Avocado"],
        "Orders": [472565, 379450, 264683, 241921, 213584]
    })
    fig = px.bar(top_products, x="Orders", y="Product", orientation="h",
                 color="Orders", color_continuous_scale="Blues",
                 title="Top 5 Most Ordered Products")
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)