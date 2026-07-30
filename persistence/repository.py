"""
Repository Layer for Query LangGraph (querylanggraph02).

Provides structured data access methods for all AIOps domain query categories,
mapped to persistence/schema.sql node output tables and combinational pipeline_results.
Executes parameterized SQL via DatabaseManager and returns clean, typed result sets.

Table mapping:
  metrics          -> metrics (raw telemetry)
  incident         -> node_classification
  severity         -> node_severity_update
  preliminary_sev  -> node_preliminary_severity
  forecast         -> node_forecasting
  feature_engineering -> node_feature_engineering
  tumbling_window  -> node_tumbling_window
  human_gate       -> node_human_gate
  system_health    -> pipeline_results (combinational)
  reliability      -> node_severity_update (escalation context) / pipeline_results
  feature_contribution -> node_feature_engineering (log features)
"""

import logging
from typing import Dict, Any, List, Optional

from persistence.database import DatabaseManager
from persistence.queries import SQLQueries

logger = logging.getLogger("QueryLangGraph.Persistence.Repository")


class AIOpsRepository:
    """
    Data access repository for AIOps persistence tables (schema.sql).

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
    #  Raw Telemetry: Metrics
    # ------------------------------------------------------------------ #
    def get_metrics(
        self,
        services: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Retrieve raw telemetry metric records from the 'metrics' table.

        Args:
            services (List[str]): Service/failure_mode name filters.
            metrics (List[str]): Unused; retained for API compatibility.
            limit (int): Max records to fetch.

        Returns:
            List[Dict[str, Any]]: Raw metrics rows.
        """
        sql, params = SQLQueries.build_parameterized_query(
            "metrics", services or [], metrics or [], limit
        )
        result = self.db.execute_query(sql, params)
        logger.info(f"AIOpsRepository.get_metrics: Fetched {len(result)} rows.")
        return result

    # ------------------------------------------------------------------ #
    #  Node 3: Classification  →  Incidents
    # ------------------------------------------------------------------ #
    def get_incidents(
        self,
        services: Optional[List[str]] = None,
        failure_modes: Optional[List[str]] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Retrieve node_classification output records (predicted failure modes).

        Args:
            services (List[str]): Failure mode filters (mapped to episode failure_mode).
            failure_modes (List[str]): Explicit failure mode type filters.
            limit (int): Max records to fetch.

        Returns:
            List[Dict[str, Any]]: node_classification rows.
        """
        where_clauses = []
        params: List[Any] = []

        all_modes = list(set((failure_modes or []) + (services or [])))
        if all_modes and all_modes[0] not in ["all", "*"]:
            placeholders = ",".join(["?"] * len(all_modes))
            where_clauses.append(f"failure_mode IN ({placeholders})")
            params.extend(all_modes)

        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        sql = f"SELECT * FROM node_classification{where_sql} ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        result = self.db.execute_query(sql, tuple(params))
        logger.info(f"AIOpsRepository.get_incidents: Fetched {len(result)} rows.")
        return result

    # ------------------------------------------------------------------ #
    #  Node 6: Severity Update  →  Severity
    # ------------------------------------------------------------------ #
    def get_severity(
        self,
        services: Optional[List[str]] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Retrieve node_severity_update records (revised severity with escalation context).

        Args:
            services (List[str]): Failure mode filters.
            limit (int): Max records.

        Returns:
            List[Dict[str, Any]]: node_severity_update rows.
        """
        sql, params = SQLQueries.build_parameterized_query(
            "node_severity_update", services or [], [], limit
        )
        result = self.db.execute_query(sql, params)
        logger.info(f"AIOpsRepository.get_severity: Fetched {len(result)} rows.")
        return result

    # ------------------------------------------------------------------ #
    #  Node 5: Forecasting  →  Forecast
    # ------------------------------------------------------------------ #
    def get_forecast(
        self,
        services: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Retrieve node_forecasting records (time-to-failure predictions).

        Args:
            services (List[str]): Failure mode filters.
            metrics (List[str]): Unused; retained for API compatibility.
            limit (int): Max records.

        Returns:
            List[Dict[str, Any]]: node_forecasting rows.
        """
        sql, params = SQLQueries.build_parameterized_query(
            "node_forecasting", services or [], metrics or [], limit
        )
        result = self.db.execute_query(sql, params)
        logger.info(f"AIOpsRepository.get_forecast: Fetched {len(result)} rows.")
        return result

    # ------------------------------------------------------------------ #
    #  Node 1: Feature Engineering  →  Feature Contribution & Reliability
    # ------------------------------------------------------------------ #
    def get_reliability(
        self,
        services: Optional[List[str]] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Retrieve reliability context from pipeline_results (SLO/SLA approximation via severity and forecast).

        Args:
            services (List[str]): Failure mode filters.
            limit (int): Max records.

        Returns:
            List[Dict[str, Any]]: pipeline_results rows with severity and forecast fields.
        """
        sql, params = SQLQueries.build_parameterized_query(
            "pipeline_results", services or [], [], limit
        )
        result = self.db.execute_query(sql, params)
        logger.info(f"AIOpsRepository.get_reliability: Fetched {len(result)} rows.")
        return result

    def get_feature_contribution(
        self,
        services: Optional[List[str]] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Retrieve node_feature_engineering records for feature importance analysis.

        Args:
            services (List[str]): Failure mode filters.
            limit (int): Max records.

        Returns:
            List[Dict[str, Any]]: node_feature_engineering rows.
        """
        sql, params = SQLQueries.build_parameterized_query(
            "node_feature_engineering", services or [], [], limit
        )
        result = self.db.execute_query(sql, params)
        logger.info(f"AIOpsRepository.get_feature_contribution: Fetched {len(result)} rows.")
        return result

    # ------------------------------------------------------------------ #
    #  Pipeline Results  →  System Health (Combinational)
    # ------------------------------------------------------------------ #
    def get_system_health(
        self,
        services: Optional[List[str]] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Retrieve combined pipeline_results snapshot rows for system health overview.

        Args:
            services (List[str]): Failure mode filters.
            limit (int): Max records.

        Returns:
            List[Dict[str, Any]]: pipeline_results rows.
        """
        sql, params = SQLQueries.build_parameterized_query(
            "pipeline_results", services or [], [], limit
        )
        result = self.db.execute_query(sql, params)
        logger.info(f"AIOpsRepository.get_system_health: Fetched {len(result)} rows.")
        return result

    # ------------------------------------------------------------------ #
    #  Node 4: Tumbling Window
    # ------------------------------------------------------------------ #
    def get_tumbling_window(
        self,
        services: Optional[List[str]] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Retrieve node_tumbling_window records (dominant state & vote distribution).

        Args:
            services (List[str]): Failure mode filters.
            limit (int): Max records.

        Returns:
            List[Dict[str, Any]]: node_tumbling_window rows.
        """
        sql, params = SQLQueries.build_parameterized_query(
            "node_tumbling_window", services or [], [], limit
        )
        result = self.db.execute_query(sql, params)
        logger.info(f"AIOpsRepository.get_tumbling_window: Fetched {len(result)} rows.")
        return result

    # ------------------------------------------------------------------ #
    #  Node 7: Human Gate
    # ------------------------------------------------------------------ #
    def get_human_gate(
        self,
        services: Optional[List[str]] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Retrieve node_human_gate review records.

        Args:
            services (List[str]): Failure mode filters.
            limit (int): Max records.

        Returns:
            List[Dict[str, Any]]: node_human_gate rows.
        """
        sql, params = SQLQueries.build_parameterized_query(
            "node_human_gate", services or [], [], limit
        )
        result = self.db.execute_query(sql, params)
        logger.info(f"AIOpsRepository.get_human_gate: Fetched {len(result)} rows.")
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
            services (List[str]): Service/failure_mode filters.
            metrics (List[str]): Metric filters.
            failure_modes (List[str]): Failure mode filters.
            limit (int): Per-category record limit.

        Returns:
            Dict[str, List[Dict[str, Any]]]: Category-keyed dictionary of retrieved rows.
        """
        # Merge services and failure_modes into one filter list
        all_filters = list(set((services or []) + (failure_modes or [])))
        filter_arg = all_filters if all_filters else services or []

        combined: Dict[str, List[Dict[str, Any]]] = {}
        dispatch = {
            "metrics": lambda: self.get_metrics(filter_arg, metrics, limit),
            "incident": lambda: self.get_incidents(filter_arg, failure_modes, limit),
            "severity": lambda: self.get_severity(filter_arg, limit),
            "forecast": lambda: self.get_forecast(filter_arg, metrics, limit),
            "reliability": lambda: self.get_reliability(filter_arg, limit),
            "feature_contribution": lambda: self.get_feature_contribution(filter_arg, limit),
            "system_health": lambda: self.get_system_health(filter_arg, limit),
            "tumbling_window": lambda: self.get_tumbling_window(filter_arg, limit),
            "human_gate": lambda: self.get_human_gate(filter_arg, limit),
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
