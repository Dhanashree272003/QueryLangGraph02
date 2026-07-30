"""
Persistence SQL Queries Module for Query LangGraph (querylanggraph02).

Contains parameterized SQL queries for retrieving Inference Graph outputs and telemetry
data from SQLite tables defined in persistence/schema.sql.

Tables served:
  Raw telemetry:     metrics, logs, traces, severity
  Node outputs:      node_feature_engineering, node_preliminary_severity,
                     node_classification, node_tumbling_window, node_forecasting,
                     node_severity_update, node_human_gate
  Combined snapshot: pipeline_results
"""

from typing import Dict, Any, Tuple, List


class SQLQueries:
    """
    SQL Query repository providing parameterized queries for AIOps domain categories.

    Guarantees parameterized SQL string generation with placeholder bindings to prevent SQL injection.
    """

    # --------------------------------------------------------------------- #
    #  Raw Telemetry
    # --------------------------------------------------------------------- #
    FETCH_METRICS = """
        SELECT episode_id, failure_mode, service, timestamp, elapsed_s,
               cpu_utilization, memory_utilization, heap_mb, p99_latency,
               error_rate, cpu_saturation, rps, http_5xx_rate
        FROM metrics
        ORDER BY timestamp DESC
        LIMIT ?;
    """

    FETCH_LOGS = """
        SELECT episode_id, failure_mode, service, timestamp, log_level, exception_type, log_message
        FROM logs
        ORDER BY timestamp DESC
        LIMIT ?;
    """

    FETCH_SEVERITY_RAW = """
        SELECT episode_id, failure_mode, timestamp, Severity, RawSeverity, WeightedScore,
               CriticalCount, WarningCount, Reason, RecommendedAction
        FROM severity
        ORDER BY timestamp DESC
        LIMIT ?;
    """

    # --------------------------------------------------------------------- #
    #  Node Output Tables
    # --------------------------------------------------------------------- #
    FETCH_FEATURE_ENGINEERING = """
        SELECT cycle, episode_id, failure_mode, timestamp, elapsed_s,
               cpu_utilization, memory_utilization, heap_mb, p99_latency, error_rate,
               log_count, log_critical_count, log_has_exception, log_has_novel_template
        FROM node_feature_engineering
        ORDER BY timestamp DESC
        LIMIT ?;
    """

    FETCH_PRELIMINARY_SEVERITY = """
        SELECT cycle, episode_id, failure_mode, timestamp, elapsed_s,
               preliminary_severity, severity_raw, weighted_score,
               critical_count, warning_count, blast_size, reason, recommended_action
        FROM node_preliminary_severity
        ORDER BY timestamp DESC
        LIMIT ?;
    """

    FETCH_CLASSIFICATION = """
        SELECT cycle, episode_id, failure_mode, timestamp, elapsed_s,
               predicted_failure, prediction_probability
        FROM node_classification
        ORDER BY timestamp DESC
        LIMIT ?;
    """

    FETCH_TUMBLING_WINDOW = """
        SELECT cycle, episode_id, failure_mode, timestamp, elapsed_s,
               dominant_state, vote_distribution, window_margin, window_full, window_size
        FROM node_tumbling_window
        ORDER BY timestamp DESC
        LIMIT ?;
    """

    FETCH_FORECASTING = """
        SELECT cycle, episode_id, failure_mode, timestamp, elapsed_s,
               algorithm_used, history_steps, forecast_horizon_s,
               time_to_failure, earliest_ttf_feature, forecast_confidence, threshold_crossed
        FROM node_forecasting
        ORDER BY timestamp DESC
        LIMIT ?;
    """

    FETCH_SEVERITY_UPDATE = """
        SELECT cycle, episode_id, failure_mode, timestamp, elapsed_s,
               preliminary_severity, forecast_confidence, time_to_failure, earliest_ttf_feature,
               impact_band, urgency_band, gate_passed, candidate_severity, revised_severity,
               is_escalated, is_deescalated, dwell_count, reason
        FROM node_severity_update
        ORDER BY timestamp DESC
        LIMIT ?;
    """

    FETCH_HUMAN_GATE = """
        SELECT review_id, incident_id, episode_id, failure_mode, failure_label,
               old_severity, new_severity, final_severity, decision, operator,
               reason, confidence, ttf_seconds, impact_band, urgency_band, recorded_at
        FROM node_human_gate
        ORDER BY recorded_at DESC
        LIMIT ?;
    """

    # --------------------------------------------------------------------- #
    #  Combinational Snapshot
    # --------------------------------------------------------------------- #
    FETCH_PIPELINE_RESULTS = """
        SELECT cycle, episode_id, failure_mode, timestamp, elapsed_s,
               fe_cpu_utilization, fe_memory_utilization, fe_heap_mb, fe_error_rate, fe_p99_latency,
               preliminary_severity, severity_weighted_score,
               predicted_failure, prediction_probability,
               dominant_state, time_to_failure, forecast_confidence,
               candidate_severity, revised_severity,
               hg_review_id, hg_decision, hg_final_severity
        FROM pipeline_results
        ORDER BY timestamp DESC
        LIMIT ?;
    """

    # --------------------------------------------------------------------- #
    #  Table whitelist (for parameterized builder)
    # --------------------------------------------------------------------- #
    ALLOWED_TABLES = {
        "metrics",
        "logs",
        "traces",
        "severity",
        "node_feature_engineering",
        "node_preliminary_severity",
        "node_classification",
        "node_tumbling_window",
        "node_forecasting",
        "node_severity_update",
        "node_human_gate",
        "pipeline_results",
    }

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
            services (List[str]): Service filter values (matched against 'service' column where present).
            metrics (List[str]): Metric name filter values (unused for node tables; kept for API compat).
            limit (int): Max records to retrieve.

        Returns:
            Tuple[str, Tuple[Any, ...]]: (SQL string, binding parameters tuple)
        """
        # Validate table against whitelist to prevent SQL injection
        safe_table = table_name if table_name in cls.ALLOWED_TABLES else "metrics"

        where_clauses = []
        params: List[Any] = []

        # Use 'failure_mode' for node tables; 'service' for raw telemetry
        service_col = "service" if safe_table in {"metrics", "logs", "traces"} else "failure_mode"

        if services and len(services) > 0 and services[0] not in ["all", "*"]:
            service_placeholders = ",".join(["?"] * len(services))
            where_clauses.append(f"{service_col} IN ({service_placeholders})")
            params.extend(services)

        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        sql = f"SELECT * FROM {safe_table}{where_sql} ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        return sql, tuple(params)
