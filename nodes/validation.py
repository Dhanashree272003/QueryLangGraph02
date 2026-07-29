"""
Validation Node for Query LangGraph (querylanggraph02).

This node performs domain-specific business rule validation on parsed QueryIntent objects
including metrics, service catalogues, failure modes, time ranges, aggregations, and bounds.
"""

import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger("QueryLangGraph.Nodes.Validation")


class ValidationNode:
    """
    Business Validation Node for AIOps queries.

    Responsibilities:
    - Validate requested metrics against platform metric registry.
    - Validate target services against service catalog.
    - Bounds checking on time ranges and aggregation parameters.
    - Provide helpful error messages and suggested corrections on failure.
    """

    ALLOWED_METRICS = {
        "cpu_usage", "memory_usage", "disk_io", "network_in", "network_out",
        "latency", "error_rate", "throughput", "response_time", "queue_depth",
        "cpu_utilization", "memory_utilization", "active_connections", "request_count"
    }

    ALLOWED_SERVICES = {
        "auth-service", "payment-service", "inventory-service", "order-service",
        "user-service", "api-gateway", "database", "cache-service", "notification-service",
        "api-service", "all", "*"
    }

    ALLOWED_AGGREGATIONS = {"avg", "max", "min", "sum", "count", "p95", "p99", "median"}

    ALLOWED_DURATIONS = {
        "last_5_mins", "last_15_mins", "last_30_mins", "last_1_hour",
        "last_6_hours", "last_12_hours", "last_24_hours", "last_7_days", "last_30_days"
    }

    def validate_query_intent(self, intent: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Validates business rules for the query intent.

        Args:
            intent (Dict[str, Any]): Parsed QueryIntent dictionary.

        Returns:
            Tuple[bool, Dict[str, Any]]:
                - isValid (bool): True if intent passes all business rules.
                - error_report (Dict[str, Any]): Details of error, explanation, and suggestions if invalid.
        """
        errors = []
        suggestions = []

        # 1. Validate Metrics
        metrics = intent.get("metrics", [])
        if metrics and isinstance(metrics, list):
            for m in metrics:
                m_str = str(m).lower()
                if m_str not in self.ALLOWED_METRICS and not any(k in m_str for k in ["usage", "rate", "time", "count"]):
                    errors.append(f"Metric '{m}' is not recognized in telemetry catalog.")
                    suggestions.append(f"Use one of the supported metrics: {', '.join(sorted(list(self.ALLOWED_METRICS)[:6]))}")

        # 2. Validate Services
        services = intent.get("services", [])
        if services and isinstance(services, list):
            for s in services:
                s_str = str(s).lower()
                if s_str not in self.ALLOWED_SERVICES and not s_str.endswith("-service"):
                    errors.append(f"Service '{s}' is not recognized in the microservice registry.")
                    suggestions.append(f"Available services include: auth-service, payment-service, api-gateway, database, order-service.")

        # 3. Validate Aggregation
        agg = intent.get("aggregation", {})
        if isinstance(agg, dict) and agg.get("function"):
            fn = str(agg["function"]).lower()
            if fn not in self.ALLOWED_AGGREGATIONS:
                errors.append(f"Aggregation function '{fn}' is unsupported.")
                suggestions.append(f"Supported functions: {', '.join(sorted(list(self.ALLOWED_AGGREGATIONS)))}")

        # 4. Bounds Check on Time Range
        time_range = intent.get("time_range", {})
        if isinstance(time_range, dict):
            duration = time_range.get("duration")
            if duration and duration not in self.ALLOWED_DURATIONS:
                # Accept custom duration if it matches standard patterns, else warn
                if not any(duration.startswith(p) for p in ["last_", "past_", "range_"]):
                    errors.append(f"Time duration '{duration}' exceeds allowed bounds or format.")
                    suggestions.append("Valid duration examples: 'last_1_hour', 'last_24_hours', 'last_7_days'.")

        if errors:
            logger.warning(f"ValidationNode: QueryIntent validation failed with {len(errors)} error(s).")
            return False, {
                "status": "validation_error",
                "error_code": "ERR_BUSINESS_VALIDATION_FAILED",
                "explanation": "One or more parameters in your query violate platform schema or operational limits.",
                "issues": errors,
                "suggested_corrections": suggestions
            }

        logger.info("ValidationNode: QueryIntent successfully validated.")
        return True, {}

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph entry point for Validation Node.

        Args:
            state (Dict[str, Any]): Incoming QueryState dictionary.

        Returns:
            Dict[str, Any]: Updated QueryState dictionary.
        """
        query_intent = state.get("query_intent", {})
        is_valid, error_report = self.validate_query_intent(query_intent)

        updated_state = dict(state)
        updated_state["is_validated"] = is_valid

        if not is_valid:
            updated_state["error_type"] = "validation_error"
            updated_state["validation_error"] = error_report
            updated_state["final_response"] = {
                "status": "validation_failed",
                "error_code": error_report.get("error_code"),
                "message": error_report.get("explanation"),
                "details": error_report.get("issues"),
                "suggestions": error_report.get("suggested_corrections"),
                "data": None,
                "metadata": {
                    "stage": "validation_node",
                    "passed": False
                }
            }

        return updated_state


def run_validation(state: Dict[str, Any]) -> Dict[str, Any]:
    """Functional wrapper for Validation Node execution."""
    node = ValidationNode()
    return node.execute(state)
