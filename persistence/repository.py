"""
Repository Layer for Query LangGraph (querylanggraph02).

Provides structured data access methods for all AIOps domain query categories.
Executes parameterized SQL via DatabaseManager and returns clean, typed result sets.
"""

import logging
from typing import Dict, Any, List, Optional

from persistence.database import DatabaseManager
from persistence.queries import SQLQueries

logger = logging.getLogger("QueryLangGraph.Persistence.Repository")


class AIOpsRepository:
    """
    Data access repository for AIOps persistence tables.

    Each method maps to a query category and executes parameterized SQL,
    returning a structured list of row dictionaries. No business logic is
    applied here — pure data retrieval only.
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None) -> None:
        """
        Initialize repository with a database manager instance.

        Args:
            db_manager (Optional[DatabaseManager]): Optional injected DB manager for testing.
        """
        self.db = db_manager or DatabaseManager()

    # ------------------------------------------------------------------ #
    #  Metrics
    # ------------------------------------------------------------------ #
    def get_metrics(
        self,
        services: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Retrieve telemetry metric records.

        Args:
            services (List[str]): Service name filters.
            metrics (List[str]): Metric name filters.
            limit (int): Max records to fetch.

        Returns:
            List[Dict[str, Any]]: Telemetry metric rows.
        """
        sql, params = SQLQueries.build_parameterized_query(
            "telemetry_metrics", services or [], metrics or [], limit
        )
        result = self.db.execute_query(sql, params)
        logger.info(f"AIOpsRepository.get_metrics: Fetched {len(result)} rows.")
        return result

    # ------------------------------------------------------------------ #
    #  Incidents
    # ------------------------------------------------------------------ #
    def get_incidents(
        self,
        services: Optional[List[str]] = None,
        failure_modes: Optional[List[str]] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Retrieve classification output / incident records.

        Args:
            services (List[str]): Service name filters.
            failure_modes (List[str]): Failure mode type filters.
            limit (int): Max records to fetch.

        Returns:
            List[Dict[str, Any]]: Classification / incident rows.
        """
        where_clauses = []
        params: List[Any] = []

        if services and services[0] not in ["all", "*"]:
            placeholders = ",".join(["?"] * len(services))
            where_clauses.append(f"service IN ({placeholders})")
            params.extend(services)

        if failure_modes:
            placeholders = ",".join(["?"] * len(failure_modes))
            where_clauses.append(f"failure_mode IN ({placeholders})")
            params.extend(failure_modes)

        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        sql = f"SELECT * FROM classification_output{where_sql} ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        result = self.db.execute_query(sql, tuple(params))
        logger.info(f"AIOpsRepository.get_incidents: Fetched {len(result)} rows.")
        return result

    # ------------------------------------------------------------------ #
    #  Severity
    # ------------------------------------------------------------------ #
    def get_severity(
        self,
        services: Optional[List[str]] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Retrieve updated severity classification records.

        Args:
            services (List[str]): Service filters.
            limit (int): Max records.

        Returns:
            List[Dict[str, Any]]: Severity rows.
        """
        sql, params = SQLQueries.build_parameterized_query(
            "updated_severity", services or [], [], limit
        )
        result = self.db.execute_query(sql, params)
        logger.info(f"AIOpsRepository.get_severity: Fetched {len(result)} rows.")
        return result

    # ------------------------------------------------------------------ #
    #  Forecast
    # ------------------------------------------------------------------ #
    def get_forecast(
        self,
        services: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Retrieve forecast and time-to-failure records.

        Args:
            services (List[str]): Service filters.
            metrics (List[str]): Metric name filters.
            limit (int): Max records.

        Returns:
            List[Dict[str, Any]]: Forecast rows.
        """
        sql, params = SQLQueries.build_parameterized_query(
            "forecast", services or [], metrics or [], limit
        )
        result = self.db.execute_query(sql, params)
        logger.info(f"AIOpsRepository.get_forecast: Fetched {len(result)} rows.")
        return result

    # ------------------------------------------------------------------ #
    #  Reliability
    # ------------------------------------------------------------------ #
    def get_reliability(
        self,
        services: Optional[List[str]] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Retrieve SLO/SLA reliability metrics.

        Args:
            services (List[str]): Service filters.
            limit (int): Max records.

        Returns:
            List[Dict[str, Any]]: Reliability rows.
        """
        sql, params = SQLQueries.build_parameterized_query(
            "reliability", services or [], [], limit
        )
        result = self.db.execute_query(sql, params)
        logger.info(f"AIOpsRepository.get_reliability: Fetched {len(result)} rows.")
        return result

    # ------------------------------------------------------------------ #
    #  Feature Contribution
    # ------------------------------------------------------------------ #
    def get_feature_contribution(
        self,
        services: Optional[List[str]] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Retrieve inference output feature importance scores.

        Args:
            services (List[str]): Service filters.
            limit (int): Max records.

        Returns:
            List[Dict[str, Any]]: Feature contribution rows.
        """
        sql, params = SQLQueries.build_parameterized_query(
            "inference_outputs", services or [], [], limit
        )
        result = self.db.execute_query(sql, params)
        logger.info(f"AIOpsRepository.get_feature_contribution: Fetched {len(result)} rows.")
        return result

    # ------------------------------------------------------------------ #
    #  System Health
    # ------------------------------------------------------------------ #
    def get_system_health(
        self,
        services: Optional[List[str]] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Retrieve combined system health data (telemetry + classification output).

        Args:
            services (List[str]): Service filters.
            limit (int): Max records.

        Returns:
            List[Dict[str, Any]]: System health rows.
        """
        where_clauses = []
        params: List[Any] = []

        if services and services[0] not in ["all", "*"]:
            placeholders = ",".join(["?"] * len(services))
            where_clauses.append(f"m.service IN ({placeholders})")
            params.extend(services)

        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        sql = f"""
            SELECT m.timestamp, m.service, m.metric_name, m.metric_value,
                   c.failure_mode, c.confidence
            FROM telemetry_metrics m
            LEFT JOIN classification_output c ON m.service = c.service
            {where_sql}
            ORDER BY m.timestamp DESC
            LIMIT ?
        """
        params.append(limit)

        result = self.db.execute_query(sql, tuple(params))
        logger.info(f"AIOpsRepository.get_system_health: Fetched {len(result)} rows.")
        return result

    # ------------------------------------------------------------------ #
    #  Combinational Query Dispatcher
    # ------------------------------------------------------------------ #
    def get_combinational_data(
        self,
        retrieval_targets: List[Dict[str, Any]],
        services: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None,
        failure_modes: Optional[List[str]] = None,
        limit: int = 200
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Executes multiple category queries and aggregates results for combinational queries.

        Args:
            retrieval_targets (List[Dict[str, Any]]): List of routing targets with category/table info.
            services (List[str]): Service filters.
            metrics (List[str]): Metric filters.
            failure_modes (List[str]): Failure mode filters.
            limit (int): Per-category record limit.

        Returns:
            Dict[str, List[Dict[str, Any]]]: Category-keyed dictionary of retrieved rows.
        """
        combined: Dict[str, List[Dict[str, Any]]] = {}
        dispatch = {
            "metrics": lambda: self.get_metrics(services, metrics, limit),
            "incident": lambda: self.get_incidents(services, failure_modes, limit),
            "severity": lambda: self.get_severity(services, limit),
            "forecast": lambda: self.get_forecast(services, metrics, limit),
            "reliability": lambda: self.get_reliability(services, limit),
            "feature_contribution": lambda: self.get_feature_contribution(services, limit),
            "system_health": lambda: self.get_system_health(services, limit),
        }

        for target in retrieval_targets:
            category = target.get("category", "")
            if category in dispatch:
                try:
                    combined[category] = dispatch[category]()
                    logger.info(f"AIOpsRepository.get_combinational_data: Fetched '{category}' data.")
                except Exception as e:
                    logger.error(f"AIOpsRepository.get_combinational_data: Failed for '{category}': {e}")
                    combined[category] = []

        return combined

    # ------------------------------------------------------------------ #
    #  Query History & Search Audit Log
    # ------------------------------------------------------------------ #
    def log_query_history(
        self,
        user_query: str,
        session_id: Optional[str] = None,
        parsed_intent: Optional[Dict[str, Any]] = None,
        status: str = "success",
        execution_time_ms: float = 0.0
    ) -> bool:
        """Logs user query execution into query_history database table."""
        try:
            import json
            intent_json = json.dumps(parsed_intent or {}, default=str)
            sql = """
                INSERT INTO query_history (session_id, user_query, parsed_intent, status, execution_time_ms)
                VALUES (?, ?, ?, ?, ?)
            """
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (session_id or "default_session", user_query, intent_json, status, execution_time_ms))
                conn.commit()
            logger.info("AIOpsRepository.log_query_history: Logged query into history DB.")
            return True
        except Exception as e:
            logger.error(f"AIOpsRepository.log_query_history failed: {e}")
            return False

    def get_query_history(
        self,
        session_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Retrieves user query execution history from query_history table."""
        if session_id:
            sql = "SELECT * FROM query_history WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?"
            return self.db.execute_query(sql, (session_id, limit))
        else:
            sql = "SELECT * FROM query_history ORDER BY timestamp DESC LIMIT ?"
            return self.db.execute_query(sql, (limit,))

