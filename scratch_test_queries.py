import graph
import json

queries = [
    "What critical incidents occurred on payment-service and what was their updated severity?",
    "What is the time to failure forecast for auth-service?",
    "What is the SLO percentage and error budget for auth-service?",
    "What feature contributed most to the outage on order-service?",
    "Show system health and plot graph for payment-service"
]

for idx, q in enumerate(queries, 1):
    print(f"==================================================")
    print(f"TEST {idx}: '{q}'")
    print(f"==================================================")
    res = graph.execute_query(q)
    print("STATUS:", res.get("status"))
    print("CATEGORIES FETCHED:", res.get("metadata", {}).get("categories_fetched"))
    print("RECORDS FETCHED:", res.get("metadata", {}).get("total_records_fetched"))
    print("VISUALIZATION GENERATED:", res.get("visualization") is not None and res.get("visualization", {}).get("base64_image") is not None)
    if res.get("answer"):
        print("ANSWER SNIPPET:\n", res.get("answer")[:200])
    print("\n")
