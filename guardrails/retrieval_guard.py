"""
Retrieval Guardrail Module for Query LangGraph (querylanggraph02).

This module runs before database retrieval. It executes query safety checks
and data access control validations on the routing information prior to database execution.
"""

import logging
from typing import Dict, Any, Tuple, List

logger = logging.getLogger("QueryLangGraph.Guardrails.RetrievalGuard")


class RetrievalGuardrail:
    """
    Guardrail before Retrieval Node.

    Responsibilities:
    - Query Safety Check (ensures target tables are restricted to read-only AIOps persistence tables)
    - Data Access Control Check (verifies table access policies and limits parameter bounds)
    """

    ALLOWED_READ_TABLES = {
        # Raw telemetry (schema.sql)
        "metrics",
        "logs",
        "traces",
        "severity",
        # Node output tables (schema.sql)
        "node_feature_engineering",
        "node_preliminary_severity",
        "node_classification",
        "node_tumbling_window",
        "node_forecasting",
        "node_severity_update",
        "node_human_gate",
        # Combinational snapshot (schema.sql)
        "pipeline_results",
    }

    MAX_RETRIEVAL_LIMIT = 5000

    def validate_retrieval_safety(self, routing_info: Dict[str, Any]) -> Tuple[bool, str, str]:
        """
        Validates target tables and retrieval constraints.

        Args:
            routing_info (Dict[str, Any]): Routing metadata output by IntentRouter.

        Returns:
            Tuple[bool, str, str]:
                - is_safe (bool): True if target tables and parameters are safe.
                - violation_type (str): Type of violation if unsafe.
                - message (str): Explanation message.
        """
        if not routing_info or not isinstance(routing_info, dict):
            return False, "invalid_routing", "Routing information is missing or invalid."

        target_tables = routing_info.get("target_tables", [])
        if not target_tables:
            return False, "no_target_tables", "No target tables specified for retrieval."

        # 1. Access Control Check (Table Whitelist)
        for tbl in target_tables:
            if str(tbl).lower() not in self.ALLOWED_READ_TABLES:
                logger.warning(f"RetrievalGuardrail: Unauthorized table access attempt: '{tbl}'")
                return (
                    False,
                    "unauthorized_table_access",
                    f"Security Alert: Table '{tbl}' is not accessible via the persistence retrieval layer."
                )

        # 2. Retrieval Bounds Check
        filters = routing_info.get("filters", {})
        limit = filters.get("limit", 100)
        try:
            limit_val = int(limit)
            if limit_val > self.MAX_RETRIEVAL_LIMIT:
                logger.warning(f"RetrievalGuardrail: Excessive limit requested ({limit_val}).")
                return (
                    False,
                    "retrieval_limit_exceeded",
                    f"Security Alert: Requested retrieval record limit ({limit_val}) exceeds maximum permitted bound ({self.MAX_RETRIEVAL_LIMIT})."
                )
        except (ValueError, TypeError):
            pass

        logger.info("RetrievalGuardrail: Retrieval routing passed safety and access control checks.")
        return True, "none", "Retrieval target routing passed all security checks."

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph node entry point.

        Args:
            state (Dict[str, Any]): QueryState dictionary.

        Returns:
            Dict[str, Any]: Updated QueryState dictionary.
        """
        routing_info = state.get("routing_info", {})
        is_safe, violation_type, detail_msg = self.validate_retrieval_safety(routing_info)

        updated_state = dict(state)
        updated_state["is_safe"] = is_safe
        updated_state["guardrail_stage"] = "retrieval"

        if not is_safe:
            updated_state["error_type"] = "security_violation"
            updated_state["security_violation"] = {
                "guardrail": "retrieval_guard",
                "violation_type": violation_type,
                "message": detail_msg
            }
            updated_state["final_response"] = {
                "status": "security_blocked",
                "error_code": f"SEC_{violation_type.upper()}",
                "message": detail_msg,
                "data": None,
                "metadata": {
                    "stage": "retrieval_guardrail",
                    "passed": False
                }
            }

        return updated_state


def run_retrieval_guard(state: Dict[str, Any]) -> Dict[str, Any]:
    """Functional wrapper for Retrieval Guardrail execution."""
    guard = RetrievalGuardrail()
    return guard.execute(state)
