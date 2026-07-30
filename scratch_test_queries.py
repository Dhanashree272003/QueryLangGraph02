"""
Test script for QueryLangGraph02 — exercises all query categories against schema.sql tables.
"""

import logging
import json
import config  # noqa: F401 — loads .env (GEMINI_API_KEY) before graph is imported
import graph

# Set INFO logging so node flow is visible
logging.basicConfig(level=logging.INFO, format="%(name)s | %(levelname)s | %(message)s")

queries = [
    # --- Single-category: node_classification (incidents) ---
    "What incidents were predicted and with what confidence?",
    # --- Single-category: node_severity_update (severity) ---
    "Show me the revised severity and escalation status for all episodes.",
    # --- Single-category: node_forecasting (forecast / TTF) ---
    "What is the time to failure forecast and how confident is the prediction?",
    # --- Single-category: node_feature_engineering (feature contribution) ---
    "Which features had the highest error rate and log critical count?",
    # --- Single-category: pipeline_results (system health) ---
    "Show overall system health and combined pipeline results.",
    # --- Combinational: incident + severity + forecast ---
    "What critical incidents occurred, what was their revised severity, and what is the time to failure?",
    # --- Visualization ---
    "Plot a graph of time to failure trend across cycles for memory leak episodes.",
]

print("=" * 70)
print(" QueryLangGraph02 — Schema.sql Node Table Integration Test Run")
print("=" * 70)

for idx, q in enumerate(queries, 1):
    print(f"\n{'='*70}")
    print(f"TEST {idx}: {q}")
    print(f"{'='*70}")
    try:
        res = graph.execute_query(q)
        status = res.get("status", "unknown")
        meta = res.get("metadata", {})
        cats  = meta.get("categories_fetched", [])
        recs  = meta.get("total_records_fetched", 0)
        has_vis = (
            isinstance(res.get("visualization"), dict)
            and res.get("visualization", {}).get("base64_image") is not None
        )

        print(f"  STATUS           : {status}")
        print(f"  CATEGORIES       : {cats}")
        print(f"  RECORDS FETCHED  : {recs}")
        print(f"  VISUALIZATION    : {'Yes (base64 PNG)' if has_vis else 'No'}")

        answer = res.get("answer", "")
        if answer:
            snippet = answer[:300].replace("\n", " ")
            print(f"  ANSWER SNIPPET   : {snippet} ...")

        error = res.get("error")
        if error:
            print(f"  ERROR            : {error}")

    except Exception as e:
        print(f"  [EXCEPTION] {e}")

print(f"\n{'='*70}")
print(" All test queries complete.")
print(f"{'='*70}")
