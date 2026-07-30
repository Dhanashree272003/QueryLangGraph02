"""
Intent Router Module for Query LangGraph (querylanggraph02).

This router analyzes validated QueryIntent objects and determines the appropriate
retrieval strategy, mapping single and combinational query categories to specific
persistence database queries and target tables.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger("QueryLangGraph.Routers.IntentRouter")


class IntentRouter:
    """
    Router for classifying and dispatching query intents to retrieval handlers.

    Supports single-intent and multi-intent (Combinational) queries:
    - Metrics Query -> telemetry_metrics
    - Incident Query -> classification_output / telemetry_logs
    - Severity Query -> updated_severity
    - Forecast Query -> forecast / time_to_failure
    - Feature Contribution Query -> inference_outputs
    - System Health Query -> telemetry_metrics / classification_output
    - Reliability Query -> reliability
    - Combinational Query -> Multi-table retrieval plan
    """

    CATEGORY_MAP = {
        "metrics":              {"table": "metrics",                   "query_key": "FETCH_METRICS"},
        "incident":             {"table": "node_classification",       "query_key": "FETCH_CLASSIFICATION"},
        "severity":             {"table": "node_severity_update",      "query_key": "FETCH_SEVERITY_UPDATE"},
        "forecast":             {"table": "node_forecasting",          "query_key": "FETCH_FORECASTING"},
        "feature_contribution": {"table": "node_feature_engineering",  "query_key": "FETCH_FEATURE_ENGINEERING"},
        "system_health":        {"table": "pipeline_results",          "query_key": "FETCH_PIPELINE_RESULTS"},
        "reliability":          {"table": "pipeline_results",          "query_key": "FETCH_PIPELINE_RESULTS"},
        "tumbling_window":      {"table": "node_tumbling_window",      "query_key": "FETCH_TUMBLING_WINDOW"},
        "human_gate":           {"table": "node_human_gate",           "query_key": "FETCH_HUMAN_GATE"},
        "preliminary_severity": {"table": "node_preliminary_severity", "query_key": "FETCH_PRELIMINARY_SEVERITY"},
    }

    def route_query(self, query_intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determines target tables, query keys, and execution plan from QueryIntent.

        Args:
            query_intent (Dict[str, Any]): Parsed and validated query intent dictionary.

        Returns:
            Dict[str, Any]: Structured routing metadata object.
        """
        categories = query_intent.get("categories", ["metrics"])
        # Standardize categories list
        if isinstance(categories, str):
            categories = [categories]
        
        # Remove meta-category 'combinational' if explicitly present to get base categories
        base_categories = [c for c in categories if c.lower() != "combinational"]
        if not base_categories:
            base_categories = ["metrics"]

        is_combinational = len(base_categories) > 1 or query_intent.get("is_combinational", False)

        retrieval_targets = []
        target_tables = set()

        for cat in base_categories:
            cat_clean = str(cat).lower()
            if cat_clean in self.CATEGORY_MAP:
                mapping = self.CATEGORY_MAP[cat_clean]
                retrieval_targets.append({
                    "category": cat_clean,
                    "query_key": mapping["query_key"],
                    "table": mapping["table"]
                })
                target_tables.add(mapping["table"])
            else:
                # Default fallback
                retrieval_targets.append({
                    "category": cat_clean,
                    "query_key": "FETCH_METRICS",
                    "table": "telemetry_metrics"
                })
                target_tables.add("telemetry_metrics")

        routing_info = {
            "is_combinational": is_combinational,
            "primary_category": base_categories[0],
            "all_categories": base_categories,
            "target_tables": list(target_tables),
            "retrieval_targets": retrieval_targets,
            "metrics": query_intent.get("metrics", []),
            "services": query_intent.get("services", []),
            "time_range": query_intent.get("time_range", {}),
            "aggregation": query_intent.get("aggregation", {}),
            "filters": query_intent.get("filters", {}),
            "sorting": query_intent.get("sorting", {}),
            "visualization_request": query_intent.get("visualization_request", {})
        }

        logger.info(
            f"IntentRouter: Routed query to categories={base_categories}, "
            f"combinational={is_combinational}, tables={list(target_tables)}"
        )
        return routing_info

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph node entry point.

        Args:
            state (Dict[str, Any]): QueryState dictionary.

        Returns:
            Dict[str, Any]: Updated QueryState with routing_info.
        """
        query_intent = state.get("query_intent", {})
        routing_info = self.route_query(query_intent)

        updated_state = dict(state)
        updated_state["routing_info"] = routing_info
        return updated_state


def run_intent_router(state: Dict[str, Any]) -> Dict[str, Any]:
    """Functional wrapper for Intent Router execution."""
    router = IntentRouter()
    return router.execute(state)
