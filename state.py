"""
State Module for Query LangGraph (querylanggraph02).

Defines the shared QueryState TypedDict passed between guardrails, nodes, and routers
in the Query LangGraph workflow.
"""

import time
from typing import TypedDict, Dict, Any, List, Optional


class QueryState(TypedDict, total=False):
    """
    Shared state dictionary for Query LangGraph execution.
    """
    # Raw input
    user_query: str
    start_time: float

    # Security & Guardrail tracking
    is_safe: bool
    guardrail_stage: Optional[str]  # 'parse', 'validation', 'retrieval', 'synthesis'
    security_violation: Optional[Dict[str, Any]]

    # Parse Query Node outputs
    parsed_successfully: bool
    query_intent: Dict[str, Any]

    # Validation Node outputs
    is_validated: bool
    validation_error: Optional[Dict[str, Any]]

    # Intent Router outputs
    routing_info: Dict[str, Any]

    # Retrieval Node outputs
    retrieved_data: Dict[str, Any]
    retrieval_metadata: Dict[str, Any]
    retrieval_successful: bool
    visualization_payload: Optional[Dict[str, Any]]

    # Sufficiency Router outputs
    is_sufficient: bool
    no_data_response: Optional[Dict[str, Any]]

    # Synthesis Node outputs
    synthesized_answer: Optional[str]
    synthesis_completed: bool

    # Error handling & final payload
    error_type: Optional[str]  # 'security_violation', 'validation_error', 'retrieval_error', etc.
    final_response: Dict[str, Any]
    execution_completed: bool


def create_initial_state(user_query: str) -> QueryState:
    """
    Factory helper to initialize a clean QueryState object.

    Args:
        user_query (str): Raw incoming user question string.

    Returns:
        QueryState: Fresh state dictionary.
    """
    return {
        "user_query": user_query,
        "start_time": time.time(),
        "is_safe": True,
        "guardrail_stage": None,
        "security_violation": None,
        "parsed_successfully": False,
        "query_intent": {},
        "is_validated": False,
        "validation_error": None,
        "routing_info": {},
        "retrieved_data": {},
        "retrieval_metadata": {},
        "retrieval_successful": False,
        "visualization_payload": None,
        "is_sufficient": True,
        "no_data_response": None,
        "synthesized_answer": None,
        "synthesis_completed": False,
        "error_type": None,
        "final_response": {},
        "execution_completed": False
    }
