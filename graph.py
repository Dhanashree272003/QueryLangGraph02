"""
Graph Workflow Module for Query LangGraph (querylanggraph02).

Assembles and compiles the Query LangGraph workflow using LangGraph StateGraph,
wiring all nodes, guardrails, and routers into a production-ready execution graph.
"""

import logging
from typing import Dict, Any

import config  # noqa: F401 — loads .env and sets env vars before any node is imported

from state import QueryState, create_initial_state
from guardrails.parse_guard import run_parse_guard
from nodes.parse_query import run_parse_query
from guardrails.validation_guard import run_validation_guard
from nodes.validation import run_validation
from routers.intent_router import run_intent_router
from guardrails.retrieval_guard import run_retrieval_guard
from nodes.retrieval import run_retrieval
from routers.sufficiency_router import run_sufficiency_router
from guardrails.synthesis_guard import run_synthesis_guard
from nodes.synthesis import run_synthesis
from nodes.respond import run_respond

logger = logging.getLogger("QueryLangGraph.Graph")


# Conditional Edge Decision Functions
def check_parse_guard_edge(state: Dict[str, Any]) -> str:
    """Routes after parse guardrail."""
    return "parse_query" if state.get("is_safe", True) else "respond"


def check_validation_guard_edge(state: Dict[str, Any]) -> str:
    """Routes after validation guardrail."""
    return "validation" if state.get("is_safe", True) else "respond"


def check_validation_node_edge(state: Dict[str, Any]) -> str:
    """Routes after validation node."""
    return "intent_router" if state.get("is_validated", True) else "respond"


def check_retrieval_guard_edge(state: Dict[str, Any]) -> str:
    """Routes after retrieval guardrail."""
    return "retrieval" if state.get("is_safe", True) else "respond"


def check_sufficiency_router_edge(state: Dict[str, Any]) -> str:
    """Routes after sufficiency router."""
    return "synthesis_guard" if state.get("is_sufficient", True) else "respond"


def check_synthesis_guard_edge(state: Dict[str, Any]) -> str:
    """Routes after synthesis guardrail."""
    return "synthesis" if state.get("is_safe", True) else "respond"


def build_query_graph():
    """
    Constructs and compiles the Query LangGraph StateGraph workflow.

    Returns:
        Compiled LangGraph instance (or functional runner wrapper).
    """
    try:
        from langgraph.graph import StateGraph, END

        workflow = StateGraph(QueryState)

        # Add Nodes
        workflow.add_node("parse_guard", run_parse_guard)
        workflow.add_node("parse_query", run_parse_query)
        workflow.add_node("validation_guard", run_validation_guard)
        workflow.add_node("validation", run_validation)
        workflow.add_node("intent_router", run_intent_router)
        workflow.add_node("retrieval_guard", run_retrieval_guard)
        workflow.add_node("retrieval", run_retrieval)
        workflow.add_node("sufficiency_router", run_sufficiency_router)
        workflow.add_node("synthesis_guard", run_synthesis_guard)
        workflow.add_node("synthesis", run_synthesis)
        workflow.add_node("respond", run_respond)

        # Set Entry Point
        workflow.set_entry_point("parse_guard")

        # Wire Conditional Edges
        workflow.add_conditional_edges("parse_guard", check_parse_guard_edge, {"parse_query": "parse_query", "respond": "respond"})
        workflow.add_edge("parse_query", "validation_guard")

        workflow.add_conditional_edges("validation_guard", check_validation_guard_edge, {"validation": "validation", "respond": "respond"})

        workflow.add_conditional_edges("validation", check_validation_node_edge, {"intent_router": "intent_router", "respond": "respond"})

        workflow.add_edge("intent_router", "retrieval_guard")

        workflow.add_conditional_edges("retrieval_guard", check_retrieval_guard_edge, {"retrieval": "retrieval", "respond": "respond"})

        workflow.add_edge("retrieval", "sufficiency_router")

        workflow.add_conditional_edges("sufficiency_router", check_sufficiency_router_edge, {"synthesis_guard": "synthesis_guard", "respond": "respond"})

        workflow.add_conditional_edges("synthesis_guard", check_synthesis_guard_edge, {"synthesis": "synthesis", "respond": "respond"})

        workflow.add_edge("synthesis", "respond")
        workflow.add_edge("respond", END)

        app = workflow.compile()
        logger.info("build_query_graph: Successfully compiled LangGraph workflow using langgraph package.")
        return app

    except ImportError:
        logger.warning("langgraph package not installed. Using pure-Python sequential graph runner fallback.")
        return PurePythonQueryGraphRunner()


class PurePythonQueryGraphRunner:
    """Sequential pure-Python graph execution runner fallback if langgraph package is not installed."""

    def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        curr_state = dict(state)

        # 1. Parse Guard
        curr_state = run_parse_guard(curr_state)
        if not curr_state.get("is_safe", True):
            return run_respond(curr_state)

        # 2. Parse Query Node
        curr_state = run_parse_query(curr_state)

        # 3. Validation Guard
        curr_state = run_validation_guard(curr_state)
        if not curr_state.get("is_safe", True):
            return run_respond(curr_state)

        # 4. Validation Node
        curr_state = run_validation(curr_state)
        if not curr_state.get("is_validated", True):
            return run_respond(curr_state)

        # 5. Intent Router
        curr_state = run_intent_router(curr_state)

        # 6. Retrieval Guard
        curr_state = run_retrieval_guard(curr_state)
        if not curr_state.get("is_safe", True):
            return run_respond(curr_state)

        # 7. Retrieval Node
        curr_state = run_retrieval(curr_state)

        # 8. Sufficiency Router
        curr_state = run_sufficiency_router(curr_state)
        if not curr_state.get("is_sufficient", True):
            return run_respond(curr_state)

        # 9. Synthesis Guard
        curr_state = run_synthesis_guard(curr_state)
        if not curr_state.get("is_safe", True):
            return run_respond(curr_state)

        # 10. Synthesis Node
        curr_state = run_synthesis(curr_state)

        # 11. Respond Node
        return run_respond(curr_state)


def execute_query(user_query: str) -> Dict[str, Any]:
    """
    Main API entry point for executing a natural language query through the Query LangGraph.

    Args:
        user_query (str): The natural language query from the client.

    Returns:
        Dict[str, Any]: Final formatted standardized response payload.
    """
    graph = build_query_graph()
    initial_state = create_initial_state(user_query)

    logger.info(f"execute_query: Processing query: '{user_query}'")
    final_state = graph.invoke(initial_state)

    return final_state.get("final_response", {})


# Compiled graph instance
query_graph_app = build_query_graph()
