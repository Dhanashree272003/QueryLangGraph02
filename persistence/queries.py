"""
Persistence SQL Queries Module for Query LangGraph (querylanggraph02).

Contains parameterized SQL queries for retrieving Inference Graph outputs and telemetry
data from SQLite tables.
"""

from typing import Dict, Any, Tuple, List


class SQLQueries:
    """
    SQL Query repository providing parameterized queries for AIOps domain categories.
    
    Guarantees parameterized SQL string generation with placeholder bindings to prevent SQL injection.
    """

    # Static parameterized templates
    FETCH_METRICS = """
        SELECT timestamp, service, metric_name, metric_value, unit
        FROM telemetry_metrics
        WHERE (? IS NULL OR service = ?)
          AND (? IS NULL OR metric_name = ?)
        ORDER BY timestamp DESC
        LIMIT ?;
    """

    FETCH_INCIDENTS = """
        SELECT incident_id, timestamp, service, failure_mode, confidence, root_cause
        FROM classification_output
        WHERE (? IS NULL OR service = ?)
          AND (? IS NULL OR failure_mode = ?)
        ORDER BY timestamp DESC
        LIMIT ?;
    """

    FETCH_SEVERITY = """
        SELECT incident_id, timestamp, service, initial_severity, updated_severity, escalation_reason
        FROM updated_severity
        WHERE (? IS NULL OR service = ?)
        ORDER BY timestamp DESC
        LIMIT ?;
    """

    FETCH_FORECAST = """
        SELECT timestamp, service, metric_name, forecast_value, time_to_failure_mins, anomaly_probability
        FROM forecast
        WHERE (? IS NULL OR service = ?)
        ORDER BY timestamp DESC
        LIMIT ?;
    """

    FETCH_RELIABILITY = """
        SELECT timestamp, service, slo_percentage, uptime_percentage, error_budget_remaining
        FROM reliability
        WHERE (? IS NULL OR service = ?)
        ORDER BY timestamp DESC
        LIMIT ?;
    """

    FETCH_FEATURE_CONTRIBUTION = """
        SELECT incident_id, timestamp, service, feature_name, importance_score, additional_metadata
        FROM inference_outputs
        WHERE (? IS NULL OR service = ?)
        ORDER BY importance_score DESC
        LIMIT ?;
    """

    FETCH_SYSTEM_HEALTH = """
        SELECT m.timestamp, m.service, m.metric_name, m.metric_value, c.failure_mode
        FROM telemetry_metrics m
        LEFT JOIN classification_output c ON m.service = c.service AND datetime(m.timestamp) = datetime(c.timestamp)
        WHERE (? IS NULL OR m.service = ?)
        ORDER BY m.timestamp DESC
        LIMIT ?;
    """

    @classmethod
    def build_parameterized_query(
        cls,
        table_name: str,
        services: List[str],
        metrics: List[str],
        limit: int = 100
    ) -> Tuple[str, Tuple[Any, ...]]:
        """
        Builds a safe parameterized SQL query and tuple of parameter bindings.

        Args:
            table_name (str): Target table name (validated against whitelist).
            services (List[str]): Service filter values.
            metrics (List[str]): Metric name filter values.
            limit (int): Max records to retrieve.

        Returns:
            Tuple[str, Tuple[Any, ...]]: (SQL string, binding parameters tuple)
        """
        where_clauses = []
        params: List[Any] = []

        if services and len(services) > 0 and services[0] not in ["all", "*"]:
            service_placeholders = ",".join(["?"] * len(services))
            where_clauses.append(f"service IN ({service_placeholders})")
            params.extend(services)

        if metrics and len(metrics) > 0 and table_name in ["telemetry_metrics", "forecast"]:
            metric_placeholders = ",".join(["?"] * len(metrics))
            where_clauses.append(f"metric_name IN ({metric_placeholders})")
            params.extend(metrics)

        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        sql = f"SELECT * FROM {table_name}{where_sql} ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        return sql, tuple(params)
