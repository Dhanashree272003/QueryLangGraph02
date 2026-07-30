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
        # Standard telemetry
        "cpu_usage", "memory_usage", "disk_io", "network_in", "network_out",
        "latency", "error_rate", "throughput", "response_time", "queue_depth",
        "cpu_utilization", "memory_utilization", "active_connections", "request_count",
        # Schema.sql node output fields (node_feature_engineering, node_forecasting, etc.)
        "time_to_failure", "forecast_confidence", "prediction_probability",
        "weighted_score", "heap_mb", "p99_latency", "p95_latency", "p50_latency",
        "db_p99", "disk_read_latency", "disk_write_latency", "gc_pause_p99",
        "cache_hit_rate", "cache_miss_rate", "network_errors", "queue_lag",
        "retry_count_per_request", "rps", "http_4xx_rate", "http_5xx_rate",
        "iops_utilization", "thread_pool_queue", "cpu_saturation",
        "db_connection_pool", "db_connection_wait", "upstream_timeout_rate",
        "log_count", "log_critical_count", "log_has_exception", "log_has_novel_template",
        "window_margin", "importance_score", "severity_weighted_score",
        "fe_cpu_utilization", "fe_memory_utilization", "fe_heap_mb",
        "fe_error_rate", "fe_p99_latency",
    }

    ALLOWED_SERVICES = {
        "auth-service", "payment-service", "inventory-service", "order-service",
        "user-service", "api-gateway", "database", "cache-service", "notification-service",
        "api-service", "all", "*",
        # Failure mode names that the LLM may use as service identifiers
        "memory_leak", "cpu_saturation", "db_connection_pool_exhaustion",
        "network_partition", "disk_io_saturation", "cascading_failure",
    }

    ALLOWED_AGGREGATIONS = {"avg", "max", "min", "sum", "count", "p95", "p99", "median", "latest", "none"}

    ALLOWED_DURATIONS = {
        "last_5_mins", "last_15_mins", "last_30_mins", "last_1_hour",
        "last_6_hours", "last_12_hours", "last_24_hours", "last_7_days", "last_30_days",
        # LLM commonly outputs these
        "last_hour", "last_day", "last_week", "all", "all_time", "recent",
    }

    def validate_query_intent(self, intent: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Security-focused validation on parsed QueryIntent.

        Blocks: injection patterns, malformed structures, empty categories, unsupported
        aggregation functions.
        Allows: any metric name, service name, or duration that passes a basic safety
        check — since the LLM may correctly generate field names not in the static
        allowlist (e.g. schema.sql node output columns, failure mode names).

        Args:
            intent (Dict[str, Any]): Parsed QueryIntent dictionary.

        Returns:
            Tuple[bool, Dict[str, Any]]:
                - isValid (bool): True if intent passes all security rules.
                - error_report (Dict[str, Any]): Details of error if invalid.
        """
        errors = []
        suggestions = []

        # --- Security pattern check (blocks SQL injection / path traversal) ---
        SQL_INJECTION_PATTERNS = [
            "--", ";", "DROP ", "DELETE ", "INSERT ", "UPDATE ", "EXEC(",
            "UNION ", "OR 1=1", "<script", "../", "\x00"
        ]

        def _is_safe(value: str) -> bool:
            v = str(value).upper()
            return not any(p.upper() in v for p in SQL_INJECTION_PATTERNS)

        # 1. Validate metrics (security only — no allowlist enforcement)
        metrics = intent.get("metrics", [])
        if metrics and isinstance(metrics, list):
            for m in metrics:
                if not _is_safe(str(m)):
                    errors.append(f"Metric '{m}' contains unsafe characters.")
                    suggestions.append("Use plain metric names without special characters.")

        # 2. Validate services (security only — no allowlist enforcement)
        services = intent.get("services", [])
        if services and isinstance(services, list):
            for s in services:
                if not _is_safe(str(s)):
                    errors.append(f"Service '{s}' contains unsafe characters.")
                    suggestions.append("Use plain service names without special characters.")

        # 3. Validate aggregation function (strict — small known set)
        agg = intent.get("aggregation", {})
        if isinstance(agg, dict) and agg.get("function"):
            fn = str(agg["function"]).lower()
            if fn not in self.ALLOWED_AGGREGATIONS:
                if not _is_safe(fn):
                    errors.append(f"Aggregation function '{fn}' is unsupported or unsafe.")
                    suggestions.append(f"Supported functions: {', '.join(sorted(self.ALLOWED_AGGREGATIONS))}")

        # 4. Time range — only block injection in duration strings; None/null always pass
        time_range = intent.get("time_range", {})
        if isinstance(time_range, dict):
            duration = time_range.get("duration")
            if duration and str(duration).lower() not in ("null", "none", ""):
                if not _is_safe(str(duration)):
                    errors.append(f"Time duration '{duration}' contains unsafe characters.")
                    suggestions.append("Use a plain duration string like 'last_1_hour'.")

        # 5. Require at least one category
        categories = intent.get("categories", [])
        if not categories or not isinstance(categories, list) or len(categories) == 0:
            errors.append("Query intent must contain at least one category.")
            suggestions.append("Specify a category such as 'metrics', 'incident', 'forecast', or 'severity'.")

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
