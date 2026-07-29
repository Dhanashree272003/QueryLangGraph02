"""
Respond Node for Query LangGraph (querylanggraph02).

This is the final node in the Query LangGraph execution pipeline.
It receives the formatted standardized response dictionary from ResponseFormatter
and emits it directly to the client/chatbot.

NO processing. NO reasoning. NO validation. NO SQL. NO LLM.
"""

import logging
from typing import Dict, Any

from services.response_formatter import ResponseFormatter

logger = logging.getLogger("QueryLangGraph.Nodes.Respond")


class RespondNode:
    """
    Final output emission node for Query LangGraph.

    Receives the formatted response payload and attaches it to the final state.
    """

    def __init__(self) -> None:
        """Initialize RespondNode with ResponseFormatter instance."""
        self.formatter = ResponseFormatter()

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph node entry point.

        Args:
            state (Dict[str, Any]): QueryState dictionary.

        Returns:
            Dict[str, Any]: Final QueryState with standardized response object.
        """
        logger.info("RespondNode: Formatting final response for client emission.")
        final_payload = self.formatter.format_response(state)

        # Log query into query_history database table for history search
        try:
            from persistence.repository import AIOpsRepository
            repo = AIOpsRepository()
            repo.log_query_history(
                user_query=state.get("user_query", ""),
                session_id=state.get("session_id"),
                parsed_intent=state.get("query_intent"),
                status=final_payload.get("status", "unknown"),
                execution_time_ms=final_payload.get("metadata", {}).get("execution_time_ms", 0.0)
            )
        except Exception as err:
            logger.warning(f"RespondNode: Failed to record query history: {err}")

        updated_state = dict(state)
        updated_state["final_response"] = final_payload
        updated_state["execution_completed"] = True

        logger.info(f"RespondNode: Emitting final response | status={final_payload.get('status')}")
        return updated_state


def run_respond(state: Dict[str, Any]) -> Dict[str, Any]:
    """Functional wrapper for Respond Node execution."""
    node = RespondNode()
    return node.execute(state)
