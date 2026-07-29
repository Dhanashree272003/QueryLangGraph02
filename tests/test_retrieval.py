"""
Unit Tests for Retrieval Node and Persistence Repository.
"""

import pytest
from persistence.repository import AIOpsRepository
from nodes.retrieval import RetrievalNode


def test_repository_get_metrics():
    repo = AIOpsRepository()
    rows = repo.get_metrics(services=["auth-service"], metrics=["cpu_usage"], limit=10)
    assert isinstance(rows, list)


def test_retrieval_node_execution():
    node = RetrievalNode()
    routing_info = {
        "primary_category": "metrics",
        "all_categories": ["metrics"],
        "target_tables": ["telemetry_metrics"],
        "services": ["auth-service"],
        "metrics": ["cpu_usage"],
        "is_combinational": False
    }
    state = {
        "user_query": "CPU usage of auth-service",
        "routing_info": routing_info,
        "query_intent": {"visualization_request": {"is_requested": False}}
    }
    res = node.execute(state)
    assert "retrieved_data" in res
    assert "retrieval_metadata" in res
