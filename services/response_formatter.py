"""
Response Formatter Service for Query LangGraph (querylanggraph02).

This service is the central response assembly engine. It formats all workflow execution
outcomes — successful LLM synthesis, security guardrail blocks, validation errors,
and no-data responses — into a unified, standardized JSON payload.

No business logic. No database access. Pure formatting only.
"""

import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("QueryLangGraph.Services.ResponseFormatter")


class ResponseFormatter:
    """
    Standardized response formatter for Query LangGraph API clients.
    """

    def format_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds a single standardized JSON response from the final QueryState.

        Args:
            state (Dict[str, Any]): The complete QueryState dictionary after graph execution.

        Returns:
            Dict[str, Any]: Unified standardized response schema dictionary.
        """
        start_time = state.get("start_time", time.time())
        execution_time_ms = round((time.time() - start_time) * 1000, 2)

        # 1. Check for Security Violation (Short-circuit response)
        if state.get("error_type") == "security_violation":
            sec_info = state.get("security_violation", {})
            return {
                "status": "security_blocked",
                "error_code": f"SEC_{sec_info.get('violation_type', 'UNKNOWN').upper()}",
                "answer": sec_info.get("message", "Security policy violation detected."),
                "data": None,
                "visualization": None,
                "metadata": {
                    "stage": sec_info.get("guardrail", "guardrail"),
                    "execution_time_ms": execution_time_ms,
                    "passed_guardrails": False
                }
            }

        # 2. Check for Validation Error
        if state.get("error_type") == "validation_error":
            val_info = state.get("validation_error", {})
            return {
                "status": "validation_failed",
                "error_code": val_info.get("error_code", "ERR_VALIDATION_FAILED"),
                "answer": val_info.get("explanation", "Query validation failed."),
                "details": val_info.get("issues", []),
                "suggested_corrections": val_info.get("suggested_corrections", []),
                "data": None,
                "visualization": None,
                "metadata": {
                    "stage": "validation_node",
                    "execution_time_ms": execution_time_ms,
                    "passed_validation": False
                }
            }

        # 3. Check for No Data Available
        if state.get("is_sufficient") is False:
            no_data_info = state.get("no_data_response") or {}
            return {
                "status": "no_data_found",
                "error_code": "WARN_NO_DATA",
                "answer": no_data_info.get("message", "No telemetric or operational data was found."),
                "data": {},
                "visualization": None,
                "metadata": {
                    **state.get("retrieval_metadata", {}),
                    "execution_time_ms": execution_time_ms,
                    "data_found": False
                }
            }

        # 4. Standard Successful Synthesis Response
        answer = state.get("synthesized_answer", "No synthesis answer generated.")
        retrieved_data = state.get("retrieved_data", {})
        retrieval_metadata = state.get("retrieval_metadata", {})
        vis_payload = state.get("visualization_payload")

        # Format visualization metadata for output
        formatted_vis = None
        if vis_payload and vis_payload.get("base64_image"):
            formatted_vis = {
                "base64_image": vis_payload.get("base64_image"),
                "chart_type": vis_payload.get("chart_type", "line"),
                "title": vis_payload.get("title", "AIOps Query Chart"),
                "x_axis": vis_payload.get("x_axis"),
                "y_axis": vis_payload.get("y_axis"),
                "metadata": vis_payload.get("metadata", {})
            }

        return {
            "status": "success",
            "error_code": None,
            "answer": answer,
            "data": retrieved_data,
            "visualization": formatted_vis,
            "metadata": {
                **retrieval_metadata,
                "execution_time_ms": execution_time_ms,
                "query_intent": state.get("query_intent", {}),
                "routing_info": state.get("routing_info", {}),
                "status_code": 200
            }
        }


def format_final_response(state: Dict[str, Any]) -> Dict[str, Any]:
        formatter = ResponseFormatter()
        return formatter.format_response(state)
